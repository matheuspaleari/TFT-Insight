"""
Configuração dos grupos competitivos usados pelos benchmarks.
"""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TierSamplingRule:
    """Define como um elo participa da amostragem do benchmark."""

    tier: str
    divisions: tuple[str, ...] = ()
    target_players: int = 0


@dataclass(slots=True, frozen=True)
class BenchmarkGroupConfiguration:
    """Configuração completa de um grupo de benchmark."""

    benchmark_id: str
    display_name: str
    sampling_rules: tuple[TierSamplingRule, ...]
    target_valid_players: int = 100
    matches_per_player: int = 30
    candidate_multiplier: float = 1.5
    target_set_number: int = 18
    target_set_core_name: str = "TFTSet18"
    match_scan_multiplier: float = 2.0

    @property
    def candidate_limit(self) -> int:
        """Quantidade estimada de candidatos a buscar."""
        return max(
            self.target_valid_players,
            round(self.target_valid_players * self.candidate_multiplier),
        )

    @property
    def match_scan_limit(self) -> int:
        """IDs recentes consultados para obter até 30 partidas do Set alvo."""
        return max(
            self.matches_per_player,
            round(self.matches_per_player * self.match_scan_multiplier),
        )


BENCHMARK_GROUP_CONFIGURATIONS = {
    "novice": BenchmarkGroupConfiguration(
        benchmark_id="novice",
        display_name="Fundamentos",
        sampling_rules=(
            TierSamplingRule("IRON", ("I", "II", "III", "IV"), 34),
            TierSamplingRule("BRONZE", ("I", "II", "III", "IV"), 33),
            TierSamplingRule("SILVER", ("I", "II", "III", "IV"), 33),
        ),
    ),
    "intermediate": BenchmarkGroupConfiguration(
        benchmark_id="intermediate",
        display_name="Competitivo",
        sampling_rules=(
            TierSamplingRule("GOLD", ("I", "II", "III", "IV"), 50),
            TierSamplingRule("PLATINUM", ("I", "II", "III", "IV"), 50),
        ),
    ),
    "advanced": BenchmarkGroupConfiguration(
        benchmark_id="advanced",
        display_name="Avançado",
        sampling_rules=(
            TierSamplingRule("EMERALD", ("I", "II", "III", "IV"), 50),
            TierSamplingRule("DIAMOND", ("I", "II", "III", "IV"), 50),
        ),
    ),
    "expert": BenchmarkGroupConfiguration(
        benchmark_id="expert",
        display_name="Especialista",
        sampling_rules=(
            TierSamplingRule("MASTER", target_players=100),
        ),
    ),
    "elite": BenchmarkGroupConfiguration(
        benchmark_id="elite",
        display_name="Elite",
        sampling_rules=(
            TierSamplingRule("GRANDMASTER", target_players=60),
            TierSamplingRule("CHALLENGER", target_players=40),
        ),
    ),
}


def get_benchmark_group_configuration(
    benchmark_id: str,
) -> BenchmarkGroupConfiguration:
    """Retorna a configuração de um benchmark pelo identificador."""

    normalized_id = benchmark_id.strip().lower()

    try:
        return BENCHMARK_GROUP_CONFIGURATIONS[normalized_id]
    except KeyError as error:
        available = ", ".join(sorted(BENCHMARK_GROUP_CONFIGURATIONS))
        raise ValueError(
            "Grupo de benchmark inválido: "
            f"{benchmark_id}. Valores disponíveis: {available}."
        ) from error
