import base64
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from partner_platform.components import (
    empty_state,
    executive_card,
    insight_banner,
    section_header,
)
from partner_platform.components.post_match_report import (
    render_post_match_report,
)
from partner_platform.components.composition_intelligence import (
    render_composition_intelligence,
)
from partner_platform.components.contest_intelligence import (
    render_contest_intelligence,
)
from partner_platform.components.economy_intelligence import (
    render_economy_intelligence,
)
from partner_platform.components.carry_item_intelligence import (
    render_carry_item_intelligence,
)
from partner_platform.components.pre_match_coach import (
    build_pre_match_coach,
    render_pre_match_coach,
)
from partner_platform.intelligence import (
    build_benchmark_insights,
)
from partner_platform.intelligence.coach_message_engine import (
    build_coach_messages,
    coach_messages_payload,
)
from partner_platform.intelligence.local_coach_narrator import (
    LocalCoachNarrator,
)
from partner_platform.intelligence.global_priority_engine import (
    build_global_priority,
)
from partner_platform.intelligence.strategic_coach_messages import (
    build_strategic_coach_messages,
)
from partner_platform.platform_core import PlatformPage
from partner_platform.session import PlayerSessionStore
from partner_platform.theme import apply_chart_theme
from partner_platform.ui import friendly_exception


BENCHMARK_OPTIONS = {
    "Fundamentos (IronSilver)": "novice",
    "Competitivo (GoldPlatinum)": "intermediate",
    "Avançado (EmeraldDiamond)": "advanced",
    "Especialista (Master)": "expert",
    "Elite (GMChallenger)": "elite",
    "Challenger BR  percentis exatos": "challenger_br",
}

TIER_OPTIONS = (
    "Iron",
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Emerald",
    "Diamond",
    "Master",
    "Grandmaster",
    "Challenger",
)

NEXT_LEVEL_BENCHMARK = {
    "Iron": "novice",
    "Bronze": "novice",
    "Silver": "intermediate",
    "Gold": "intermediate",
    "Platinum": "advanced",
    "Emerald": "advanced",
    "Diamond": "expert",
    "Master": "elite",
    "Grandmaster": "challenger_br",
    "Challenger": "challenger_br",
}

NEXT_TIER = {
    "Iron": "Bronze",
    "Bronze": "Silver",
    "Silver": "Gold",
    "Gold": "Platinum",
    "Platinum": "Emerald",
    "Emerald": "Diamond",
    "Diamond": "Master",
    "Master": "Grandmaster",
    "Grandmaster": "Challenger",
    "Challenger": "Challenger",
}

METRIC_LABELS = {
    "Top 4": "Taxa de Top 4",
    "Win rate": "Taxa de vitória",
    "Average placement": "Colocação média",
    "Average level": "Nível médio",
    "Damage": "Dano aos jogadores",
    "Consistency": "Consistência",
    "top4_rate": "Taxa de Top 4",
    "win_rate": "Taxa de vitória",
    "average_placement": "Colocação média",
    "average_level": "Nível médio",
    "average_damage_to_players": "Dano aos jogadores",
    "placement_standard_deviation": "Consistência",
    "average_players_eliminated": "Eliminações por partida",
    "average_gold_left": "Ouro restante",
    "bottom4_rate": "Taxa de Bottom 4",
}

ASSESSMENT_LABELS = {
    "Elite Challenger level": "Nível de elite Challenger",
    "Above Challenger median": "Acima da mediana Challenger",
    "Near upper Challenger range": "Próximo da faixa superior Challenger",
    "Near Challenger median": "Próximo da mediana Challenger",
    "Below Challenger median": "Abaixo da mediana Challenger",
    "Large gap to Challenger reference": "Gap elevado para a referência Challenger",
    "Acima da referência": "Acima da referência",
    "Na referência": "Na referência",
    "Abaixo da referência": "Abaixo da referência",
}

CLASSIFICATION_LABELS = {
    "Challenger-like": "Perfil próximo de Challenger",
    "Very competitive": "Muito competitivo",
    "Competitive": "Competitivo",
    "Developing": "Em desenvolvimento",
    "Large benchmark gap": "Gap elevado",
    "Acima da referência": "Acima da referência",
    "Competitivo": "Competitivo",
    "Abaixo da referência": "Abaixo da referência",
    "Sem dados": "Sem dados",
}


def _metric_label(value: str) -> str:
    return METRIC_LABELS.get(value, value)


def _public_coach_text(value: str) -> str:
    """
    Normaliza termos públicos sem corromper palavras portuguesas.

    "contest" é termo interno.
    Para o jogador usamos "contestação", preservando palavras como
    "contestado", "contestada", "contestados" e "contestadas".
    """
    text = str(value or "")

    malformed = (
        ("Contestaçãoação", "Contestação"),
        ("contestaçãoação", "contestação"),
        ("Contestaçãoado", "Contestado"),
        ("contestaçãoado", "contestado"),
        ("Contestaçãoada", "Contestada"),
        ("contestaçãoada", "contestada"),
        ("Contestaçãoados", "Contestados"),
        ("contestaçãoados", "contestados"),
        ("Contestaçãoadas", "Contestadas"),
        ("contestaçãoadas", "contestadas"),
    )

    for old, new in malformed:
        text = text.replace(old, new)

    semantic_patterns = (
        (
            r"\bcontest\s+score\b",
            "índice de contestação",
        ),
        (
            r"\bhigh\s+contest\b",
            "alta contestação",
        ),
        (
            r"\bcontest\b",
            "contestação",
        ),
    )

    for pattern, replacement in semantic_patterns:
        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    return text


def _human_stage_label(value: str) -> str:
    mapping = {
        "NOVICE": "Fundamentos",
        "INTERMEDIATE": "Competitivo",
        "ADVANCED": "Avançado",
        "EXPERT": "Especialista",
        "ELITE": "Elite",
        "TOP1": "Topo do servidor",
    }
    normalized = str(value or "").strip()
    return mapping.get(
        normalized.upper(),
        normalized or "Em avaliação",
    )


def _analysis_competitive_context(report: dict) -> dict:
    analysis = _analysis_payload(report)

    value = analysis.get("competitive_context")
    if isinstance(value, dict):
        return value

    value = report.get("competitive_context")
    return value if isinstance(value, dict) else {}


def _analysis_spectrum(report: dict) -> dict:
    context = _analysis_competitive_context(report)

    value = context.get("spectrum")
    if isinstance(value, dict):
        return value

    analysis = _analysis_payload(report)
    value = analysis.get("spectrum")
    return value if isinstance(value, dict) else {}


def _spectrum_band_sentence(spectrum: dict) -> str:
    if not spectrum.get("available"):
        return (
            "Ainda não há população individual suficiente para posicionar "
            "você dentro deste grupo competitivo."
        )

    band = str(
        spectrum.get("spectrum_band") or "posição atual"
    ).strip()

    percentile = spectrum.get("spectrum_percentile")
    population = int(
        spectrum.get("population_size") or 0
    )

    if percentile is None:
        return f"Você está na faixa {band.lower()} deste grupo competitivo."

    pct = max(0.0, min(float(percentile) * 100.0, 100.0))

    if pct <= 10:
        moment = "no início"
    elif pct < 40:
        moment = "na primeira metade"
    elif pct < 70:
        moment = "na região central"
    elif pct < 90:
        moment = "na parte superior"
    else:
        moment = "próximo do topo"

    suffix = (
        f", comparado com {population} jogadores da amostra"
        if population
        else ""
    )

    return (
        f"Você está {moment} deste grupo competitivo "
        f"(faixa {band.lower()}){suffix}. "
        "Essa posição descreve onde seu elo está no grupo; "
        "não é uma previsão de promoção."
    )


def _render_spectrum_bar(
    *,
    spectrum: dict,
    rank_label: str,
    benchmark_name: str,
) -> None:
    if not spectrum.get("available"):
        insight_banner(
            eyebrow="Sua posição no grupo",
            title="Espectro ainda indisponível",
            description=_spectrum_band_sentence(spectrum),
            tone="neutral",
        )
        return

    percentile = float(
        spectrum.get("spectrum_percentile") or 0.0
    )
    percentile = max(
        0.0,
        min(
            percentile,
            1.0,
        ),
    )

    band = str(
        spectrum.get("spectrum_band") or "Entrada"
    )

    insight_banner(
        eyebrow="Sua posição no grupo competitivo",
        title=f"{rank_label} · {band}",
        description=(
            f"Seu elo está na faixa {band.lower()} do grupo "
            f"{benchmark_name}."
        ),
        tone="neutral",
    )

    st.progress(
        percentile,
        text=(
            f"Posição relativa no grupo: "
            f"{percentile * 100:.0f}%"
        ),
    )

    labels = st.columns(4)

    with labels[0]:
        st.caption("Entrada")

    with labels[1]:
        st.caption("Consolidação")

    with labels[2]:
        st.caption("Avançado")

    with labels[3]:
        st.caption("Transição")

    st.caption(
        _spectrum_band_sentence(spectrum)
    )


def _spectrum_profile_rows(
    spectrum: dict,
) -> list[dict]:
    labels = {
        "STRENGTH": "Ponto forte",
        "NEUTRAL": "Dentro do padrão",
        "ATTENTION": "Ponto de atenção",
    }

    rows = []

    for item in spectrum.get(
        "performance_profile",
        [],
    ):
        if not isinstance(item, dict):
            continue

        classification = str(
            item.get("classification") or "NEUTRAL"
        )

        rows.append(
            {
                "Fundamento": _metric_label(
                    str(item.get("metric") or "-")
                ),
                "Leitura": labels.get(
                    classification,
                    "Dentro do padrão",
                ),
                "Score comparativo": round(
                    float(item.get("score") or 0.0),
                    1,
                ),
            }
        )

    return rows


def _benchmark_label_from_id(benchmark_id: str) -> str:
    for label, value in BENCHMARK_OPTIONS.items():
        if value == benchmark_id:
            return label

    return benchmark_id


def _player_label(
    item: dict,
) -> str:
    tag = item.get(
        "tag_line",
        "",
    )

    return (
        item.get(
            "game_name",
            "Desconhecido",
        )
        + (
            f" #{tag}"
            if tag
            else ""
        )
    )


def _relative_gap_percent(item: dict) -> float:
    benchmark_value = item.get(
        "benchmark_mean",
        item.get("challenger_mean"),
    )

    if benchmark_value in (None, 0):
        return 0.0

    performance_delta = float(
        item.get("performance_delta", 0.0)
    )

    return (
        performance_delta
        / abs(float(benchmark_value))
        * 100.0
    )


def _recommendation_from_item(
    item: dict,
    *,
    benchmark_name: str,
) -> tuple[str, str]:
    label = _metric_label(
        item.get("label", item.get("metric", "Métrica"))
    )
    gap = _relative_gap_percent(item)

    if gap >= 0:
        return (
            f"Manter {label}",
            (
                f"Você já está {abs(gap):.1f}% acima da referência "
                f"{benchmark_name}. Preserve esse padrão enquanto trabalha "
                "nos gaps prioritários."
            ),
        )

    magnitude = abs(gap)

    if magnitude >= 20:
        priority = "Prioridade crítica"
    elif magnitude >= 10:
        priority = "Prioridade alta"
    elif magnitude >= 5:
        priority = "Prioridade moderada"
    else:
        priority = "Ajuste fino"

    return (
        f"{priority}: {label}",
        (
            f"Você está {magnitude:.1f}% abaixo de {benchmark_name} nessa "
            "dimensão. Use esta métrica como foco principal nas próximas "
            "partidas e acompanhe se o gap reduz ao longo da amostra."
        ),
    )


def _benchmark_selector() -> tuple[str, str, str, str | None, str | None]:
    selector_left, selector_right = st.columns(
        [1.25, 1]
    )

    with selector_left:
        comparison_mode = st.radio(
            "Modo de comparação",
            (
                "Escolher referência",
                "Próximo nível",
            ),
            horizontal=True,
            key="benchmark-comparison-mode",
            help=(
                "Escolha uma referência manualmente ou informe seu elo "
                "para receber a próxima referência competitiva."
            ),
        )

    if comparison_mode == "Próximo nível":
        with selector_right:
            current_tier = st.selectbox(
                "Seu elo atual",
                TIER_OPTIONS,
                index=3,
                key="benchmark-current-tier",
            )

        benchmark_id = NEXT_LEVEL_BENCHMARK[
            current_tier
        ]
        selected_label = _benchmark_label_from_id(
            benchmark_id
        )
        selector_context = (
            f"Progressão sugerida para {current_tier}"
        )
        return (
            benchmark_id,
            selected_label,
            selector_context,
            current_tier,
            NEXT_TIER[current_tier],
        )

    with selector_right:
        selected_label = st.selectbox(
            "Benchmark de comparação",
            list(BENCHMARK_OPTIONS),
            index=5,
            key="benchmark-reference-selector",
            help=(
                "Benchmarks por faixa utilizam dados agregados. "
                "Challenger BR possui distribuição individual e "
                "permite calcular percentis reais."
            ),
        )

    return (
        BENCHMARK_OPTIONS[selected_label],
        selected_label,
        "Referência escolhida manualmente",
        None,
        None,
    )



