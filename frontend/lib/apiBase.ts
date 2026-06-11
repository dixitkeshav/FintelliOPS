/**
 * Django API base URL. In the browser we route through Next.js `/api/proxy` so
 * requests stay same-origin (no CORS) and work when the backend is on another host.
 */
const DJANGO_ORIGIN =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8000';

export function djangoApiUrl(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  if (typeof window !== 'undefined') {
    return `/api/proxy${normalized}`;
  }
  return `${DJANGO_ORIGIN}${normalized}`;
}

export function djangoOrigin(): string {
  return DJANGO_ORIGIN;
}
