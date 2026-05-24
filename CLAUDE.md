# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Full-stack archive explorer — users upload `.zip` or `.tar.zst` files, the backend reads metadata without extracting, and the frontend displays a collapsible file tree with sizes. JWT + API key auth with SQLite-backed users.

## Commands

```bash
# Docker (simplest)
docker compose up -d          # backend :8000, frontend :8080

# Backend (Python 3.14+)
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000         # dev server
python -m pytest tests/ -v                        # run tests (includes --cov from pyproject.toml)
python -m pytest tests/ --no-cov -v               # skip coverage for fast runs
python -m pytest tests/test_auth.py::test_login_success -v --no-cov  # single test
ruff check app/                                    # lint
ruff check app/ --fix                              # auto-fix
ruff format app/                                   # format (double-quote style)

# Frontend (Node 25+)
cd frontend
npm run dev                # dev server on :5173, proxies /api → :8000
npm test                   # vitest with coverage
npm test -- -t "FileTree"  # run tests matching pattern
npm run test:watch         # run tests in watch mode
npm run build              # production build to dist/
npm run storybook          # Storybook on :6006

# Convenience
./dev.sh                   # launch tmux session with both dev servers
```

## Architecture

```
backend/                         frontend/
  app/main.py     FastAPI app      src/App.jsx       auth gate (token → dashboard, else login)
  app/auth.py     bcrypt+JWT+API keys  src/pages/     LoginPage, DashboardPage
  app/routers/    API endpoints    src/components/   LoginForm, RegisterForm, UploadZone, FileTree
  app/services/   archive logic    src/api.js        fetch wrapper with JWT interceptor
  app/models.py   User + ApiKey + Job ORM
  app/schemas.py  Pydantic models
  app/config.py   env-driven settings
  app/database.py SQLAlchemy setup
```

**Auth flow**: Register/Login → JWT in localStorage → fetch wrapper attaches `Authorization: Bearer` header. Backend `get_current_user` FastAPI dependency decodes JWT, loads User from DB. The `Request` object is injected as a plain type-hinted parameter (no `Depends()` wrapper — FastAPI auto-injects `Request`). Also supports `X-API-Key` header for programmatic access — API keys are SHA-256 hashed in the DB, generated via `POST /api/auth/api-keys`. When both JWT and API key are present, JWT takes precedence via parameter ordering. On the frontend, `api.js` checks JWT expiry client-side before each request and dispatches an `auth-change` custom event on 401 or expiry — `App.jsx` listens for both `storage` (cross-tab) and `auth-change` (in-tab) events to keep auth state consistent.

**Upload flow**: `UploadZone` sends multipart form-data to `POST /api/archives/upload`. Backend enforces `MAX_UPLOAD_SIZE` (default 500 MB), saves to a random session folder under `uploads/<user_id>/<session_id>/`, reads archive metadata (`.zip` central directory or `.tar.zst` tar headers — no file extraction), builds the tree, persists the result as a `Job` row, deletes the session folder, and returns the tree inline. `FileTree` renders recursive collapsible `<ul>`. `GET /api/archives/history` returns paginated jobs with full tree data.

**Archive service** (`app/services/archive.py`): `list_archive()` reads `.zip` via `zipfile.ZipFile.infolist()` (central directory only) and `.tar.zst` by streaming zstd decompression + parsing tar headers (no file contents written to disk). `_build_tree()` constructs the nested `{name, path, is_dir, size, children}` dict from flat path entries.

**Database**: SQLite via SQLAlchemy 2.0 ORM. `users`, `api_keys`, and `jobs` tables. Uploaded files are ephemeral — saved to a session folder, read for metadata, then deleted. The resulting file tree is persisted in the `jobs` table (JSON column) for history. Tables are auto-created on startup via `Base.metadata.create_all`.

## Key conventions

- B008 ("do not perform function call in argument defaults") is ignored in ruff config — FastAPI uses `Depends()` in function signatures as a standard pattern.
- `bcrypt` is used directly, not via `passlib` (passlib is unmaintained and incompatible with bcrypt ≥ 4.1).
- Frontend Vite dev server proxies `/api` to `localhost:8000`; in Docker, nginx proxies `/api/` to `backend:8000`.
- JWT is handled via `python-jose` (not `pyjwt`); `python-multipart` is required for `UploadFile` parsing.
- `config.py` settings are all env-configurable: `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `UPLOAD_DIR`, `MAX_UPLOAD_SIZE`, and `CORS_ORIGINS` (comma-separated).
- CORS is configured from `CORS_ORIGINS` env var (defaults to both `:5173` for Vite dev and `:8080` for Docker).
- `FileTree` uses `child.path` as the React key (every node has a unique path string from the backend).
- `ruff format` uses double-quote style; line length is 100.
- `pyproject.toml` `[tool.pytest.ini_options]` `addopts` auto-includes `--cov`, so all `pytest` runs produce coverage. Use `--no-cov` for fast iteration on a single test.

### Test architecture

**Backend** (`tests/conftest.py`):
- `tmp_db` fixture creates a temp SQLite DB once per *session*, then `Base.metadata.create_all()` / `drop_all()` around it.
- `client` fixture overrides `get_db` via `app.dependency_overrides` to use the temp DB, yields a `TestClient`, clears overrides after.
- `auth_headers` fixture registers + logs in a test user and returns the `Authorization: Bearer <token>` dict. API key tests pass `X-API-Key` directly.
- `upload_dir` fixture saves+restores `config.UPLOAD_DIR` around a `tempfile.mkdtemp()`, cleaning up after.

**Frontend** (`src/test-setup.js`):
- `localStorage` is mocked with a plain object store so JWT-based auth state works in tests.
- `@testing-library/jest-dom/vitest` provides DOM matchers like `toBeInTheDocument()`.
- Component tests use Vitest + React Testing Library. `api.js` is mocked with `vi.mock` to avoid real HTTP calls.
- Storybook is configured (`npm run storybook`) for isolated component development.
