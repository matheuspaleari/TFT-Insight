"""
Configuração dos grupos competitivos usados pelos benchmarks.
"""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TierSamplingRule:
    """
    Define como um elo participa da amostragem do benchmark.
    """

    tier: str

    divisions: tuple[str, ...] = ()

    target_players: int = 0


@dataclass(slots=True, frozen=True)
class BenchmarkGroupConfiguration:
    """
    Configuração completa de um grupo de benchmark.
    """

    benchmark_id: str

    display_name: str

    sampling_rules: tuple[
        TierSamplingRule,
        ...,
    ]

    target_valid_players: int = 50

    matches_per_player: int = 30

    candidate_multiplier: float = 1.5

    @property
    def candidate_limit(self) -> int:
        """
        Quantidade estimada de candidatos a buscar.

        O valor é maior que a meta porque alguns jogadores podem
        falhar durante a coleta ou não possuir partidas suficientes.
        """

        return max(
            self.target_valid_players,
            round(
                self.target_valid_players
                * self.candidate_multiplier
            ),
        )


BENCHMARK_GROUP_CONFIGURATIONS = {
    "novice": BenchmarkGroupConfiguration(
        benchmark_id="novice",
        display_name="Fundamentos",
        sampling_rules=(
            TierSamplingRule(
                tier="IRON",
                divisions=("I", "II", "III", "IV"),
                target_players=17,
            ),
            TierSamplingRule(
                tier="BRONZE",
                divisions=("I", "II", "III", "IV"),
                target_players=17,
            ),
            TierSamplingRule(
                tier="SILVER",
                divisions=("I", "II", "III", "IV"),
                target_players=16,
            ),
        ),
    ),
    "intermediate": BenchmarkGroupConfiguration(
        benchmark_id="intermediate",
        display_name="Competitivo",
        sampling_rules=(
            TierSamplingRule(
                tier="GOLD",
                divisions=("I", "II", "III", "IV"),
                target_players=25,
            ),
            TierSamplingRule(
                tier="PLATINUM",
                divisions=("I", "II", "III", "IV"),
                target_players=25,
            ),
        ),
    ),
    "advanced": BenchmarkGroupConfiguration(
        benchmark_id="advanced",
        display_name="Avançado",
        sampling_rules=(
            TierSamplingRule(
                tier="EMERALD",
                divisions=("I", "II", "III", "IV"),
                target_players=25,
            ),
            TierSamplingRule(
                tier="DIAMOND",
                divisions=("I", "II", "III", "IV"),
                target_players=25,
            ),
        ),
    ),
    "expert": BenchmarkGroupConfiguration(
        benchmark_id="expert",
        display_name="Especialista",
        sampling_rules=(
            TierSamplingRule(
                tier="MASTER",
                target_players=50,
            ),
        ),
    ),
    "elite": BenchmarkGroupConfiguration(
        benchmark_id="elite",
        display_name="Elite",
        sampling_rules=(
            TierSamplingRule(
                tier="GRANDMASTER",
                target_players=30,
            ),
            TierSamplingRule(
                tier="CHALLENGER",
                target_players=20,
            ),
        ),
    ),
}


def get_benchmark_group_configuration(
    benchmark_id: str,
) -> BenchmarkGroupConfiguration:
    """
    Retorna a configuração de um benchmark pelo identificador.
    """

    normalized_id = benchmark_id.strip().lower()

    try:
        return BENCHMARK_GROUP_CONFIGURATIONS[
            normalized_id
        ]

    except KeyError as error:
        available = ", ".join(
            sorted(
                BENCHMARK_GROUP_CONFIGURATIONS
            )
        )

        raise ValueError(
            "Grupo de benchmark inválido: "
            f"{benchmark_id}. "
            f"Valores disponíveis: {available}."
        ) from error