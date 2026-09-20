from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Holiday:
    id: str
    name: str
    date: date
    type: str
    substitute: bool = False
    sources: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.isoformat(),
            "type": self.type,
            "substitute": self.substitute,
            "sources": list(self.sources),
        }