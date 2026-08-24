from __future__ import annotations

import re


class CarryItemPlayerPresenter:
    @classmethod
    def build(
        cls,
        report,
    ) -> dict:
        return {
            "summary": {
                "matches_analyzed": report.matches_analyzed,
                "matches_with_carry": report.matches_with_carry,
                "carry_detection_rate": report.carry_detection_rate,
                "itemization_score": report.itemization_score,
                "itemization_label": report.itemization_label,
                "carry_item_share": report.carry_item_share,
                "carry_full_item_rate": report.carry_full_item_rate,
                "unique_carries": report.unique_carries,
            },
            "most_used_carry": (
                report.most_used_carry.to_dict()
                if report.most_used_carry
                else None
            ),
            "best_supported_carry": (
                report.best_supported_carry.to_dict()
                if report.best_supported_carry
                else None
            ),
            "carries": [
                profile.to_dict()
                for profile in report.carry_profiles
            ],
            "latest": (
                report.latest.to_dict()
                if report.latest
                else None
            ),
            "coach": cls._coach(
                report
            ),
            "limitations": list(
                report.limitations
            ),
        }

    @classmethod
    def _coach(
        cls,
        report,
    ) -> dict:
        observations = []

        if report.most_used_carry:
            carry = report.most_used_carry
            observations.append(
                f"{cls._friendly_character(carry.character_id)} foi seu carry "
                f"mais recorrente no histórico, aparecendo em "
                f"{carry.matches_played} partida(s)."
            )

        if report.best_supported_carry:
            carry = report.best_supported_carry
            observations.append(
                f"Entre os carries com pelo menos 3 partidas, "
                f"{cls._friendly_character(carry.character_id)} teve colocação "
                f"média {carry.average_placement:.2f}. Isso descreve seu "
                "histórico e não significa que seja a melhor escolha para "
                "qualquer lobby."
            )
        else:
            observations.append(
                "Nenhum carry atingiu ainda a amostra mínima de 3 partidas "
                "para comparação histórica."
            )

        observations.append(
            f"O carry terminou com três ou mais itens em "
            f"{report.carry_full_item_rate:.1f}% das partidas analisadas."
        )

        return {
            "headline": "Carries e itemizações no seu histórico",
            "latest_reading": (
                (
                    f"Na partida mais recente, o carry identificado foi "
                    f"{cls._friendly_character(report.latest.character_id)}, "
                    f"com {len(report.latest.item_ids)} item(ns) no board final."
                )
                if report.latest
                else "Não foi possível identificar um carry com evidência "
                "suficiente na partida mais recente."
            ),
            "observations": observations,
            "next_match_principle": (
                "Use seu histórico para reconhecer padrões, mas adapte itens "
                "ao lobby, aos componentes disponíveis e à função que o carry "
                "precisa cumprir naquela partida."
            ),
            "guardrails": [
                "Item final não revela quando foi construído.",
                "Build histórica não é uma receita obrigatória.",
                "Desempenho com um conjunto não prova causalidade.",
                "Comparações de build só são úteis dentro do mesmo carry e com amostra suficiente.",
            ],
        }

    @staticmethod
    def _friendly_character(
        value: str,
    ) -> str:
        text = str(
            value
            or ""
        ).strip()

        text = re.sub(
            r"^TFT\d+_",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"(?<=[a-z])(?=[A-Z])",
            " ",
            text,
        )

        return (
            text
            or "carry identificado"
        )
