from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PlatformHealth:
    api_online: bool
    engine_status: str = "Healthy"
    learning_status: str = "Ready"
    sdk_version: str = "v0.1"

    @classmethod
    def resolve(
        cls,
        api_client,
    ) -> "PlatformHealth":
        try:
            response = api_client.health()
            api_online = (
                response.get("status") == "ok"
            )
        except Exception:
            api_online = False

        return cls(
            api_online=api_online
        )
