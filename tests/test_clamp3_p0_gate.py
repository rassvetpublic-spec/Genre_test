from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_launcher_exposes_p0_gate_command() -> None:
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    assert 'if /I "%~1"=="retrieval-p0-gate" goto WORKING_RETRIEVAL_P0_GATE' in launcher
    assert 'Genre_test_START.cmd retrieval-p0-gate "D:\\path\\track.wav"' in launcher
    assert 'scripts\\clamp3_p0_gate.py' in launcher


def test_launcher_does_not_pass_trailing_slash_repo_root_to_python() -> None:
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    gate_line = next(
        line
        for line in launcher.splitlines()
        if 'clamp3_p0_gate.py" --audio' in line
    )
    assert '--repo-root "%ROOT%"' not in gate_line
    assert '--audio "%RETRIEVAL_AUDIO%"' in gate_line


def test_p0_gate_requires_real_core_cuda_cross_path_and_shutdown_checks() -> None:
    gate = (ROOT / "scripts" / "clamp3_p0_gate.py").read_text(encoding="utf-8")
    assert "MAEST+AST CUDA probe" in gate
    assert '"maest_cuda"' in gate
    assert '"maest_windows_positive"' in gate
    assert '"ast_present"' in gate
    assert '"ast_status_ok"' in gate
    assert '"ast_cuda"' in gate
    assert '"ast_windows_positive"' in gate
    assert '"flat_state_layout"' in gate
    assert '"direct_text_repeatable"' in gate
    assert '"direct_audio_repeatable"' in gate
    assert '"sidecar_text_repeatable"' in gate
    assert '"sidecar_audio_repeatable"' in gate
    assert '"cross_text_head_match"' in gate
    assert '"cross_audio_head_match"' in gate
    assert '"cross_text_audio_cosine_match"' in gate
    assert '"sidecar_shutdown"' in gate
    assert '"sidecar_vram_released"' in gate


def test_clamp_runtime_uses_flat_state_layout_and_common_log_folder() -> None:
    gate = (ROOT / "scripts" / "clamp3_p0_gate.py").read_text(encoding="utf-8")
    setup = (ROOT / "scripts" / "setup_clamp3_runtime.ps1").read_text(encoding="utf-8")
    smoke = (ROOT / "scripts" / "clamp3_runtime_smoke.py").read_text(encoding="utf-8")
    local_gate = (ROOT / "scripts" / "run_local_retrieval_p0_tests.ps1").read_text(
        encoding="utf-8"
    )
    inventory = (ROOT / "scripts" / "clamp3_windows_inventory.ps1").read_text(
        encoding="utf-8"
    )

    assert 'state_root = repo_root / ".genre_test"' in gate
    assert '/ "runtimes"\n        / "clamp3"' in gate
    assert 'log_dir = state_root / "logs"' in gate

    assert '$StateDir = Join-Path $RepoRoot ".genre_test"' in setup
    assert '$RuntimeDir = Join-Path $StateDir "runtimes\\clamp3"' in setup
    assert '$ModelsDir = Join-Path $StateDir "models"' in setup
    assert '$UpstreamDir = Join-Path $StateDir "upstream\\clamp3"' in setup
    assert '$LogDir = Join-Path $StateDir "logs"' in setup
    assert '$RetrievalDb = Join-Path $StateDir "retrieval.sqlite3"' in setup
    assert '$LegacyRoot = Join-Path $StateDir "retrieval"' in setup
    assert 'Migrate-LegacyLayout' in setup
    assert 'Cannot migrate ${Label}:' in setup
    assert 'Cannot migrate $Label:' not in setup
    assert 'print(sys.executable)' not in setup
    assert '$RuntimeRoot =' not in setup
    assert '$EvidenceDir' not in setup

    assert 'return REPO_ROOT / ".genre_test"' in smoke
    assert 'return REPO_ROOT / ".genre_test" / "retrieval"' not in smoke

    assert "$LogDir = Join-Path $RepoRoot '.genre_test\\logs'" in local_gate
    assert "results\\retrieval_p0_local" not in local_gate
    assert 'Join-Path $repoRoot ".genre_test\\logs"' in inventory
    assert 'results\\clamp3_spike' not in inventory


def test_sidecar_backend_defaults_to_flat_state_layout() -> None:
    backend = (
        ROOT / "src" / "genre_test" / "retrieval" / "clamp3_sidecar_backend.py"
    ).read_text(encoding="utf-8")
    assert 'state_root = repo_root / ".genre_test"' in backend
    assert '/ "runtimes"\n                / "clamp3"' in backend
    assert 'upstream_root=state_root / "upstream" / "clamp3"' in backend
    assert 'runtime_root=state_root' in backend
    assert 'runtime_root = repo_root / ".genre_test" / "retrieval"' not in backend


def test_sidecar_backend_forces_utf8_child_and_exposes_process_id() -> None:
    backend = (
        ROOT / "src" / "genre_test" / "retrieval" / "clamp3_sidecar_backend.py"
    ).read_text(encoding="utf-8")
    assert '"-X",\n            "utf8",' in backend
    assert 'encoding="utf-8"' in backend
    assert "def process_id(self) -> int | None:" in backend


def test_p0_subprocesses_force_utf8_capture() -> None:
    gate = (ROOT / "scripts" / "clamp3_p0_gate.py").read_text(encoding="utf-8")
    assert 'env["PYTHONUTF8"] = "1"' in gate
    assert 'env["PYTHONIOENCODING"] = "utf-8"' in gate


def test_sidecar_smoke_records_lifecycle_memory_evidence() -> None:
    smoke = (ROOT / "scripts" / "clamp3_sidecar_client_smoke.py").read_text(encoding="utf-8")
    assert '"rss_bytes_before_close"' in smoke
    assert '"gpu_memory_mib_before_close"' in smoke
    assert '"running_after_close"' in smoke
    assert '"gpu_memory_mib_after_close"' in smoke
