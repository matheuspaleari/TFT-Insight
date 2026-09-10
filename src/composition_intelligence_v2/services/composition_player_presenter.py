from __future__ import annotations

from src.role_inference.repositories.unit_catalog_repository import (
    UnitCatalogRepository,
)


class CompositionPlayerPresenter:
    """
    Camada pública simples para o #25.

    Não recalcula analytics.
    Apenas transforma o relatório já calculado em payload amigável.
    """

    @classmethod
    def build(cls, report) -> dict:
        profiles = [
            cls._profile(item)
            for item in report.profiles
        ]

        best = (
            cls._profile(report.best_supported)
            if report.best_supported is not None
            else None
        )

        return {
            "summary": {
                "matches_analyzed": report.matches_analyzed,
                "unique_compositions": report.unique_compositions,
                "diversity_rate": report.diversity_rate,
                "repetition_rate": report.repetition_rate,
                "repetition_signal": report.repetition_signal,
                "repetition_interpretation": (
                    report.repetition_interpretation
                ),
            },
            "most_used": cls._profile(report.most_used),
            "best_supported": best,
            "compositions": profiles,
            "coach": cls._coach(report),
            "limitations": list(report.limitations),
        }

    @classmethod
    def _profile(cls, profile) -> dict:
        return {
            "composition_key": profile.composition_key,
            "carry_character_id": profile.carry_character_id,
            "carry_name": cls._display_name(profile.carry_character_id),
            "tank_character_id": profile.tank_character_id,
            "tank_name": cls._display_name(profile.tank_character_id),
            # Support foi retirado da camada pública porque a auditoria
            # real encontrou 0/30 identificações confiáveis.
            "primary_trait_names": list(
                profile.primary_trait_names
            ),
            "core_unit_ids": list(profile.core_unit_ids),
            "matches_played": profile.matches_played,
            "usage_rate": profile.usage_rate,
            "average_placement": profile.average_placement,
            "top4_rate": profile.top4_rate,
            "win_rate": profile.win_rate,
            "average_contest_score": (
                profile.average_contest_score
            ),
            "eligible_for_comparison": (
                profile.matches_played >= 3
            ),
            "statistical_confidence": {
                "score": profile.confidence_score,
                "level": profile.confidence_level,
            },
            "recommendation": {
                "score": profile.recommendation_score,
                "label": profile.recommendation_label,
            },
        }


    @staticmethod
    def _display_name(character_id, fallback: str = "") -> str:
        if not character_id:
            return fallback
        return UnitCatalogRepository.display_name(
            character_id=str(character_id),
            fallback=fallback,
        )

    @classmethod
    def _coach(cls, report) -> dict:
        most = report.most_used
        best = report.best_supported

        observations = [
            report.repetition_interpretation,
        ]

        if best is not None:
            observations.append(
                "Entre as composições elegíveis para comparação, "
                f"{best.composition_key} apresentou média "
                f"{best.average_placement:.2f} em "
                f"{best.matches_played} partidas. "
                "Isso descreve o histórico; não prova que ela seja "
                "a melhor escolha para qualquer lobby."
            )
        else:
            observations.append(
                "Nenhuma composição atingiu ainda a amostra mínima "
                "de 3 partidas para comparação."
            )

        return {
            "headline": (
                "Seu histórico de composições"
            ),
            "most_used_reading": (
                f"{most.composition_key} foi sua estrutura mais repetida "
                f"no período, aparecendo em {most.matches_played} partida(s)."
            ),
            "observations": observations,
            "guardrails": [
                "Repetição não prova intenção de forçar composição.",
                "Board final não reconstrói todas as transições da partida.",
                "Desempenho histórico não substitui leitura do lobby.",
            ],
        }
