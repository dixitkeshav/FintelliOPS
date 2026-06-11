# Financial Intelligence Platform - Frontend Setup Guide

## 🎯 Overview

A modern, production-ready financial intelligence dashboard has been created with:
- **TradingView-style dark theme** with glassmorphism effects
- **Real-time market data** via WebSockets
- **AI-powered agent insights** with sentiment analysis
- **Live news feed** with sentiment indicators
- **Interactive charts** for market analysis

## 📦 Technology Stack

| Category | Technology | Version |
|----------|-----------|---------|
| **Framework** | Next.js | 15.5.12 |
| **Language** | TypeScript | 5.x |
| **Styling** | Tailwind CSS | v4 |
| **UI Library** | shadcn/ui | Latest |
| **State** | Zustand | Latest |
| **Data Fetching** | TanStack Query | Latest |
| **Charts** | Recharts | Latest |
| **Animation** | Framer Motion | Latest |
| **Icons** | Lucide React | Latest |
| **Build** | Turbopack | Built-in |

## 🚀 Quick Start

```bash
# Navigate to frontend directory
cd Financial-News-Sentiment-Analysis/frontend

# Install dependencies (already done)
npm install

# Start development server
npm run dev

# Open browser
# http://localhost:3000
```

## 🏗️ Project Architecture

### Directory Structure

```
frontend/
├── app/
│   ├── dashboard/          # Main dashboard route
│   │   ├── layout.tsx     # Sidebar + navbar layout
│   │   └── page.tsx       # Dashboard content
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Redirect to dashboard
│   └── globals.css        # Theme + global styles
├── components/
│   ├── agents/            # AI agent cards
│   ├── charts/            # Trading & sentiment charts
│   ├── news/              # News feed components
│   ├── ticker/            # Market ticker & widgets
│   └── ui/                # shadcn components
├── store/
│   ├── marketStore.ts     # Market data (Zustand)
│   └── agentStore.ts      # Agent insights (Zustand)
├── hooks/
│   ├── useTickerStream.ts # WebSocket for prices
│   └── useNewsFeed.ts     # News data with WS
├── lib/
│   ├── apiClient.ts       # REST API client
│   ├── websocket.ts       # WebSocket client
│   └── utils.ts           # Utility functions
└── next.config.ts         # Next.js config + SVG support
```

### Key Features Implemented

#### 1. **Multi-Panel Dashboard Layout**
- **Left Sidebar**: Collapsible navigation with 7 sections
- **Top Navbar**: Search, market status, mini price widgets, user menu
- **Main Grid**: TradingView-style chart + News feed (responsive)
- **Bottom Ticker**: Infinite scrolling price ticker

#### 2. **AI Agent Insights**
Four specialized agents displaying:
- **Sentiment Agent**: News sentiment analysis (BULLISH/BEARISH/NEUTRAL)
- **Risk Agent**: Volatility and VIX tracking
- **Macro Agent**: Economic indicators (CPI, yields)
- **Market Reaction**: Options flow analysis

Each agent card shows:
- Signal strength with visual indicators
- Confidence percentage with animated progress bar
- LLM-generated explanation
- Real-time metrics

#### 3. **Live Market Chart**
- Area chart with gradient fill
- Volume bar chart
- Multiple timeframes (1D, 1W, 1M, 3M, 1Y, ALL)
- Interactive tooltips
- Responsive container

#### 4. **News Feed**
- Real-time scrollable feed
- Sentiment badges (positive/negative/neutral)
- Source and timestamp
- Symbol tags
- Hover effects

#### 5. **Bottom Ticker**
- Seamless infinite scroll animation
- Real-time price updates
- Color-coded changes (green/red)
- 30s loop cycle

## 🎨 Design System

### Color Palette

