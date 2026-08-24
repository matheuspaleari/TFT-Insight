from __future__ import annotations

from typing import Iterable

from src.learning.models.skill_assessment import SkillAssessment
from src.learning.models.skill_level import SkillLevel
from src.learning.models.skill_signal import SkillSignal
from src.learning.models.skill_fusion_result import SkillFusionResult


class SkillEvidenceFusionService:
    """
    Combina SkillAssessment oficial com SkillSignals históricos.

    Regras:
    - o assessment oficial continua sendo a referência de nível/score;
    - Habits acrescentam evidência longitudinal;
    - não há média cega entre níveis ou scores;
    - Signal divergente não promove/rebaixa automaticamente;
    - contexto não avaliável nunca vira nota;
    - Skill sem assessment oficial fica como candidata.

    O modelo Skill oficial do TFT Insight usa o atributo `id`.
    """

    @classmethod
    def fuse(
        cls,
        *,
        assessments: tuple[SkillAssessment, ...],
        signals: tuple[SkillSignal, ...],
    ) -> tuple[SkillFusionResult, ...]:
        assessments_by_id = {
            cls._assessment_skill_id(assessment): assessment
            for assessment in assessments
        }

        signals_by_id: dict[str, list[SkillSignal]] = {}

        for signal in signals:
            signals_by_id.setdefault(
                signal.skill_id,
                [],
            ).append(signal)

        skill_ids = tuple(
            dict.fromkeys(
                [
                    *assessments_by_id.keys(),
                    *signals_by_id.keys(),
                ]
            )
        )

        results = tuple(
            cls._fuse_skill(
                skill_id=skill_id,
                assessment=assessments_by_id.get(skill_id),
                signals=tuple(
                    signals_by_id.get(
                        skill_id,
                        (),
                    )
                ),
            )
            for skill_id in skill_ids
        )

        return tuple(
            sorted(
                results,
                key=cls._result_order,
            )
        )

    @staticmethod
    def _assessment_skill_id(
        assessment: SkillAssessment,
    ) -> str:
        skill = assessment.skill

        value = getattr(
            skill,
            "id",
            None,
        )

        if not value:
            value = getattr(
                skill,
                "skill_id",
                None,
            )

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "SkillAssessment contém Skill sem identificador válido."
            )

        return value.strip()

    @classmethod
    def _fuse_skill(
        cls,
        *,
        skill_id: str,
        assessment: SkillAssessment | None,
        signals: tuple[SkillSignal, ...],
    ) -> SkillFusionResult:
        if assessment is None:
            return cls._candidate_skill(
                skill_id=skill_id,
                signals=signals,
            )

        baseline_level = assessment.level
        baseline_score = float(assessment.score)
        baseline_confidence = float(
            assessment.confidence
        )

        assessable = tuple(
            signal
            for signal in signals
            if signal.assessable
            and signal.level_hint is not None
        )

        contextual = tuple(
            signal
            for signal in signals
            if not signal.assessable
        )

        evidence_ids = cls._unique(
            [
                *assessment.evidence_metric_ids,
                *(
                    evidence_id
                    for signal in signals
                    for evidence_id in signal.evidence_ids
                ),
            ]
        )

        limitations = cls._unique(
            [
                *assessment.limitations,
                *(
                    limitation
                    for signal in signals
                    for limitation in signal.limitations
                ),
            ]
        )

        if not signals:
            return SkillFusionResult(
                skill_id=skill_id,
                skill_label=assessment.skill.title,
                baseline_available=True,
                baseline_level=baseline_level,
                baseline_score=baseline_score,
                baseline_confidence=baseline_confidence,
                fused_level=baseline_level,
                fused_score=baseline_score,
                fused_confidence=baseline_confidence,
                decision="baseline_only",
                supporting_signals=(),
                evidence_ids=evidence_ids,
                interpretation=(
                    "A avaliação oficial foi preservada porque não há "
                    "evidências históricas adicionais para esta Skill."
                ),
                limitations=limitations,
            )

        if baseline_level == SkillLevel.NOT_EVALUATED:
            return SkillFusionResult(
                skill_id=skill_id,
                skill_label=assessment.skill.title,
                baseline_available=True,
                baseline_level=baseline_level,
                baseline_score=baseline_score,
                baseline_confidence=baseline_confidence,
                fused_level=baseline_level,
                fused_score=baseline_score,
                fused_confidence=baseline_confidence,
                decision="context_only",
                supporting_signals=signals,
                evidence_ids=evidence_ids,
                interpretation=(
                    "Há evidências históricas relacionadas à Skill, mas "
                    "o assessment oficial continua não avaliado. A fusão "
                    "não promove uma Skill sem base oficial suficiente."
                ),
                limitations=limitations,
            )

        if not assessable:
            return SkillFusionResult(
                skill_id=skill_id,
                skill_label=assessment.skill.title,
                baseline_available=True,
                baseline_level=baseline_level,
                baseline_score=baseline_score,
                baseline_confidence=baseline_confidence,
                fused_level=baseline_level,
                fused_score=baseline_score,
                fused_confidence=baseline_confidence,
                decision="context_added",
                supporting_signals=contextual,
                evidence_ids=evidence_ids,
                interpretation=(
                    "O nível e o score oficiais foram preservados. Os Habits "
                    "acrescentam contexto, mas não possuem evidência direta "
                    "suficiente para alterar a Skill."
                ),
                limitations=limitations,
            )

        strongest = max(
            assessable,
            key=lambda signal: signal.confidence,
        )

        if strongest.level_hint == baseline_level:
            confidence = cls._reinforced_confidence(
                baseline=baseline_confidence,
                signal=strongest.confidence,
            )

            return SkillFusionResult(
                skill_id=skill_id,
                skill_label=assessment.skill.title,
                baseline_available=True,
                baseline_level=baseline_level,
                baseline_score=baseline_score,
                baseline_confidence=baseline_confidence,
                fused_level=baseline_level,
                fused_score=baseline_score,
                fused_confidence=confidence,
                decision="reinforced",
                supporting_signals=signals,
                evidence_ids=evidence_ids,
                interpretation=(
                    "A evidência longitudinal dos Habits é compatível com "
                    "o nível oficial. O nível e o score foram preservados; "
                    "somente a confiança recebeu reforço limitado."
                ),
                limitations=limitations,
            )

        return SkillFusionResult(
            skill_id=skill_id,
            skill_label=assessment.skill.title,
            baseline_available=True,
            baseline_level=baseline_level,
            baseline_score=baseline_score,
            baseline_confidence=baseline_confidence,
            fused_level=baseline_level,
            fused_score=baseline_score,
            fused_confidence=baseline_confidence,
            decision="evidence_disagreement",
            supporting_signals=signals,
            evidence_ids=evidence_ids,
            interpretation=(
                "O padrão histórico sugere um nível diferente do assessment "
                "oficial. O TFT Insight preserva a avaliação oficial e "
                "registra a divergência para acompanhamento, sem fazer média "
                "ou alterar o nível automaticamente."
            ),
            limitations=cls._unique(
                [
                    *limitations,
                    (
                        "Há divergência entre a avaliação pontual e o padrão "
                        "histórico; são necessárias mais evidências antes de "
                        "revisar o nível oficial."
                    ),
                ]
            ),
        )

    @classmethod
    def _candidate_skill(
        cls,
        *,
        skill_id: str,
        signals: tuple[SkillSignal, ...],
    ) -> SkillFusionResult:
        if not signals:
            raise ValueError(
                "Skill sem assessment e sem signal não pode ser fundida."
            )

        strongest = max(
            signals,
            key=lambda signal: signal.confidence,
        )

        assessable = (
            strongest.assessable
            and strongest.level_hint is not None
        )

        return SkillFusionResult(
            skill_id=skill_id,
            skill_label=strongest.skill_label,
            baseline_available=False,
            baseline_level=None,
            baseline_score=None,
            baseline_confidence=None,
            fused_level=(
                strongest.level_hint
                if assessable
                else None
            ),
            fused_score=None,
            fused_confidence=strongest.confidence,
            decision=(
                "candidate_skill"
                if assessable
                else "candidate_context"
            ),
            supporting_signals=signals,
            evidence_ids=cls._unique(
                evidence_id
                for signal in signals
                for evidence_id in signal.evidence_ids
            ),
            interpretation=(
                (
                    "Existe evidência histórica suficiente para propor esta "
                    "Skill ao catálogo, mas ainda não existe SkillAssessment "
                    "oficial. O nível é apenas uma sugestão de evidência."
                )
                if assessable
                else
                (
                    "Existe contexto histórico relacionado a esta Skill, mas "
                    "ainda não há evidência suficiente para avaliá-la nem "
                    "assessment oficial."
                )
            ),
            limitations=cls._unique(
                limitation
                for signal in signals
                for limitation in signal.limitations
            ),
        )

    @staticmethod
    def _reinforced_confidence(
        *,
        baseline: float,
        signal: float,
    ) -> float:
        support = (
            min(
                max(
                    signal,
                    0.0,
                ),
                100.0,
            )
            / 100.0
            * 5.0
        )

        return round(
            min(
                100.0,
                baseline + support,
            ),
            2,
        )

    @staticmethod
    def _unique(
        values: Iterable[str],
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                value
                for value in values
                if value
            )
        )

    @staticmethod
    def _result_order(
        result: SkillFusionResult,
    ) -> tuple[int, int, float]:
        decision_order = {
            "evidence_disagreement": 0,
            "candidate_skill": 1,
            "reinforced": 2,
            "context_added": 3,
            "candidate_context": 4,
            "context_only": 5,
            "baseline_only": 6,
        }

        level = (
            int(result.fused_level)
            if result.fused_level is not None
            else 999
        )

        confidence = (
            result.fused_confidence
            if result.fused_confidence is not None
            else 0.0
        )

        return (
            decision_order.get(
                result.decision,
                99,
            ),
            level,
            -confidence,
        )
