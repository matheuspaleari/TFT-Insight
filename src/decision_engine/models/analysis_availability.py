from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AnalysisAvailability:
    available: bool
    reason: str = ""

    @classmethod
    def yes(cls) -> "AnalysisAvailability":
        return cls(available=True)

    @classmethod
    def no(
        cls,
        reason: str,
    ) -> "AnalysisAvailability":
        return cls(
            available=False,
            reason=reason,
        )
