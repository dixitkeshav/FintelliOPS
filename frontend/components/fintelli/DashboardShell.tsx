'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { useLiveTicker } from '@/hooks/useLiveTicker';
import { useMarketStore } from '@/store/marketStore';
import { useApiHealth } from '@/hooks/useApiHealth';
import { fmtPct, fmtPrice } from '@/lib/fintelli/format';
import { TickerStrip } from './TickerStrip';
import { ThemeDock } from './ThemeDock';

const NAV = [
  {
    section: 'Reasoning Agents',
    items: [
      { href: '/dashboard/learning', icon: '🎓', label: 'Learning Certification' },
      { href: '/dashboard/agents', icon: '🤖', label: 'Financial Agents (Legacy)' },
    ],
  },
];

function marketStatusLabel(status: string) {
  if (status === 'OPEN') return { text: 'Market Open · IST', cls: 'mkt-pill' };
  if (status === 'PRE_MARKET') return { text: 'Pre-Market', cls: 'mkt-pill' };
  if (status === 'AFTER_HOURS') return { text: 'After Hours', cls: 'mkt-pill' };
  return { text: 'Market Closed', cls: 'mkt-pill' };
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  useLiveTicker();
  const indices = useMarketStore((s) => s.indices);
  const marketStatus = useMarketStore((s) => s.marketStatus);
  const { isConnected, isLoading } = useApiHealth();
  const mkt = marketStatusLabel(marketStatus);

  return (
    <>
      <ThemeDock />
      <div className="dash-layout">
        <aside className={`sidebar ${collapsed ? 'coll' : ''}`}>
          <div className="sb-head">
            <div className="sb-logo-icon">E</div>
            <div className="sb-brand">Enterprise Learning</div>
            <button type="button" className="sb-toggle" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar">
              {collapsed ? '▶' : '◀'}
            </button>
          </div>
          <nav className="sb-nav">
            {NAV.map((group) => (
              <div key={group.section}>
                <div className="sb-sec-lbl">{group.section}</div>
                {group.items.map((item) => {
                  const active = pathname === item.href || pathname.startsWith(item.href);
                  return (
                    <Link key={item.href} href={item.href} className={`sb-item ${active ? 'act' : ''}`}>
                      <span className="sb-icon">{item.icon}</span>
                      <span className="sb-lbl">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            ))}
          </nav>
        </aside>

        <div className="dash-main">
          <header className="topbar">
            <div className="tb-search">
              <span style={{ color: 'var(--text-4)', fontSize: 13 }}>🤖</span>
              <input type="text" placeholder="Multi-agent enterprise learning certification system" readOnly />
            </div>
            <div className={mkt.cls}>
              <div className="ldot" />
              {mkt.text}
            </div>
            {!isLoading && (
              <span
                className="badge"
                style={{
                  background: isConnected ? 'var(--green-soft)' : 'var(--red-soft)',
                  color: isConnected ? 'var(--green)' : 'var(--red)',
                }}
              >
                {isConnected ? 'API live' : 'API offline'}
              </span>
            )}
            {indices.slice(0, 4).map((idx) => {
              const up = idx.changePercent >= 0;
              return (
                <div key={idx.symbol} className="tb-ticker">
                  <span className="tb-sym">{idx.symbol}</span>
                  <span className="tb-price">{fmtPrice(idx.price)}</span>
                  <span className={`tb-chg ${up ? 'up' : 'dn'}`}>
                    {up ? '▲' : '▼'}
                    {fmtPct(idx.changePercent)}
                  </span>
                </div>
              );
            })}
          </header>

          <div className="dash-content">{children}</div>
          <TickerStrip />
        </div>
      </div>
    </>
  );
}
