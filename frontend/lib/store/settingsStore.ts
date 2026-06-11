import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type SignalSensitivity = 'conservative' | 'balanced' | 'aggressive';

export interface BrokerConnectionProfile {
  user_shortname?: string;
  user_name?: string;
  user_id?: string;
  email?: string;
}

export const sensitivityToThreshold: Record<SignalSensitivity, number> = {
  conservative: 7,
  balanced: 5,
  aggressive: 3,
};

type EnabledIndicators = {
  vwap: boolean;
  bollingerBands: boolean;
  dema9: boolean;
  dema15: boolean;
  rsi: boolean;
  macd: boolean;
  mfi: boolean;
};

export interface SettingsState {
  broker: string;
  apiKey: string;
  apiSecret: string;
  accessToken: string;
  openAIKey: string;
  telegramBotToken: string;
  telegramChatId: string;
  signalSensitivity: SignalSensitivity;
  enabledIndicators: EnabledIndicators;
  soundAlerts: boolean;
  watchlist: string[];
  isConnected: boolean;
  connectionProfile: BrokerConnectionProfile | null;
  connectionFunds: { available: number; used: number } | null;

  updateSettings: (partial: Partial<SettingsState>) => void;
  saveToLocalStorage: () => void;
  loadFromLocalStorage: () => void;
}

type PersistedSlice = Omit<SettingsState, 'updateSettings' | 'saveToLocalStorage' | 'loadFromLocalStorage'>;

function encodeToken(raw: string): string {
  // Minimal obfuscation only (NOT encryption). For production use encrypted storage or server-side secrets.
  try {
    return typeof window === 'undefined' ? raw : btoa(unescape(encodeURIComponent(raw)));
  } catch {
    return raw;
  }
}

function decodeToken(encoded: string): string {
  try {
    return typeof window === 'undefined' ? encoded : decodeURIComponent(escape(atob(encoded)));
  } catch {
    return encoded;
  }
}

const STORAGE_KEY = 'edge_settings_v1';

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, _get) => ({
      broker: 'zerodha',
      apiKey: '',
      apiSecret: '',
      accessToken: '',
      openAIKey: '',
      telegramBotToken: '',
      telegramChatId: '',
      signalSensitivity: 'balanced',
      enabledIndicators: {
        vwap: true,
        bollingerBands: true,
        dema9: true,
        dema15: true,
        rsi: true,
        macd: true,
        mfi: true,
      },
      soundAlerts: true,
      watchlist: [],
      isConnected: false,
      connectionProfile: null,
      connectionFunds: null,

      updateSettings: (partial) => set(partial),

      saveToLocalStorage: () => {
        // `persist` already saves on changes; this is an explicit affordance for the UI.
        set({} as Partial<SettingsState>);
      },

      loadFromLocalStorage: () => {
        // `persist` rehydrates automatically on first load; this just forces rehydrate in UI flows.
        const withPersist = useSettingsStore as unknown as { persist?: { rehydrate?: () => void } };
        withPersist.persist?.rehydrate?.();
      },
    }),
    {
      name: STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state): PersistedSlice => ({
        ...state,
        accessToken: encodeToken(state.accessToken),
      }),
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        state.accessToken = decodeToken(state.accessToken);
      },
    }
  )
);

