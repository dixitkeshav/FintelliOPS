from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response

from shock_predictor.models import ShockEvent, ShockAlert, ShockPrecursorPattern
from shock_predictor.scoring import get_current_score
from shock_predictor.symbols import get_universe


@api_view(['GET'])
def current_score(request):
    return Response(get_current_score())


@api_view(['GET'])
def shock_universe(request):
    group = request.query_params.get('group', 'all')
    return Response(get_universe(group))


@api_view(['GET'])
def shock_history(request):
    qs = ShockEvent.objects.all()
    cause = request.query_params.get('cause')
    direction = request.query_params.get('direction')
    index_name = request.query_params.get('index')
    min_magnitude = request.query_params.get('min_magnitude') or request.query_params.get('threshold')
    if cause:
        qs = qs.filter(cause_type=cause)
    if direction:
        qs = qs.filter(direction=direction.upper())
    if index_name:
        qs = qs.filter(index__iexact=index_name.strip())
    if min_magnitude:
        try:
            qs = qs.filter(magnitude__gte=float(min_magnitude))
        except (TypeError, ValueError):
            pass

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.query_params.get('page', 1))
    data = []
    for e in page:
        prec = e.precursor_signals if isinstance(e.precursor_signals, dict) else {}
        headlines = prec.get('headlines') or []
        data.append({
            'date': e.date.isoformat(),
            'direction': e.direction,
            'magnitude': e.magnitude,
            'intraday_range': e.intraday_range,
            'cause_type': e.cause_type,
            'cause_summary': e.cause_summary,
            'headline': e.headline,
            'vix_open': e.vix_open,
            'index': e.index,
            'news_evidence': headlines,
            'threshold_points': prec.get('threshold_points'),
        })
    return Response({
        'results': data,
        'total': paginator.count,
        'pages': paginator.num_pages,
    })


@api_view(['GET'])
def alert_log(request):
    alerts = ShockAlert.objects.all()[:50]
    data = [{
        'fired_at': a.fired_at.isoformat(),
        'score': a.score,
        'cause': a.cause_hypothesis,
        'headline': a.trigger_headline,
        'source': a.trigger_source,
        'hedge': a.suggested_hedge,
        'status': a.status,
        'eod_nifty_change': a.eod_nifty_change,
    } for a in alerts]
    return Response(data)


@api_view(['GET'])
def precursor_patterns(request):
    patterns = ShockPrecursorPattern.objects.all()
    return Response([{
        'cause_type': p.cause_type,
        'avg_iv_change_1hr': p.avg_iv_change_1hr,
        'avg_pcr_shift': p.avg_pcr_shift,
        'avg_vix_open': p.avg_vix_open,
        'keyword_fingerprint': p.keyword_fingerprint,
        'sample_count': p.sample_count,
        'updated_at': p.updated_at.isoformat(),
    } for p in patterns])


@api_view(['GET'])
def live_move_scan(request):
    """
    Scan index for sudden directional move vs threshold (points).
    Query: threshold=100, index=nifty|sensex|banknifty
    """
    import datetime

    import yfinance as yf

    threshold = 100
    try:
        threshold = max(10, int(request.query_params.get('threshold', 100)))
    except (TypeError, ValueError):
        pass

    index_key = (request.query_params.get('index') or 'nifty').lower()
    tickers = {
        'nifty': '^NSEI',
        'banknifty': '^NSEBANK',
        'sensex': '^BSESN',
    }
    yf_t = tickers.get(index_key, '^NSEI')
    label = index_key.upper() if index_key != 'nifty' else 'NIFTY'

    df = yf.download(yf_t, period='5d', progress=False, auto_adjust=True)
    if df is None or df.empty:
        return Response({'error': 'No price data', 'index': label})

    if hasattr(df.columns, 'levels'):
        df.columns = df.columns.get_level_values(0)
    row = df.iloc[-1]
    o, c = float(row['Open']), float(row['Close'])
    net = c - o
    alert = abs(net) >= threshold
    return Response({
        'index': label,
        'date': datetime.date.today().isoformat(),
        'open': o,
        'close': c,
        'net_move_pts': round(net, 1),
        'threshold_pts': threshold,
        'direction': 'UP' if net > 0 else 'DOWN' if net < 0 else 'FLAT',
        'shock_alert': alert,
    })
