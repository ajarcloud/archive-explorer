# Code Review & Changes — 2026-05-24

## Review Summary

Full review of the Archive Explorer codebase (backend + frontend). Found 8 issues across both stacks — 3 bugs, 5 missing features/enhancements. All fixed with **55 passing tests** (38 backend, 17 frontend).

---

## Findings & Fixes

### 🔴 Bug: FastAPI `Request` injection unreliable

**File:** `backend/app/auth.py:37`

`request: Request = None` — FastAPI may not inject `Request` when the parameter has a default of `None`. Also, `None`-guarding with `if request else None` on the API key path was fragile.

**Fix:** Removed default value and reordered parameters so `request: Request` comes first (non-default before default). FastAPI auto-injects `Request` by type. Removed the `if request` guard.

```diff
-    request: Request = None,
+    request: Request,
...
-    api_key = request.headers.get("X-API-Key") if request else None
+    api_key = request.headers.get("X-API-Key")
```

---

### 🟡 Bug: Hard browser redirect breaks SPA

**File:** `frontend/src/api.js:32`

On 401, `window.location.href = '/login'` performs a full browser navigation, tearing down the React tree and losing in-memory state.

**Fix:** Replaced with a custom event dispatch:

```diff
-    window.location.href = '/login';
+    window.dispatchEvent(new Event('auth-change'));
```

`App.jsx` now also listens for `auth-change` alongside the existing `storage` event (used for cross-tab sync), so auth state stays consistent within and across tabs.

---

### 🟡 Bug: React index-as-fallback key

**File:** `frontend/src/components/FileTree.jsx`

`key={child.path || i}` — using array index as a fallback key causes incorrect React reconciliation when tree nodes are reordered or added/removed.

**Fix:** Removed the fallback. Every node produced by the backend (`_build_tree` / `_ensure_dir`) always has a unique `path` string, so the fallback is unnecessary.

```diff
-          {node.children.map((child, i) => (
-            <TreeNode key={child.path || i} node={child} />
+          {node.children.map((child) => (
+            <TreeNode key={child.path} node={child} />
```

---

### 🟡 Missing: CORS hardcoded to dev origin only

**File:** `backend/app/main.py:12`

CORS was hardcoded to `http://localhost:5173`. Docker users on `:8080` and production deployments had no CORS coverage.

**Fix:** Made it configurable via `CORS_ORIGINS` env var, defaulting to both dev and Docker ports:

```python
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:8080",
).split(",")
```

---

### 🟡 Missing: No upload file size limit

**Files:** `backend/app/config.py`, `backend/app/routers/archives.py`

Unbounded file uploads could exhaust disk space or memory.

**Fix:** Added `MAX_UPLOAD_SIZE` env var (default 500 MB). The upload endpoint tracks total bytes read and returns `413 Request Entity Too Large` if exceeded.

---

### 🟡 Missing: `JWT_EXPIRE_MINUTES` not configurable

**File:** `backend/app/config.py`

Token expiry was hardcoded to `60 * 24` (1440 minutes). No way to change it without editing code.

**Fix:**

```diff
- JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours
+ JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours
```

---

### 🟡 Missing: No client-side JWT expiry check

**File:** `frontend/src/api.js`

Expired JWTs would be sent to the server, always getting a 401. The user would see a flash of error before redirect.

**Fix:** Added `isTokenExpired()` helper that decodes the JWT payload (base64, no library needed) and checks the `exp` claim. If expired, it clears the token and dispatches `auth-change` before any network request:

```javascript
function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}
```

---

## New Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE` | `524288000` | Max upload size in bytes (500 MB) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080` | Comma-separated allowed origins |

Previously existing but now documented as configurable:

| Variable | Default | Notes |
|----------|---------|-------|
| `JWT_EXPIRE_MINUTES` | `1440` | Was hardcoded, now reads from env |

---

## Files Changed

| File | Type |
|------|------|
| `backend/app/auth.py` | Bug fix — `Request` injection |
| `backend/app/main.py` | Feature — configurable CORS |
| `backend/app/config.py` | Feature — `JWT_EXPIRE_MINUTES` + `MAX_UPLOAD_SIZE` |
| `backend/app/routers/archives.py` | Feature — file size enforcement |
| `frontend/src/api.js` | Bug fix + feature — SPA-safe redirect, JWT expiry |
| `frontend/src/App.jsx` | Feature — `auth-change` event listener |
| `frontend/src/components/FileTree.jsx` | Bug fix — React key |
| `README.md` | Docs — API table, config table, test count |
| `CLAUDE.md` | Docs — architecture, auth flow, conventions |

---

## Test Results

```
Backend:  38 passed (was 38 — no regressions)
Frontend: 17 passed (was 17 — no regressions)
Total:    55 passed
```
