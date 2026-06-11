'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { useState, useMemo } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/apiClient';
import { Skeleton } from '@/components/ui/skeleton';

const DEFAULT_SYMBOL = '^NSEI';
const timeframes: Record<string, string> = {
  '1D': '5d',
  '1W': '5d',
  '1M': '1mo',
  '3M': '3mo',
  '1Y': '1y',
  'ALL': '2y',
};

export function TradingChart() {
  const [selectedTimeframe, setSelectedTimeframe] = useState('1M');
  const [symbol, setSymbol] = useState(DEFAULT_SYMBOL);

  const period = timeframes[selectedTimeframe] || '1mo';
  const { data: history = [], isLoading } = useQuery({
    queryKey: ['chart-data', symbol, period],
    queryFn: () => apiClient.getChartData(symbol, period),
    refetchInterval: 60000, // refresh chart data
    refetchIntervalInBackground: true,
    staleTime: 60000,
  });

  const chartData = useMemo(() => {
    if (!history.length) return [];
    return history.map((d) => ({
      timestamp: d.timestamp,
      price: d.close,
      volume: d.volume,
      date: new Date(d.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }));
  }, [history]);

  const priceChange = useMemo(() => {
    if (chartData.length < 2) return { value: 0, percent: 0 };
    const first = chartData[0].price;
    const last = chartData[chartData.length - 1].price;
    const change = last - first;
    const percent = first ? (change / first) * 100 : 0;
    return { value: change, percent };
  }, [chartData]);

  const displaySymbol = symbol.replace(/^\^/, '');
  const chartConfig = {
    price: { label: 'Price', color: '#3b82f6' },
    volume: { label: 'Volume', color: '#10b981' },
  };

  return (
    <Card className="glass-effect h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg font-semibold">{displaySymbol}</CardTitle>
            <div
              className={`flex items-center gap-1 text-sm ${priceChange.percent >= 0 ? 'text-price-up' : 'text-price-down'}`}
            >
              {priceChange.percent >= 0 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span className="font-semibold">
                {priceChange.percent >= 0 ? '+' : ''}
                {priceChange.percent.toFixed(2)}%
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
            {Object.keys(timeframes).map((tf) => (
              <Button
                key={tf}
                variant={selectedTimeframe === tf ? 'default' : 'ghost'}
                size="sm"
                className="h-7 px-3 text-xs"
                onClick={() => setSelectedTimeframe(tf)}
              >
                {tf}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-4 space-y-4">
        {isLoading ? (
          <Skeleton className="h-[300px] w-full" />
        ) : (
          chartData.length ? (
            <>
            <ChartContainer config={chartConfig} className="h-[300px] w-full">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date"
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis
                  domain={['dataMin - 10', 'dataMax + 10']}
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => v.toFixed(0)}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  type="monotone"
                  dataKey="price"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="url(#priceGradient)"
                />
              </AreaChart>
            </ChartContainer>

            <ChartContainer config={chartConfig} className="h-[100px] w-full">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date"
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis
                  stroke="#94a3b8"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => `${(v / 1000000).toFixed(1)}M`}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="volume" fill="#10b981" opacity={0.6} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ChartContainer>
            </>
          ) : (
            <div className="py-10 text-center">
              <p className="text-sm text-muted-foreground">No chart data returned for {displaySymbol}.</p>
            </div>
          )
        )}
      </CardContent>
    </Card>
  );
}
