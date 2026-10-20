"""Validated wire models. Time is an integer logical timestamp, not wall time."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Event:
    event_id: str
    tenant: str
    key: str
    value: str
    at: int
    subject: str = "default"
    operation: str = "put"
    source: str = "user"
    supersedes: str | None = None

    def __post_init__(self):
        for name in ("event_id", "tenant", "subject", "key", "source"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a nonempty string")
        if type(self.at) is not int or self.at < 0:
            raise ValueError("at must be a nonnegative integer")
        if not isinstance(self.value, str):
            raise ValueError("value must be a string")
        if self.operation not in {"put", "delete"}:
            raise ValueError("operation must be put or delete")
        if self.operation == "delete" and self.value:
            raise ValueError("deletion events cannot carry a value")
        if self.supersedes is not None and (
            not isinstance(self.supersedes, str) or not self.supersedes.strip()
        ):
            raise ValueError("supersedes must name an event")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise ValueError("event must be an object")
        try:
            return cls(**value)
        except TypeError as exc:
            raise ValueError(f"invalid event fields: {exc}") from exc


@dataclass(frozen=True)
class Memory:
    tenant: str
    key: str
    value: str
    event_id: str
    at: int
    source: str
    subject: str = "default"


@dataclass(frozen=True)
class Query:
    tenant: str
    key: str
    as_of: int
    subject: str = "default"

    def __post_init__(self):
        if not isinstance(self.tenant, str) or not self.tenant.strip():
            raise ValueError("tenant must be nonempty")
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("key must be nonempty")
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("subject must be nonempty")
        if type(self.as_of) is not int or self.as_of < 0:
            raise ValueError("as_of must be a nonnegative integer")
