/** WebSocket base URL — connects directly to Django ASGI (daphne), not Next proxy. */
export function shockWebSocketUrl(): string {
  const base =
    process.env.NEXT_PUBLIC_WS_URL?.replace(/\/$/, '') || 'ws://127.0.0.1:8000';
  const wsBase = base.replace(/^http/, 'ws');
  return `${wsBase}/ws/shock/`;
}