```css
/* Dark Background */
--background: #0a0e1a        /* Main background */
--card: #131823              /* Card background */
--popover: #1a1f2e          /* Dropdown background */

/* Price Indicators */
--price-up: #10b981          /* Green (bullish) */
--price-down: #ef4444        /* Red (bearish) */
--price-neutral: #94a3b8     /* Gray (neutral) */

/* Chart Colors */
--chart-1: #10b981           /* Primary green */
--chart-2: #3b82f6           /* Blue */
--chart-3: #8b5cf6           /* Purple */
--chart-4: #f59e0b           /* Orange */
--chart-5: #ef4444           /* Red */

/* Glassmorphism */
--glass-bg: rgba(19, 24, 35, 0.7)
--glass-border: rgba(255, 255, 255, 0.1)
```

### Custom Utilities

```css
.glass-effect        /* Glassmorphism background */
.price-flash-up      /* Green flash animation */
.price-flash-down    /* Red flash animation */
```

### Typography

- **Font Family**: Inter (fallback: system fonts)
- **Font Weights**: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)
- **Code**: Monospace for prices and numbers

## 🔌 Backend Integration

### Environment Variables

`.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Expected REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/news/` | GET | Fetch news articles (limit param) |
| `/api/market/{symbol}/chart` | GET | Get OHLCV data (interval param) |
| `/api/agents/insights` | GET | Get AI insights (symbol param) |
| `/api/analytics/sentiment` | GET | Sentiment trends |

### WebSocket Endpoints

| Endpoint | Event Type | Payload |
|----------|-----------|---------|
| `/ws/market/ticker/` | `price_update` | `{symbol, price, change, changePercent}` |
| `/ws/news/` | `new_article` | `{type: 'new_article'}` |

### Sample API Responses

**News Item:**
```json
{
  "id": "1",
  "headline": "Tech stocks rally...",
  "source": "Bloomberg",
  "sentiment": "positive",
  "sentimentScore": 0.78,
  "timestamp": "2026-02-11T10:00:00Z",
  "symbols": ["AAPL", "MSFT"],
  "url": "https://...",
  "imageUrl": "https://..."
}
```

**Agent Insight:**
```json
{
  "id": "1",
  "agentName": "Sentiment",
  "signal": "BULLISH",
  "confidence": 78,
  "explanation": "Strong positive sentiment...",
  "timestamp": "2026-02-11T10:00:00Z",
  "metrics": {
    "newsVolume": 156,
    "positiveRatio": 0.72
  }
}
```

## 🎯 Next Steps

### To Connect with Django Backend:

1. **Start Django server** on port 8000:
   ```bash
   cd Financial-News-Sentiment-Analysis/backend
   python manage.py runserver
   ```

2. **Configure Django CORS** (already done in settings.py):
   ```python
   CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
   ```

3. **Implement WebSocket consumers** in Django Channels

4. **Test real-time features**:
   - Price updates in ticker
   - News feed refresh
   - Agent insights updates

### To Deploy:

1. **Build production**:
   ```bash
   npm run build
   npm start
   ```

2. **Configure environment** for production API URL

3. **Deploy to Vercel/Netlify** or Docker container

## 📊 Performance Optimizations

- ✅ Server-side rendering with Next.js App Router
- ✅ Automatic code splitting
- ✅ React Query caching (30s refetch interval)
- ✅ WebSocket connection pooling
- ✅ Optimized images with next/image
- ✅ Turbopack for fast dev builds

## 🐛 Troubleshooting

### Port 3000 already in use
```bash
lsof -ti:3000 | xargs kill
npm run dev
```

### WebSocket connection fails
- Ensure Django Channels is running
- Check CORS settings
- Verify WS_URL in .env.local

### Charts not rendering
- Check browser console for errors
- Verify mock data format
- Ensure Recharts is installed

## 📝 Development Tips

1. **Hot Reload**: Changes auto-refresh in dev mode
2. **Type Safety**: All components are TypeScript
3. **State Management**: Use Zustand stores for global state
4. **Styling**: Prefer Tailwind utilities over custom CSS
5. **Components**: Use shadcn components for consistency

## 🎉 Success!

The Financial Intelligence Platform frontend is ready at:
**http://localhost:3000**

Navigate to `/dashboard` to see the full interface with:
- Live market charts
- AI agent insights
- Real-time news feed
- Bottom ticker
- Responsive sidebar navigation
