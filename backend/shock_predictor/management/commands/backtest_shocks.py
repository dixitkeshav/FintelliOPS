import datetime
import re
from collections import Counter

import pandas as pd
import yfinance as yf
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count

from shock_predictor.models import ShockEvent, ShockPrecursorPattern
from shock_predictor.nlp import classify_cause_from_text, get_finbert_sentiment
from shock_predictor.news_fetcher import fetch_headlines_bundle_for_date

DEFAULT_SHOCK_THRESHOLD_POINTS = 100
NIFTY_TICKER = "^NSEI"
# Bank Nifty index on Yahoo Finance
BANKNIFTY_TICKER = "^NSEBANK"
# Sensex (optional; same threshold in index points)
SENSEX_TICKER = "^BSESN"
START_DATE = "2015-01-01"


def _normalize_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.title)
    for col in ('Open', 'High', 'Low', 'Close'):
        if col not in df.columns:
            raise ValueError(f"Missing column {col}")
    return df


def _find_shock_days(
    ticker: str,
    index_name: str,
    threshold_points: float,
    *,
    directional_only: bool = True,
) -> list[tuple]:
    end = datetime.date.today().strftime("%Y-%m-%d")
    df = yf.download(ticker, start=START_DATE, end=end, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return []
    df = _normalize_ohlc(df.copy())
    df.index = pd.to_datetime(df.index)
    df["Range"] = df["High"] - df["Low"]
    df["NetMove"] = df["Close"] - df["Open"]
    df["AbsNet"] = df["NetMove"].abs()
    max_range_pct = 0.12
    min_range = max(float(threshold_points), (df["Open"] * 0.015))
    plausible = df["Range"] <= (df["Open"] * max_range_pct)
    # Sudden one-direction move: |close-open| >= threshold (not just intraday chop)
    move_ok = df["AbsNet"] >= min_range
    if directional_only:
        shock_days = df[plausible & move_ok]
    else:
        shock_days = df[plausible & (df["Range"] >= min_range)]
    rows = []
    for date, row in shock_days.iterrows():
        rows.append((date.date(), index_name, row))
    return rows


class Command(BaseCommand):
    help = "Backtest Nifty/BankNifty history, identify shock events, classify causes"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-newsapi',
            action='store_true',
            help='Use fallback headlines only (no NewsAPI calls)',
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Skip FinBERT scoring (keyword-only classification, much faster)',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing shock events and patterns before backtest',
        )
        parser.add_argument(
            '--indices',
            type=str,
            default='nifty',
            help='Comma-separated: nifty, banknifty, sensex (default: nifty only; sensex yfinance often noisy)',
        )
        parser.add_argument(
            '--threshold',
            type=int,
            default=DEFAULT_SHOCK_THRESHOLD_POINTS,
            help='Minimum index points |close-open| for a shock day (default 100)',
        )

    def handle(self, *args, **options):
        threshold = max(10, int(options.get('threshold') or DEFAULT_SHOCK_THRESHOLD_POINTS))
        if options['reset']:
            n, _ = ShockEvent.objects.all().delete()
            ShockPrecursorPattern.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {n} shock events and patterns."))

        index_map = {
            'nifty': (NIFTY_TICKER, 'NIFTY'),
            'banknifty': (BANKNIFTY_TICKER, 'BANKNIFTY'),
            'sensex': (SENSEX_TICKER, 'SENSEX'),
        }
        selected = [s.strip().lower() for s in options['indices'].split(',') if s.strip()]
        self.stdout.write(f"Fetching OHLCV for: {', '.join(selected)}...")
        all_shocks = []
        for key in selected:
            if key not in index_map:
                self.stdout.write(self.style.WARNING(f"Unknown index key: {key}"))
                continue
            ticker, name = index_map[key]
            all_shocks.extend(_find_shock_days(ticker, name, threshold))
        self.stdout.write(
            self.style.NOTICE(
                f"Found {len(all_shocks)} shock days (|net move| >= {threshold} pts, directional)"
            )
        )

        saved = 0
        for date_obj, index_name, row in all_shocks:
            if ShockEvent.objects.filter(date=date_obj, index=index_name).exists():
                continue

            direction = 'UP' if float(row['NetMove']) >= 0 else 'DOWN'
            magnitude = abs(float(row['NetMove']))

            if options["skip_newsapi"]:
                headline = (
                    f"{index_name} large directional move on {date_obj}: "
                    f"net {float(row['NetMove']):+.0f} pts, range {float(row['Range']):.0f}."
                )
                news_bundle = {"headlines": [{"title": headline, "summary": headline}]}
            else:
                news_bundle = fetch_headlines_bundle_for_date(date_obj, index_name=index_name)
                headline = news_bundle.get("top_title") or news_bundle.get("combined_text", "")[:300]

            combined = news_bundle.get("combined_text") or headline
            sentiment_score = 0.0 if options["fast"] else get_finbert_sentiment(combined)
            cause_type, cause_summary = classify_cause_from_text(
                combined,
                date=date_obj,
                headlines=news_bundle.get("headlines"),
            )

            ShockEvent.objects.create(
                date=date_obj,
                index=index_name,
                open_price=float(row["Open"]),
                close_price=float(row["Close"]),
                high_price=float(row["High"]),
                low_price=float(row["Low"]),
                intraday_range=float(row["Range"]),
                direction=direction,
                magnitude=float(magnitude),
                cause_type=cause_type,
                cause_summary=cause_summary,
                headline=headline[:500] if headline else "",
                precursor_signals={
                    "finbert_sentiment": sentiment_score,
                    "threshold_points": threshold,
                    "headlines": (news_bundle.get("headlines") or [])[:5],
                },
            )
            saved += 1
            self.stdout.write(
                f"  Saved: {date_obj} {index_name} | {direction} {magnitude:.0f}pts | {cause_type}"
            )

        self.stdout.write(self.style.SUCCESS(f"\nSaved {saved} new shock events."))
        self._compute_patterns()

    def _compute_patterns(self):
        self.stdout.write("Computing precursor patterns...")
        for cause in ['policy', 'macro', 'geopolitical', 'technical', 'corporate']:
            events = ShockEvent.objects.filter(cause_type=cause)
            if not events.exists():
                continue
            agg = events.aggregate(
                avg_iv=Avg('iv_change_pct'),
                avg_pcr=Avg('pcr_before'),
                avg_vix=Avg('vix_open'),
                count=Count('id'),
            )
            all_words = []
            for e in events:
                words = re.findall(r'\b[a-zA-Z]{4,}\b', (e.headline or '').lower())
                all_words.extend(words)
            stopwords = {
                'that', 'this', 'with', 'from', 'have', 'will', 'been', 'were',
                'they', 'their', 'nifty', 'market', 'indian', 'sensex',
            }
            top_keywords = [
                w for w, _ in Counter(all_words).most_common(30) if w not in stopwords
            ][:20]

            ShockPrecursorPattern.objects.update_or_create(
                cause_type=cause,
                defaults={
                    'avg_iv_change_1hr': agg['avg_iv'] or 0,
                    'avg_pcr_shift': agg['avg_pcr'] or 0,
                    'avg_vix_open': agg['avg_vix'] or 0,
                    'keyword_fingerprint': top_keywords,
                    'sample_count': agg['count'],
                },
            )
            self.stdout.write(f"  Pattern updated: {cause} (n={agg['count']})")