def _friendly_evidence_label(key: str) -> str:
    labels = {
        "diversity_rate": "Diversidade de composições",
        "usage_rate": "Uso da composição mais frequente",
        "repetition_rate": "Taxa de repetição",
        "matches": "Partidas com essa composição",
        "average_placement": "Colocação média",
        "top4_rate": "Taxa de Top 4",
        "carry": "Carry mais frequente",
        "carry_contest_rate": "Carry contestado",
        "high_contest_rate": "Contestação alta",
        "placement_impact": "Impacto observado na colocação",
        "placement_impact_label": "Classificação do impacto",
        "flexibility_label": "Classificação da flexibilidade",
        "confidence": "Confiança da recomendação",
        "most_contested_unit": "Unidade mais contestada",
        "latest_carry": "Carry da partida mais recente",
        "latest_carry_contested": "Carry recente terminou contestado",
        "latest_opponents": "Adversários contestando o carry",
        "score": "Score econômico",
        "label": "Classificação econômica",
        "average_gold_left": "Ouro restante médio",
        "average_level": "Nível médio",
        "level_8_rate": "Chegou ao nível 8",
        "level_9_rate": "Chegou ao nível 9",
        "low_level_late_rate": "Partidas longas terminando em nível baixo",
    }
    return labels.get(key, key.replace("_", " ").capitalize())


def _friendly_evidence_value(key: str, value: object) -> str:
    if isinstance(value, bool):
        return "Sim" if value else "Não"

    if isinstance(value, (int, float)):
        percentage_keys = {
            "diversity_rate", "usage_rate", "repetition_rate", "top4_rate",
            "carry_contest_rate", "high_contest_rate", "confidence",
            "level_8_rate", "level_9_rate", "low_level_late_rate",
        }

        if key in percentage_keys:
            return f"{float(value):.1f}%"
        if key == "placement_impact":
            return f"{float(value):+.2f} posições"
        if key in {
            "average_placement", "average_level",
            "average_gold_left", "score",
        }:
            return f"{float(value):.2f}"
        if isinstance(value, int):
            return str(value)
        return f"{float(value):.2f}"

    return str(value)


def _build_next_match_focus(
    strategic_messages: list[dict],
) -> str | None:
    if not strategic_messages:
        return None

    priority = next(
        (item for item in strategic_messages if item.get("role") == "priority"),
        None,
    )
    if priority is None:
        priority = next(
            (item for item in strategic_messages if item.get("role") == "adjustment"),
            None,
        )

    if priority is None:
        return (
            "Seu histórico não aponta um ajuste estratégico dominante agora. "
            "Preserve os padrões que aparecem como força e use as próximas "
            "partidas para confirmar se eles continuam estáveis."
        )

    metric = priority.get("metric")
    evidence = priority.get("evidence", {})

    if metric == "contest_pattern":
        carry_rate = evidence.get("carry_contest_rate")
        impact = evidence.get("placement_impact")
        rate_text = (
            f" ({float(carry_rate):.1f}% na amostra)"
            if isinstance(carry_rate, (int, float))
            else ""
        )

        if isinstance(impact, (int, float)) and float(impact) >= 0.5:
            return (
                "Antes de comprometer muitos recursos com o carry, confira "
                f"o quanto ele já está disputado no lobby{rate_text}. Como "
                "a amostra também mostra piora de colocação quando há "
                "contestação, trate esse sinal como parte importante da "
                "decisão de manter a linha ou usar uma alternativa."
            )

        return (
            "Antes de comprometer muitos recursos com o carry, confira "
            f"o quanto ele já está disputado no lobby{rate_text}. Não "
            "abandone a linha automaticamente: use a contestação como mais "
            "uma informação na decisão, porque o histórico ainda não mostra "
            "impacto negativo claro na colocação."
        )

    if metric == "composition_pattern":
        return (
            "Nas próximas partidas, observe se sua composição preferida "
            "continua sendo a melhor linha quando o lobby muda. A ideia não "
            "é evitar uma composição conhecida, mas perceber cedo quando a "
            "partida oferece uma alternativa melhor."
        )

    if metric == "economy_pattern":
        return (
            "Nas próximas partidas, preste atenção à conversão dos recursos "
            "antes da eliminação. Use esse ponto como foco de observação sem "
            "inventar um timing específico que o histórico não consegue medir."
        )

    return priority.get("message")




def _build_coach_fallback_narrative(
    strategic_messages: list[dict],
    coach_messages: list,
) -> str:
    """
    Fallback determinístico para quando o narrador local/Ollama
    não estiver disponível ou a resposta for rejeitada.

    Usa somente mensagens já calculadas pelo TFT Insight.
    """
    paragraphs: list[str] = []

    priority = next(
        (
            item
            for item in strategic_messages
            if item.get("role") == "priority"
        ),
        None,
    )

    adjustment = next(
        (
            item
            for item in strategic_messages
            if item.get("role") == "adjustment"
        ),
        None,
    )

    strengths = [
        item
        for item in strategic_messages
        if item.get("role") == "strength"
    ]

    if priority:
        paragraphs.append(
            str(priority.get("message", "")).strip()
        )
    elif adjustment:
        paragraphs.append(
            str(adjustment.get("message", "")).strip()
        )
    elif coach_messages:
        paragraphs.append(
            str(coach_messages[0].message).strip()
        )

    # Complementa a prioridade com no máximo dois pontos fortes.
    for item in strengths[:2]:
        text = str(
            item.get("message", "")
        ).strip()

        if text:
            paragraphs.append(text)

    # Se não houver contexto estratégico suficiente, reaproveita
    # mensagens determinísticas do benchmark.
    if len(paragraphs) < 2:
        for item in coach_messages:
            text = str(
                item.message
            ).strip()

            if (
                text
                and text not in paragraphs
            ):
                paragraphs.append(text)

            if len(paragraphs) >= 3:
                break

    paragraphs = [
        paragraph
        for paragraph in paragraphs
        if paragraph
    ]

    if not paragraphs:
        return (
            "A análise foi concluída, mas não há mensagens suficientes "
            "para montar uma leitura de coach nesta amostra."
        )

    return "\n\n".join(
        paragraphs[:3]
    )




def _find_latest_training_cycle_for_skill(
    history: list,
    *,
    skill_id: str,
) -> dict | None:
    for cycle in history:
        if not isinstance(
            cycle,
            dict,
        ):
            continue

        if str(
            cycle.get(
                "skill_id",
                "",
            )
        ) == skill_id:
            return cycle

    return None


def _training_result_summary(
    evaluation: dict | None,
) -> tuple[str, str]:
    if not isinstance(
        evaluation,
        dict,
    ):
        return (
            "Sem avaliação anterior",
            "O ciclo anterior dessa Skill ainda não possui uma avaliação Before/After.",
        )

    result = str(
        evaluation.get(
            "result",
            "INCONCLUSIVE",
        )
    ).upper()

    confidence = str(
        evaluation.get(
            "confidence",
            "LOW",
        )
    ).upper()

    result_labels = {
        "POSITIVE": " Mudança positiva observada",
        "STABLE": " Indicadores estáveis",
        "NEGATIVE": " Mudança negativa observada",
        "INCONCLUSIVE": "? Resultado inconclusivo",
    }

    confidence_labels = {
        "HIGH": "alta",
        "MODERATE": "moderada",
        "LOW": "baixa",
    }

    score = float(
        evaluation.get(
            "confidence_score",
            0.0,
        )
        or 0.0
    )

    return (
        result_labels.get(
            result,
            result,
        ),
        (
            "Confiança "
            f"{confidence_labels.get(confidence, confidence.lower())}"
            f" · {score:.0f}%"
        ),
    )


def _mission_progress_dots(
    *,
    completed: int,
    target: int,
) -> str:
    safe_target = max(
        int(target),
        0,
    )

    safe_completed = max(
        0,
        min(
            int(completed),
            safe_target,
        ),
    )

    return " ".join(
        (
            ""
            if index < safe_completed
            else ""
        )
        for index in range(
            safe_target
        )
    )


def _mission_status(
    *,
    completed: int,
    target: int,
    is_completed: bool,
) -> tuple[str, str]:
    if is_completed:
        return (
            "Ciclo concluído",
            "As partidas do ciclo foram concluídas. "
            "O histórico e a avaliação do treino serão atualizados pelo TFT Insight.",
        )

    if completed <= 0:
        return (
            "Novo ciclo",
            "O exercício já está ativo. "
            "Somente partidas novas contam para este ciclo.",
        )

    remaining = max(
        target - completed,
        0,
    )

    return (
        "Em progresso",
        (
            f"Faltam {remaining} partida(s) para concluir este ciclo."
            if remaining
            else "Ciclo em fase final."
        ),
    )


def _render_training_mission(
    training: dict | None,
) -> None:
    """
    Training Experience UI V2.

    A UI apresenta o estado pedagógico, mas não recalcula prioridade,
    avaliação, progresso ou exercício.
    """

    if not isinstance(training, dict):
        return

    mission = training.get("mission")

    if not isinstance(mission, dict):
        return

    skill_id = str(
        mission.get("skill_id", "")
        or ""
    )

    skill_name = str(
        mission.get(
            "skill_name",
            skill_id or "Treino",
        )
    )

    title = str(
        mission.get(
            "title",
            "Missão atual",
        )
    )

    objective = str(
        mission.get(
            "objective",
            "",
        )
        or ""
    ).strip()

    completed = int(
        mission.get(
            "games_completed",
            0,
        )
        or 0
    )

    target = int(
        mission.get(
            "games_target",
            0,
        )
        or 0
    )

    remaining = int(
        mission.get(
            "remaining_games",
            max(target - completed, 0),
        )
        or 0
    )

    progress_percentage = float(
        mission.get(
            "progress_percentage",
            0.0,
        )
        or 0.0
    )

    progress_value = max(
        0.0,
        min(
            progress_percentage / 100.0,
            1.0,
        ),
    )

    is_completed = bool(
        mission.get(
            "is_completed",
            False,
        )
    )

    checklist = mission.get(
        "checklist",
        [],
    )

    history = training.get(
        "history",
        [],
    )

    if not isinstance(history, list):
        history = []

    latest_cycle = (
        history[0]
        if history
        and isinstance(history[0], dict)
        else None
    )

    previous_same_skill = (
        _find_latest_training_cycle_for_skill(
            history,
            skill_id=skill_id,
        )
        if skill_id
        else None
    )

    is_new_cycle = (
        completed == 0
        and not is_completed
        and latest_cycle is not None
    )

    current_priority_id = training.get(
        "current_priority_skill_id"
    )

    current_priority_name = training.get(
        "current_priority_name"
    )

    mission_skill_id = mission.get(
        "skill_id"
    )

    has_next_priority = bool(
        current_priority_id
        and mission_skill_id
        and current_priority_id != mission_skill_id
    )

    section_header(
        "Treino atual",
        subtitle=(
            "Um foco por ciclo. "
            "Acompanhe o exercício, o progresso e a próxima transição."
        ),
    )

    mission_columns = st.columns(
        [1.2, 1, 1]
    )

    with mission_columns[0]:
        executive_card(
            title="Foco",
            value=skill_name,
            caption="Skill em treinamento",
            icon="",
        )

    with mission_columns[1]:
        executive_card(
            title="Progresso",
            value=f"{completed}/{target}",
            caption=(
                "Ciclo concluído"
                if is_completed
                else "Partidas do ciclo"
            ),
            icon="",
        )

    with mission_columns[2]:
        executive_card(
            title="Restantes",
            value=str(remaining),
            caption=(
                "Pronto para transição"
                if is_completed
                else "Partidas para concluir"
            ),
            icon="",
        )

    # 9.5  Completed Cycle Experience
    if is_completed:
        completed_description = (
            "As partidas previstas para este ciclo foram concluídas. "
            "O TFT Insight já pode arquivar o treino, avaliar o Before/After "
            "e transformar a prioridade atual na próxima missão."
        )

        if has_next_priority:
            completed_description += (
                " A próxima prioridade identificada é "
                f"{current_priority_name or current_priority_id}."
            )

        insight_banner(
            eyebrow="Ciclo concluído",
            title=f"{skill_name} · {title}",
            description=completed_description,
            tone="positive",
        )

    # Novo ciclo recém-criado.
    elif is_new_cycle:
        previous_skill = str(
            latest_cycle.get(
                "skill_name",
                latest_cycle.get(
                    "skill_id",
                    "treino anterior",
                ),
            )
        )

        if isinstance(
            previous_same_skill,
            dict,
        ):
            previous_task_title = str(
                previous_same_skill.get(
                    "title",
                    "exercício anterior",
                )
            )

            result_label, confidence_label = (
                _training_result_summary(
                    previous_same_skill.get(
                        "evaluation"
                    )
                )
            )

            current_task_id = str(
                mission.get(
                    "task_id",
                    "",
                )
                or ""
            )

            previous_task_id = str(
                previous_same_skill.get(
                    "task_id",
                    "",
                )
                or ""
            )

            rotated = (
                current_task_id
                and previous_task_id
                and current_task_id
                != previous_task_id
            )

            transition_description = (
                f"O ciclo anterior de {previous_skill} foi concluído. "
                f"Em {skill_name}, você já treinou {previous_task_title}: "
                f"{result_label.lower()}, {confidence_label.lower()}."
            )

            if rotated:
                transition_description += (
                    " O exercício foi rotacionado para este novo ciclo."
                )
        else:
            transition_description = (
                f"O ciclo anterior de {previous_skill} foi concluído. "
                f"A prioridade atual agora é {skill_name}."
            )

        insight_banner(
            eyebrow="Novo ciclo",
            title=f"{skill_name} · {title}",
            description=transition_description,
            tone="neutral",
        )

    # Exercício é o centro do treino enquanto o ciclo estiver ativo.
    if not is_completed:
        insight_banner(
            eyebrow="Exercício atual",
            title=title,
            description=(
                objective
                or "Continue executando o foco definido para este ciclo."
            ),
            tone="neutral",
        )

    status_title, status_description = (
        _mission_status(
            completed=completed,
            target=target,
            is_completed=is_completed,
        )
    )

    progress_dots = _mission_progress_dots(
        completed=completed,
        target=target,
    )

    progress_columns = st.columns(
        [1.4, 1]
    )

    with progress_columns[0]:
        st.markdown(
            f"**{progress_dots}**"
        )

    with progress_columns[1]:
        st.markdown(
            f"**{completed}/{target} partidas**"
        )

    st.caption(
        f"{status_title} · {status_description}"
    )

    st.progress(
        progress_value
    )

    if checklist and not is_completed:
        st.markdown(
            "#### Checklist para a partida"
        )
        st.caption(
            "Use estas perguntas como lembrete de decisão; "
            "não é necessário marcar nada no TFT Insight."
        )

        with st.container(
            border=True
        ):
            for item in checklist:
                st.markdown(
                    f" {item}"
                )

    cycle_stage_label = str(
        training.get(
            "cycle_stage_label",
            "",
        )
        or ""
    ).strip()

    cycle_message = str(
        training.get(
            "cycle_message",
            "",
        )
        or ""
    ).strip()

    if (
        cycle_stage_label
        and cycle_message
        and not is_new_cycle
        and not is_completed
    ):
        st.caption(
            f"**{cycle_stage_label}:** "
            f"{cycle_message}"
        )

    # 9.6  Próximo foco / transição
    if has_next_priority:
        if is_completed:
            transition_title = (
                "Próxima missão pronta para transição"
            )
            transition_description = (
                "O ciclo atual já terminou. Na próxima atualização do coach, "
                f"{current_priority_name or current_priority_id} pode assumir "
                "como nova missão."
            )
            eyebrow = "Próximo passo"
        else:
            transition_title = (
                "Nova prioridade detectada"
            )
            transition_description = (
                "A análise identificou "
                f"{current_priority_name or current_priority_id} como próxima "
                "prioridade, mas a missão atual permanece protegida até o 5/5."
            )
            eyebrow = "Depois deste ciclo"

        insight_banner(
            eyebrow=eyebrow,
            title=transition_title,
            description=transition_description,
            tone="neutral",
        )

    if (
        previous_same_skill
        and not is_new_cycle
        and completed > 0
        and not is_completed
    ):
        previous_task_title = str(
            previous_same_skill.get(
                "title",
                "exercício anterior",
            )
        )

        result_label, confidence_label = (
            _training_result_summary(
                previous_same_skill.get(
                    "evaluation"
                )
            )
        )

        with st.expander(
            f"Contexto do treino anterior de {skill_name}",
            expanded=False,
        ):
            st.write(
                f"Exercício anterior: {previous_task_title}"
            )
            st.caption(
                f"{result_label} · {confidence_label}"
            )


