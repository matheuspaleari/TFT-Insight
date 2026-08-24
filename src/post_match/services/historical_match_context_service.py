from __future__ import annotations
import statistics
from src.post_match.models.historical_match_context import (
    HistoricalMatchContext, HistoricalMetricContext, HistoricalSignal
)

class HistoricalMatchContextService:
    RECENT_SIZE = 5
    PREVIOUS_SIZE = 5
    TREND_THRESHOLD = 0.35

    METRICS = (
        ("placement", "Colocação", False),
        ("level", "Nível final", True),
        ("gold_left", "Ouro restante", True),
        ("total_damage_to_players", "Dano aos jogadores", True),
        ("players_eliminated", "Jogadores eliminados", True),
    )

    @classmethod
    def analyze(cls, *, target_match, prior_matches, baseline_report):
        recent = list(prior_matches[:cls.RECENT_SIZE])
        previous = list(prior_matches[cls.RECENT_SIZE:cls.RECENT_SIZE+cls.PREVIOUS_SIZE])
        baseline_by_id = {x.metric_id:x for x in baseline_report.comparisons}
        metrics = []
        for metric_id,label,higher_is_better in cls.METRICS:
            metrics.append(cls._metric(
                target_match=target_match, recent=recent, previous=previous,
                metric_id=metric_id, label=label, higher_is_better=higher_is_better,
                baseline_item=baseline_by_id.get(metric_id)
            ))
        interesting=[m for m in metrics if m.signal not in (HistoricalSignal.STABLE,HistoricalSignal.INSUFFICIENT)]
        if interesting:
            summary="; ".join(f"{m.label}: {m.explanation}" for m in interesting[:3])
        else:
            summary="O histórico recente está estável nas métricas observadas."
        return HistoricalMatchContext(
            target_match_id=str(target_match.match_id), metrics=tuple(metrics), summary=summary
        )

    @classmethod
    def _metric(cls, *, target_match, recent, previous, metric_id, label, higher_is_better, baseline_item):
        if len(recent)<cls.RECENT_SIZE or len(previous)<cls.PREVIOUS_SIZE:
            return HistoricalMetricContext(metric_id,label,HistoricalSignal.INSUFFICIENT,None,None,len(recent),len(previous),0,None,"Histórico insuficiente para separar tendência de caso isolado.")

        rv=[float(getattr(x,metric_id)) for x in recent]
        pv=[float(getattr(x,metric_id)) for x in previous]
        recent_mean=statistics.mean(rv); previous_mean=statistics.mean(pv)
        combined=rv+pv
        std=statistics.pstdev(combined)
        direction=(recent_mean-previous_mean) if higher_is_better else (previous_mean-recent_mean)
        normalized=direction/std if std>1e-9 else 0.0

        current_band=getattr(getattr(baseline_item,"band",None),"value",None)
        current=float(getattr(target_match,metric_id))
        base_mean=getattr(baseline_item,"baseline_mean",None)
        base_std=getattr(baseline_item,"baseline_std",None)

        repeated=0
        if base_mean is not None and base_std not in (None,0):
            for value in rv:
                z=(value-base_mean)/base_std
                oriented=z if higher_is_better else -z
                if current_band=="BELOW" and oriented<=-0.75: repeated+=1
                if current_band=="ABOVE" and oriented>=0.75: repeated+=1

        if normalized>=cls.TREND_THRESHOLD:
            signal=HistoricalSignal.IMPROVING
            explanation="o bloco recente está melhor que o bloco anterior."
        elif normalized<=-cls.TREND_THRESHOLD:
            signal=HistoricalSignal.WORSENING
            explanation="o bloco recente está pior que o bloco anterior."
        elif current_band=="BELOW" and repeated>=2:
            signal=HistoricalSignal.RECURRING_LOW
            explanation=f"o sinal abaixo do padrão aparece repetidamente ({repeated}/5 partidas recentes)."
        elif current_band=="ABOVE" and repeated>=2:
            signal=HistoricalSignal.RECURRING_HIGH
            explanation=f"o sinal acima do padrão aparece repetidamente ({repeated}/5 partidas recentes)."
        elif current_band=="BELOW":
            signal=HistoricalSignal.ATYPICAL_LOW
            explanation="a partida atual ficou abaixo do padrão, sem repetição forte nas cinco anteriores."
        elif current_band=="ABOVE":
            signal=HistoricalSignal.ATYPICAL_HIGH
            explanation="a partida atual ficou acima do padrão, sem repetição forte nas cinco anteriores."
        else:
            signal=HistoricalSignal.STABLE
            explanation="a métrica permanece próxima do padrão recente."

        return HistoricalMetricContext(
            metric_id,label,signal,recent_mean,previous_mean,len(recent),len(previous),
            repeated,current_band,explanation
        )
