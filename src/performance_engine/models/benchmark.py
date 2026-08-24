from dataclasses import dataclass
from typing import Any

from .benchmark_metric import BenchmarkMetric


@dataclass(slots=True, frozen=True)
class Benchmark:
    """
    Valores de referência obtidos a partir de jogadores
    de alto nível do ranking de TFT.
    """

    name: str

    players_analyzed: int
    matches_analyzed: int

    average_placement: float
    top4_rate: float
    win_rate: float

    average_level: BenchmarkMetric
    placement_standard_deviation: BenchmarkMetric

    bottom4_rate: float

    average_damage_to_players: BenchmarkMetric
    average_players_eliminated: BenchmarkMetric

    average_gold_left: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "O nome do benchmark não pode ser vazio."
            )

        if self.players_analyzed < 1:
            raise ValueError(
                "O benchmark deve possuir ao menos um jogador."
            )

        if self.matches_analyzed < 1:
            raise ValueError(
                "O benchmark deve possuir ao menos uma partida."
            )

        if not 1.0 <= self.average_placement <= 8.0:
            raise ValueError(
                "A colocação média deve estar entre 1 e 8."
            )

        if self.average_gold_left < 0:
            raise ValueError(
                "A média de ouro restante não pode ser negativa."
            )

        self._validate_percentage(
            "top4_rate",
            self.top4_rate,
        )

        self._validate_percentage(
            "win_rate",
            self.win_rate,
        )

        self._validate_percentage(
            "bottom4_rate",
            self.bottom4_rate,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Converte o benchmark em um dicionário serializável.
        """

        return {
            "name": self.name,
            "players_analyzed": self.players_analyzed,
            "matches_analyzed": self.matches_analyzed,
            "average_placement": self.average_placement,
            "top4_rate": self.top4_rate,
            "win_rate": self.win_rate,
            "average_level": self.average_level.to_dict(),
            "placement_standard_deviation": (
                self.placement_standard_deviation.to_dict()
            ),
            "bottom4_rate": self.bottom4_rate,
            "average_damage_to_players": (
                self.average_damage_to_players.to_dict()
            ),
            "average_players_eliminated": (
                self.average_players_eliminated.to_dict()
            ),
            "average_gold_left": self.average_gold_left,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Benchmark":
        """
        Reconstrói um Benchmark a partir de um dicionário.
        """

        required_fields = {
            "name",
            "players_analyzed",
            "matches_analyzed",
            "average_placement",
            "top4_rate",
            "win_rate",
            "average_level",
            "placement_standard_deviation",
            "bottom4_rate",
            "average_damage_to_players",
            "average_players_eliminated",
            "average_gold_left",
        }

        missing_fields = required_fields - data.keys()

        if missing_fields:
            raise ValueError(
                "Campos ausentes no benchmark: "
                + ", ".join(sorted(missing_fields))
            )

        return cls(
            name=str(data["name"]),
            players_analyzed=int(
                data["players_analyzed"]
            ),
            matches_analyzed=int(
                data["matches_analyzed"]
            ),
            average_placement=float(
                data["average_placement"]
            ),
            top4_rate=float(data["top4_rate"]),
            win_rate=float(data["win_rate"]),
            average_level=BenchmarkMetric.from_dict(
                data["average_level"]
            ),
            placement_standard_deviation=(
                BenchmarkMetric.from_dict(
                    data[
                        "placement_standard_deviation"
                    ]
                )
            ),
            bottom4_rate=float(data["bottom4_rate"]),
            average_damage_to_players=(
                BenchmarkMetric.from_dict(
                    data["average_damage_to_players"]
                )
            ),
            average_players_eliminated=(
                BenchmarkMetric.from_dict(
                    data[
                        "average_players_eliminated"
                    ]
                )
            ),
            average_gold_left=float(
                data["average_gold_left"]
            ),
        )

    @staticmethod
    def _validate_percentage(
        name: str,
        value: float,
    ) -> None:
        if not 0.0 <= value <= 100.0:
            raise ValueError(
                f"{name} deve estar entre 0 e 100."
            )