import 'server-only';

import type { BrokerClient } from './contract';
import { ZerodhaKiteBroker } from './providers/zerodha-kite';

/** Matches settings UI dropdown — swap by config / env (`EDGE_BROKER`). */
export type BrokerRegistryId = 'ZERODHA' | 'UPSTOX' | 'FYERS' | 'ANGEL_ONE' | 'CUSTOM';

const REGISTRY_IDS: BrokerRegistryId[] = ['ZERODHA', 'UPSTOX', 'FYERS', 'ANGEL_ONE', 'CUSTOM'];

export function normalizeBrokerRegistryId(raw: string | undefined | null): BrokerRegistryId {
  const id = String(raw ?? 'ZERODHA').trim().toUpperCase() as BrokerRegistryId;
  if (!REGISTRY_IDS.includes(id)) {
    throw new Error(`Unknown EDGE_BROKER "${raw}". Expected one of: ${REGISTRY_IDS.join(', ')}`);
  }
  return id;
}

export function brokerIdFromEnv(): BrokerRegistryId {
  return normalizeBrokerRegistryId(process.env.EDGE_BROKER);
}

/**
 * Factory for executable broker adapters (Node-only; uses kiteconnect for Zerodha).
 */
export function createBroker(registryId?: BrokerRegistryId): BrokerClient {
  const id = registryId ?? brokerIdFromEnv();
  switch (id) {
    case 'ZERODHA':
      return new ZerodhaKiteBroker();
    default:
      throw new Error(
        `Broker "${id}" adapter not implemented yet — add ./providers and wire createBroker server factory.`
      );
  }
}