_TRAINING_RESULT_LABELS = {
    "POSITIVE": "Mudança positiva observada",
    "STABLE": "Indicadores estáveis",
    "NEGATIVE": "Mudança negativa observada",
    "INCONCLUSIVE": "Resultado inconclusivo",
}

_TRAINING_CONFIDENCE_LABELS = {
    "HIGH": "Alta",
    "MODERATE": "Moderada",
    "LOW": "Baixa",
}

_TRAINING_METRIC_LABELS = {
    "average_level": "Nível médio",
    "average_damage_to_players": "Dano a jogadores",
    "average_players_eliminated": "Eliminações",
    "placement_standard_deviation": "Oscilação de colocação",
    "average_gold_left": "Ouro restante",
}


def _training_delta_text(
    relative_change,
) -> str:
    if not isinstance(
        relative_change,
        (int, float),
    ):
        return "sem delta disponível"

    return (
        f"{float(relative_change) * 100:+.2f}%"
    )


_SKILL_LABELS = {
    "leveling": "Leveling",
    "consistency": "Consistência",
    "board_pressure": "Pressão de tabuleiro",
    "economy": "Economia",
}


_LEARNING_TREND_LABELS = {
    "INSUFFICIENT_HISTORY": "Histórico insuficiente",
    "IMPROVING": "Melhorando",
    "STABLE": "Estável",
    "REGRESSING": "Regredindo",
}

_LEARNING_ACTION_LABELS = {
    "CONTINUE": "Continuar",
    "ROTATE_TASK": "Rotacionar exercício",
    "REASSESS": "Reavaliar abordagem",
    "COOLDOWN_SKILL": "Pausa pedagógica",
}

_TASK_DIFFICULTY_LABELS = {
    "FOUNDATION": "Fundamentos",
    "INTERMEDIATE": "Intermediário",
    "ADVANCED": "Avançado",
}


def _render_learning_state(
    training: dict | None,
) -> None:
    if not isinstance(
        training,
        dict,
    ):
        return

    learning_state = training.get(
        "learning_state"
    )

    if not isinstance(
        learning_state,
        dict,
    ):
        return

    skills = learning_state.get(
        "skills",
        {},
    )

    if not isinstance(
        skills,
        dict,
    ) or not skills:
        return

    current_skill_id = (
        learning_state.get(
            "current_skill_id"
        )
    )

    section_header(
        "Estado de aprendizagem",
        subtitle=(
            "Memória pedagógica dos ciclos já concluídos. "
            "Ela orienta como treinar, sem substituir a prioridade atual."
        ),
    )

    ordered_skills = sorted(
        skills.items(),
        key=lambda item: (
            0
            if item[0] == current_skill_id
            else 1,
            item[0],
        ),
    )

    for skill_id, state in ordered_skills:
        if not isinstance(
            state,
            dict,
        ):
            continue

        skill_name = _SKILL_LABELS.get(
            skill_id,
            skill_id.replace(
                "_",
                " ",
            ).title(),
        )

        trend = str(
            state.get(
                "trend",
                "INSUFFICIENT_HISTORY",
            )
        ).upper()

        action = str(
            state.get(
                "anti_loop_action",
                "CONTINUE",
            )
        ).upper()

        difficulty = state.get(
            "current_difficulty"
        )

        cycles_total = int(
            state.get(
                "cycles_total",
                0,
            )
            or 0
        )

        conclusive = int(
            state.get(
                "conclusive_cycles",
                0,
            )
            or 0
        )

        latest_result = (
            state.get(
                "latest_result"
            )
        )

        is_current = (
            skill_id
            == current_skill_id
        )

        label = (
            f"{' ' if is_current else ''}"
            f"{skill_name} · "
            f"{_LEARNING_TREND_LABELS.get(trend, trend)}"
        )

        with st.expander(
            label,
            expanded=is_current,
        ):
            cols = st.columns(
                [1, 1, 1]
            )

            with cols[0]:
                st.caption(
                    "Ciclos"
                )
                st.markdown(
                    f"**{cycles_total}**"
                )

            with cols[1]:
                st.caption(
                    "Conclusivos"
                )
                st.markdown(
                    f"**{conclusive}**"
                )

            with cols[2]:
                st.caption(
                    "ltimo resultado"
                )
                st.markdown(
                    f"**{latest_result or ''}**"
                )

            st.write(
                "**Leitura do coach:** "
                + _LEARNING_TREND_LABELS.get(
                    trend,
                    trend,
                )
            )

            st.caption(
                "Ação anti-loop: "
                + _LEARNING_ACTION_LABELS.get(
                    action,
                    action,
                )
            )

            if difficulty:
                difficulty_value = str(
                    difficulty
                ).upper()

                st.caption(
                    "Dificuldade atual: "
                    + _TASK_DIFFICULTY_LABELS.get(
                        difficulty_value,
                        difficulty_value,
                    )
                )

            progression = str(
                state.get(
                    "task_progression",
                    "HOLD",
                )
            ).upper()

            st.caption(
                f"Sinal de progressão: {progression}"
            )


_PROGRESS_STATUS_LABELS = {
    "IMPROVING": "Em evolução",
    "STABLE": "Estável",
    "NEEDS_ATTENTION": "Pede atenção",
    "INSUFFICIENT_HISTORY": "Histórico em construção",
}

_PROGRESS_CONFIDENCE_LABELS = {
    "LOW": "Baixa",
    "MODERATE": "Moderada",
    "HIGH": "Alta",
}

_PROGRESS_LEVEL_LABELS = {
    "NOT_EVALUATED": "Não avaliado",
    "BEGINNER": "Iniciante",
    "DEVELOPING": "Em desenvolvimento",
    "COMPETENT": "Competente",
    "ADVANCED": "Avançado",
    "MASTERED": "Dominado",
}


def _render_progress_dashboard(
    progress: dict | None,
) -> None:
    if not isinstance(progress, dict):
        return

    timelines = progress.get("timelines", {})
    overall = progress.get("overall_development", {})
    insights = progress.get("insights", [])
    milestones = progress.get("milestones", [])
    snapshot_count = int(progress.get("snapshot_count", 0) or 0)

    if not isinstance(timelines, dict) or not timelines:
        return

    section_header(
        "Sua evolução",
        subtitle=(
            "Acompanhamento longitudinal das Skills do TFT Insight. "
            "O progresso usa snapshots do Learning Profile e não o elo."
        ),
    )

    status_id = str(
        overall.get("status", "INSUFFICIENT_HISTORY")
    ).upper()
    confidence_id = str(
        overall.get("confidence", "LOW")
    ).upper()
    primary_skill = str(
        overall.get("primary_skill_id") or ""
    )

    columns = st.columns([1.2, 1, 1])

    with columns[0]:
        executive_card(
            title="Desenvolvimento",
            value=_PROGRESS_STATUS_LABELS.get(
                status_id,
                status_id,
            ),
            caption=f"{snapshot_count} snapshot(s) longitudinal(is)",
            icon="",
        )

    with columns[1]:
        executive_card(
            title="Skill em foco",
            value=_SKILL_LABELS.get(
                primary_skill,
                primary_skill,
            ),
            caption="Prioridade atual",
            icon="",
        )

    with columns[2]:
        executive_card(
            title="Confiança",
            value=_PROGRESS_CONFIDENCE_LABELS.get(
                confidence_id,
                confidence_id,
            ),
            caption="Leitura longitudinal",
            icon="",
        )

    if snapshot_count < 2:
        insight_banner(
            eyebrow="Histórico em construção",
            title="Ainda é cedo para afirmar evolução de longo prazo",
            description=(
                "Existe apenas um snapshot real do seu Learning Profile. "
                "O TFT Insight já registrou o ponto de partida, mas só vai "
                "classificar evolução quando houver novos estados comparáveis."
            ),
            tone="neutral",
        )
    else:
        primary_points = timelines.get(primary_skill, [])
        valid_points = [
            item
            for item in primary_points
            if isinstance(item, dict)
            and isinstance(item.get("score"), (int, float))
        ]

        if len(valid_points) >= 2:
            frame = pd.DataFrame(
                [
                    {
                        "Data": item.get("created_at"),
                        "Score": float(item["score"]),
                    }
                    for item in valid_points
                ]
            )

            figure = go.Figure(
                go.Scatter(
                    x=frame["Data"],
                    y=frame["Score"],
                    mode="lines+markers",
                    name=_SKILL_LABELS.get(
                        primary_skill,
                        primary_skill,
                    ),
                )
            )

            apply_chart_theme(
                figure,
                height=360,
            )
            figure.update_yaxes(
                title="Score da Skill"
            )
            figure.update_xaxes(
                title="Snapshots"
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
            )

    st.markdown("**Estado atual das Skills**")

    skill_ids = list(timelines.keys())
    for start in range(0, len(skill_ids), 2):
        row = st.columns(2)

        for column, skill_id in zip(
            row,
            skill_ids[start:start + 2],
        ):
            points = timelines.get(skill_id, [])
            if not points:
                continue

            latest = points[-1]
            score = latest.get("score")
            level_id = str(
                latest.get("level", "NOT_EVALUATED")
            ).upper()
            trend_id = str(
                latest.get(
                    "trend",
                    "INSUFFICIENT_HISTORY",
                )
            ).upper()

            with column:
                st.markdown(
                    f"**{_SKILL_LABELS.get(skill_id, skill_id)}**"
                )
                st.write(
                    (
                        f"Score: **{float(score):.2f}**"
                        if isinstance(score, (int, float))
                        else "Score: **Não avaliado**"
                    )
                )
                st.caption(
                    "Nível: "
                    + _PROGRESS_LEVEL_LABELS.get(
                        level_id,
                        level_id,
                    )
                    + " · Tendência: "
                    + _LEARNING_TREND_LABELS.get(
                        trend_id,
                        trend_id,
                    )
                    + f" · Snapshots: {len(points)}"
                )

    if isinstance(insights, list) and insights:
        st.markdown("**Leituras de progresso**")
        for item in insights[:3]:
            if not isinstance(item, dict):
                continue
            insight_banner(
                eyebrow="Evolução observada",
                title=str(
                    item.get(
                        "title",
                        "Leitura longitudinal",
                    )
                ),
                description=str(
                    item.get("message", "")
                ),
                tone=(
                    "warning"
                    if item.get("role") == "attention"
                    else "positive"
                    if item.get("role") in {"progress", "milestone"}
                    else "neutral"
                ),
            )

    if isinstance(milestones, list) and milestones:
        with st.expander(
            "Marcos detectados neste snapshot",
            expanded=False,
        ):
            for item in milestones:
                if not isinstance(item, dict):
                    continue
                st.markdown(
                    f"**{item.get('title', 'Marco')}**"
                )
                st.write(
                    item.get("description", "")
                )

    st.caption(
        "A evolução é observacional. Esta seção não escolhe a Skill, "
        "não altera a missão e não usa elo como prova de aprendizado."
    )


