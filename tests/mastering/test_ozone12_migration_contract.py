from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_backend_neutral_mastering_qc_has_single_active_owner() -> None:
    assert (ROOT / "src/genre_test/technical/mastering_metrics.py").is_file()
    assert (ROOT / "src/genre_test/technical/mastering_cli.py").is_file()

    forbidden_duplicates = (
        ROOT / "tools/mastering/ozone12/stage_toolkit/oz12_mastering_meter.py",
        ROOT / "tools/mastering/ozone12/stage_toolkit/oz12_analyze_stage.py",
        ROOT / "src/genre_test/mastering/ozone12/mastering_meter.py",
        ROOT / "src/genre_test/mastering/ozone12/analyze_stage.py",
    )
    assert all(not path.exists() for path in forbidden_duplicates)


def test_ozone_specific_xml_has_namespaced_active_owner() -> None:
    assert (ROOT / "src/genre_test/mastering/ozone12/xml.py").is_file()
    assert (ROOT / "src/genre_test/mastering/ozone12/xml_cli.py").is_file()

    reference_dir = ROOT / "tools/mastering/ozone12/xml_patch"
    assert (reference_dir / "ozone12_confirmed_ts_schema_v1_3.json").is_file()
    assert (reference_dir / "example_patch_streaming_safe.json").is_file()

    retired_duplicates = (
        reference_dir / "patch_ozone_stabilizer.py",
        reference_dir / "validate_elementchain.py",
        reference_dir / "validate_confirmed_ts_schema.py",
    )
    assert all(not path.exists() for path in retired_duplicates)


def test_migration_doc_records_deferred_render_boundary_and_blocked_semantics() -> None:
    text = (ROOT / "docs/mastering/ozone12/EXECUTABLE_MIGRATION.md").read_text(
        encoding="utf-8"
    )
    assert "CONSOLIDATED for the current executable-migration scope" in text
    assert "BLOCKED` must never be promoted to `PASS`" in text
    assert "REAPER/Ozone rendering" in text
    assert "intentionally deferred" in text
    assert "old autocheck is not copied" in text
