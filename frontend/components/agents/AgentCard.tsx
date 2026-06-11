'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AgentInsight } from '@/store/agentStore';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus, Brain, Shield, Globe, Activity, LineChart, Scale, Newspaper } from 'lucide-react';
import { motion } from 'framer-motion';

interface AgentCardProps {
  insight: AgentInsight;
}

const agentIcons: Record<string, typeof Brain> = {
  'News Scout': Newspaper,
  Sentiment: Brain,
  Risk: Shield,
  Macro: Globe,
  Technical: LineChart,
  'Market Reaction': Activity,
  Decision: Scale,
};

const signalConfig = {
  BULLISH: {
    label: 'Bullish',
    color: 'text-price-up',
    bgColor: 'bg-price-up/10',
    borderColor: 'border-price-up/30',
    icon: TrendingUp,
  },
  BEARISH: {
    label: 'Bearish',
    color: 'text-price-down',
    bgColor: 'bg-price-down/10',
    borderColor: 'border-price-down/30',
    icon: TrendingDown,
  },
  NEUTRAL: {
    label: 'Neutral',
    color: 'text-price-neutral',
    bgColor: 'bg-price-neutral/10',
    borderColor: 'border-price-neutral/30',
    icon: Minus,
  },
};

export function AgentCard({ insight }: AgentCardProps) {
  const config = signalConfig[insight.signal];
  const AgentIcon = agentIcons[insight.agentName] ?? Brain;
  const SignalIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="glass-effect hover:border-primary/30 transition-all duration-300 group">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary/10">
                <AgentIcon className="w-4 h-4 text-primary" />
              </div>
              <CardTitle className="text-sm font-semibold">{insight.agentName}</CardTitle>
            </div>
            <Badge
              className={cn(
                'flex items-center gap-1 px-2 py-1',
                config.bgColor,
                config.color,
                config.borderColor,
                'border'
              )}
            >
              <SignalIcon className="w-3 h-3" />
              {config.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Confidence</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${insight.confidence}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                  className={cn('h-full rounded-full', config.bgColor.replace('/10', ''))}
                />
              </div>
              <span className={cn('text-xs font-semibold', config.color)}>
                {insight.confidence}%
              </span>
            </div>
          </div>
          <p className="text-xs text-foreground/80 leading-relaxed">{insight.explanation}</p>
          {insight.metrics && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-border/50">
              {Object.entries(insight.metrics).map(([key, value]) => (
                <div key={key} className="flex items-center gap-1 text-xs">
                  <span className="text-muted-foreground">{key}:</span>
                  <span className="font-mono font-semibold">
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