_ADAPTIVE_STRATEGY_LABELS = {
    "BUILD_FOUNDATION": "Construir fundamentos",
    "CONSOLIDATE": "Consolidar execução",
    "CHALLENGE": "Aumentar o desafio",
    "CHANGE_APPROACH": "Mudar a abordagem",
    "MAINTAIN": "Manter o plano",
}

_ADAPTIVE_CONFIDENCE_LABELS = {
    "LOW": "Baixa",
    "MODERATE": "Moderada",
    "HIGH": "Alta",
}


_PROGRESS_COACH_ACTION_LABELS = {
    "OBSERVE": "Observar sem reagir",
    "MAINTAIN": "Manter abordagem",
    "REINFORCE_FOUNDATION": "Reforçar fundamentos",
    "RECOGNIZE_AND_PREPARE_ADVANCE": "Reconhecer e preparar avanço",
}

_PROGRESS_COACH_SIGNAL_LABELS = {
    "WATCH": "Em observação",
    "REGRESSION": "Queda persistente",
    "IMPROVEMENT": "Melhora consistente",
    "STABLE_OR_MIXED": "Estável ou misto",
}

def _render_progress_aware_coach(payload: dict | None) -> None:
    if not isinstance(payload, dict): return
    context = payload.get("context", {}); strategy = payload.get("strategy", {}); adaptation = payload.get("adaptation", {}); explanation = payload.get("explanation", {})
    if not all(isinstance(x, dict) for x in (context,strategy,adaptation,explanation)): return
    section_header("Coach acompanhando sua evolução", subtitle="Como o histórico longitudinal influencia a abordagem do treino sem trocar sua prioridade automaticamente.")
    cols=st.columns(3)
    signal=str(context.get("signal","WATCH")).upper(); action=str(strategy.get("action","OBSERVE")).upper(); confidence=str(context.get("confidence","LOW")).upper()
    with cols[0]: executive_card(title="Sinal", value=_PROGRESS_COACH_SIGNAL_LABELS.get(signal,signal), caption=f"{context.get('snapshot_count',0)} snapshots avaliáveis", icon="")
    with cols[1]: executive_card(title="Reação do coach", value=_PROGRESS_COACH_ACTION_LABELS.get(action,action), caption="Abordagem longitudinal", icon="")
    with cols[2]: executive_card(title="Confiança", value=_PROGRESS_CONFIDENCE_LABELS.get(confidence,confidence), caption="Força da evidência", icon="")
    insight_banner(eyebrow="Por que o coach reagiu assim", title=str(explanation.get("title","Leitura longitudinal")), description=str(explanation.get("summary","")), tone="warning" if signal=="REGRESSION" else "positive" if signal=="IMPROVEMENT" else "neutral")
    next_step=str(explanation.get("next_step","")).strip()
    if next_step: insight_banner(eyebrow="Adaptação do treino", title="Como abordar as próximas partidas", description=next_step, tone="neutral")
    with st.expander("Ver evidências e proteções", expanded=False):
        for item in explanation.get("evidence",[]): st.write(" "+str(item))
        for item in explanation.get("limitations",[]): st.caption(" "+str(item))
    st.caption("Esta camada orienta como treinar. Learning Priority continua escolhendo o que treinar; Learning Loop continua controlando missão e dificuldade.")


def _render_adaptive_coach(
    adaptive_coach: dict | None,
) -> None:
    if not isinstance(
        adaptive_coach,
        dict,
    ):
        return

    strategy = adaptive_coach.get(
        "strategy",
        {},
    )
    explanation = adaptive_coach.get(
        "explanation",
        {},
    )

    if not isinstance(
        strategy,
        dict,
    ) or not isinstance(
        explanation,
        dict,
    ):
        return

    strategy_id = str(
        strategy.get(
            "strategy",
            "MAINTAIN",
        )
    ).upper()

    confidence = str(
        strategy.get(
            "confidence",
            "LOW",
        )
    ).upper()

    section_header(
        "Inteligência adaptativa do coach",
        subtitle=(
            "Como o TFT Insight pretende abordar a prioridade atual, "
            "usando perfil, evolução e histórico de treino."
        ),
    )

    columns = st.columns(
        [1.25, 1, 1]
    )

    with columns[0]:
        executive_card(
            title="Estratégia",
            value=_ADAPTIVE_STRATEGY_LABELS.get(
                strategy_id,
                strategy_id,
            ),
            caption="Abordagem pedagógica atual",
            icon="",
        )

    with columns[1]:
        trend_id = str(
            strategy.get(
                "training_trend",
                "INSUFFICIENT_HISTORY",
            )
        ).upper()

        executive_card(
            title="Tendência",
            value=_LEARNING_TREND_LABELS.get(
                trend_id,
                trend_id,
            ),
            caption="Histórico da Skill",
            icon="",
        )

    with columns[2]:
        executive_card(
            title="Confiança",
            value=_ADAPTIVE_CONFIDENCE_LABELS.get(
                confidence,
                confidence,
            ),
            caption="Confiança da estratégia",
            icon="",
        )

    insight_banner(
        eyebrow="Leitura adaptativa",
        title=str(
            explanation.get(
                "title",
                "Estratégia atual",
            )
        ),
        description=str(
            explanation.get(
                "summary",
                "",
            )
        ),
        tone="neutral",
    )

    next_step = str(
        explanation.get(
            "next_step",
            "",
        )
    ).strip()

    if next_step:
        insight_banner(
            eyebrow="Próximo princípio",
            title="Como abordar este treino",
            description=next_step,
            tone="neutral",
        )

    evidence = explanation.get(
        "evidence",
        [],
    )

    limitations = explanation.get(
        "limitations",
        [],
    )

    with st.expander(
        "Por que o coach escolheu esta estratégia?",
        expanded=False,
    ):
        if isinstance(
            evidence,
            list,
        ):
            st.markdown(
                "**Evidências usadas**"
            )
            for item in evidence:
                st.markdown(
                    f" {item}"
                )

        if isinstance(
            limitations,
            list,
        ) and limitations:
            st.markdown(
                "**Limitações**"
            )
            for item in limitations:
                st.caption(
                    f" {item}"
                )

        st.caption(
            "A Skill prioritária continua sendo definida pelo Learning Priority. "
            "Esta camada adapta somente a abordagem."
        )


def _training_metric_number(
    value,
) -> str:
    if not isinstance(
        value,
        (int, float),
    ):
        return ""

    return f"{float(value):.2f}"


def _render_cycle_before_after(
    evaluation: dict,
) -> None:
    metrics = evaluation.get(
        "metrics",
        [],
    )

    if not isinstance(
        metrics,
        list,
    ) or not metrics:
        st.caption(
            "Before/After detalhado ainda não disponível para este ciclo."
        )
        return

    st.markdown(
        "**Before  After**"
    )

    for metric in metrics:
        if not isinstance(
            metric,
            dict,
        ):
            continue

        metric_id = str(
            metric.get(
                "metric_id",
                "",
            )
        )

        label = _TRAINING_METRIC_LABELS.get(
            metric_id,
            metric_id,
        )

        before = metric.get(
            "before"
        )
        after = metric.get(
            "after"
        )
        relative_change = metric.get(
            "relative_change"
        )

        left, center, right = st.columns(
            [1.25, 1.25, 1]
        )

        with left:
            st.caption(
                f"{label} · Before"
            )
            st.markdown(
                f"**{_training_metric_number(before)}**"
            )

        with center:
            st.caption(
                f"{label} · After"
            )
            st.markdown(
                f"**{_training_metric_number(after)}**"
            )

        with right:
            st.caption(
                "Variação"
            )
            st.markdown(
                f"**{_training_delta_text(relative_change)}**"
            )


def _render_training_history(
    training: dict | None,
) -> None:
    """
    9.7 + 9.8:
    - Before/After visual por métrica;
    - um accordion por ciclo;
    - histórico escalável para muitos ciclos.
    """

    if not isinstance(
        training,
        dict,
    ):
        return

    history = training.get(
        "history",
        [],
    )

    if not isinstance(
        history,
        list,
    ) or not history:
        return

    section_header(
        "Histórico de treino",
        subtitle=(
            f"{len(history)} ciclo(s) concluído(s). "
            "Abra um ciclo para ver resultado, Before/After e evidências."
        ),
    )

    for index, cycle in enumerate(
        history,
        start=1,
    ):
        if not isinstance(
            cycle,
            dict,
        ):
            continue

        skill_name = str(
            cycle.get(
                "skill_name",
                cycle.get(
                    "skill_id",
                    "Treino",
                ),
            )
        )

        title = str(
            cycle.get(
                "title",
                "Ciclo de treinamento",
            )
        )

        games_completed = int(
            cycle.get(
                "games_completed",
                0,
            )
            or 0
        )

        games_target = int(
            cycle.get(
                "games_target",
                0,
            )
            or 0
        )

        evaluation = cycle.get(
            "evaluation"
        )

        if isinstance(
            evaluation,
            dict,
        ):
            result = str(
                evaluation.get(
                    "result",
                    "INCONCLUSIVE",
                )
            ).upper()

            confidence = str(
                evaluation.get(
                    "confidence",
                    "LOW",
                )
            ).upper()

            result_label = (
                _TRAINING_RESULT_LABELS.get(
                    result,
                    result,
                )
            )

            confidence_label = (
                _TRAINING_CONFIDENCE_LABELS.get(
                    confidence,
                    confidence,
                )
            )

            confidence_score = float(
                evaluation.get(
                    "confidence_score",
                    0.0,
                )
                or 0.0
            )

            icon = {
                "POSITIVE": "",
                "STABLE": "",
                "NEGATIVE": "",
                "INCONCLUSIVE": "?",
            }.get(
                result,
                "",
            )

            summary = (
                f"{icon} {result_label} · "
                f"{confidence_label.lower()} {confidence_score:.0f}%"
            )
        else:
            summary = "Resultado ainda não disponível"

        expander_title = (
            f"{skill_name} · {title} · "
            f"{games_completed}/{games_target} · {summary}"
        )

        with st.expander(
            expander_title,
            expanded=False,
        ):
            st.markdown(
                f"**{skill_name}  {title}**"
            )

            st.caption(
                f"Ciclo concluído · {games_completed}/{games_target} partidas"
            )

            if isinstance(
                evaluation,
                dict,
            ):
                result = str(
                    evaluation.get(
                        "result",
                        "INCONCLUSIVE",
                    )
                ).upper()

                confidence = str(
                    evaluation.get(
                        "confidence",
                        "LOW",
                    )
                ).upper()

                result_label = (
                    _TRAINING_RESULT_LABELS.get(
                        result,
                        result,
                    )
                )

                confidence_label = (
                    _TRAINING_CONFIDENCE_LABELS.get(
                        confidence,
                        confidence,
                    )
                )

                confidence_score = float(
                    evaluation.get(
                        "confidence_score",
                        0.0,
                    )
                    or 0.0
                )

                result_columns = st.columns(
                    [1.2, 1]
                )

                with result_columns[0]:
                    st.markdown(
                        f"**Resultado: {result_label}**"
                    )

                with result_columns[1]:
                    st.markdown(
                        f"**Confiança: "
                        f"{confidence_label} · {confidence_score:.0f}%**"
                    )

                _render_cycle_before_after(
                    evaluation
                )

                reason = str(
                    evaluation.get(
                        "reason",
                        "",
                    )
                    or ""
                )

                caveat = str(
                    evaluation.get(
                        "caveat",
                        "",
                    )
                    or ""
                )

                if reason:
                    st.caption(
                        f"Leitura: {reason}"
                    )

                if caveat:
                    st.caption(
                        f"Limitação: {caveat}"
                    )
            else:
                st.caption(
                    "Resultado Before/After ainda não disponível."
                )


def _benchmark_session_key(
    *,
    benchmark_id: str,
    game_name: str,
    tag_line: str,
    match_count: int,
) -> str:
    return (
        f"{benchmark_id.strip().lower()}::"
        f"{game_name.strip().lower()}::"
        f"{tag_line.strip().lower()}::"
        f"{int(match_count)}"
    )




