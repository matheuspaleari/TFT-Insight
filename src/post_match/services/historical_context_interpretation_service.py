from __future__ import annotations

from src.post_match.models.historical_context_interpretation import (
    HistoricalContextInterpretation,
    HistoricalInterpretationItem,
)


class HistoricalContextInterpretationService:
    """
    V1.5: traduz o contexto histórico para linguagem pública segura.

    Regra central:
    mudança estatística != melhora/piora de decisão.

    Algumas métricas têm direção de resultado interpretável (placement,
    damage, eliminations). Outras são ambíguas (gold_left e final level
    fora do contexto da missão), portanto usamos "subiu/caiu" em vez de
    "melhorou/piorou".
    """

    QUALITY_DIRECTION_METRICS = {
        "placement",
        "total_damage_to_players",
        "players_eliminated",
    }

    AMBIGUOUS_DIRECTION_METRICS = {
        "gold_left",
    }

    @classmethod
    def interpret(
        cls,
        *,
        historical_context,
        active_skill_id: str | None,
        active_skill_label: str | None,
    ) -> HistoricalContextInterpretation:
        by_id = {item.metric_id: item for item in historical_context.metrics}

        overview = cls._overview(by_id)

        focus_metric_id = cls._focus_metric_id(active_skill_id)
        focus_metric = by_id.get(focus_metric_id) if focus_metric_id else None
        focus_reading = cls._focus_reading(
            metric=focus_metric,
            skill_id=active_skill_id,
            skill_label=active_skill_label,
        )

        items = []
        for metric in historical_context.metrics:
            if focus_metric is not None and metric.metric_id == focus_metric.metric_id:
                continue
            item = cls._public_item(metric)
            if item is not None:
                items.append(item)

        items.sort(key=lambda x: x.importance, reverse=True)

        return HistoricalContextInterpretation(
            overview=overview,
            focus_reading=focus_reading,
            additional_readings=tuple(items[:2]),
            conclusion=(
                "O histórico ajuda a separar uma partida isolada de um sinal que "
                "vem se repetindo. Ele não identifica sozinho a causa da mudança "
                "e não altera automaticamente seu foco de treino."
            ),
        )

    @classmethod
    def _overview(cls, by_id: dict) -> str:
        placement = by_id.get("placement")
        damage = by_id.get("total_damage_to_players")

        p = cls._signal(placement)
        d = cls._signal(damage)

        if p == "IMPROVING" and d == "IMPROVING":
            return (
                "Seu histórico recente mostra avanço em resultado e pressão sobre "
                "o lobby. Por isso, uma partida atual abaixo do padrão pode destoar "
                "do momento recente em vez de representar, sozinha, uma piora geral."
            )

        if p == "WORSENING" and d == "WORSENING":
            return (
                "Resultado e pressão sobre o lobby vêm terminando mais baixos no "
                "bloco recente. É um sinal para acompanhar, sem atribuir essa mudança "
                "a uma decisão específica."
            )

        return (
            "O histórico recente tem sinais mistos. A leitura abaixo destaca o que "
            "vem mudando ou se repetindo sem transformar correlação em causa."
        )

    @classmethod
    def _focus_reading(cls, *, metric, skill_id, skill_label) -> str:
        label = skill_label or "foco atual"
        if metric is None:
            return (
                f"Ainda não há uma métrica histórica específica ligada a {label} "
                "nesta versão."
            )

        recent = cls._fmt(metric.recent_mean)
        previous = cls._fmt(metric.previous_mean)
        signal = cls._signal(metric)

        if metric.metric_id == "level" and (skill_id or "").lower() == "leveling":
            if signal == "WORSENING":
                return (
                    f"No seu foco de {label}, o nível final médio caiu de {previous} "
                    f"para {recent} nas cinco partidas mais recentes. Isso não significa "
                    "que suas decisões de Leveling pioraram; mostra apenas que sua "
                    "progressão final vem terminando em níveis mais baixos."
                )
            if signal == "IMPROVING":
                return (
                    f"No seu foco de {label}, o nível final médio subiu de {previous} "
                    f"para {recent}. Isso não prova melhora nas decisões de Leveling; "
                    "mostra apenas uma mudança no ponto final da progressão."
                )
            if signal in ("RECURRING_LOW", "ATYPICAL_LOW"):
                return (
                    f"No seu foco de {label}, o nível final atual ficou abaixo do seu "
                    "padrão recente. Como não temos o timing de XP, isso não permite "
                    "julgar a qualidade do planejamento."
                )
            return (
                f"No seu foco de {label}, o nível final permaneceu relativamente "
                f"estável entre os blocos ({previous} → {recent}). O timing e o "
                "contexto da compra de XP continuam sendo necessários para avaliar "
                "a missão diretamente."
            )

        return (
            f"Em {label}, o histórico mostra {metric.label.lower()} em "
            f"{previous} → {recent}. Essa mudança é descritiva e não prova "
            "qualidade da decisão treinada."
        )

    @classmethod
    def _public_item(cls, metric):
        signal = cls._signal(metric)
        if signal in ("STABLE", "INSUFFICIENT"):
            return None

        recent = cls._fmt(metric.recent_mean)
        previous = cls._fmt(metric.previous_mean)
        quality = metric.metric_id in cls.QUALITY_DIRECTION_METRICS

        if metric.metric_id == "gold_left":
            if signal == "IMPROVING":
                text = (
                    f"O ouro restante médio subiu de {previous} para {recent}. "
                    "Isso é uma mudança de comportamento, não uma melhora automática: "
                    "terminar com mais ouro pode significar boa reserva ou recursos "
                    "não convertidos antes da eliminação."
                )
            elif signal == "WORSENING":
                text = (
                    f"O ouro restante médio caiu de {previous} para {recent}. "
                    "Isso é uma mudança de comportamento, não uma piora automática: "
                    "gastar mais pode ser correto dependendo de vida, tabuleiro e lobby."
                )
            else:
                text = (
                    f"O ouro restante mostrou um sinal recorrente em torno do seu "
                    "padrão. Sem o contexto dos gastos, não tratamos isso como qualidade."
                )
            return HistoricalInterpretationItem(
                metric.metric_id, "Uso de recursos", text, 55, signal, False
            )

        if signal == "IMPROVING":
            phrase = "vem melhorando" if quality else "vem subindo"
        elif signal == "WORSENING":
            phrase = "vem piorando" if quality else "vem caindo"
        elif signal == "RECURRING_LOW":
            phrase = "aparece repetidamente abaixo do seu padrão"
        elif signal == "RECURRING_HIGH":
            phrase = "aparece repetidamente acima do seu padrão"
        elif signal == "ATYPICAL_LOW":
            phrase = "ficou abaixo do padrão nesta partida, sem repetição forte"
        else:
            phrase = "ficou acima do padrão nesta partida, sem repetição forte"

        text = (
            f"{metric.label} {phrase}. O bloco anterior ficou em {previous} e o "
            f"recente em {recent}. "
        )
        if quality:
            text += (
                "Isso descreve uma tendência de resultado, mas não identifica "
                "qual decisão causou a mudança."
            )
        else:
            text += (
                "A direção é estatística; não tratamos mais ou menos como qualidade "
                "sem contexto adicional."
            )

        importance = {
            "placement": 90,
            "total_damage_to_players": 80,
            "players_eliminated": 65,
            "level": 70,
        }.get(metric.metric_id, 50)

        return HistoricalInterpretationItem(
            metric.metric_id,
            metric.label,
            text,
            importance,
            signal,
            quality,
        )

    @staticmethod
    def _focus_metric_id(skill_id: str | None) -> str | None:
        mapping = {
            "leveling": "level",
            "economy": "gold_left",
        }
        return mapping.get((skill_id or "").lower())

    @staticmethod
    def _signal(metric) -> str | None:
        if metric is None:
            return None
        return getattr(metric.signal, "value", str(metric.signal))

    @staticmethod
    def _fmt(value: float | None) -> str:
        if value is None:
            return "-"
        return f"{value:.2f}".replace(".", ",")
