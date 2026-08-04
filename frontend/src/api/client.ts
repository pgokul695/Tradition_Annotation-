// Production talks directly to the Cloudflare-tunnel backend; local Vite keeps
// using its /api proxy when no production value is supplied.
const API = import.meta.env.VITE_API_BASE_URL || '/api';

export const get = (path: string) =>
  fetch(API + path).then(r => r.json());

export const post = (path: string, body?: unknown) =>
  fetch(API + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  }).then(r => r.json());

export const patch = (path: string, body: unknown) =>
  fetch(API + path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => r.json());

export const imageUrl = (path: string) =>
  '/dataset/' + path.replace(/^dataset\//, '');
