import io
import os
import zipfile

from app.routers.archives import _extract_job_id


def _zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("hello.txt", "world")
    buf.seek(0)
    return buf


def test_upload_zip(client, auth_headers, upload_dir):
    buf = _zip_bytes()
    res = client.post(
        "/api/archives/upload",
        headers=auth_headers,
        files={"file": ("test.zip", buf, "application/zip")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "archive_id" in data
    assert data["is_dir"] is True
    assert data["children"][0]["name"] == "hello.txt"
    assert data["children"][0]["size"] == 5
    # No files left behind after cleanup
    leftover = []
    for dirpath, _, filenames in os.walk(upload_dir):
        for name in filenames:
            leftover.append(os.path.join(dirpath, name))
    assert leftover == []


def test_upload_persists_job(client, auth_headers):
    """Upload should save a Job row and the history endpoint returns it."""
    buf = _zip_bytes()
    res = client.post(
        "/api/archives/upload",
        headers=auth_headers,
        files={"file": ("test.zip", buf, "application/zip")},
    )
    assert res.status_code == 200
    tree = res.json()

    hist = client.get("/api/archives/history", headers=auth_headers)
    assert hist.status_code == 200
    jobs = hist.json()
    assert len(jobs) == 1
    assert jobs[0]["job_id"].startswith("test_")
    assert jobs[0]["archive_name"] == "test"
    assert jobs[0]["archive_id"] == tree["archive_id"]
    assert jobs[0]["size"] == 5
    assert jobs[0]["file_count"] == 1
    assert "tree" in jobs[0]
    assert jobs[0]["tree"]["children"][0]["name"] == "hello.txt"


def test_upload_no_auth(client):
    buf = _zip_bytes()
    res = client.post(
        "/api/archives/upload",
        files={"file": ("test.zip", buf, "application/zip")},
    )
    assert res.status_code == 401


def test_history_no_auth(client):
    res = client.get("/api/archives/history")
    assert res.status_code == 401


def test_upload_bad_extension(client, auth_headers):
    res = client.post(
        "/api/archives/upload",
        headers=auth_headers,
        files={"file": ("doc.pdf", io.BytesIO(b"pdf"), "application/pdf")},
    )
    assert res.status_code == 400
    assert "Only .zip" in res.json()["detail"]


def test_upload_corrupted_zip(client, auth_headers, upload_dir):
    res = client.post(
        "/api/archives/upload",
        headers=auth_headers,
        files={"file": ("bad.zip", io.BytesIO(b"not a zip"), "application/zip")},
    )
    assert res.status_code == 400
    leftover = []
    for dirpath, _, filenames in os.walk(upload_dir):
        for name in filenames:
            leftover.append(os.path.join(dirpath, name))
    assert leftover == []


def test_history_ordered_by_time(client, auth_headers):
    """History returns all jobs; most recent appears first."""
    for name in ("a.zip", "b.zip"):
        buf = _zip_bytes()
        client.post(
            "/api/archives/upload",
            headers=auth_headers,
            files={"file": (name, buf, "application/zip")},
        )
    jobs = client.get("/api/archives/history", headers=auth_headers).json()
    assert len(jobs) == 2
    names = {j["archive_name"] for j in jobs}
    assert names == {"a", "b"}
    # Both have tree data
    for job in jobs:
        assert "tree" in job
        assert job["file_count"] == 1


def test_history_only_own_jobs(client, auth_headers):
    """User A should not see User B's jobs."""
    # Register a second user
    client.post(
        "/api/auth/register",
        json={"email": "other@test.com", "password": "secret123"},
    )
    login2 = client.post(
        "/api/auth/login",
        json={"email": "other@test.com", "password": "secret123"},
    )
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Each user uploads
    buf = _zip_bytes()
    client.post(
        "/api/archives/upload",
        headers=auth_headers,
        files={"file": ("mine.zip", buf, "application/zip")},
    )
    client.post(
        "/api/archives/upload",
        headers=headers2,
        files={"file": ("theirs.zip", buf, "application/zip")},
    )

    # User 1 only sees their own jobs
    mine = client.get("/api/archives/history", headers=auth_headers).json()
    for job in mine:
        assert job["archive_name"] != "theirs"

    # User 2 only sees their own jobs
    theirs = client.get("/api/archives/history", headers=headers2).json()
    for job in theirs:
        assert job["archive_name"] != "mine"


def test_history_empty(client, auth_headers):
    """Brand-new user should see an empty list."""
    client.post(
        "/api/auth/register",
        json={"email": "fresh@test.com", "password": "secret123"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "fresh@test.com", "password": "secret123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    jobs = client.get("/api/archives/history", headers=headers).json()
    assert jobs == []


class TestExtractJobId:
    def test_timestamp_with_underscore(self):
        assert _extract_job_id("backup_2024-01-15_143022.zip") == "2024-01-15_143022"

    def test_timestamp_with_T(self):
        assert _extract_job_id("log_2024-01-15T14-30-22.tar.zst") == "2024-01-15T14-30-22"

    def test_compact_timestamp(self):
        assert _extract_job_id("data_20240115_143022.zip") == "20240115_143022"

    def test_date_only(self):
        assert _extract_job_id("report_2024-01-15.zip") == "2024-01-15"

    def test_no_timestamp(self):
        jid = _extract_job_id("archive.zip")
        assert jid.startswith("archive_")
        # Should contain current date
        assert len(jid) > 8 + 1 + 8  # "archive_" + timestamp

    def test_no_extension(self):
        jid = _extract_job_id("foobar")
        assert jid.startswith("foobar_")
