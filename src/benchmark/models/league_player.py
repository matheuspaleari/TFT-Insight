"""
Modelo que representa um jogador selecionado para benchmark.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class LeaguePlayer:
    """
    Representa um jogador ranqueado selecionado como candidato.

    O modelo evita que dicionários crus da Riot API circulem
    entre o Provider e o BenchmarkCollector.
    """

    puuid: str

    tier: str
    division: str

    league_points: int = 0
    wins: int = 0
    losses: int = 0

    veteran: bool = False
    inactive: bool = False
    fresh_blood: bool = False
    hot_streak: bool = False

    def __post_init__(self) -> None:
        if not self.puuid.strip():
            raise ValueError(
                "LeaguePlayer.puuid não pode ser vazio."
            )

        if not self.tier.strip():
            raise ValueError(
                "LeaguePlayer.tier não pode ser vazio."
            )

        if not self.division.strip():
            raise ValueError(
                "LeaguePlayer.division não pode ser vazia."
            )

        if self.league_points < 0:
            raise ValueError(
                "LeaguePlayer.league_points não pode ser negativo."
            )

        if self.wins < 0:
            raise ValueError(
                "LeaguePlayer.wins não pode ser negativo."
            )

        if self.losses < 0:
            raise ValueError(
                "LeaguePlayer.losses não pode ser negativo."
            )

    @property
    def games_played(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0

        return round(
            self.wins
            / self.games_played
            * 100,
            2,
        )

    @property
    def rank_label(self) -> str:
        return (
            f"{self.tier} "
            f"{self.division}"
        ).strip()

    @classmethod
    def from_riot_entry(
        cls,
        entry: dict[str, Any],
        *,
        fallback_tier: str = "",
        fallback_division: str = "I",
    ) -> "LeaguePlayer":
        """
        Converte uma entrada da Riot API em LeaguePlayer.
        """

        puuid = entry.get("puuid")

        if not isinstance(puuid, str) or not puuid.strip():
            raise ValueError(
                "A entrada da Riot não possui um PUUID válido."
            )

        tier = str(
            entry.get(
                "tier",
                fallback_tier,
            )
        ).strip().upper()

        division = str(
            entry.get(
                "rank",
                fallback_division,
            )
        ).strip().upper()

        if not tier:
            tier = fallback_tier.strip().upper()

        if not division:
            division = fallback_division.strip().upper()

        return cls(
            puuid=puuid.strip(),
            tier=tier,
            division=division,
            league_points=cls._to_non_negative_int(
                entry.get("leaguePoints")
            ),
            wins=cls._to_non_negative_int(
                entry.get("wins")
            ),
            losses=cls._to_non_negative_int(
                entry.get("losses")
            ),
            veteran=bool(
                entry.get("veteran", False)
            ),
            inactive=bool(
                entry.get("inactive", False)
            ),
            fresh_blood=bool(
                entry.get("freshBlood", False)
            ),
            hot_streak=bool(
                entry.get("hotStreak", False)
            ),
        )

    @staticmethod
    def _to_non_negative_int(
        value: Any,
    ) -> int:
        try:
            converted = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(converted, 0)