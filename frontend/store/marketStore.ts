import { create } from 'zustand';

interface MarketData {
  symbol: string;
  rawSymbol?: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

interface MarketState {
  indices: MarketData[];
  selectedSymbol: string | null;
  marketStatus: 'OPEN' | 'CLOSED' | 'PRE_MARKET' | 'AFTER_HOURS';
  setIndices: (indices: MarketData[]) => void;
  updateIndex: (symbol: string, data: Partial<MarketData>) => void;
  setSelectedSymbol: (symbol: string | null) => void;
  setMarketStatus: (status: MarketState['marketStatus']) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  indices: [
    { symbol: 'NIFTY', rawSymbol: '^NSEI', price: 23850.45, change: 125.30, changePercent: 0.53, volume: 125000000 },
    { symbol: 'SENSEX', rawSymbol: '^BSESN', price: 78923.12, change: -85.67, changePercent: -0.11, volume: 95000000 },
    { symbol: 'BTC', rawSymbol: 'BTC-USD', price: 52345.78, change: 1234.56, changePercent: 2.41, volume: 28000000000 },
    { symbol: 'GOLD', rawSymbol: 'GC=F', price: 2145.30, change: -12.45, changePercent: -0.58, volume: 15000000 },
  ],
  selectedSymbol: null,
  marketStatus: 'OPEN',
  setIndices: (indices) => set({ indices }),
  updateIndex: (symbol, data) =>
    set((state) => ({
      indices: state.indices.map((index) =>
        index.symbol === symbol ? { ...index, ...data } : index
      ),
    })),
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
  setMarketStatus: (status) => set({ marketStatus: status }),
}));
