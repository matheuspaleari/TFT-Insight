from dataclasses import dataclass
import os


@dataclass(slots=True, frozen=True)
class IntegrationSettings:
    app_name: str = "TFT Insight API"
    api_version: str = "1.0.0"
    contract_version: str = "1.0.0"
    environment: str = "development"
    api_keys: tuple[str, ...] = ()
    allow_unauthenticated_dev: bool = True

    @classmethod
    def from_environment(cls) -> "IntegrationSettings":
        raw_keys = os.getenv("TFT_INSIGHT_API_KEYS", "")

        api_keys = tuple(
            value.strip()
            for value in raw_keys.split(",")
            if value.strip()
        )

        environment = os.getenv(
            "TFT_INSIGHT_ENV",
            "development",
        ).strip().lower()

        allow_dev = os.getenv(
            "TFT_INSIGHT_ALLOW_UNAUTHENTICATED_DEV",
            "true",
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        return cls(
            environment=environment,
            api_keys=api_keys,
            allow_unauthenticated_dev=allow_dev,
        )