def _analysis_payload(report: dict) -> dict:
    value = report.get("analysis", {}) if isinstance(report, dict) else {}
    return value if isinstance(value, dict) else {}


def _analysis_benchmark_id(report: dict) -> str:
    analysis = _analysis_payload(report)
    value = str(analysis.get("benchmark_id", "")).strip()
    return value or "novice"


def _analysis_rank(report: dict) -> str:
    analysis = _analysis_payload(report)
    value = str(analysis.get("current_rank", "")).strip()
    if not value:
        return "Não ranqueado"
    if value.lower() == "não ranqueado":
        return "Não ranqueado"

    tier_labels = {
        "IRON": "Ferro",
        "BRONZE": "Bronze",
        "SILVER": "Prata",
        "GOLD": "Ouro",
        "PLATINUM": "Platina",
        "EMERALD": "Emerald",
        "DIAMOND": "Diamond",
        "MASTER": "Master",
        "GRANDMASTER": "Grão-Mestre",
        "CHALLENGER": "Challenger",
    }
    parts = value.split(" ", 1)
    tier = tier_labels.get(parts[0].upper(), parts[0].title())
    suffix = parts[1] if len(parts) > 1 else ""
    return f"{tier} {suffix}".strip()


def _analysis_stage(report: dict) -> str:
    analysis = _analysis_payload(report)
    value = str(analysis.get("current_stage", "")).strip()
    return _human_stage_label(
        value or "Perfil em avaliação"
    )


def _analysis_target(report: dict) -> str:
    analysis = _analysis_payload(report)
    value = str(analysis.get("target_stage", "")).strip()
    return _human_stage_label(
        value or "Próximo nível competitivo"
    )



def _benchmark_context_description(
    *,
    rank_label: str,
    stage_label: str,
    target_label: str,
    benchmark_name: str,
) -> str:
    if rank_label == "Não ranqueado":
        return (
            f"Como não encontramos um elo ranqueado de TFT, "
            f"{benchmark_name} é usada como referência inicial para "
            "avaliar seus fundamentos."
        )
    return (
        f"Você está em {rank_label} e pertence ao grupo competitivo "
        f"{benchmark_name}. Dentro da leitura do TFT Insight, seu estágio "
        f"atual é {stage_label}. O próximo grupo de desenvolvimento é "
        f"{target_label}. Isso não significa que {target_label} seja seu "
        "próximo elo; é apenas o próximo patamar usado pelo TFT Insight "
        "para organizar a evolução. O grupo competitivo contextualiza "
        "seu desempenho recente e não exige superar todas as métricas."
    )


def _comparison_summary_text(
    *,
    above_count: int,
    total_count: int,
    benchmark_name: str,
) -> str:
    below_count = max(total_count - above_count, 0)
    if total_count <= 0:
        return "Ainda não existem dimensões suficientes para resumir a comparação."
    if below_count == 0:
        return (
            f"Você ficou na ou acima da referência em todas as "
            f"{total_count} áreas comparáveis contra {benchmark_name}."
        )
    if above_count == 0:
        return (
            f"As {total_count} áreas comparáveis ficaram abaixo de "
            f"{benchmark_name}. A análise abaixo mostra onde atacar primeiro."
        )
    return (
        f"Você ficou na ou acima da referência em {above_count} de "
        f"{total_count} áreas analisadas. As outras {below_count} "
        "mostram as oportunidades mais claras de evolução."
    )


def _metric_status_rows(compare_items: list[dict]) -> list[dict]:
    rows = []
    for item in compare_items:
        percentile = item.get("percentile")
        delta = item.get("performance_delta", 0)
        above = percentile >= 50 if percentile is not None else (delta or 0) >= 0
        rows.append(
            {
                "Área": _metric_label(item.get("label", item.get("metric", "-"))),
                "Status": "Na/acima da referência" if above else "Abaixo da referência",
                "Diferença": (
                    f"{_relative_gap_percent(item):+.1f}%"
                    if percentile is None
                    else f"P{float(percentile):.0f}"
                ),
            }
        )
    return rows

def _fusion_authorized_strength(
    fusion: dict | None,
) -> dict | None:
    if not isinstance(fusion, dict):
        return None

    value = fusion.get(
        "strength_to_preserve"
    )

    return (
        value
        if isinstance(value, dict) and value
        else None
    )


def _filter_messages_by_fusion(
    messages: list[dict],
    fusion: dict | None,
) -> list[dict]:
    """
    A Fusion é a autoridade pública sobre "ponto forte".

    Sem strength_to_preserve aprovado, nenhuma mensagem role=strength
    entra na narrativa local ou no fallback.
    """
    approved = _fusion_authorized_strength(
        fusion
    )

    if approved is None:
        return [
            item
            for item in messages
            if item.get("role") != "strength"
        ]

    approved_skill = str(
        approved.get("skill_id") or ""
    ).strip().lower()

    approved_label = str(
        approved.get("skill_label") or ""
    ).strip().lower()

    output: list[dict] = []

    for item in messages:
        if item.get("role") != "strength":
            output.append(item)
            continue

        haystack = " ".join(
            (
                str(item.get("metric") or ""),
                str(item.get("metric_label") or ""),
                str(item.get("title") or ""),
            )
        ).lower()

        if (
            approved_skill
            and approved_skill in haystack
        ) or (
            approved_label
            and approved_label in haystack
        ):
            output.append(item)

    return output


def _fusion_priority_message(
    *,
    fusion: dict | None,
    training: dict | None,
) -> dict | None:
    """
    Cria o primeiro contexto entregue ao narrador.

    Ele NO escolhe a prioridade: apenas serializa a decisão já tomada
    pelo Learning Priority / Coach Context Fusion.
    """
    if not isinstance(fusion, dict):
        return None

    problem = fusion.get(
        "problem_observed",
        {},
    )
    focus = fusion.get(
        "training_focus",
        {},
    )

    if not isinstance(problem, dict):
        problem = {}
    if not isinstance(focus, dict):
        focus = {}

    summary = _coach_training_summary(
        training
    )

    skill = str(
        problem.get("skill_label")
        or summary.get("skill_name")
        or "Foco atual"
    )

    problem_text = str(
        problem.get("description")
        or problem.get("title")
        or ""
    ).strip()

    mission_title = str(
        focus.get("mission_title")
        or summary.get("title")
        or ""
    ).strip()

    action = str(
        focus.get("next_action")
        or focus.get("training_focus")
        or summary.get("objective")
        or ""
    ).strip()

    if not any(
        (
            problem_text,
            mission_title,
            action,
        )
    ):
        return None

    message_parts = [
        (
            f"O foco oficial atual é {skill}. "
            "Esta prioridade já foi escolhida pelo TFT Insight e deve aparecer "
            "antes de sinais complementares."
        )
    ]

    if problem_text:
        message_parts.append(
            problem_text
        )

    if mission_title:
        message_parts.append(
            f"A missão atual é {mission_title}."
        )

    if action:
        message_parts.append(
            f"Para a próxima partida: {action}"
        )

    return {
        "role": "priority",
        "metric": str(
            problem.get("skill_id")
            or ""
        ),
        "metric_label": skill,
        "title": (
            f"{skill} é o foco oficial atual"
        ),
        "message": " ".join(
            message_parts
        ),
        "source": "coach_context_fusion",
        "priority": 0,
    }


def _mission_first_next_focus(
    *,
    training: dict | None,
    strategic_messages: list[dict],
) -> str | None:
    """
    O bloco "Próxima partida" começa pela missão ativa.

    Leituras de contestação, economia e composição entram apenas como
    observações complementares.
    """
    summary = _coach_training_summary(
        training
    )

    primary_action = str(
        summary.get("objective") or ""
    ).strip()

    secondary_action = _build_next_match_focus(
        strategic_messages
    )

    if primary_action and secondary_action:
        secondary = str(
            secondary_action
        ).strip()

        if secondary:
            secondary = (
                secondary[:1].lower()
                + secondary[1:]
            )

            return (
                f"{primary_action} "
                f"Como sinal complementar, {secondary}"
            )

    return (
        primary_action
        or secondary_action
    )


def _coach_narrative_payload(
    *,
    comparison: dict,
    benchmark_name: str,
    spectrum: dict | None = None,
    fusion: dict | None = None,
    training: dict | None = None,
) -> tuple[str, str, str]:
    coach_messages = build_coach_messages(
        comparison,
        benchmark_name=benchmark_name,
        max_priorities=2,
        include_strength=True,
    )

    strategic_messages = build_strategic_coach_messages(
        comparison.get("coach_context")
    )

    coach_payload = (
        coach_messages_payload(
            coach_messages
        )
        if coach_messages
        else []
    )

    global_priority = build_global_priority(
        strategic_messages=strategic_messages,
        benchmark_messages=coach_payload,
        max_adjustments=2,
        max_strengths=2,
    )

    narrator_messages = _filter_messages_by_fusion(
        list(
            global_priority.ordered_messages
        ),
        fusion,
    )

    fusion_priority = _fusion_priority_message(
        fusion=fusion,
        training=training,
    )

    if fusion_priority is not None:
        narrator_messages = [
            fusion_priority,
            *narrator_messages,
        ]

    narrator = LocalCoachNarrator.from_env()

    narrative = narrator.narrate(
        narrator_messages,
        benchmark_name=benchmark_name,
        competitive_spectrum=spectrum,
    )

    if narrative is not None:
        coach_text = narrative.text
        source = "Narrativa local do TFT Insight"
    else:
        coach_text = _build_coach_fallback_narrative(
            narrator_messages,
            [],
        )
        source = "Narrativa determinística de segurança"

    next_focus = _mission_first_next_focus(
        training=training,
        strategic_messages=_filter_messages_by_fusion(
            list(
                global_priority.ordered_messages
            ),
            fusion,
        ),
    )

    return (
        _public_coach_text(
            coach_text
        ),
        _public_coach_text(
            next_focus or ""
        ),
        source,
    )


def _coach_training_summary(
    training: dict | None,
) -> dict:
    if not isinstance(training, dict):
        return {}

    mission = training.get("mission")
    if not isinstance(mission, dict):
        return {}

    completed = int(
        mission.get("games_completed", 0) or 0
    )
    target = int(
        mission.get("games_target", 0) or 0
    )
    remaining = int(
        mission.get(
            "remaining_games",
            max(target - completed, 0),
        )
        or 0
    )

    return {
        "skill_name": str(
            mission.get(
                "skill_name",
                mission.get("skill_id", "Treino"),
            )
        ),
        "title": str(
            mission.get(
                "title",
                "Missão atual",
            )
        ),
        "objective": str(
            mission.get("objective", "") or ""
        ).strip(),
        "completed": completed,
        "target": target,
        "remaining": remaining,
        "checklist": (
            mission.get("checklist", [])
            if isinstance(
                mission.get("checklist", []),
                list,
            )
            else []
        ),
    }


def _render_compact_training(
    training: dict | None,
) -> None:
    summary = _coach_training_summary(training)

    if not summary:
        return

    skill_name = summary["skill_name"]
    mission_title = summary["title"]
    objective = summary["objective"]
    completed = summary["completed"]
    target = summary["target"]
    remaining = summary["remaining"]

    section_header(
        "Seu foco agora",
        subtitle=(
            "Uma orientação simples para levar às próximas partidas."
        ),
    )

    columns = st.columns(
        [1.2, 1, 1]
    )

    with columns[0]:
        executive_card(
            title="Foco",
            value=skill_name,
            caption=mission_title,
            icon="",
        )

    with columns[1]:
        executive_card(
            title="Ciclo atual",
            value=f"{completed}/{target}",
            caption="Partidas concluídas",
            icon="",
        )

    with columns[2]:
        executive_card(
            title="Restam",
            value=str(remaining),
            caption="Partidas neste ciclo",
            icon="",
        )

    if objective:
        insight_banner(
            eyebrow="Missão",
            title=mission_title,
            description=objective,
            tone="neutral",
        )


def _render_training_details(
    training: dict | None,
) -> None:
    summary = _coach_training_summary(training)

    if not summary:
        st.caption(
            "Nenhum detalhe adicional de treino disponível."
        )
        return

    st.write(
        f"**Foco:** {summary['skill_name']}"
    )
    st.write(
        f"**Missão:** {summary['title']}"
    )

    if summary["objective"]:
        st.write(
            f"**Objetivo:** {summary['objective']}"
        )

    st.write(
        "**Progresso:** "
        f"{summary['completed']}/{summary['target']} partidas"
    )

    checklist = summary["checklist"]

    if checklist:
        st.markdown("**Checklist para a partida**")
        for item in checklist:
            if isinstance(item, dict):
                text = (
                    item.get("text")
                    or item.get("label")
                    or item.get("question")
                )
            else:
                text = item

            if text:
                st.write(
                    " " + str(text)
                )


