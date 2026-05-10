import io
import os
import tempfile
import zipfile

from app.services.archive import list_archive


def _write_zip(path: str) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("readme.txt", "hello")
        zf.writestr("subdir/data.txt", "nested")


def test_list_zip():
    tmp = tempfile.mkdtemp()
    zip_path = os.path.join(tmp, "test.zip")
    _write_zip(zip_path)

    tree = list_archive(zip_path, "test")
    assert tree["name"] == "test"
    assert tree["is_dir"] is True
    assert tree["size"] == 11  # 5 + 6
    names = {c["name"] for c in tree["children"]}
    assert names == {"readme.txt", "subdir"}

    subdir = next(c for c in tree["children"] if c["name"] == "subdir")
    assert subdir["is_dir"] is True
    assert subdir["size"] == 6
    assert subdir["children"][0]["name"] == "data.txt"
    assert subdir["children"][0]["size"] == 6

    os.remove(zip_path)
    os.rmdir(tmp)


def test_list_unsupported():
    try:
        list_archive("file.rar", "name")
    except ValueError as e:
        assert "Unsupported" in str(e)


def test_list_zip_empty():
    tmp = tempfile.mkdtemp()
    zip_path = os.path.join(tmp, "empty.zip")
    with zipfile.ZipFile(zip_path, "w"):
        pass  # empty archive

    tree = list_archive(zip_path, "empty")
    assert tree["name"] == "empty"
    assert tree["children"] == []
    assert tree["size"] == 0

    os.remove(zip_path)
    os.rmdir(tmp)


def test_list_zip_implicit_dirs():
    """Directories not explicitly listed as entries should be created implicitly."""
    tmp = tempfile.mkdtemp()
    zip_path = os.path.join(tmp, "flat.zip")
    # Write a file with a directory path but no explicit dir entry.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("a/b/c.txt", "deep")
    buf.seek(0)
    with open(zip_path, "wb") as f:
        f.write(buf.read())

    tree = list_archive(zip_path, "flat")
    assert tree["children"][0]["name"] == "a"
    assert tree["children"][0]["is_dir"] is True
    assert tree["children"][0]["children"][0]["name"] == "b"
    assert tree["children"][0]["children"][0]["children"][0]["name"] == "c.txt"

    os.remove(zip_path)
    os.rmdir(tmp)
