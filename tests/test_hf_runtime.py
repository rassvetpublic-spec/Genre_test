from pathlib import Path

from genre_test import hf_runtime


def test_repo_local_cache_does_not_override_hf_home(monkeypatch, tmp_path: Path) -> None:
    cache_root = tmp_path / "repo-cache"
    monkeypatch.setattr(hf_runtime, "default_hf_home", lambda: cache_root)
    monkeypatch.setenv("HF_HOME", str(tmp_path / "user-hf-home"))
    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    monkeypatch.delenv("HF_XET_CACHE", raising=False)

    paths = hf_runtime.configure_hf_runtime()

    assert paths.cache_root == cache_root
    assert paths.hub_cache == cache_root / "hub"
    assert paths.xet_cache == cache_root / "xet"
    assert paths.hub_cache.is_dir()
    assert paths.xet_cache.is_dir()
    assert hf_runtime.os.environ["HF_HOME"] == str(tmp_path / "user-hf-home")
    assert hf_runtime.os.environ["HF_HUB_CACHE"] == str(cache_root / "hub")
    assert hf_runtime.os.environ["HF_XET_CACHE"] == str(cache_root / "xet")


def test_explicit_hf_cache_overrides_are_respected(monkeypatch, tmp_path: Path) -> None:
    cache_root = tmp_path / "repo-cache"
    explicit_hub = tmp_path / "custom-hub"
    explicit_xet = tmp_path / "custom-xet"
    monkeypatch.setattr(hf_runtime, "default_hf_home", lambda: cache_root)
    monkeypatch.setenv("HF_HUB_CACHE", str(explicit_hub))
    monkeypatch.setenv("HF_XET_CACHE", str(explicit_xet))

    hf_runtime.configure_hf_runtime()

    assert hf_runtime.os.environ["HF_HUB_CACHE"] == str(explicit_hub)
    assert hf_runtime.os.environ["HF_XET_CACHE"] == str(explicit_xet)
