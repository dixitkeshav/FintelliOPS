'use client';

import { DashboardShell } from '@/components/fintelli/DashboardShell';
import { ApiConnectionBanner } from '@/components/ApiConnectionBanner';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardShell>
      <ApiConnectionBanner />
      {children}
    </DashboardShell>
  );
}
