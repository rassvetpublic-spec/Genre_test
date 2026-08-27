from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_launcher_exposes_p0_gate_command() -> None:
    launcher = (ROOT / "Genre_test_START.cmd").read_text(encoding="utf-8")
    assert 'if /I "%~1"=="retrieval-p0-gate" goto WORKING_RETRIEVAL_P0_GATE' in launcher
    assert 'Genre_test_START.cmd retrieval-p0-gate "D:\\path\\track.wav"' in launcher
    assert 'scripts\\clamp3_p0_gate.py' in launcher


def test_p0_gate_requires_repeatability_and_shutdown_checks() -> None:
    gate = (ROOT / "scripts" / "clamp3_p0_gate.py").read_text(encoding="utf-8")
    assert "MAEST+AST CUDA probe" in gate
    assert '"direct_text_repeatable"' in gate
    assert '"direct_audio_repeatable"' in gate
    assert '"sidecar_text_repeatable"' in gate
    assert '"sidecar_audio_repeatable"' in gate
    assert '"sidecar_shutdown"' in gate
    assert '"sidecar_vram_released"' in gate


def test_sidecar_backend_exposes_process_id_for_evidence() -> None:
    backend = (
        ROOT / "src" / "genre_test" / "retrieval" / "clamp3_sidecar_backend.py"
    ).read_text(encoding="utf-8")
    assert "def process_id(self) -> int | None:" in backend


def test_sidecar_smoke_records_lifecycle_memory_evidence() -> None:
    smoke = (ROOT / "scripts" / "clamp3_sidecar_client_smoke.py").read_text(encoding="utf-8")
    assert '"rss_bytes_before_close"' in smoke
    assert '"gpu_memory_mib_before_close"' in smoke
    assert '"running_after_close"' in smoke
    assert '"gpu_memory_mib_after_close"' in smoke
