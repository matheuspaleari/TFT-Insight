from __future__ import annotations

from typing import Any

from src.post_match.models import (
    EvidenceClass,
    PostMatchAnalysis,
    PostMatchEvidence,
    PostMatchVerdict,
)


class PostMatchAnalysisService:
    """
    Post Match Analysis V1.1.

    Formaliza cada evidência como:
    - DIRECT: mede diretamente o comportamento treinado;
    - PROXY: relacionado ao comportamento, mas não prova execução;
    - CONTEXT: ajuda a explicar a partida, não avalia a missão;
    - UNAVAILABLE: seria necessária para avaliar a missão, mas não existe
      na telemetria atual.

    Regra conservadora:
    só uma evidência DIRECT pode, futuramente, ser candidata a alimentar
    o Learning Loop automaticamente. A V1.1 ainda NÃO faz essa integração.
    """

    @classmethod
    def analyze(
        cls,
        *,
        match: Any,
        training: Any = None,
        contest_report: Any = None,
    ) -> PostMatchAnalysis:
        skill_id = cls._first(
            training,
            "primary_skill_id",
            "skill_id",
            "focus_skill_id",
        )
        skill_label = cls._first(
            training,
            "primary_skill_label",
            "skill_label",
            "focus_skill_label",
            "skill_name",
        )
        mission_title = cls._first(
            training,
            "mission_title",
            "title",
            "exercise_title",
        )
        mission_objective = cls._first(
            training,
            "objective",
            "mission_objective",
            "task",
        )

        evidence = [
            cls._placement_evidence(match),
            cls._level_evidence(
                match=match,
                skill_id=skill_id,
                skill_label=skill_label,
            ),
            cls._gold_evidence(
                match=match,
                skill_id=skill_id,
                skill_label=skill_label,
            ),
            cls._pressure_evidence(
                match=match,
                skill_id=skill_id,
                skill_label=skill_label,
            ),
        ]

        if contest_report is not None:
            evidence.append(
                cls._contest_evidence(
                    contest_report
                )
            )

        unavailable = cls._unavailable_for_focus(
            skill_id=skill_id,
            skill_label=skill_label,
            mission_title=mission_title,
            mission_objective=mission_objective,
        )

        direct_count = cls._count(
            evidence,
            EvidenceClass.DIRECT,
        )
        proxy_count = cls._count(
            evidence,
            EvidenceClass.PROXY,
        )
        context_count = cls._count(
            evidence,
            EvidenceClass.CONTEXT,
        )
        unavailable_count = len(unavailable)

        verdict = (
            PostMatchVerdict.NOT_EVALUATED
            if direct_count == 0
            else PostMatchVerdict.OBSERVATIONAL
        )

        if direct_count == 0:
            verdict_reason = (
                "Nenhuma evidência direta do comportamento treinado está "
                "disponível nesta partida. Existem proxies e contexto, "
                "mas eles não são suficientes para avaliar a execução "
                "da missão."
            )
        else:
            verdict_reason = (
                "Existe ao menos uma evidência direta disponível, mas a V1.1 "
                "ainda não altera o Learning Loop automaticamente."
            )

        focus = str(
            skill_label or skill_id or "foco atual"
        )

        headline = (
            f"Partida {match.match_id}: mapa de evidências para {focus}"
        )

        summary = (
            f"A partida terminou em {int(match.placement)}º, nível "
            f"{int(match.level)}, com {int(match.gold_left)} de ouro. "
            f"A análise encontrou {direct_count} evidência(s) DIRECT, "
            f"{proxy_count} PROXY, {context_count} CONTEXT e "
            f"{unavailable_count} UNAVAILABLE."
        )

        limitations = (
            "PROXY não pode ser tratado como prova de execução da missão.",
            "CONTEXT ajuda a explicar a partida, mas não avalia o comportamento treinado.",
            "UNAVAILABLE registra explicitamente quais dados faltam para uma avaliação pedagógica mais forte.",
            "A V1.1 ainda não alimenta Learning Priority, missão ou dificuldade.",
        )

        return PostMatchAnalysis(
            match_id=str(match.match_id),
            placement=int(match.placement),
            level=int(match.level),
            gold_left=int(match.gold_left),
            last_round=int(match.last_round),
            players_eliminated=int(
                match.players_eliminated
            ),
            total_damage_to_players=int(
                match.total_damage_to_players
            ),
            active_skill_id=(
                str(skill_id)
                if skill_id is not None
                else None
            ),
            active_skill_label=(
                str(skill_label)
                if skill_label is not None
                else None
            ),
            mission_title=(
                str(mission_title)
                if mission_title is not None
                else None
            ),
            mission_objective=(
                str(mission_objective)
                if mission_objective is not None
                else None
            ),
            verdict=verdict,
            verdict_reason=verdict_reason,
            headline=headline,
            summary=summary,
            evidence=tuple(evidence),
            unavailable_evidence=tuple(unavailable),
            limitations=limitations,
            direct_count=direct_count,
            proxy_count=proxy_count,
            context_count=context_count,
            unavailable_count=unavailable_count,
            changes_learning_priority=False,
            changes_mission=False,
            changes_difficulty=False,
            predicts_rank_up=False,
            counts_as_mission_evidence=False,
        )

    @staticmethod
    def _count(
        evidence: list[PostMatchEvidence],
        evidence_class: EvidenceClass,
    ) -> int:
        return sum(
            item.evidence_class == evidence_class
            for item in evidence
        )

    @classmethod
    def _placement_evidence(
        cls,
        match: Any,
    ) -> PostMatchEvidence:
        placement = int(
            match.placement
        )

        return PostMatchEvidence(
            signal_id="placement",
            label="Colocação",
            value=f"{placement}º",
            interpretation=(
                cls._placement_text(
                    placement
                )
            ),
            evidence_class=EvidenceClass.CONTEXT,
            relation="result",
            confidence=100.0,
            supports_mission_evaluation=False,
            limitation=(
                "Resultado final não revela se a missão foi executada."
            ),
        )

    @classmethod
    def _level_evidence(
        cls,
        *,
        match: Any,
        skill_id: Any,
        skill_label: Any,
    ) -> PostMatchEvidence:
        relation = cls._skill_relation(
            skill_id,
            skill_label,
            {"leveling", "level", "nivel", "nível"},
        )

        evidence_class = (
            EvidenceClass.PROXY
            if relation == "focus"
            else EvidenceClass.CONTEXT
        )

        return PostMatchEvidence(
            signal_id="final_level",
            label="Nível final",
            value=str(int(match.level)),
            interpretation=(
                "O nível final se relaciona à progressão de nível, "
                "mas não mostra o timing da compra de XP nem a intenção "
                "da decisão."
            ),
            evidence_class=evidence_class,
            relation=relation,
            confidence=100.0,
            supports_mission_evaluation=False,
            limitation=(
                "Nível final é proxy de Leveling; não mede planejamento."
            ),
        )

    @classmethod
    def _gold_evidence(
        cls,
        *,
        match: Any,
        skill_id: Any,
        skill_label: Any,
    ) -> PostMatchEvidence:
        relation = cls._skill_relation(
            skill_id,
            skill_label,
            {"economy", "economia", "gold"},
        )

        evidence_class = (
            EvidenceClass.PROXY
            if relation == "focus"
            else EvidenceClass.CONTEXT
        )

        return PostMatchEvidence(
            signal_id="gold_left",
            label="Ouro restante",
            value=str(int(match.gold_left)),
            interpretation=(
                "O ouro final pode apoiar a leitura de economia, mas "
                "não revela sozinho se gastar ou guardar foi correto."
            ),
            evidence_class=evidence_class,
            relation=relation,
            confidence=100.0,
            supports_mission_evaluation=False,
            limitation=(
                "Não há histórico de decisões de gasto nesta evidência."
            ),
        )

    @classmethod
    def _pressure_evidence(
        cls,
        *,
        match: Any,
        skill_id: Any,
        skill_label: Any,
    ) -> PostMatchEvidence:
        relation = cls._skill_relation(
            skill_id,
            skill_label,
            {
                "board_pressure",
                "pressão de tabuleiro",
                "pressao de tabuleiro",
            },
        )

        evidence_class = (
            EvidenceClass.PROXY
            if relation == "focus"
            else EvidenceClass.CONTEXT
        )

        return PostMatchEvidence(
            signal_id="board_pressure",
            label="Pressão de tabuleiro",
            value=(
                f"{int(match.total_damage_to_players)} dano · "
                f"{int(match.players_eliminated)} eliminações"
            ),
            interpretation=(
                "Dano e eliminações descrevem pressão observada, "
                "mas não isolam qual decisão gerou esse resultado."
            ),
            evidence_class=evidence_class,
            relation=relation,
            confidence=100.0,
            supports_mission_evaluation=False,
            limitation=(
                "Não há causalidade entre pressão final e uma decisão específica."
            ),
        )

    @classmethod
    def _contest_evidence(
        cls,
        report: Any,
    ) -> PostMatchEvidence:
        score = cls._first(
            report,
            "score",
        )
        level = cls._first(
            report,
            "level",
        )
        carry = cls._first(
            report,
            "carry_character_id",
        )
        contested = bool(
            cls._first(
                report,
                "carry_contested",
            )
            or False
        )
        opponents = cls._first(
            report,
            "opponents_contesting_carry",
        )

        if hasattr(level, "value"):
            level = level.value

        score_text = (
            f"{float(score):.2f}"
            if score is not None
            else "-"
        )

        parts = [
            f"score {score_text}",
            (
                "carry contestado"
                if contested
                else "carry sem contestação direta"
            ),
        ]

        if opponents is not None:
            parts.append(
                f"{int(opponents)} adversário(s) no carry"
            )

        if carry:
            parts.append(
                f"carry {carry}"
            )

        if level:
            parts.append(
                f"classificação {level}"
            )

        return PostMatchEvidence(
            signal_id="contestacao",
            label="Contestação",
            value=" · ".join(parts),
            interpretation=(
                "É contexto estratégico da partida. Sem uma missão "
                "específica de contestação/scouting, não avalia o foco atual."
            ),
            evidence_class=EvidenceClass.CONTEXT,
            relation="context",
            confidence=100.0,
            source="contest_analyzer",
            supports_mission_evaluation=False,
            limitation=(
                "Contestação observada não prova que o jogador fez scout "
                "ou reagiu corretamente ao lobby."
            ),
        )

    @classmethod
    def _unavailable_for_focus(
        cls,
        *,
        skill_id: Any,
        skill_label: Any,
        mission_title: Any,
        mission_objective: Any,
    ) -> list[PostMatchEvidence]:
        haystack = " ".join(
            (
                str(skill_id or ""),
                str(skill_label or ""),
                str(mission_title or ""),
                str(mission_objective or ""),
            )
        ).lower()

        unavailable: list[PostMatchEvidence] = []

        if any(
            token in haystack
            for token in (
                "leveling",
                "nível",
                "nivel",
                "subida de nível",
            )
        ):
            unavailable.extend(
                (
                    cls._unavailable(
                        signal_id="xp_purchase_timing",
                        label="Timing de compra de XP",
                        interpretation=(
                            "Necessário para saber quando o jogador decidiu "
                            "acelerar a progressão de nível."
                        ),
                    ),
                    cls._unavailable(
                        signal_id="level_up_decision_context",
                        label="Contexto da decisão de subir de nível",
                        interpretation=(
                            "Necessário para avaliar se a subida foi planejada "
                            "considerando ouro, vida, força do tabuleiro e lobby."
                        ),
                    ),
                    cls._unavailable(
                        signal_id="pre_spend_plan",
                        label="Plano antes de gastar ouro",
                        interpretation=(
                            "É o comportamento central da missão atual, mas a "
                            "API não registra a intenção declarada do jogador."
                        ),
                    ),
                )
            )

        elif any(
            token in haystack
            for token in (
                "economy",
                "economia",
                "ouro",
            )
        ):
            unavailable.extend(
                (
                    cls._unavailable(
                        signal_id="gold_spend_timeline",
                        label="Linha do tempo de gasto",
                        interpretation=(
                            "Necessária para separar gasto planejado de gasto "
                            "reativo ou tardio."
                        ),
                    ),
                    cls._unavailable(
                        signal_id="roll_timing",
                        label="Timing de roll",
                        interpretation=(
                            "Necessário para avaliar quando a economia foi "
                            "convertida em força de tabuleiro."
                        ),
                    ),
                )
            )

        elif any(
            token in haystack
            for token in (
                "contest",
                "contestação",
                "scout",
            )
        ):
            unavailable.extend(
                (
                    cls._unavailable(
                        signal_id="scouting_timeline",
                        label="Linha do tempo de scouting",
                        interpretation=(
                            "Necessária para provar se o jogador observou o "
                            "lobby antes de comprometer recursos."
                        ),
                    ),
                    cls._unavailable(
                        signal_id="decision_after_scout",
                        label="Decisão após scouting",
                        interpretation=(
                            "Necessária para avaliar se a informação de "
                            "contestação realmente mudou a linha de jogo."
                        ),
                    ),
                )
            )

        else:
            unavailable.append(
                cls._unavailable(
                    signal_id="decision_timeline",
                    label="Linha do tempo da decisão",
                    interpretation=(
                        "A telemetria atual não descreve a intenção e o "
                        "momento das decisões necessárias para avaliar "
                        "diretamente este foco."
                    ),
                )
            )

        return unavailable

    @staticmethod
    def _unavailable(
        *,
        signal_id: str,
        label: str,
        interpretation: str,
    ) -> PostMatchEvidence:
        return PostMatchEvidence(
            signal_id=signal_id,
            label=label,
            value="Não disponível",
            interpretation=interpretation,
            evidence_class=EvidenceClass.UNAVAILABLE,
            relation="focus",
            confidence=None,
            source="telemetry_gap",
            supports_mission_evaluation=False,
            limitation=(
                "Dado não disponível na telemetria atual."
            ),
        )

    @staticmethod
    def _first(
        obj: Any,
        *names: str,
    ) -> Any:
        if obj is None:
            return None

        for name in names:
            if isinstance(obj, dict):
                value = obj.get(name)
            else:
                value = getattr(
                    obj,
                    name,
                    None,
                )

            if value not in (
                None,
                "",
                [],
                {},
            ):
                return value

        return None

    @staticmethod
    def _skill_relation(
        skill_id: Any,
        skill_label: Any,
        aliases: set[str],
    ) -> str:
        haystack = " ".join(
            (
                str(skill_id or ""),
                str(skill_label or ""),
            )
        ).lower()

        return (
            "focus"
            if any(
                alias in haystack
                for alias in aliases
            )
            else "context"
        )

    @staticmethod
    def _placement_text(
        placement: int,
    ) -> str:
        if placement == 1:
            return (
                "Vitória observada. Resultado final é CONTEXT, "
                "não prova isolada de execução da missão."
            )

        if placement <= 4:
            return (
                "Top 4 observado. Resultado final é CONTEXT, "
                "não prova isolada de execução da missão."
            )

        return (
            "Bottom 4 observado. Resultado final é CONTEXT, "
            "não prova isolada de falha na missão."
        )
