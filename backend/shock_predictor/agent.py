from shock_predictor.models import ShockPrecursorPattern
from shock_predictor.scoring import get_current_score, get_hedge_suggestion


class ShockAgent:
    """
    Market shock prediction agent — integrates with AgentOrchestrator via analyze().
    """

    name = "ShockAgent"

    def analyze(self, agent_context: dict) -> dict:
        sentiment_score = abs(float(agent_context.get('sentiment_score', 0)))
        macro_stress = float(agent_context.get('macro_stress_index', 0))
        risk_level = agent_context.get('risk_level', 'low')

        risk_multipliers = {'low': 0.8, 'medium': 1.0, 'high': 1.2}
        risk_mult = risk_multipliers.get(risk_level, 1.0)

        live = get_current_score()
        news_score = int(live.get('score', 0) or 0)
        cause_type = live.get('cause', 'unknown') or 'unknown'

        pattern_bonus = self._match_pattern(cause_type, agent_context)

        cross_agent_score = (sentiment_score * 30 + macro_stress * 20) * risk_mult
        shock_probability = min(
            100,
            int((news_score * 0.5) + (cross_agent_score * 0.35) + (pattern_bonus * 0.15)),
        )

        return {
            'shock_probability': shock_probability,
            'trigger_cause': cause_type,
            'trigger_headline': live.get('headline', ''),
            'suggested_hedge': get_hedge_suggestion(cause_type, 0),
            'news_score': news_score,
            'cross_agent_score': round(cross_agent_score, 1),
            'pattern_bonus': round(pattern_bonus, 1),
        }

    def run(self, context: dict) -> dict:
        """Alias for orchestrator compatibility with BaseAgent.run()."""
        out = self.analyze(context)
        out['summary'] = (
            f"Shock probability {out['shock_probability']}/100 "
            f"({out['trigger_cause']}). {out['trigger_headline'][:80]}"
        )
        return out

    def _match_pattern(self, cause_type: str, context: dict) -> float:
        try:
            pattern = ShockPrecursorPattern.objects.get(cause_type=cause_type)
            vix = float(context.get('vix', 0) or 0)
            if vix and pattern.avg_vix_open:
                vix_match = max(0, 1 - abs(vix - pattern.avg_vix_open) / 20)
                return vix_match * 15
        except ShockPrecursorPattern.DoesNotExist:
            pass
        return 0.0


def build_shock_context_from_pipeline(ctx: dict) -> dict:
    """Map orchestrator context to ShockAgent inputs."""
    articles = ctx.get('articles', [])
    neg = sum(1 for a in articles if (a.get('sentiment') or '').lower() == 'negative')
    pos = sum(1 for a in articles if (a.get('sentiment') or '').lower() == 'positive')
    total = len(articles) or 1
    sentiment_score = (neg - pos) / total

    macro_out = ctx.get('agent_outputs', {}).get('MacroContext', {})
    macro_links = macro_out.get('macro_links') or []
    macro_stress = min(1.0, len(macro_links) * 0.2) if macro_links else 0.3

    risk_out = ctx.get('agent_outputs', {}).get('Risk', {})
    flags = risk_out.get('risk_flags') or []
    if len(flags) >= 2:
        risk_level = 'high'
    elif len(flags) == 1:
        risk_level = 'medium'
    else:
        risk_level = 'low'

    return {
        'sentiment_score': sentiment_score,
        'macro_stress_index': macro_stress,
        'risk_level': risk_level,
        'vix': ctx.get('vix', 0),
    }
