# FintelliAI - Financial Intelligence Platform Frontend

A modern, dark-themed financial intelligence dashboard built with Next.js 15, featuring real-time market data, AI-powered insights, and TradingView-style charts.

## 🚀 Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Charts**: Recharts
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Build Tool**: Turbopack
- **Real-time**: WebSockets

## 📋 Features

### 🎨 Design
- Dark mode primary theme with glassmorphism effects
- Neon accent colors (green/red) for price movements
- Professional typography (Inter font family)
- Dense but readable data-first layout
- Smooth micro-animations and transitions

### 📊 Dashboard Components

1. **Top Navigation Bar**
   - Global search for stocks, indices, and news
   - Market status indicator (OPEN/CLOSED/PRE_MARKET/AFTER_HOURS)
   - Mini price widgets for major indices (NIFTY, SENSEX, BTC, GOLD)
   - User profile and notifications

2. **Left Sidebar**
   - Collapsible navigation menu
   - Quick access to all platform sections
   - Professional branding

3. **Live Market Chart (TradingView-style)**
   - Large candlestick/area chart
   - Multiple timeframe options (1D, 1W, 1M, 3M, 1Y, ALL)
   - Volume bars
   - Hover tooltips with price details
   - Responsive chart container

4. **AI Agent Insights**
   - Four intelligent agents:
     - **Sentiment Agent**: News sentiment analysis
     - **Risk Agent**: Volatility and risk assessment
     - **Macro Agent**: Economic indicators and trends
     - **Market Reaction Agent**: Options flow and positioning
   - Signal strength indicators (BULLISH/BEARISH/NEUTRAL)
   - Confidence percentages
   - LLM-generated explanations
   - Real-time metrics display

5. **Live News Stream**
   - Scrollable news feed with sentiment badges
   - Company logos and headlines
   - Timestamp with relative time
   - Sentiment indicators (positive/negative/neutral)
   - Symbol tags
   - Hover expansion for details

6. **Sentiment Analytics**
   - 24-hour sentiment trend chart
   - News volume correlation
   - Sector-specific insights

7. **Bottom Ticker Bar**
   - News-channel style infinite scrolling ticker
   - Real-time price updates
   - Index movements with color-coded changes
   - Seamless loop animation

### ⚡ Real-time Features

- WebSocket connections for live data
- Price flash animations (green/red)
- Auto-updating news feed
- Live market status tracking

## 🗂️ Project Structure

```
frontend/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx          # Main dashboard page
│   │   └── layout.tsx         # Dashboard layout with sidebar
│   ├── layout.tsx             # Root layout with providers
│   ├── page.tsx               # Home page (redirects to dashboard)
│   └── globals.css            # Global styles and theme
├── components/
│   ├── agents/
│   │   └── AgentCard.tsx      # AI agent insight cards
│   ├── charts/
│   │   ├── TradingChart.tsx   # Main market chart
│   │   └── SentimentChart.tsx # Sentiment trend chart
│   ├── news/
│   │   ├── NewsCard.tsx       # Individual news item
│   │   └── NewsFeed.tsx       # News feed container
│   ├── ticker/
│   │   ├── MarketTicker.tsx   # Bottom scrolling ticker
│   │   ├── PriceWidget.tsx    # Mini price display
│   │   └── MarketStatus.tsx   # Market status indicator
│   └── ui/                    # shadcn components
├── store/
│   ├── marketStore.ts         # Market data state
│   └── agentStore.ts          # AI agent insights state
├── hooks/
│   ├── useTickerStream.ts     # WebSocket hook for prices
│   └── useNewsFeed.ts         # News feed data hook
├── lib/
│   ├── apiClient.ts           # API client functions
│   ├── websocket.ts           # WebSocket client class
│   └── utils.ts               # Utility functions
└── next.config.ts             # Next.js configuration
```

## 🛠️ Getting Started

### Prerequisites

- Node.js 18+ or 20+
- npm, yarn, or pnpm
- Django backend running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 🔌 Backend Integration

### Django Endpoints

The frontend expects the following REST endpoints:

- `GET /api/news/?limit={limit}` - Fetch news articles
- `GET /api/market/{symbol}/chart?interval={interval}` - Get chart data
- `GET /api/agents/insights?symbol={symbol}` - Get AI agent insights
- `GET /api/analytics/sentiment` - Get sentiment analytics

### WebSocket Endpoints

- `/ws/market/ticker/` - Live price updates
- `/ws/news/` - New article notifications

### Expected Data Formats

**News Item:**
```typescript
{
  id: string;
  headline: string;
  source: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentimentScore: number;
  timestamp: Date;
  symbols: string[];
  url?: string;
  imageUrl?: string;
}
```

**Agent Insight:**
```typescript
{
  id: string;
  agentName: 'Sentiment' | 'Risk' | 'Macro' | 'Market Reaction';
  signal: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;
  explanation: string;
  timestamp: Date;
  metrics?: Record<string, number>;
}
```

## 🎨 Customization

### Theme Colors

Edit `app/globals.css` to customize colors:

```css
:root {
  --background: #0a0e1a;
  --price-up: #10b981;
  --price-down: #ef4444;
  /* ... more colors */
}
```

### Adding New Components

1. Create component in appropriate directory
2. Use shadcn components for consistency
3. Follow existing patterns for styling
4. Add to relevant store if state is needed

## 📱 Responsive Design

- Desktop-first layout (optimized for 1920x1080+)
- Tablet: Grid compression, stacked panels
- Mobile: Single column, collapsible sidebar

## 🚦 Performance

- Server-side rendering with Next.js App Router
- Automatic code splitting
- Optimized images with next/image
- WebSocket connection pooling
- React Query caching and background refetch

## 📝 License

Part of the Financial News Sentiment Analysis platform.

## 🤝 Contributing

This is a professional financial intelligence platform. Follow existing code patterns and maintain type safety.
