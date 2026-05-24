# Archive Explorer

Full-stack app for uploading and browsing archive files (`.zip`, `.tar.zst`) without full extraction. JWT + API key authentication, SQLite-backed.

## Quick start

### Docker (simplest)

```bash
docker compose up -d
# Frontend: http://localhost:8080
# Backend:  http://localhost:8000
```

### Local development

**Prerequisites**: Python 3.14+, Node 25+

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173 (proxies /api → :8000)
```

Or launch both in a tmux session:

```bash
./dev.sh
```

## Project structure

```
├── dev.sh                       Tmux session with both dev servers
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI entry, CORS, router registration
│   │   ├── auth.py              Password hashing, JWT + API key auth
│   │   ├── config.py            DATABASE_URL, JWT_SECRET, UPLOAD_DIR (env-driven)
│   │   ├── database.py          SQLAlchemy engine, session factory
│   │   ├── models.py            User + ApiKey + Job ORM models
│   │   ├── schemas.py           Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── auth.py          POST register/login/api-keys, GET me/api-keys
│   │   │   └── archives.py      POST /api/archives/upload, GET /api/archives/history
│   │   └── services/
│   │       └── archive.py       List archive contents without extraction
│   ├── tests/                   pytest suite with TestClient
│   ├── requirements.txt
│   ├── pyproject.toml           Ruff + pytest config
│   └── Dockerfile
├── frontend/
│   ├── .storybook/              Storybook configuration
│   ├── src/
│   │   ├── App.jsx              Auth gate (token → Dashboard, else → Login)
│   │   ├── api.js               Fetch wrapper, JWT interceptor
│   │   ├── test-setup.js        localStorage mock + jest-dom matchers
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx    Login / Register toggle
│   │   │   └── DashboardPage.jsx
│   │   ├── components/
│   │   │   ├── LoginForm.jsx
│   │   │   ├── RegisterForm.jsx
│   │   │   ├── UploadZone.jsx   Drag-and-drop + file input
│   │   │   └── FileTree.jsx     Recursive collapsible tree with sizes
│   │   └── __tests__/           Vitest + React Testing Library suite
│   ├── index.html
│   ├── vite.config.js           Dev proxy /api → :8000
│   ├── vitest.config.js         jsdom + v8 coverage
│   ├── nginx.conf               Production reverse proxy
│   └── Dockerfile               Multi-stage (Node build → nginx serve)
├── CLAUDE.md
└── README.md
```

## API

Base URL: `http://localhost:8000/api`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | No | `{email, password}` → `{access_token}` |
| `POST` | `/auth/login` | No | `{email, password}` → `{access_token}` |
| `GET` | `/auth/me` | Yes | Current user `{id, email}` |
| `POST` | `/auth/api-keys` | Yes | `{name?}` → `{raw_key, prefix, id}` (raw key returned once) |
| `GET` | `/auth/api-keys` | Yes | List API keys (prefix + metadata, no raw key) |
| `DELETE` | `/auth/api-keys/{id}` | Yes | Revoke an API key |
| `GET` | `/health` | No | Health check |
| `GET` | `/archives/history` | Yes | List previously uploaded archives (paginated via `?limit=&offset=`) |
| `POST` | `/archives/upload` | Yes | Multipart `file` (.zip or .tar.zst) → file tree JSON (also persisted to history) |

The upload response is a recursive tree:

```json
{
  "archive_id": "abc123",
  "name": "myarchive",
  "is_dir": true,
  "size": 1024,
  "children": [
    { "name": "readme.md", "path": "abc123/readme.md", "is_dir": false, "size": 512, "children": null },
    { "name": "src", "path": "abc123/src", "is_dir": true, "size": 512, "children": [...] }
  ]
}
```

Auth for all protected endpoints accepts either `Authorization: Bearer <jwt>` or `X-API-Key: <api-key>`. When both are present, JWT takes precedence.

## Configuration

Backend environment variables (set in `docker-compose.yml` or shell):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///backend/app.db` | SQLAlchemy connection string |
| `JWT_SECRET` | `dev-secret-...` | JWT signing key |
| `JWT_EXPIRE_MINUTES` | `1440` | Token expiry in minutes (24h) |
| `UPLOAD_DIR` | `backend/uploads/` | Temp session folder root (auto-cleaned) |
| `MAX_UPLOAD_SIZE` | `524288000` | Max upload size in bytes (500 MB) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | Comma-separated allowed origins |

## Testing

```bash
# Backend — 38 tests, 91% coverage
cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend — 17 tests, ~62% coverage
cd frontend && npm test

# Single test / fast iteration
python -m pytest tests/test_auth.py::test_login_success -v  # --cov added by default; use --no-cov for speed
npm test -- -t "FileTree"
npm run test:watch                                           # vitest watch mode
npm run test:ui                                              # vitest UI
```

Backend tests use a temp SQLite database and FastAPI `dependency_overrides` to swap in test sessions. Frontend tests mock `api.js` with Vitest and use React Testing Library for component rendering. Storybook is available for isolated component development (`npm run storybook`).

## Linting

```bash
cd backend
ruff check app/        # lint
ruff check app/ --fix  # auto-fix
ruff format app/       # format
```

Rules: `E, F, I, N, W, UP, B, C4, SIM`. B008 is ignored (FastAPI's `Depends()` in defaults is standard). Line length: 100.
