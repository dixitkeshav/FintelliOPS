import 'server-only';

import type { BrokerAdapter, BrokerConfig } from './types';
import { ZerodhaAdapter } from './zerodha';
import { UpstoxAdapter } from './upstox';

export * from './types';

export function createBrokerAdapter(broker: string): BrokerAdapter {
  switch (broker) {
    case 'zerodha':
      return new ZerodhaAdapter();
    case 'upstox':
      return new UpstoxAdapter();
    default:
      throw new Error(`Broker ${broker} not yet supported`);
  }
}

// Singleton instance stored in module scope (process lifetime)
let activeAdapter: BrokerAdapter | null = null;

export function getActiveAdapter(): BrokerAdapter {
  if (!activeAdapter) throw new Error('No broker connected');
  return activeAdapter;
}

export function setActiveAdapter(adapter: BrokerAdapter | null) {
  activeAdapter = adapter;
}

let lastBrokerConfig: BrokerConfig | null = null;

export function setLastBrokerConfig(config: BrokerConfig | null) {
  lastBrokerConfig = config;
}

export function getLastBrokerConfig(): BrokerConfig | null {
  return lastBrokerConfig;
}