def _render_coach_fusion(
    fusion: dict | None,
) -> None:
    if not isinstance(
        fusion,
        dict,
    ) or not fusion:
        return

    problem = fusion.get(
        "problem_observed",
        {},
    ) or {}
    focus = fusion.get(
        "training_focus",
        {},
    ) or {}
    strength = fusion.get(
        "strength_to_preserve"
    )

    section_header(
        "Leitura do Coach",
        subtitle=(
            "O que foi observado, o que treinar agora e o que vale preservar."
        ),
    )

    if problem:
        insight_banner(
            eyebrow="Problema observado",
            title=_public_coach_text(
                str(
                    problem.get("title")
                    or problem.get("skill_label")
                    or "Principal oportunidade"
                )
            ),
            description=_public_coach_text(
                str(
                    problem.get("description")
                    or (
                        "Este é o sinal que mais sustenta "
                        "a prioridade de treino atual."
                    )
                )
            ),
            tone="warning",
        )

    if focus:
        next_action = _public_coach_text(
            str(
                focus.get("next_action")
                or focus.get("training_focus")
                or focus.get("objective")
                or ""
            )
        )

        if next_action:
            insight_banner(
                eyebrow="Foco de treino",
                title=str(
                    focus.get("mission_title")
                    or "O que praticar agora"
                ),
                description=next_action,
                tone="neutral",
            )

    if isinstance(
        strength,
        dict,
    ) and strength:
        insight_banner(
            eyebrow="Ponto forte a preservar",
            title=_public_coach_text(
                str(
                    strength.get("skill_label")
                    or "Padrão positivo"
                )
            ),
            description=_public_coach_text(
                str(
                    strength.get("description")
                    or (
                        "Preserve este padrão enquanto "
                        "trabalha o foco principal."
                    )
                )
            ),
            tone="positive",
        )

    signals = fusion.get(
        "supporting_signals",
        [],
    )

    if isinstance(
        signals,
        list,
    ) and signals:
        with st.expander(
            "Ver sinais que apoiam esta leitura",
            expanded=False,
        ):
            for signal in signals:
                if not isinstance(
                    signal,
                    dict,
                ):
                    continue

                label = _public_coach_text(
                    str(
                        signal.get("label")
                        or "Sinal"
                    )
                )
                action = _public_coach_text(
                    str(
                        signal.get("action")
                        or ""
                    )
                )
                explanation = _public_coach_text(
                    str(
                        signal.get("explanation")
                        or ""
                    )
                )

                st.markdown(
                    f"**{label}**"
                )
                if action:
                    st.write(action)
                if explanation:
                    st.caption(explanation)


def _render_coach_contents(
    *,
    comparison: dict,
    benchmark_name: str,
    spectrum: dict | None = None,
) -> None:
    st.caption(
        "Seu foco atual, o próximo passo e os detalhes do treino quando você quiser aprofundar."
    )

    if isinstance(
        spectrum,
        dict,
    ) and spectrum:
        insight_banner(
            eyebrow="Contexto competitivo",
            title=(
                f"{spectrum.get('spectrum_band', 'Posição atual')} "
                f"· {benchmark_name}"
                if spectrum.get("available")
                else benchmark_name
            ),
            description=_spectrum_band_sentence(
                spectrum
            ),
            tone="neutral",
        )

    fusion = comparison.get(
        "coach_fusion"
    )

    _render_coach_fusion(
        fusion
    )

    training = comparison.get(
        "training"
    )

    _render_compact_training(
        training
    )

    coach_text, next_focus, source = (
        _coach_narrative_payload(
            comparison=comparison,
            benchmark_name=benchmark_name,
            spectrum=spectrum,
            fusion=(
                fusion
                if isinstance(
                    fusion,
                    dict,
                )
                else None
            ),
            training=(
                training
                if isinstance(
                    training,
                    dict,
                )
                else None
            ),
        )
    )

    if next_focus:
        insight_banner(
            eyebrow="Próxima partida",
            title="O que colocar em prática",
            description=next_focus,
            tone="neutral",
        )

    with st.expander(
        "Ver leitura completa do Coach",
        expanded=False,
    ):
        st.write(
            coach_text
        )
        st.caption(
            source
            + ". Os cálculos continuam sendo do TFT Insight."
        )

    with st.expander(
        "Ver missão e checklist",
        expanded=False,
    ):
        _render_training_details(
            training
        )

    with st.expander(
        "Ver inteligência adaptativa",
        expanded=False,
    ):
        _render_adaptive_coach(
            comparison.get(
                "adaptive_coach"
            )
        )
        _render_progress_aware_coach(
            comparison.get(
                "progress_aware_coach"
            )
        )

    with st.expander(
        "Ver evolução e histórico",
        expanded=False,
    ):
        _render_learning_state(
            training
        )
        _render_progress_dashboard(
            comparison.get(
                "progress"
            )
        )
        _render_training_history(
            training
        )


