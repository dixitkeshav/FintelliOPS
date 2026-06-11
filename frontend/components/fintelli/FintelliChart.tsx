'use client';

import { useEffect, useRef } from 'react';
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  BarController,
  BarElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { useFintelliTheme } from '@/lib/fintelli/theme';

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  BarController,
  BarElement,
  Filler,
  Tooltip,
  Legend
);

type Dataset = {
  label: string;
  data: number[];
  color: string;
  fill?: boolean;
  yAxisID?: string;
  dashed?: boolean;
};

export function FintelliChart({
  id,
  labels,
  datasets,
  height = 230,
  yPrefix = '',
}: {
  id: string;
  labels: string[];
  datasets: Dataset[];
  height?: number;
  yPrefix?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);
  const { theme } = useFintelliTheme();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dark = theme === 'dark';
    const grid = dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.05)';
    const txt = dark ? '#606880' : '#78736C';

    chartRef.current?.destroy();
    chartRef.current = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: datasets.map((d) => ({
          label: d.label,
          data: d.data,
          borderColor: d.color,
          backgroundColor: d.fill ? `${d.color}22` : 'transparent',
          borderWidth: 2,
          fill: d.fill ?? false,
          tension: 0.4,
          pointRadius: 0,
          yAxisID: d.yAxisID || 'y',
          borderDash: d.dashed ? [5, 4] : undefined,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: txt } } },
        scales: {
          x: { grid: { display: false }, ticks: { color: txt, maxTicksLimit: 8 } },
          y: {
            position: 'right',
            grid: { color: grid },
            ticks: {
              color: txt,
              callback: (v) => `${yPrefix}${Number(v).toLocaleString()}`,
            },
          },
        },
      },
    });
    return () => chartRef.current?.destroy();
  }, [id, labels, datasets, theme, yPrefix]);

  return (
    <div className="chart-area" style={{ height }}>
      <canvas ref={canvasRef} className="mc" />
    </div>
  );
}
