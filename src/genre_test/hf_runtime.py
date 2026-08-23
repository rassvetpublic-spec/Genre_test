from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .runtime_meta import default_hf_home


@dataclass(frozen=True)
class HfRuntimePaths:
    cache_root: Path
    hub_cache: Path
    xet_cache: Path


def configure_hf_runtime() -> HfRuntimePaths:
    """Keep model/Xet cache repo-local without moving the user's HF auth home/token."""
    cache_root = default_hf_home()
    hub_cache = cache_root / "hub"
    xet_cache = cache_root / "xet"
    hub_cache.mkdir(parents=True, exist_ok=True)
    xet_cache.mkdir(parents=True, exist_ok=True)

    # HF_HOME contains both cache configuration and the persisted login token.
    # Do not override it: doing so can hide the token created by `hf auth login`.
    os.environ.setdefault("HF_HUB_CACHE", str(hub_cache))
    os.environ.setdefault("HF_XET_CACHE", str(xet_cache))

    return HfRuntimePaths(
        cache_root=cache_root,
        hub_cache=hub_cache,
        xet_cache=xet_cache,
    )
