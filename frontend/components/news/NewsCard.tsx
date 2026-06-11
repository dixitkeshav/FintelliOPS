'use client';

import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { NewsItem } from '@/lib/apiClient';
import { cn } from '@/lib/utils';
import { ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';

interface NewsCardProps {
  news: NewsItem;
  index: number;
}

const sentimentConfig = {
  positive: {
    label: 'Positive',
    color: 'text-price-up',
    bgColor: 'bg-price-up/10',
    borderColor: 'border-price-up/30',
    icon: TrendingUp,
  },
  negative: {
    label: 'Negative',
    color: 'text-price-down',
    bgColor: 'bg-price-down/10',
    borderColor: 'border-price-down/30',
    icon: TrendingDown,
  },
  neutral: {
    label: 'Neutral',
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/50',
    borderColor: 'border-muted',
    icon: Minus,
  },
};

export function NewsCard({ news, index }: NewsCardProps) {
  // Fallback to neutral if sentiment is not recognized
  const sentiment = news.sentiment && sentimentConfig[news.sentiment] 
    ? news.sentiment 
    : 'neutral';
  const config = sentimentConfig[sentiment];
  const SentimentIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card className="p-4 hover:bg-card/80 transition-all duration-200 cursor-pointer group border-l-2 border-l-transparent hover:border-l-primary">
        <div className="flex items-start gap-3">
          {news.imageUrl && (
            <img
              src={news.imageUrl}
              alt=""
              className="w-16 h-16 rounded-lg object-cover flex-shrink-0"
            />
          )}
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-sm font-semibold leading-tight line-clamp-2 group-hover:text-primary transition-colors">
                {news.headline}
              </h3>
              {news.url && (
                <ExternalLink className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              )}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <Badge
                variant="outline"
                className={cn(
                  'flex items-center gap-1 px-2 py-0.5 text-xs',
                  config.bgColor,
                  config.color,
                  config.borderColor
                )}
              >
                <SentimentIcon className="w-3 h-3" />
                {config.label}
              </Badge>
              <span className="text-xs text-muted-foreground">{news.source}</span>
              <span className="text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(news.timestamp), { addSuffix: true })}
              </span>
            </div>
            {news.symbols && news.symbols.length > 0 && (
              <div className="flex items-center gap-1.5 flex-wrap">
                {news.symbols.map((symbol) => (
                  <Badge key={symbol} variant="secondary" className="text-xs px-2 py-0">
                    {symbol}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
