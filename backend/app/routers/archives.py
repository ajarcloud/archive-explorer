import asyncio
import os
import re
import shutil
import uuid
from datetime import UTC, datetime

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import MAX_UPLOAD_SIZE, UPLOAD_DIR
from ..database import get_db
from ..models import Job, User
from ..schemas import JobDetail
from ..services.archive import list_archive

router = APIRouter()

_TIMESTAMP_RE = re.compile(r"(\d{4}[-_]?\d{2}[-_]?\d{2}[_T]?\d{2}[-:]?\d{2}[-:]?\d{2})")
_DATE_RE = re.compile(r"(\d{4}[-_]?\d{2}[-_]?\d{2})")


def _extract_job_id(filename: str) -> str:
    """Pull a date+time from *filename* to use as job_id, or append upload time."""
    for ext in (".tar.zst", ".zip"):
        if filename.endswith(ext):
            stem = filename[: -len(ext)]
            break
    else:
        stem = filename

    m = _TIMESTAMP_RE.search(stem)
    if m:
        return m.group(1)

    m = _DATE_RE.search(stem)
    if m:
        return m.group(1)

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%S")
    return f"{stem}_{now}"


def _count_files(node: dict) -> int:
    if not node.get("children"):
        return 0 if node["is_dir"] else 1
    return sum(_count_files(c) for c in node["children"])


@router.post("/upload")
async def upload_archive(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file selected")

    if not (file.filename.endswith(".zip") or file.filename.endswith(".tar.zst")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .zip and .tar.zst files are supported",
        )

    session_id = uuid.uuid4().hex
    archive_id = uuid.uuid4().hex[:12]
    ext = ".tar.zst" if file.filename.endswith(".tar.zst") else ".zip"
    root_name = file.filename.removesuffix(ext)
    session_dir = os.path.join(UPLOAD_DIR, str(current_user.id), session_id)
    archive_path = os.path.join(session_dir, f"{archive_id}{ext}")

    os.makedirs(session_dir, exist_ok=True)

    try:
        total = 0
        async with aiofiles.open(archive_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
                    )
                await f.write(chunk)

        tree = await asyncio.to_thread(list_archive, archive_path, root_name)
    except Exception as e:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)

    tree["archive_id"] = archive_id

    job_id = _extract_job_id(file.filename)
    job = Job(
        job_id=job_id,
        user_id=current_user.id,
        archive_name=root_name,
        archive_id=archive_id,
        tree=tree,
    )
    db.add(job)
    db.commit()

    shutil.rmtree(session_dir, ignore_errors=True)

    return tree


@router.get("/history")
def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    rows = (
        db.execute(
            select(Job)
            .where(Job.user_id == current_user.id)
            .order_by(Job.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        .scalars()
        .all()
    )

    return [
        JobDetail(
            job_id=r.job_id,
            archive_name=r.archive_name,
            archive_id=r.archive_id,
            size=r.tree["size"],
            file_count=_count_files(r.tree),
            created_at=r.created_at,
            tree=r.tree,
        )
        for r in rows
    ]
