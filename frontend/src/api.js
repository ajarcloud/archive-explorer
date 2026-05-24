const BASE_URL = '/api';

function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

async function request(method, path, {body, params, signal} = {}) {
  const headers = {};
  const token = localStorage.getItem('token');
  if (token) {
    if (isTokenExpired(token)) {
      localStorage.removeItem('token');
      window.dispatchEvent(new Event('auth-change'));
      const err = new Error('Session expired');
      err.status = 401;
      throw err;
    }
    headers.Authorization = `Bearer ${token}`;
  }

  let url = `${BASE_URL}${path}`;
  if (params) {
    url += '?' + new URLSearchParams(params);
  }

  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, {
    method,
    headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    signal,
  });

  if (res.status === 401) {
    localStorage.removeItem('token');
    window.dispatchEvent(new Event('auth-change'));
    const err = new Error('Unauthorized');
    err.status = 401;
    throw err;
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const err = new Error(data.detail || res.statusText);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  if (res.status === 204) return null;
  return res.json();
}

const api = {
  get: (path, opts) => request('GET', path, opts),
  post: (path, body, opts) => request('POST', path, {...opts, body}),
  put: (path, body, opts) => request('PUT', path, {...opts, body}),
  delete: (path, opts) => request('DELETE', path, opts),
};

export default api;
