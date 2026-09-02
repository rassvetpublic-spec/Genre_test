from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Literal, Protocol, runtime_checkable

ProviderId = Literal["cpu", "cuda", "rocm", "mps", "xpu", "unknown"]
HealthState = Literal["available", "degraded", "unavailable"]


class BackendRuntimeError(ValueError):
    """Raised when runtime evidence violates the shared heavy-backend contract."""


def _required_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BackendRuntimeError(f"{field_name} must be a non-empty string")
    if "\x00" in value:
        raise BackendRuntimeError(f"{field_name} must not contain NUL")
    return value.strip()


def _optional_text(value: object, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field_name=field_name)


@dataclass(frozen=True)
class BackendIdentity:
    """Stable backend/model identity recorded beside every heavy operation."""

    backend_id: str
    backend_version: str
    model_id: str | None = None
    model_revision: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "backend_id",
            _required_text(self.backend_id, field_name="backend_id"),
        )
        object.__setattr__(
            self,
            "backend_version",
            _required_text(self.backend_version, field_name="backend_version"),
        )
        model_id = _optional_text(self.model_id, field_name="model_id")
        model_revision = _optional_text(self.model_revision, field_name="model_revision")
        if model_revision is not None and model_id is None:
            raise BackendRuntimeError("model_revision requires model_id")
        object.__setattr__(self, "model_id", model_id)
        object.__setattr__(self, "model_revision", model_revision)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BackendHealth:
    """Backend availability without triggering model acquisition or inference."""

    state: HealthState
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.state not in {"available", "degraded", "unavailable"}:
            raise BackendRuntimeError(f"unsupported health state: {self.state}")
        reason = _optional_text(self.reason, field_name="health.reason")
        if self.state != "available" and reason is None:
            raise BackendRuntimeError(f"health state {self.state!r} requires a reason")
        object.__setattr__(self, "reason", reason)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class BackendCapabilities:
    """Declared execution compatibility; this is not proof of an acquired provider."""

    providers: tuple[ProviderId, ...]
    dtypes: tuple[str, ...] = ()
    supports_cancel: bool = False
    requires_network: bool = False

    def __post_init__(self) -> None:
        providers = tuple(self.providers)
        if not providers:
            raise BackendRuntimeError("providers must contain at least one provider")
        allowed = {"cpu", "cuda", "rocm", "mps", "xpu", "unknown"}
        if any(item not in allowed for item in providers):
            raise BackendRuntimeError("providers contains an unsupported provider")
        if len(set(providers)) != len(providers):
            raise BackendRuntimeError("providers must not contain duplicates")
        dtypes = tuple(_required_text(item, field_name="dtypes item") for item in self.dtypes)
        if len(set(dtypes)) != len(dtypes):
            raise BackendRuntimeError("dtypes must not contain duplicates")
        object.__setattr__(self, "providers", providers)
        object.__setattr__(self, "dtypes", dtypes)

    def to_dict(self) -> dict[str, object]:
        return {
            "providers": list(self.providers),
            "dtypes": list(self.dtypes),
            "supports_cancel": self.supports_cancel,
            "requires_network": self.requires_network,
        }


