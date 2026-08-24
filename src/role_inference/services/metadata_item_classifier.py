import re

from src.role_inference.models import (
    ItemCategory,
    ItemClassification,
    RichItemData,
)


class MetadataItemClassifier:
    """
    Classifica pelos efeitos estruturados e pela descrição.

    Não depende de nomes específicos de itens.
    """

    OFFENSE_TERMS = (
        "attackdamage", "abilitypower", "attackspeed",
        "criticalstrike", "crit", "dano de ataque",
        "poder de habilidade", "velocidade de ataque",
        "dano", "crítico",
    )

    DEFENSE_TERMS = (
        "health", "armor", "magicresist",
        "damage reduction", "vida", "armadura",
        "resistência mágica", "redução de dano",
        "escudo",
    )

    UTILITY_TERMS = (
        "mana", "healing", "shielding", "omnivamp",
        "cura", "mana", "equipe", "aliados",
        "controle", "stun", "slow",
    )

    @classmethod
    def classify(
        cls,
        item: RichItemData,
    ) -> ItemClassification:
        searchable = " ".join(
            [
                item.description,
                *item.effects.keys(),
            ]
        ).lower()

        offense = cls._term_score(
            searchable,
            cls.OFFENSE_TERMS,
        )
        defense = cls._term_score(
            searchable,
            cls.DEFENSE_TERMS,
        )
        utility = cls._term_score(
            searchable,
            cls.UTILITY_TERMS,
        )

        evidence = []

        for label, score in (
            ("sinais ofensivos", offense),
            ("sinais defensivos", defense),
            ("sinais utilitários", utility),
        ):
            if score > 0:
                evidence.append(f"{label}: {score:.0f}")

        maximum = max(
            offense,
            defense,
            utility,
        )

        if maximum == 0:
            category = ItemCategory.UNKNOWN
            confidence = 0.0
        else:
            ordered = sorted(
                (offense, defense, utility),
                reverse=True,
            )
            margin = ordered[0] - ordered[1]

            if margin < 15:
                category = ItemCategory.HYBRID
            elif maximum == offense:
                category = ItemCategory.OFFENSE
            elif maximum == defense:
                category = ItemCategory.DEFENSE
            else:
                category = ItemCategory.UTILITY

            confidence = min(
                100.0,
                55.0 + margin,
            )

        return ItemClassification(
            item_id=item.item_id,
            category=category,
            confidence=round(confidence, 2),
            offense_score=offense,
            defense_score=defense,
            utility_score=utility,
            evidence=tuple(evidence),
            source="communitydragon_metadata",
        )

    @staticmethod
    def _term_score(
        searchable: str,
        terms: tuple[str, ...],
    ) -> float:
        matches = sum(
            1
            for term in terms
            if re.search(
                re.escape(term.lower()),
                searchable,
            )
        )

        return min(
            100.0,
            matches * 25.0,
        )
