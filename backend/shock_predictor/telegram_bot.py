import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_alert(payload: dict):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None) or ''
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None) or ''
    if not token or not chat_id:
        return

    score = payload.get('score', 0)
    cause = payload.get('cause', 'unknown').upper()
    headline = (payload.get('headline', '') or '')[:150]
    source = payload.get('source', '')
    hedge = payload.get('hedge', '')

    emoji = "🔴" if score >= 85 else "🟠" if score >= 70 else "🟡"
    message = (
        f"{emoji} *SHOCK ALERT — Score: {score}/100*\n\n"
        f"*Cause:* {cause}\n"
        f"*Source:* {source}\n"
        f"*Headline:* {headline}\n\n"
        f"*Suggested hedge:* {hedge}\n\n"
        f"_Check your ShockAlert dashboard for full details._"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(
            url,
            json={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'},
            timeout=10,
        )
    except Exception as e:
        logger.debug("Telegram send failed: %s", e)