@dataclass(frozen=True)
class ExecutionEvidence:
    """Requested-vs-actual execution truth for one backend operation."""

    requested_provider: ProviderId
    actual_provider: ProviderId
    requested_dtype: str | None = None
    actual_dtype: str | None = None
    fallback_reason: str | None = None
    device_name: str | None = None

    def __post_init__(self) -> None:
        allowed = {"cpu", "cuda", "rocm", "mps", "xpu", "unknown"}
        if self.requested_provider not in allowed:
            raise BackendRuntimeError("requested_provider is unsupported")
        if self.actual_provider not in allowed:
            raise BackendRuntimeError("actual_provider is unsupported")
        requested_dtype = _optional_text(
            self.requested_dtype,
            field_name="requested_dtype",
        )
        actual_dtype = _optional_text(self.actual_dtype, field_name="actual_dtype")
        fallback_reason = _optional_text(
            self.fallback_reason,
            field_name="fallback_reason",
        )
        device_name = _optional_text(self.device_name, field_name="device_name")

        provider_changed = self.requested_provider != self.actual_provider
        dtype_changed = (
            requested_dtype is not None
            and actual_dtype is not None
            and requested_dtype != actual_dtype
        )
        requested_dtype_missing = requested_dtype is not None and actual_dtype is None
        if (provider_changed or dtype_changed or requested_dtype_missing) and fallback_reason is None:
            raise BackendRuntimeError(
                "execution fallback must include fallback_reason; silent fallback is forbidden"
            )
        if fallback_reason is not None and not (
            provider_changed or dtype_changed or requested_dtype_missing
        ):
            raise BackendRuntimeError(
                "fallback_reason is only valid when actual execution differs from the request"
            )

        object.__setattr__(self, "requested_dtype", requested_dtype)
        object.__setattr__(self, "actual_dtype", actual_dtype)
        object.__setattr__(self, "fallback_reason", fallback_reason)
        object.__setattr__(self, "device_name", device_name)

    @property
    def used_fallback(self) -> bool:
        return self.fallback_reason is not None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "requested_provider": self.requested_provider,
            "actual_provider": self.actual_provider,
            "used_fallback": self.used_fallback,
        }
        if self.requested_dtype is not None:
            payload["requested_dtype"] = self.requested_dtype
        if self.actual_dtype is not None:
            payload["actual_dtype"] = self.actual_dtype
        if self.fallback_reason is not None:
            payload["fallback_reason"] = self.fallback_reason
        if self.device_name is not None:
            payload["device_name"] = self.device_name
        return payload


@dataclass(frozen=True)
class BackendRunResult:
    """One backend result inseparably paired with post-execution truth.

    Acquisition evidence may describe the provider/device selected before inference,
    but it cannot prove that an engine did not fall back during execution. Every
    heavy-backend `run()` therefore returns this envelope with fresh evidence that
    describes the execution which produced `result`.
    """

    result: object
    execution: ExecutionEvidence

    def __post_init__(self) -> None:
        if not isinstance(self.execution, ExecutionEvidence):
            raise BackendRuntimeError(
                "BackendRunResult.execution must be post-run ExecutionEvidence"
            )


@dataclass(frozen=True)
class BackendPreflight:
    """No-inference admission result for a heavy backend request."""

    identity: BackendIdentity
    health: BackendHealth
    capabilities: BackendCapabilities
    requested_provider: ProviderId
    requested_dtype: str | None = None

    def __post_init__(self) -> None:
        if self.requested_provider not in self.capabilities.providers:
            raise BackendRuntimeError(
                "requested_provider is not declared by backend capabilities"
            )
        requested_dtype = _optional_text(
            self.requested_dtype,
            field_name="requested_dtype",
        )
        if (
            requested_dtype is not None
            and self.capabilities.dtypes
            and requested_dtype not in self.capabilities.dtypes
        ):
            raise BackendRuntimeError("requested_dtype is not declared by backend capabilities")
        object.__setattr__(self, "requested_dtype", requested_dtype)

    def to_dict(self) -> dict[str, object]:
        return {
            "identity": self.identity.to_dict(),
            "health": self.health.to_dict(),
            "capabilities": self.capabilities.to_dict(),
            "requested_provider": self.requested_provider,
            "requested_dtype": self.requested_dtype,
        }


@runtime_checkable
class HeavyBackend(Protocol):
    """Minimal lifecycle seam shared by future repair/stem/restoration backends.

    The full residency/VRAM scheduler remains owned by #55. Implementations may use
    sidecars or in-process engines, but must expose actual execution evidence after
    acquire and again after every run; provider/dtype fallback must never be hidden.
    """

    @property
    def identity(self) -> BackendIdentity: ...

    @property
    def capabilities(self) -> BackendCapabilities: ...

    def health(self) -> BackendHealth: ...

    def preflight(
        self,
        *,
        requested_provider: ProviderId,
        requested_dtype: str | None = None,
    ) -> BackendPreflight: ...

    def acquire(self, preflight: BackendPreflight) -> ExecutionEvidence: ...

    def run(self, request: Mapping[str, Any]) -> BackendRunResult: ...

    def release(self) -> None: ...
