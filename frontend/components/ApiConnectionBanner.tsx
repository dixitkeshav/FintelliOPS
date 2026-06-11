'use client';

import { useApiHealth } from '@/hooks/useApiHealth';

export function ApiConnectionBanner() {
  const { isConnected, message, backendUrl, isLoading, refetch } = useApiHealth();

  if (isLoading) {
    return (
      <div style={{ margin: '0 0 14px', padding: 12, borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-inset)', fontSize: 13, color: 'var(--text-3)' }}>
        Connecting to Django API at {backendUrl}…
      </div>
    );
  }

  if (isConnected) return null;

  return (
    <div
      style={{
        margin: '0 0 14px',
        padding: 14,
        borderRadius: 10,
        border: '1px solid var(--red)',
        background: 'var(--red-soft)',
        display: 'flex',
        flexWrap: 'wrap',
        gap: 12,
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <div>
        <p style={{ fontWeight: 600, color: 'var(--red)', fontSize: 13 }}>Backend API not connected</p>
        <p style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4 }}>
          {message || `Cannot reach ${backendUrl}`}. Start Django:{' '}
          <code style={{ background: 'var(--bg-surface)', padding: '2px 6px', borderRadius: 4 }}>
            cd backend && python manage.py runserver
          </code>
        </p>
      </div>
      <button type="button" className="btn-ghost" onClick={() => refetch()}>
        Retry
      </button>
    </div>
  );
}

export function ApiConnectionBadge() {
  return null;
}
