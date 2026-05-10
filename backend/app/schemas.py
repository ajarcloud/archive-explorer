from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApiKeyCreate(BaseModel):
    name: str | None = None


class ApiKeyCreated(BaseModel):
    raw_key: str
    prefix: str
    name: str | None
    id: int
    created_at: datetime


class ApiKeyInfo(BaseModel):
    id: int
    prefix: str
    name: str | None
    created_at: datetime
    last_used_at: datetime | None


class FileNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    children: list[FileNode] | None = None


class ArchiveTree(BaseModel):
    archive_id: str
    name: str
    is_dir: bool
    size: int
    children: list[FileNode]


class JobSummary(BaseModel):
    job_id: str
    archive_name: str
    archive_id: str
    size: int
    file_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDetail(JobSummary):
    tree: ArchiveTree
