from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


class Sprint1Formatter:
    @classmethod
    def to_dict(cls, value: Any) -> Any:
        if is_dataclass(value):
            return cls.to_dict(asdict(value))
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: cls.to_dict(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls.to_dict(item) for item in value]
        return value
