import tarfile
import zipfile

import zstandard


def list_archive(filepath: str, archive_name: str) -> dict:
    """Return a file tree dict from an archive without extracting files.

    For .zip files the central directory is read directly.  For .tar.zst the
    zstd layer is decompressed but only tar headers are parsed — no file
    contents are written to disk.
    """
    if filepath.endswith(".zip"):
        entries = _list_zip(filepath)
    elif filepath.endswith(".tar.zst"):
        entries = _list_tar_zst(filepath)
    else:
        raise ValueError(f"Unsupported archive format: {filepath}")

    return _build_tree(entries, archive_name)


def _list_zip(filepath: str) -> list[dict]:
    entries = []
    with zipfile.ZipFile(filepath, "r") as zf:
        for info in zf.infolist():
            path = info.filename.rstrip("/")
            if not path:
                continue
            parts = path.split("/")
            entries.append(
                {
                    "name": parts[-1],
                    "path": path,
                    "is_dir": info.is_dir(),
                    "size": info.file_size,
                }
            )
    return entries


def _list_tar_zst(filepath: str) -> list[dict]:
    entries = []
    with open(filepath, "rb") as f:
        dctx = zstandard.ZstdDecompressor()
        reader = dctx.stream_reader(f)
        with tarfile.open(fileobj=reader, mode="r|") as tf:
            for member in tf:
                path = member.name.lstrip("/")
                if not path or member.name in (".", "./"):
                    continue
                parts = path.split("/")
                entries.append(
                    {
                        "name": parts[-1],
                        "path": path,
                        "is_dir": member.isdir(),
                        "size": member.size if not member.isdir() else 0,
                    }
                )
    return entries


def _build_tree(entries: list[dict], root_name: str) -> dict:
    """Build a nested file tree from a flat list of entries.

    Each entry has ``name``, ``path``, ``is_dir``, and ``size``.  Directories
    that are not explicitly listed are created implicitly.
    """
    root = {
        "name": root_name,
        "is_dir": True,
        "size": 0,
        "children": [],
    }
    lookup: dict[str, dict] = {"": root}

    # Sort so directories come before their children
    entries.sort(key=lambda e: (e["path"].count("/"), not e["is_dir"], e["path"]))

    for entry in entries:
        path = entry["path"]
        parent_path = "/".join(path.split("/")[:-1])

        # Ensure parent exists (implicit directory creation)
        if parent_path not in lookup:
            _ensure_dir(lookup, root, parent_path)

        parent = lookup.get(parent_path, root)
        node = {
            "name": entry["name"],
            "path": path,
            "is_dir": entry["is_dir"],
            "size": entry["size"] if not entry["is_dir"] else 0,
            "children": [] if entry["is_dir"] else None,
        }
        parent["children"].append(node)
        _bubble_size(lookup, parent_path, node["size"])

        if entry["is_dir"]:
            lookup[path] = node

    return root


def _ensure_dir(lookup: dict, root: dict, path: str):
    """Create implicit directory nodes for every prefix of *path*."""
    parts = path.split("/")
    for i in range(1, len(parts) + 1):
        sub = "/".join(parts[:i])
        if sub not in lookup:
            parent_path = "/".join(parts[: i - 1])
            parent = lookup.get(parent_path, root)
            node = {
                "name": parts[i - 1],
                "path": sub,
                "is_dir": True,
                "size": 0,
                "children": [],
            }
            parent["children"].append(node)
            lookup[sub] = node


def _bubble_size(lookup: dict, path: str, size: int):
    """Add *size* to *path* and every ancestor."""
    parts = path.split("/") if path else []
    for i in range(len(parts) + 1):
        ancestor = "/".join(parts[:i]) if i > 0 else ""
        node = lookup.get(ancestor)
        if node:
            node["size"] += size
