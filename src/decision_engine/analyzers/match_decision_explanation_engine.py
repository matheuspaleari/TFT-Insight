from __future__ import annotations

from statistics import mean

from src.decision_engine.models import (
    ContestHistoryReport,
    ExplanationImpact,
    MatchDecisionExplanationReport,
    MatchExplanationFactor,
)
from src.performance_engine.models import Match
from src.role_inference.models import ItemClassification
from src.role_inference.repositories.unit_catalog_repository import (
    UnitCatalogRepository,
)
from src.role_inference.services import RoleInferenceEngine

from .contest_analyzer import ContestAnalyzer


class MatchDecisionExplanationEngine:
    """
    Explica uma partida específica comparando-a ao histórico recente.

    O resultado é consequência observada e não participa da nota causal.

    Pesos:
    - itemização: 25%;
    - progressão de nível: 20%;
    - pressão no lobby: 20%;
    - sobrevivência/tempo: 15%;
    - contestação: 15%;
    - conversão de economia: 5%.
    """

    FACTOR_WEIGHTS = {
        "itemization": 0.25,
        "level": 0.20,
        "pressure": 0.20,
        "tempo": 0.15,
        "contest": 0.15,
        "economy": 0.05,
    }

    @classmethod
    def explain(
        cls,
        *,
        match: Match,
        history_matches: list[Match],
        item_classifications: dict[str, ItemClassification],
        contest_history: ContestHistoryReport | None = None,
    ) -> MatchDecisionExplanationReport:
        if not history_matches:
            raise ValueError(
                "history_matches não pode ser vazio."
            )

        participant = match.analyzed_participant

        if participant is None:
            raise ValueError(
                "A partida não possui participante analisado."
            )

        role_report = RoleInferenceEngine.infer_participant(
            participant=participant,
            item_classifications=item_classifications,
        )

        contest_report = ContestAnalyzer.analyze(match)

        result_factor = cls._placement_factor(
            match=match,
            history_matches=history_matches,
        )

        strategic_factors = (
            cls._level_factor(
                match=match,
                history_matches=history_matches,
            ),
            cls._economy_factor(
                match=match,
                history_matches=history_matches,
            ),
            cls._tempo_factor(
                match=match,
                history_matches=history_matches,
            ),
            cls._pressure_factor(
                match=match,
                history_matches=history_matches,
            ),
            cls._itemization_factor(
                role_report=role_report,
            ),
            cls._contest_factor(
                match=match,
                contest_report=contest_report,
                contest_history=contest_history,
            ),
        )

        overall_score = sum(
            factor.score
            * cls.FACTOR_WEIGHTS[factor.factor_id]
            for factor in strategic_factors
        )

        positive = tuple(
            sorted(
                (
                    factor
                    for factor in strategic_factors
                    if factor.impact
                    == ExplanationImpact.POSITIVE
                ),
                key=lambda factor: (
                    factor.score
                    * cls.FACTOR_WEIGHTS[factor.factor_id]
                ),
                reverse=True,
            )
        )

        attention = tuple(
            sorted(
                (
                    factor
                    for factor in strategic_factors
                    if (
                        factor.impact
                        == ExplanationImpact.NEGATIVE
                        and factor.score >= 40.0
                    )
                ),
                key=lambda factor: factor.score,
            )
        )

        critical = tuple(
            sorted(
                (
                    factor
                    for factor in strategic_factors
                    if (
                        factor.impact
                        == ExplanationImpact.NEGATIVE
                        and factor.score < 40.0
                    )
                ),
                key=lambda factor: factor.score,
            )
        )

        neutral = tuple(
            sorted(
                (
                    factor
                    for factor in strategic_factors
                    if factor.impact
                    == ExplanationImpact.NEUTRAL
                ),
                key=lambda factor: factor.score,
            )
        )

        strongest = max(
            strategic_factors,
            key=lambda factor: (
                factor.score
                * cls.FACTOR_WEIGHTS[factor.factor_id]
            ),
        )

        weakest = min(
            strategic_factors,
            key=lambda factor: factor.score,
        )

        return MatchDecisionExplanationReport(
            match_id=match.match_id,
            placement=match.placement,
            overall_score=round(overall_score, 2),
            label=cls._label(overall_score),
            headline=cls._headline(
                placement=match.placement,
                positive=positive,
                critical=critical,
                attention=attention,
            ),
            summary=cls._summary(
                match=match,
                score=overall_score,
                strongest=strongest,
                weakest=weakest,
                contest_report=contest_report,
            ),
            strongest_factor=strongest,
            weakest_factor=weakest,
            positive_factors=positive,
            attention_factors=attention,
            critical_factors=critical,
            neutral_factors=(result_factor, *neutral),
            recommendations=cls._recommendations(
                match=match,
                attention=attention,
                critical=critical,
                neutral=neutral,
            ),
            caveats=(
                (
                    "O resultado observado é mostrado separadamente "
                    "e não é usado como causa da própria colocação."
                ),
                (
                    "A explicação usa o estado final da partida e não "
                    "reconstrói cada decisão por rodada."
                ),
                (
                    "Diferenças para o histórico representam "
                    "associação, não prova de causalidade."
                ),
            ),
        )

    @staticmethod
    def _impact(score: float) -> ExplanationImpact:
        if score >= 70.0:
            return ExplanationImpact.POSITIVE
        if score >= 55.0:
            return ExplanationImpact.NEUTRAL
        return ExplanationImpact.NEGATIVE

    @classmethod
    def _factor(
        cls,
        *,
        factor_id: str,
        title: str,
        score: float,
        historical_reference: float | None,
        explanation: str,
        evidence: tuple[str, ...],
        impact: ExplanationImpact | None = None,
    ) -> MatchExplanationFactor:
        difference = (
            score - historical_reference
            if historical_reference is not None
            else None
        )

        return MatchExplanationFactor(
            factor_id=factor_id,
            title=title,
            impact=impact or cls._impact(score),
            score=round(score, 2),
            historical_reference=(
                round(historical_reference, 2)
                if historical_reference is not None
                else None
            ),
            difference_from_history=(
                round(difference, 2)
                if difference is not None
                else None
            ),
            explanation=explanation,
            evidence=evidence,
        )

    @classmethod
    def _placement_factor(
        cls,
        *,
        match: Match,
        history_matches: list[Match],
    ) -> MatchExplanationFactor:
        score = (
            100.0
            - (match.placement - 1)
            / 7.0
            * 100.0
        )
        historical_placement = mean(
            item.placement
            for item in history_matches
        )
        historical_score = (
            100.0
            - (historical_placement - 1)
            / 7.0
            * 100.0
        )

        return cls._factor(
            factor_id="result",
            title="Resultado observado",
            score=score,
            historical_reference=historical_score,
            explanation=(
                "Consequência observada da partida; "
                "não é tratada como causa estratégica."
            ),
            evidence=(
                f"Colocação: {match.placement}º",
                (
                    "Colocação média recente: "
                    f"{historical_placement:.2f}"
                ),
            ),
            impact=ExplanationImpact.NEUTRAL,
        )

    @classmethod
    def _level_factor(
        cls,
        *,
        match: Match,
        history_matches: list[Match],
    ) -> MatchExplanationFactor:
        score = min(match.level / 9.0 * 100.0, 100.0)
        historical_level = mean(
            item.level
            for item in history_matches
        )
        historical_score = min(
            historical_level / 9.0 * 100.0,
            100.0,
        )

        explanation = (
            "O nível final ficou acima da média recente."
            if match.level > historical_level
            else (
                "O nível final ficou abaixo da média recente."
                if match.level < historical_level
                else "O nível final acompanhou a média recente."
            )
        )

        return cls._factor(
            factor_id="level",
            title="Progressão de nível",
            score=score,
            historical_reference=historical_score,
            explanation=explanation,
            evidence=(
                f"Nível final: {match.level}",
                f"Nível médio recente: {historical_level:.2f}",
            ),
        )

    @classmethod
    def _economy_factor(
        cls,
        *,
        match: Match,
        history_matches: list[Match],
    ) -> MatchExplanationFactor:
        historical_gold = mean(
            item.gold_left
            for item in history_matches
        )

        def score_gold(value: float) -> float:
            if value <= 10:
                return 75.0
            if value <= 20:
                return 65.0
            if value <= 35:
                return 55.0
            return 45.0

        score = score_gold(match.gold_left)
        historical_score = score_gold(historical_gold)

        explanation = (
            "O ouro final ficou em uma faixa compatível "
            "com conversão de recursos."
            if match.gold_left <= 20
            else (
                "A partida terminou com bastante ouro não convertido. "
                "Em derrotas, esse sinal merece revisão."
            )
        )

        return cls._factor(
            factor_id="economy",
            title="Conversão de economia",
            score=score,
            historical_reference=historical_score,
            explanation=explanation,
            evidence=(
                f"Ouro final: {match.gold_left}",
                (
                    "Ouro final médio recente: "
                    f"{historical_gold:.2f}"
                ),
            ),
        )

    @classmethod
    def _tempo_factor(
        cls,
        *,
        match: Match,
        history_matches: list[Match],
    ) -> MatchExplanationFactor:
        score = min(
            match.last_round / 38.0 * 100.0,
            100.0,
        )
        historical_round = mean(
            item.last_round
            for item in history_matches
        )
        historical_score = min(
            historical_round / 38.0 * 100.0,
            100.0,
        )

        explanation = (
            "A partida avançou mais que o padrão recente."
            if match.last_round > historical_round
            else (
                "A eliminação ocorreu antes do padrão recente."
                if match.last_round < historical_round
                else "A duração acompanhou o padrão recente."
            )
        )

        return cls._factor(
            factor_id="tempo",
            title="Sobrevivência e tempo",
            score=score,
            historical_reference=historical_score,
            explanation=explanation,
            evidence=(
                f"Round final: {match.last_round}",
                (
                    "Round final médio recente: "
                    f"{historical_round:.2f}"
                ),
            ),
        )

    @classmethod
    def _pressure_factor(
        cls,
        *,
        match: Match,
        history_matches: list[Match],
    ) -> MatchExplanationFactor:
        score = (
            min(
                match.total_damage_to_players / 120.0 * 100.0,
                100.0,
            )
            * 0.70
            + min(
                match.players_eliminated / 3.0 * 100.0,
                100.0,
            )
            * 0.30
        )

        historical_damage = mean(
            item.total_damage_to_players
            for item in history_matches
        )
        historical_eliminations = mean(
            item.players_eliminated
            for item in history_matches
        )
        historical_score = (
            min(historical_damage / 120.0 * 100.0, 100.0)
            * 0.70
            + min(
                historical_eliminations / 3.0 * 100.0,
                100.0,
            )
            * 0.30
        )

        explanation = (
            "A partida gerou pressão acima do padrão recente."
            if score > historical_score
            else (
                "A pressão sobre o lobby ficou abaixo do padrão recente."
                if score < historical_score
                else "A pressão acompanhou o padrão recente."
            )
        )

        return cls._factor(
            factor_id="pressure",
            title="Pressão no lobby",
            score=score,
            historical_reference=historical_score,
            explanation=explanation,
            evidence=(
                (
                    "Dano aos jogadores: "
                    f"{match.total_damage_to_players}"
                ),
                (
                    "Jogadores eliminados: "
                    f"{match.players_eliminated}"
                ),
                f"Dano médio recente: {historical_damage:.1f}",
            ),
        )

    @classmethod
    def _itemization_factor(
        cls,
        *,
        role_report,
    ) -> MatchExplanationFactor:
        carry_items = (
            len(role_report.damage_carry.item_ids)
            if role_report.damage_carry is not None
            else 0
        )
        tank_items = (
            len(role_report.main_tank.item_ids)
            if role_report.main_tank is not None
            else 0
        )
        support_items = (
            len(role_report.support.item_ids)
            if role_report.support is not None
            else 0
        )

        score = min(
            carry_items / 3.0 * 55.0
            + tank_items / 3.0 * 35.0
            + support_items / 3.0 * 10.0,
            100.0,
        )

        explanation = (
            "Carry e tank terminaram com itemização completa."
            if carry_items >= 3 and tank_items >= 3
            else (
                "O carry terminou completo, mas o tank não."
                if carry_items >= 3
                else (
                    "O tank terminou completo, mas o carry não."
                    if tank_items >= 3
                    else "Carry e tank terminaram incompletos."
                )
            )
        )

        return cls._factor(
            factor_id="itemization",
            title="Itemização da partida",
            score=score,
            historical_reference=None,
            explanation=explanation,
            evidence=(
                f"Itens no carry: {carry_items}",
                f"Itens no tank: {tank_items}",
                f"Itens no suporte: {support_items}",
                (
                    "Carry detectado: "
                    f"{cls._role_display_name(role_report.damage_carry)}"
                ),
                (
                    "Tank detectado: "
                    f"{cls._role_display_name(role_report.main_tank)}"
                ),
            ),
        )

    @staticmethod
    def _role_display_name(assessment) -> str:
        if assessment is None:
            return "-"

        character_id = str(
            getattr(assessment, "character_id", "") or ""
        ).strip()

        if not character_id:
            return "-"

        return UnitCatalogRepository.display_name(
            character_id=character_id,
            fallback="-",
        )

    @classmethod
    def _contest_factor(
        cls,
        *,
        match: Match,
        contest_report,
        contest_history: ContestHistoryReport | None,
    ) -> MatchExplanationFactor:
        base_score = max(0.0, 100.0 - contest_report.score)
        carry_contested = bool(contest_report.carry_contested)
        opponents = int(
            contest_report.opponents_contesting_carry
        )

        placement_bonus = (
            12.0
            if match.placement == 1
            else (
                8.0
                if match.placement <= 2
                else 4.0 if match.placement <= 4 else 0.0
            )
        )
        no_direct_bonus = (
            15.0
            if not carry_contested and opponents == 0
            else 0.0
        )
        direct_penalty = min(
            30.0,
            opponents * 10.0
            + (10.0 if carry_contested else 0.0),
        )

        score = max(
            0.0,
            min(
                100.0,
                base_score
                + placement_bonus
                + no_direct_bonus
                - direct_penalty,
            ),
        )

        historical_reference = (
            max(
                0.0,
                100.0 - contest_history.average_score,
            )
            if contest_history is not None
            else None
        )

        if not carry_contested and opponents == 0:
            explanation = (
                "Houve sobreposição, mas o carry não foi diretamente "
                "contestado e a composição pôde ser finalizada."
            )
        elif carry_contested or opponents > 0:
            explanation = (
                "O carry foi diretamente disputado, aumentando "
                "o risco da composição."
            )
        elif contest_report.score < 35.0:
            explanation = "A contestação foi baixa."
        elif contest_report.score < 60.0:
            explanation = (
                "A contestação geral foi moderada, sem bloqueio "
                "claro ao carry."
            )
        else:
            explanation = (
                "A composição esteve fortemente contestada."
            )

        return cls._factor(
            factor_id="contest",
            title="Contestação da partida",
            score=score,
            historical_reference=historical_reference,
            explanation=explanation,
            evidence=(
                (
                    "Score bruto de contestação: "
                    f"{contest_report.score:.1f}"
                ),
                (
                    "Carry contestado: "
                    f"{'Sim' if carry_contested else 'Não'}"
                ),
                f"Adversários no carry: {opponents}",
                (
                    "Ajuste contextual: "
                    f"{score - base_score:+.1f}"
                ),
            ),
        )

    @staticmethod
    def _recommendations(
        *,
        match: Match,
        attention: tuple[MatchExplanationFactor, ...],
        critical: tuple[MatchExplanationFactor, ...],
        neutral: tuple[MatchExplanationFactor, ...],
    ) -> tuple[str, ...]:
        recommendations = []

        for factor in critical:
            recommendations.append(
                f"Corrija {factor.title.lower()}: {factor.explanation}"
            )

        for factor in attention:
            recommendations.append(
                f"Revise {factor.title.lower()}: {factor.explanation}"
            )

        if not recommendations and match.placement > 4:
            for factor in neutral[:2]:
                recommendations.append(
                    f"Refine {factor.title.lower()}: {factor.explanation}"
                )

        return tuple(recommendations[:3])

    @staticmethod
    def _headline(
        *,
        placement: int,
        positive: tuple[MatchExplanationFactor, ...],
        critical: tuple[MatchExplanationFactor, ...],
        attention: tuple[MatchExplanationFactor, ...],
    ) -> str:
        if placement <= 2 and not critical:
            return (
                "A partida teve execução forte e converteu "
                "os principais recursos em resultado."
            )
        if placement >= 7 and critical:
            return (
                "A partida teve sinais claros que ajudam a explicar "
                "a eliminação precoce."
            )
        if critical or attention:
            return (
                "O resultado foi limitado por fatores estratégicos "
                "identificáveis."
            )
        if positive:
            return (
                "A partida foi consistente e teve mais sinais "
                "positivos do que negativos."
            )
        return (
            "A partida ficou próxima do padrão recente."
        )

    @staticmethod
    def _summary(
        *,
        match: Match,
        score: float,
        strongest: MatchExplanationFactor,
        weakest: MatchExplanationFactor,
        contest_report,
    ) -> str:
        if weakest.score >= 70.0:
            weakest_sentence = (
                "O fator com menor contribuição foi "
                f"{weakest.title.lower()}, ainda em nível positivo "
                f"({weakest.score:.0f}/100)."
            )
        elif weakest.score >= 55.0:
            weakest_sentence = (
                "O principal espaço de refinamento foi "
                f"{weakest.title.lower()} "
                f"({weakest.score:.0f}/100)."
            )
        else:
            weakest_sentence = (
                "O maior limitador foi "
                f"{weakest.title.lower()} "
                f"({weakest.score:.0f}/100)."
            )

        contest_sentence = (
            "A contestação não atingiu diretamente o carry."
            if (
                not contest_report.carry_contested
                and contest_report.opponents_contesting_carry == 0
            )
            else "O carry sofreu contestação direta."
        )

        return (
            f"A partida terminou em {match.placement}º lugar e recebeu "
            f"nota estratégica {score:.1f}/100. O principal fator "
            f"positivo foi {strongest.title.lower()} "
            f"({strongest.score:.0f}/100). "
            f"{weakest_sentence} {contest_sentence}"
        )

    @staticmethod
    def _label(score: float) -> str:
        if score < 40.0:
            return "Crítica"
        if score < 55.0:
            return "Atenção"
        if score < 70.0:
            return "Regular"
        if score < 80.0:
            return "Boa"
        return "Muito forte"
