'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { NewsCard } from './NewsCard';
import { useNewsFeed } from '@/hooks/useNewsFeed';
import { Newspaper } from 'lucide-react';

export function NewsFeed() {
  const { news, isLoading } = useNewsFeed();

  return (
    <Card className="glass-effect h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Newspaper className="w-5 h-5 text-primary" />
          <CardTitle className="text-lg font-semibold">Live News Stream</CardTitle>
          <div className="ml-auto">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-price-up animate-pulse" />
              <span className="text-xs text-muted-foreground">Live</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6 pb-6">
          <div className="space-y-3">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <Card key={i} className="p-4">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </Card>
              ))
            ) : (
              news.length ? (
                news.map((item, index) => <NewsCard key={item.id} news={item} index={index} />)
              ) : (
                <div className="py-8 text-center">
                  <p className="text-sm text-muted-foreground">No live news available right now.</p>
                </div>
              )
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
