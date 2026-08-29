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
    assert "COMPLETE for the approved #101 executable-migration scope" in text
    assert "BLOCKED` must never be promoted to `PASS`" in text
    assert "REAPER/Ozone rendering" in text
    assert "intentionally deferred" in text
    assert "old autocheck is not copied" in text
    assert "status: RETIRED / NOT MIGRATED" in text
    assert "must not revive or" in text
    assert "copy the retired standalone P0/autocheck architecture" in text


def test_operational_mastering_docs_use_shared_qc_cli() -> None:
    docs_root = ROOT / "docs/mastering/ozone12"
    operational_text = "\n".join(
        path.read_text(encoding="utf-8") for path in docs_root.rglob("*.md")
    )

    assert "python tools/stage_toolkit/oz12_mastering_meter.py" not in operational_text
    assert "--decoded-peak-target-dbtp" not in operational_text
    assert "--keep-codec-files" not in operational_text

    meter_doc = (
        docs_root / "core/15_AUTOMATIC_MASTERING_METER.md"
    ).read_text(encoding="utf-8")
    checklist = (
        docs_root / "checklists/FINAL_APPROVAL_CHECKLIST.md"
    ).read_text(encoding="utf-8")
    assert "genre-test-mastering-qc" in meter_doc
    assert "genre-test-mastering-qc" in checklist


def test_supercombine_marks_ozone_executable_migration_complete() -> None:
    todo = (ROOT / "docs/SUPERCOMBINE_TODO.md").read_text(encoding="utf-8")

    assert (
        "- [x] migrate Ozone executable toolkit by ownership and promote "
        "backend-neutral mastering metrics (#101" in todo
    )
    assert "- [x] finish Ozone executable XML/preset toolkit migration (#101" in todo
