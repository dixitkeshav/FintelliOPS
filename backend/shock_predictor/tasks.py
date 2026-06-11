import datetime
import logging
from zoneinfo import ZoneInfo

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from shock_predictor.models import ShockAlert
from shock_predictor.news_fetcher import poll_all_feeds
from shock_predictor.scoring import (
    compute_article_score,
    update_shock_score,
    SCORE_THRESHOLD,
)
from shock_predictor.telegram_bot import send_telegram_alert

logger = logging.getLogger(__name__)
IST = ZoneInfo('Asia/Kolkata')


def _within_market_hours() -> bool:
    now = datetime.datetime.now(IST)
    if now.weekday() >= 5:
        return False
    return datetime.time(9, 0) <= now.time() <= datetime.time(15, 35)


@shared_task(name='shock_predictor.tasks.poll_and_score')
def poll_and_score():
    if not _within_market_hours():
        return "Outside market hours — skipping"

    articles = poll_all_feeds()
    if not articles:
        return "No new articles"

    scored = [compute_article_score(a) for a in articles]
    top = max(scored, key=lambda x: x['shock_score'])
    payload = update_shock_score(top['shock_score'], top)

    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            "shock_alerts",
            {"type": "shock.update", "data": payload},
        )

    if top['shock_score'] >= SCORE_THRESHOLD:
        fire_shock_alert.delay(payload)

    return (
        f"Top score: {top['shock_score']} | {top.get('cause_type')} | "
        f"{top.get('title', '')[:60]}"
    )


@shared_task(name='shock_predictor.tasks.fire_shock_alert')
def fire_shock_alert(payload: dict):
    ShockAlert.objects.create(
        score=payload['score'],
        cause_hypothesis=payload.get('cause', 'unknown'),
        trigger_headline=payload.get('headline', ''),
        trigger_source=payload.get('source', ''),
        suggested_hedge=payload.get('hedge', ''),
    )
    send_telegram_alert(payload)
    return f"Alert fired: score={payload['score']}"


@shared_task(name='shock_predictor.tasks.update_eod_feedback')
def update_eod_feedback():
    import yfinance as yf

    today = datetime.date.today()
    ticker = yf.Ticker("^NSEI")
    hist = ticker.history(period="1d")
    if hist.empty:
        return "No data"
    eod_change = float(hist['Close'].iloc[-1] - hist['Open'].iloc[-1])

    ShockAlert.objects.filter(
        fired_at__date=today,
        eod_nifty_change__isnull=True,
    ).update(eod_nifty_change=eod_change)

    return f"EOD feedback updated: {eod_change:.1f}pts"
