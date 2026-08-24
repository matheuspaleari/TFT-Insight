from __future__ import annotations

from src.post_match.models.post_match_report import (
    PostMatchReport,
    PostMatchReportSection,
)


class PostMatchReportService:
    """
    V1.6 — Final Post Match Fusion.

    Junta:
    - análise objetiva da partida;
    - EvidenceClass;
    - Personal Baseline;
    - contexto histórico;
    - interpretação histórica;
    - missão atual.

    Não recalcula nenhum motor anterior.
    Não altera Learning Priority, missão, EvidenceClass ou Learning Loop.
    """

    @classmethod
    def build(
        cls,
        *,
        analysis,
        baseline,
        post_match_interpretation,
        historical_context,
        historical_interpretation,
    ) -> PostMatchReport:
        skill = analysis.active_skill_label or "foco atual"
        mission = analysis.mission_title or "missão atual"

        focus_text = cls._merge_focus(
            skill=skill,
            mission=mission,
            post_match_interpretation=post_match_interpretation,
            historical_interpretation=historical_interpretation,
        )

        focus_section = PostMatchReportSection(
            section_id="focus",
            title=f"Seu foco nesta partida: {skill}",
            text=focus_text,
            importance=100,
        )

        supporting = cls._supporting_sections(
            post_match_interpretation=post_match_interpretation,
            historical_interpretation=historical_interpretation,
        )

        headline = cls._headline(
            analysis=analysis,
            historical_interpretation=historical_interpretation,
        )

        summary = cls._summary(
            analysis=analysis,
            post_match_interpretation=post_match_interpretation,
            historical_interpretation=historical_interpretation,
        )

        cannot_measure = (
            post_match_interpretation.missing_information
            or "Ainda há decisões importantes que a telemetria não consegue medir."
        )

        takeaway = cls._takeaway(
            analysis=analysis,
            skill=skill,
            mission=mission,
        )

        return PostMatchReport(
            match_id=str(analysis.match_id),
            player_context=f"{skill} · {mission}",
            headline=headline,
            summary=summary,
            focus_section=focus_section,
            supporting_sections=supporting,
            what_we_cannot_measure=cannot_measure,
            coach_takeaway=takeaway,
            source_verdict=analysis.verdict.value,
            baseline_matches=int(baseline.matches_used),
            historical_matches=10,
            changes_learning_priority=False,
            changes_mission=False,
            changes_evidence_class=False,
            counts_as_mission_evidence=False,
            predicts_rank_up=False,
        )

    @staticmethod
    def _merge_focus(
        *,
        skill: str,
        mission: str,
        post_match_interpretation,
        historical_interpretation,
    ) -> str:
        current = post_match_interpretation.focus_reading.strip()
        historical = historical_interpretation.focus_reading.strip()

        return (
            f"{current} "
            f"Olhando o histórico recente: {historical} "
            f"A missão continua sendo “{mission}”."
        )

    @classmethod
    def _supporting_sections(
        cls,
        *,
        post_match_interpretation,
        historical_interpretation,
    ) -> tuple[PostMatchReportSection, ...]:
        candidates: list[PostMatchReportSection] = []

        for item in post_match_interpretation.context_readings:
            candidates.append(
                PostMatchReportSection(
                    section_id=f"match_{item.signal_id}",
                    title=item.title,
                    text=item.text.strip(),
                    importance=int(item.importance),
                )
            )

        for item in historical_interpretation.additional_readings:
            candidates.append(
                PostMatchReportSection(
                    section_id=f"history_{item.metric_id}",
                    title=f"Histórico: {item.title}",
                    text=item.text.strip(),
                    importance=max(
                        0,
                        int(item.importance) - 5,
                    ),
                )
            )

        # Evita duplicar a mesma dimensão em "partida" e "histórico".
        selected: list[PostMatchReportSection] = []
        seen_dimensions: set[str] = set()

        for item in sorted(
            candidates,
            key=lambda value: value.importance,
            reverse=True,
        ):
            dimension = cls._dimension(
                item.section_id
            )

            if dimension in seen_dimensions:
                continue

            seen_dimensions.add(dimension)
            selected.append(item)

            if len(selected) >= 3:
                break

        return tuple(selected)

    @staticmethod
    def _dimension(section_id: str) -> str:
        value = (
            section_id
            .replace("match_", "")
            .replace("history_", "")
        )

        aliases = {
            "board_pressure": "pressure",
            "total_damage_to_players": "pressure",
            "placement": "placement",
            "gold_left": "gold",
            "contestacao": "contestacao",
            "players_eliminated": "eliminations",
        }

        return aliases.get(
            value,
            value,
        )

    @staticmethod
    def _headline(
        *,
        analysis,
        historical_interpretation,
    ) -> str:
        placement = int(
            analysis.placement
        )

        if placement <= 4:
            result = f"Top {placement}"
        else:
            result = f"{placement}º lugar"

        return (
            f"{result}: o que esta partida acrescenta ao seu treino"
        )

    @staticmethod
    def _summary(
        *,
        analysis,
        post_match_interpretation,
        historical_interpretation,
    ) -> str:
        return (
            f"{post_match_interpretation.overview.strip()} "
            f"{historical_interpretation.overview.strip()} "
            "A leitura final separa resultado da partida, mudança em relação "
            "ao seu próprio padrão e execução da missão."
        )

    @staticmethod
    def _takeaway(
        *,
        analysis,
        skill: str,
        mission: str,
    ) -> str:
        if int(analysis.direct_count) == 0:
            return (
                f"Com os dados desta partida, ainda não dá para saber se você "
                f"executou bem “{mission}”. Continue treinando {skill} sem "
                "interpretar esta partida isolada como sucesso ou falha da missão."
            )

        return (
            f"Há sinal direto disponível para {skill}, mas uma única partida "
            "ainda não altera automaticamente o ciclo de treino."
        )