def _render_floating_coach(
    *,
    comparison: dict,
    benchmark_name: str,
    spectrum: dict | None = None,
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    crystal_path = project_root / "assets" / "crystal.png"
    crystal_data = ""
    if crystal_path.exists():
        crystal_data = base64.b64encode(
            crystal_path.read_bytes()
        ).decode("ascii")

    background = (
        f"url(data:image/png;base64,{crystal_data})"
        if crystal_data
        else "none"
    )

    st.markdown(
        f"""
        <style>
        .st-key-tft_coach_floating {{
            position: fixed;
            right: 28px;
            top: 43%;
            z-index: 9999;
            width: 76px;
        }}
        .st-key-tft_coach_floating button {{
            width: 72px !important;
            height: 72px !important;
            min-height: 72px !important;
            border-radius: 22px !important;
            border: 1px solid rgba(130, 170, 255, .55) !important;
            background-image: {background} !important;
            background-size: 58px 58px !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            background-color: rgba(8, 17, 32, .93) !important;
            box-shadow: 0 10px 34px rgba(32, 96, 220, .35) !important;
            color: transparent !important;
            font-size: 0 !important;
        }}
        .st-key-tft_coach_floating button:hover {{
            transform: translateY(-2px);
            border-color: rgba(216, 173, 87, .8) !important;
            box-shadow: 0 12px 38px rgba(58, 119, 255, .48) !important;
        }}
        @media (max-width: 800px) {{
            .st-key-tft_coach_floating {{
                right: 14px;
                top: auto;
                bottom: 22px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    @st.dialog(" Seu Coach", width="large")
    def coach_dialog() -> None:
        _render_coach_contents(
            comparison=comparison,
            benchmark_name=benchmark_name,
            spectrum=spectrum,
        )

    with st.container(key="tft_coach_floating"):
        if st.button(
            "Abrir Coach",
            key="tft_coach_floating_button",
            help="Abrir seu Coach TFT Insight",
        ):
            coach_dialog()


def _post_match_training_payload(comparison: dict) -> dict:
    training = comparison.get("training", {})
    if not isinstance(training, dict):
        training = {}
    mission = training.get("mission", {})
    if not isinstance(mission, dict):
        mission = {}
    return {
        "skill_id": str(mission.get("skill_id", "leveling") or "leveling"),
        "skill_label": str(
            mission.get("skill_name", mission.get("skill_id", "Leveling"))
            or "Leveling"
        ),
        "mission_title": str(
            mission.get("title", "Planejar o próximo nível")
            or "Planejar o próximo nível"
        ),
        "objective": str(mission.get("objective", "") or ""),
    }


def _post_match_cache_key(
    game_name: str,
    tag_line: str,
    comparison: dict,
) -> str:
    training = _post_match_training_payload(comparison)
    return (
        "post-match::"
        f"{game_name.strip().lower()}::"
        f"{tag_line.strip().lower()}::"
        f"{training['skill_id']}::"
        f"{training['mission_title']}"
    )


def _render_post_match_integration(
    *,
    api_client,
    game_name: str,
    tag_line: str,
    comparison: dict,
    benchmark_name: str,
    spectrum: dict | None,
) -> None:
    section_header(
        "Análise da última partida",
        subtitle=(
            "Veja o que o jogo mais recente acrescenta ao seu treino, "
            "sem transformar uma partida isolada em diagnóstico."
        ),
    )

    training = _post_match_training_payload(comparison)
    cache_key = _post_match_cache_key(
        game_name,
        tag_line,
        comparison,
    )
    cached = st.session_state.get(cache_key)

    action_columns = st.columns([1.4, 2.6])

    with action_columns[0]:
        analyze_latest = st.button(
            "Analisar última partida",
            type="primary",
            use_container_width=True,
            key="post-match-analyze-" + cache_key,
        )

    with action_columns[1]:
        st.caption(
            "A leitura usa a partida mais recente + 10 anteriores "
            "do próprio jogador. Ela não altera sua missão."
        )

    if analyze_latest:
        try:
            with st.spinner("Comparando a última partida com seu histórico..."):
                cached = api_client.latest_post_match_report(
                    game_name=game_name,
                    tag_line=tag_line,
                    skill_id=training["skill_id"],
                    skill_label=training["skill_label"],
                    mission_title=training["mission_title"],
                    objective=training["objective"],
                    history_size=10,
                    competitive_context={
                        "group_label": benchmark_name,
                        "spectrum_band": (
                            spectrum.get("spectrum_band")
                            if isinstance(spectrum, dict)
                            else None
                        ),
                    },
                    coach_fusion=(
                        comparison.get("coach_fusion", {})
                        if isinstance(comparison.get("coach_fusion"), dict)
                        else {}
                    ),
                )
                st.session_state[cache_key] = cached
        except Exception as error:
            friendly_exception(
                error,
                context="a análise da última partida",
            )
            return

    if isinstance(cached, dict):
        render_post_match_report(cached)
    else:
        st.caption(
            "Clique em Analisar última partida para gerar "
            "a leitura pós-partida."
        )


def _render_pre_match_coach_integration(
    *,
    api_client,
    game_name: str,
    tag_line: str,
    comparison: dict,
) -> None:
    section_header(
        "Plano consolidado para a próxima partida",
        subtitle=(
            "Junta os módulos já validados sem criar uma nova prioridade de treino."
        ),
    )

    key = (
        "pre-match-coach::"
        f"{game_name.strip().lower()}::"
        f"{tag_line.strip().lower()}"
    )
    cached = st.session_state.get(key)

    cols = st.columns([1.4, 2.6])
    with cols[0]:
        analyze = st.button(
            "Gerar plano pré-partida",
            type="primary",
            use_container_width=True,
            key="pre-match-coach-button-" + key,
        )
    with cols[1]:
        st.caption(
            "Consolida composição, contestação, economia e carries/itens. "
            "Sua missão atual continua sendo a prioridade."
        )

    if analyze:
        try:
            with st.spinner("Consolidando seu plano para a próxima partida..."):
                composition = api_client.composition_intelligence(
                    game_name=game_name, tag_line=tag_line, match_count=30
                )
                contest = api_client.contest_intelligence(
                    game_name=game_name, tag_line=tag_line, match_count=30
                )
                economy = api_client.economy_intelligence(
                    game_name=game_name, tag_line=tag_line, match_count=30
                )
                carry_item = api_client.carry_item_intelligence(
                    game_name=game_name, tag_line=tag_line, match_count=30
                )

                # Reaproveita os mesmos caches das seções detalhadas.
                st.session_state[_composition_intelligence_cache_key(game_name, tag_line)] = composition
                st.session_state[_contest_intelligence_cache_key(game_name, tag_line)] = contest
                st.session_state[_economy_intelligence_cache_key(game_name, tag_line)] = economy
                st.session_state[_carry_item_intelligence_cache_key(game_name, tag_line)] = carry_item

                cached = build_pre_match_coach(
                    training=_post_match_training_payload(comparison),
                    composition=composition,
                    contest=contest,
                    economy=economy,
                    carry_item=carry_item,
                )
                st.session_state[key] = cached
        except Exception as error:
            friendly_exception(error, context="o plano pré-partida consolidado")
            return

    if isinstance(cached, dict):
        render_pre_match_coach(cached)
    else:
        st.caption(
            "Clique em Gerar plano pré-partida para transformar as análises "
            "já existentes em uma única orientação para o próximo jogo."
        )


def _composition_intelligence_cache_key(
    game_name: str,
    tag_line: str,
) -> str:
    return (
        "composition-intelligence::"
        f"{game_name.strip().lower()}::"
        f"{tag_line.strip().lower()}"
    )


def _render_composition_intelligence_integration(
    *,
    api_client,
    game_name: str,
    tag_line: str,
) -> None:
    section_header(
        "🧩 Composições",
        subtitle=(
            "Entenda os padrões de composição do seu histórico e transforme "
            "a leitura em uma decisão para a próxima partida."
        ),
    )

    cache_key = (
        _composition_intelligence_cache_key(
            game_name,
            tag_line,
        )
    )

    cached = st.session_state.get(
        cache_key
    )

    action_columns = st.columns(
        [1.4, 2.6]
    )

    with action_columns[0]:
        analyze = st.button(
            "Atualizar análise de composições" if isinstance(cached, dict) else "Analisar composições",
            use_container_width=True,
            key=(
                "composition-intelligence-button-"
                + cache_key
            ),
        )

    with action_columns[1]:
        st.caption(
            "Usa até 30 partidas válidas. "
            "Boards finais semelhantes são agrupados por estrutura."
        )

    if analyze:
        try:
            with st.spinner(
                "Analisando suas composições recentes..."
            ):
                cached = (
                    api_client.composition_intelligence(
                        game_name=game_name,
                        tag_line=tag_line,
                        match_count=30,
                    )
                )

                st.session_state[
                    cache_key
                ] = cached

        except Exception as error:
            friendly_exception(
                error,
                context=(
                    "a análise de composições"
                ),
            )
            return

    if isinstance(
        cached,
        dict,
    ):
        st.caption(
            "Leitura pronta. Use a recomendação do módulo como decisão; "
            "abra as evidências quando quiser conferir os dados que a sustentam."
        )
        with st.expander(
            "Ver evidências e detalhes de composições",
            expanded=bool(analyze),
        ):
            render_composition_intelligence(
                cached
            )
    else:
        st.caption(
            "Clique em Analisar composições para gerar "
            "seu perfil de composições."
        )


def _contest_intelligence_cache_key(
    game_name: str,
    tag_line: str,
) -> str:
    return (
        "contest-intelligence::"
        f"{game_name.strip().lower()}::"
        f"{tag_line.strip().lower()}"
    )


def _render_contest_intelligence_integration(
    *,
    api_client,
    game_name: str,
    tag_line: str,
) -> None:
    section_header(
        "⚔️ Contestação",
        subtitle=(
            "Veja quando a disputa por carry, unidades e traits merece "
            "mudar sua decisão antes de comprometer recursos."
        ),
    )

    cache_key = _contest_intelligence_cache_key(
        game_name,
        tag_line,
    )
    cached = st.session_state.get(cache_key)

    action_columns = st.columns([1.4, 2.6])

    with action_columns[0]:
        analyze = st.button(
            "Atualizar análise de contestação" if isinstance(cached, dict) else "Analisar contestação",
            use_container_width=True,
            key="contest-intelligence-button-" + cache_key,
        )

    with action_columns[1]:
        st.caption(
            "Usa até 30 partidas válidas e descreve "
            "a contestação observada nos boards finais."
        )

    if analyze:
        try:
            with st.spinner("Analisando contestação recente..."):
                cached = api_client.contest_intelligence(
                    game_name=game_name,
                    tag_line=tag_line,
                    match_count=30,
                )
                st.session_state[cache_key] = cached
        except Exception as error:
            friendly_exception(
                error,
                context="a análise de contestação",
            )
            return

    if isinstance(cached, dict):
        st.caption(
            "Leitura pronta. Priorize a ação recomendada e abra as evidências "
            "somente quando precisar conferir a contestação observada."
        )
        with st.expander(
            "Ver evidências e detalhes de contestação",
            expanded=bool(analyze),
        ):
            render_contest_intelligence(cached)
    else:
        st.caption(
            "Clique em Analisar contestação para gerar "
            "seu perfil de contestação."
        )



def _economy_intelligence_cache_key(
    game_name: str,
    tag_line: str,
) -> str:
    return (
        "economy-intelligence::"
        f"{game_name.strip().lower()}::"
        f"{tag_line.strip().lower()}"
    )


def _render_economy_intelligence_integration(
    *,
    api_client,
    game_name: str,
    tag_line: str,
) -> None:
    section_header(
        "💰 Economia",
        subtitle=(
            "Leia seu padrão de nível e recursos e leve uma orientação "
            "econômica objetiva para a próxima partida."
        ),
    )

    cache_key = _economy_intelligence_cache_key(
        game_name,
        tag_line,
    )
    cached = st.session_state.get(cache_key)

    action_columns = st.columns([1.4, 2.6])

    with action_columns[0]:
        analyze = st.button(
            "Atualizar análise de economia" if isinstance(cached, dict) else "Analisar economia",
            use_container_width=True,
            key="economy-intelligence-button-" + cache_key,
        )

    with action_columns[1]:
        st.caption(
            "Usa até 30 partidas válidas. A leitura descreve "
            "estados finais; não reconstrói rolls ou timing de compra de XP."
        )

    if analyze:
        try:
            with st.spinner("Analisando economia recente..."):
                cached = api_client.economy_intelligence(
                    game_name=game_name,
                    tag_line=tag_line,
                    match_count=30,
                )
                st.session_state[cache_key] = cached
        except Exception as error:
            friendly_exception(
                error,
                context="a análise de economia",
            )
            return

    if isinstance(cached, dict):
        st.caption(
            "Leitura pronta. A orientação econômica fica em primeiro plano; "
            "os números completos permanecem disponíveis como evidência."
        )
        with st.expander(
            "Ver evidências e detalhes de economia",
            expanded=bool(analyze),
        ):
            render_economy_intelligence(cached)
    else:
        st.caption(
            "Clique em Analisar economia para gerar "
            "seu perfil econômico."
        )



def _carry_item_intelligence_cache_key(
    game_name: str,
    tag_line: str,
) -> str:
    return (
        "carry-item-intelligence::"
        f"{game_name.strip().lower()}::"
        f"{tag_line.strip().lower()}"
    )


def _render_carry_item_intelligence_integration(
    *,
    api_client,
    game_name: str,
    tag_line: str,
) -> None:
    section_header(
        "🎯 Carries + Itens",
        subtitle=(
            "Veja quais carries e itemizações aparecem no seu histórico "
            "e use as evidências para orientar sua próxima decisão."
        ),
    )

    cache_key = _carry_item_intelligence_cache_key(
        game_name,
        tag_line,
    )
    cached = st.session_state.get(cache_key)

    columns = st.columns([1.4, 2.6])

    with columns[0]:
        analyze = st.button(
            "Atualizar análise de carries e itens" if isinstance(cached, dict) else "Analisar carries e itens",
            use_container_width=True,
            key="carry-item-intelligence-button-" + cache_key,
        )

    with columns[1]:
        st.caption(
            "Usa até 30 partidas válidas e analisa "
            "o carry e os itens observados no board final."
        )

    if analyze:
        try:
            with st.spinner("Analisando carries e itemizações..."):
                cached = api_client.carry_item_intelligence(
                    game_name=game_name,
                    tag_line=tag_line,
                    match_count=30,
                )
                st.session_state[cache_key] = cached
        except Exception as error:
            friendly_exception(
                error,
                context="a análise de carries e itens",
            )
            return

    if isinstance(cached, dict):
        st.caption(
            "Leitura pronta. Use a recomendação como guia e consulte carries, "
            "itens e amostra completa apenas quando precisar de evidência."
        )
        with st.expander(
            "Ver evidências e detalhes de carries + itens",
            expanded=bool(analyze),
        ):
            render_carry_item_intelligence(cached)
    else:
        st.caption(
            "Clique em Analisar carries e itens "
            "para gerar seu histórico."
        )


def _render_roadmap22_priority(
    *,
    comparison: dict,
    benchmark_name: str,
    spectrum: dict | None = None,
) -> None:
    """
    Roadmap 22 — coloca a decisão mais importante antes dos detalhes.

    Não calcula métricas novas. Apenas reorganiza sinais já produzidos
    pelo Coach/benchmark para que a prioridade apareça primeiro.
    """
    fusion = comparison.get("coach_fusion")
    training = comparison.get("training")

    problem = (
        fusion.get("problem_observed", {})
        if isinstance(fusion, dict)
        else {}
    ) or {}
    focus = (
        fusion.get("training_focus", {})
        if isinstance(fusion, dict)
        else {}
    ) or {}
    strength = (
        fusion.get("strength_to_preserve")
        if isinstance(fusion, dict)
        else None
    )

    coach_text, next_focus, source = _coach_narrative_payload(
        comparison=comparison,
        benchmark_name=benchmark_name,
        spectrum=spectrum,
        fusion=fusion if isinstance(fusion, dict) else None,
        training=training if isinstance(training, dict) else None,
    )

    section_header(
        "Prioridade do Coach",
        subtitle=(
            "O ponto mais importante para levar à próxima partida, "
            "antes de entrar nos detalhes da análise."
        ),
    )

    if problem:
        insight_banner(
            eyebrow="Prioridade principal",
            title=_public_coach_text(
                str(
                    problem.get("title")
                    or problem.get("skill_label")
                    or "Principal oportunidade"
                )
            ),
            description=_public_coach_text(
                str(
                    problem.get("description")
                    or "Este é o sinal que mais sustenta seu foco atual."
                )
            ),
            tone="warning",
        )
    elif next_focus:
        insight_banner(
            eyebrow="Prioridade principal",
            title="Foco para a próxima partida",
            description=next_focus,
            tone="warning",
        )
    else:
        insight_banner(
            eyebrow="Prioridade principal",
            title="Mantenha a leitura do seu contexto competitivo",
            description=(
                "Ainda não há um único sinal forte o suficiente para "
                "virar prioridade isolada. Use o conjunto de evidências abaixo."
            ),
            tone="neutral",
        )

    next_action = _public_coach_text(
        str(
            focus.get("next_action")
            or focus.get("training_focus")
            or focus.get("objective")
            or next_focus
            or ""
        )
    )

    if next_action:
        insight_banner(
            eyebrow="Na próxima partida",
            title=str(
                focus.get("mission_title")
                or "O que colocar em prática"
            ),
            description=next_action,
            tone="neutral",
        )

    if isinstance(strength, dict) and strength:
        with st.expander(
            "Ver ponto forte a preservar",
            expanded=False,
        ):
            st.markdown(
                "**"
                + _public_coach_text(
                    str(
                        strength.get("skill_label")
                        or "Padrão positivo"
                    )
                )
                + "**"
            )
            st.write(
                _public_coach_text(
                    str(
                        strength.get("description")
                        or "Preserve este padrão enquanto trabalha o foco principal."
                    )
                )
            )

    with st.expander(
        "Abrir leitura completa do Coach",
        expanded=False,
    ):
        st.write(coach_text)
        st.caption(
            source
            + ". Os cálculos continuam sendo do TFT Insight."
        )
        _render_compact_training(training)


def render(
    *,
    context,
    api_client,
) -> None:
    page = PlatformPage(
        title="Análise",
        subtitle=(
            "Informe seu Riot ID uma vez. O TFT Insight identifica seu contexto "
            "competitivo, seleciona a referência adequada e mostra como você joga."
        ),
        environment=context.environment,
        platform_version=context.platform_version,
        hero_badges=(
            "Benchmark automático",
            "Análise competitiva",
            "Evolução",
        ),
    )
    page.begin(platform_online=True)

    default_name, default_tag, default_matches = (
        PlayerSessionStore.current_defaults(
            fallback_name="Pinador doss",
            fallback_tag="000",
            fallback_matches=30,
        )
    )

    current = PlayerSessionStore.current()

    analysis_report = (
        current.analysis_report
        if current is not None
        else None
    )
    comparison = (
        current.benchmark_report
        if current is not None
        else None
    )

    show_form = (
        current is None
        or bool(
            st.session_state.get(
                "tft_show_analysis_form",
                False,
            )
        )
    )

    submitted = False
    game_name = default_name
    tag_line = default_tag
    match_count = default_matches

    if show_form:
        section_header(
            "Analisar jogador",
            subtitle=(
                "Escolha a quantidade de partidas. A referência competitiva é "
                "selecionada automaticamente pelo elo/contexto do jogador."
            ),
        )

        with st.form("tft-unified-analysis-form"):
            c1, c2, c3 = st.columns([1.5, .75, .8])

            with c1:
                game_name = st.text_input(
                    "Riot ID",
                    value=default_name,
                )

            with c2:
                tag_line = st.text_input(
                    "Tag",
                    value=default_tag,
                )

            with c3:
                options = [10, 20, 30, 50]
                default_index = (
                    options.index(default_matches)
                    if default_matches in options
                    else 2
                )
                match_count = st.selectbox(
                    "Partidas",
                    options,
                    index=default_index,
                    help=(
                        "30 partidas é a amostra recomendada "
                        "para uma leitura mais estável."
                    ),
                )

            submitted = st.form_submit_button(
                "Analisar",
                use_container_width=True,
                type="primary",
            )

    else:
        with st.container(
            border=True,
            key="tft_active_player_bar",
        ):
            c1, c2, c3 = st.columns(
                [1.7, .8, .55],
                vertical_alignment="center",
            )

            with c1:
                st.caption("JOGADOR ATIVO")
                st.markdown(
                    f"### {default_name} #{default_tag}"
                )

            with c2:
                st.caption("HISTÓRICO")
                st.markdown(
                    f"**{default_matches} partidas**"
                )

            with c3:
                if st.button(
                    "Nova análise",
                    key="tft_new_analysis",
                    use_container_width=True,
                ):
                    st.session_state[
                        "tft_show_analysis_form"
                    ] = True
                    st.rerun()

    if submitted:
        game_name = game_name.strip()
        tag_line = tag_line.strip().lstrip("#")

        if not game_name or not tag_line:
            friendly_error(
                "Riot ID incompleto",
                "Informe o nome do jogador e a Tag para iniciar a análise.",
                hint="Digite a Tag sem #. Exemplo: Pinador doss / 000.",
            )
            page.end()
            return

        try:
            with st.status(
                "Preparando sua análise...",
                expanded=True,
            ) as status:
                st.write("Identificando jogador e histórico recente.")

                analysis_report = api_client.analyze_player(
                    game_name=game_name,
                    tag_line=tag_line,
                    match_count=match_count,
                    learn=True,
                )

                PlayerSessionStore.save_analysis(
                    analysis_report,
                    game_name=game_name,
                    tag_line=tag_line,
                    match_count=match_count,
                )

                st.write("Definindo sua referência competitiva.")

                benchmark_id = _analysis_benchmark_id(
                    analysis_report
                )

                comparison = api_client.compare_player_to_benchmark(
                    benchmark_id=benchmark_id,
                    game_name=game_name,
                    tag_line=tag_line,
                    match_count=match_count,
                )

                PlayerSessionStore.save_benchmark(
                    comparison
                )

                status.update(
                    label="Análise pronta.",
                    state="complete",
                    expanded=False,
                )

            st.session_state[
                "tft_show_analysis_form"
            ] = False

        except Exception as error:
            friendly_exception(
                error,
                context="a análise do jogador",
            )
            page.end()
            return

    if not isinstance(
        analysis_report,
        dict,
    ):
        empty_state(
            title="Pronto para analisar",
            description=(
                "Informe seu Riot ID, Tag e quantidade de partidas. "
                "O TFT Insight cuidará da escolha do benchmark."
            ),
            icon="◆",
        )
        page.end()
        return

    benchmark_id = _analysis_benchmark_id(
        analysis_report
    )

    if not isinstance(
        comparison,
        dict,
    ):
        try:
            with st.status(
                "Completando comparação competitiva...",
                expanded=False,
            ):
                comparison = api_client.compare_player_to_benchmark(
                    benchmark_id=benchmark_id,
                    game_name=default_name,
                    tag_line=default_tag,
                    match_count=default_matches,
                )
                PlayerSessionStore.save_benchmark(
                    comparison
                )
        except Exception as error:
            friendly_exception(
                error,
                context="a comparação competitiva",
            )
            page.end()
            return

    try:
        overview = api_client.benchmark(
            benchmark_id=benchmark_id,
            include_players=True,
        )
    except Exception as error:
        friendly_exception(
            error,
            context="o carregamento da referência competitiva",
        )
        page.end()
        return

    benchmark_name = overview.get(
        "name",
        benchmark_id,
    )
    exact_percentiles = (
        benchmark_id == "challenger_br"
    )

    rank_label = _analysis_rank(
        analysis_report
    )
    stage_label = _analysis_stage(
        analysis_report
    )
    target_label = _analysis_target(
        analysis_report
    )
    spectrum = _analysis_spectrum(
        analysis_report
    )

    active_game_name = (
        game_name.strip()
        if submitted
        else default_name
    )
    active_tag_line = (
        tag_line.strip().lstrip("#")
        if submitted
        else default_tag
    )
    active_match_count = (
        match_count
        if submitted
        else default_matches
    )

    # ------------------------------------------------------------------
    # ROADMAP 22 — RESUMO DO JOGADOR
    # ------------------------------------------------------------------
    section_header(
        "Seu diagnóstico",
        subtitle=(
            "Contexto essencial primeiro. Os detalhes continuam disponíveis "
            "mais abaixo para quando você quiser aprofundar."
        ),
    )

    player_cols = st.columns(4)

    with player_cols[0]:
        executive_card(
            title="Jogador",
            value=active_game_name,
            caption=f"#{active_tag_line}",
            icon="◆",
        )

    with player_cols[1]:
        executive_card(
            title="Elo atual",
            value=rank_label,
            caption="RANKED TFT",
            icon="◇",
        )

    with player_cols[2]:
        executive_card(
            title="Grupo competitivo",
            value=benchmark_name,
            caption=f"Estágio {stage_label}",
            icon="↗",
        )

    with player_cols[3]:
        executive_card(
            title="Histórico",
            value=str(active_match_count),
            caption="partidas analisadas",
            icon="◉",
        )

    # ------------------------------------------------------------------
    # ROADMAP 22 — COACH PRIMEIRO
    # ------------------------------------------------------------------
    _render_roadmap22_priority(
        comparison=comparison,
        benchmark_name=benchmark_name,
        spectrum=spectrum,
    )

    compare_items = comparison.get(
        "comparisons",
        [],
    )

    if not compare_items:
        empty_state(
            title="Comparação sem métricas",
            description=(
                "Nenhuma dimensão comparável foi retornada."
            ),
            icon="◇",
        )
        page.end()
        return

    insights = build_benchmark_insights(
        comparison,
        benchmark_name=benchmark_name,
    )

    # ------------------------------------------------------------------
    # LEITURA RECENTE
    # ------------------------------------------------------------------
    section_header(
        "Seu desempenho recente",
        subtitle=(
            "O que mais se destaca e o que mais merece atenção "
            "dentro do seu grupo competitivo."
        ),
    )

    summary_cols = st.columns(2)

    with summary_cols[0]:
        insight_banner(
            eyebrow="Seu destaque",
            title=(
                insights["strength_metric"]
                or "Ponto forte"
            ),
            description=(
                insights["strength"]
                .replace(
                    "referência",
                    "seu grupo competitivo",
                )
                .replace(
                    "benchmark",
                    "grupo competitivo",
                )
            ),
            tone="positive",
        )

    with summary_cols[1]:
        insight_banner(
            eyebrow="Maior oportunidade",
            title=(
                insights["opportunity_metric"]
                or "Oportunidade"
            ),
            description=(
                insights["opportunity"]
                .replace(
                    "referência",
                    "seu grupo competitivo",
                )
                .replace(
                    "benchmark",
                    "grupo competitivo",
                )
            ),
            tone="warning",
        )

    profile_rows = _spectrum_profile_rows(
        spectrum
    )

    if profile_rows:
        attention_count = sum(
            row["Leitura"] == "Ponto de atenção"
            for row in profile_rows
        )
        strength_count = sum(
            row["Leitura"] == "Ponto forte"
            for row in profile_rows
        )

        if attention_count:
            quick_title = (
                f"{attention_count} fundamento"
                + (
                    "s"
                    if attention_count != 1
                    else ""
                )
                + " merece"
                + (
                    "m"
                    if attention_count != 1
                    else ""
                )
                + " mais atenção agora"
            )
        elif strength_count:
            quick_title = (
                "Seu perfil recente está bem alinhado "
                "ao grupo competitivo"
            )
        else:
            quick_title = (
                "Seu perfil recente está próximo do padrão "
                "do grupo competitivo"
            )

        insight_banner(
            eyebrow="Leitura rápida",
            title=quick_title,
            description=(
                "Essas diferenças ajudam a escolher o foco de treino. "
                "Elas não representam requisitos para subir de elo."
            ),
            tone=(
                "warning"
                if attention_count
                else "positive"
            ),
        )

    # ------------------------------------------------------------------
    # CONTEXTO COMPETITIVO — AGORA SECUNDÁRIO
    # ------------------------------------------------------------------
    with st.expander(
        "Entender seu contexto competitivo",
        expanded=False,
    ):
        profile_cols = st.columns(3)

        with profile_cols[0]:
            executive_card(
                title="Seu elo atual",
                value=rank_label,
                caption="RANKED_TFT",
                icon="◇",
            )

        with profile_cols[1]:
            executive_card(
                title="Próximo grupo de desenvolvimento",
                value=target_label,
                caption=f"Grupo atual: {stage_label}",
                icon="↗",
            )

        with profile_cols[2]:
            executive_card(
                title="Grupo competitivo",
                value=benchmark_name,
                caption="Definido pelo seu elo",
                icon="◆",
            )

        insight_banner(
            eyebrow="Entenda seu grupo competitivo",
            title=(
                f"{benchmark_name} · "
                f"estágio atual {stage_label}"
            ),
            description=_benchmark_context_description(
                rank_label=rank_label,
                stage_label=stage_label,
                target_label=target_label,
                benchmark_name=benchmark_name,
            ),
            tone="neutral",
        )

        _render_spectrum_bar(
            spectrum=spectrum,
            rank_label=rank_label,
            benchmark_name=benchmark_name,
        )

        if profile_rows:
            st.dataframe(
                pd.DataFrame(profile_rows),
                use_container_width=True,
                hide_index=True,
            )

    # ------------------------------------------------------------------
    # NÚMEROS / GRÁFICOS
    # ------------------------------------------------------------------
    with st.expander(
        "Ver números e comparação detalhada",
        expanded=False,
    ):
        st.dataframe(
            pd.DataFrame(
                _metric_status_rows(
                    compare_items
                )
            ),
            use_container_width=True,
            hide_index=True,
        )

        if exact_percentiles:
            chart_left, chart_right = st.columns(
                [1.65, 1]
            )

            with chart_left:
                radar = comparison.get(
                    "radar",
                    [],
                )

                if radar:
                    labels = [
                        _metric_label(
                            item["metric"]
                        )
                        for item in radar
                    ]

                    figure = go.Figure()

                    figure.add_trace(
                        go.Scatterpolar(
                            r=[
                                item["player"]
                                for item in radar
                            ],
                            theta=labels,
                            fill="toself",
                            name="Jogador",
                        )
                    )

                    figure.add_trace(
                        go.Scatterpolar(
                            r=[50.0] * len(labels),
                            theta=labels,
                            name="Mediana da referência",
                        )
                    )

                    figure.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 100],
                            )
                        )
                    )

                    apply_chart_theme(
                        figure,
                        height=540,
                    )

                    st.plotly_chart(
                        figure,
                        use_container_width=True,
                    )

            with chart_right:
                frame = pd.DataFrame(
                    [
                        {
                            "Métrica": _metric_label(
                                item["label"]
                            ),
                            "Percentil": item.get(
                                "percentile",
                                0,
                            ),
                        }
                        for item in compare_items
                    ]
                )

                figure = go.Figure(
                    go.Bar(
                        x=frame["Percentil"],
                        y=frame["Métrica"],
                        orientation="h",
                    )
                )

                figure.add_vline(
                    x=50,
                    line_dash="dash",
                )

                apply_chart_theme(
                    figure,
                    height=540,
                )

                figure.update_xaxes(
                    range=[0, 100],
                    title="Percentil",
                )

                st.plotly_chart(
                    figure,
                    use_container_width=True,
                )

        else:
            frame = pd.DataFrame(
                [
                    {
                        "Métrica": _metric_label(
                            item["label"]
                        ),
                        "Gap relativo (%)": round(
                            _relative_gap_percent(
                                item
                            ),
                            1,
                        ),
                    }
                    for item in compare_items
                ]
            )

            figure = go.Figure(
                go.Bar(
                    x=frame["Gap relativo (%)"],
                    y=frame["Métrica"],
                    orientation="h",
                )
            )

            figure.add_vline(
                x=0,
                line_dash="dash",
            )

            apply_chart_theme(
                figure,
                height=480,
            )

            figure.update_xaxes(
                title=(
                    "Diferença relativa "
                    "para o grupo (%)"
                )
            )

            st.plotly_chart(
                figure,
                use_container_width=True,
            )

    # O cristal continua disponível como atalho para a leitura completa.
    _render_floating_coach(
        comparison=comparison,
        benchmark_name=benchmark_name,
        spectrum=spectrum,
    )

    # ------------------------------------------------------------------
    # INTELIGÊNCIAS APLICADAS
    # ------------------------------------------------------------------
    section_header(
        "Inteligências da sua partida",
        subtitle=(
            "Quatro leituras para transformar seu histórico em decisões. "
            "A recomendação vem primeiro; evidências e detalhes ficam recolhidos."
        ),
    )

    _render_post_match_integration(
        api_client=api_client,
        game_name=active_game_name,
        tag_line=active_tag_line,
        comparison=comparison,
        benchmark_name=benchmark_name,
        spectrum=spectrum,
    )

    _render_pre_match_coach_integration(
        api_client=api_client,
        game_name=active_game_name,
        tag_line=active_tag_line,
        comparison=comparison,
    )

    _render_composition_intelligence_integration(
        api_client=api_client,
        game_name=active_game_name,
        tag_line=active_tag_line,
    )

    _render_contest_intelligence_integration(
        api_client=api_client,
        game_name=active_game_name,
        tag_line=active_tag_line,
    )

    _render_economy_intelligence_integration(
        api_client=api_client,
        game_name=active_game_name,
        tag_line=active_tag_line,
    )

    _render_carry_item_intelligence_integration(
        api_client=api_client,
        game_name=active_game_name,
        tag_line=active_tag_line,
    )

    with st.expander(
        "Detalhamento técnico dos fundamentos",
        expanded=False,
    ):
        table = pd.DataFrame(
            [
                {
                    "Métrica": _metric_label(
                        item["label"]
                    ),
                    "Jogador": item[
                        "player_value"
                    ],
                    "Média da referência": item.get(
                        "benchmark_mean",
                        item.get(
                            "challenger_mean"
                        ),
                    ),
                    "Mediana": item.get(
                        "benchmark_median",
                        item.get(
                            "challenger_median"
                        ),
                    ),
                    "Diferença de desempenho": item[
                        "performance_delta"
                    ],
                    "Percentil": (
                        item.get("percentile")
                        if item.get(
                            "percentile"
                        ) is not None
                        else "N/A"
                    ),
                    "Avaliação": ASSESSMENT_LABELS.get(
                        item["assessment"],
                        item["assessment"],
                    ),
                }
                for item in compare_items
            ]
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
        )

    page.end()
