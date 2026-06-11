'use client';

interface ShockScoreGaugeProps {
  score: number;
}

export function ShockScoreGauge({ score }: ShockScoreGaugeProps) {
  const color = score >= 70 ? '#E24B4A' : score >= 40 ? '#EF9F27' : '#1D9E75';
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const filled = (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="140" height="140" viewBox="0 0 140 140" aria-label={`Shock score ${score}`}>
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          className="stroke-muted"
          strokeWidth="10"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={`${filled} ${circumference - filled}`}
          strokeDashoffset={circumference / 4}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
        <text
          x="70"
          y="66"
          textAnchor="middle"
          fontSize="28"
          fontWeight="500"
          className="fill-foreground"
        >
          {score}
        </text>
        <text x="70" y="85" textAnchor="middle" fontSize="12" className="fill-muted-foreground">
          / 100
        </text>
      </svg>
      <span className="text-sm text-muted-foreground">Shock probability</span>
    </div>
  );
}
