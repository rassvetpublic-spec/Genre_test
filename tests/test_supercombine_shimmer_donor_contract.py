from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT / "docs" / "SHIMMER_EXTERNAL_REFERENCE.md"
ARCHITECTURE = ROOT / "docs" / "SUPERCOMBINE_UI_ARCHITECTURE.md"
TODO = ROOT / "docs" / "SUPERCOMBINE_SHIMMER_DONOR_TODO.md"
COLD_START = ROOT / "docs" / "REPOSITORY_COLD_START.md"

PUBLIC_DONOR_SHA = "ff8344ae1a77bd7eb5be46b55c83813e923d3d2c"
OZONE_CORE_SHA256 = "9f165e9194797e1e6ba51d1d248dfb6d2a7f734df33c1265c70ddf0826117cc7"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_shimmer_is_authorized_donor_not_parallel_product() -> None:
    donor = _read(DONOR)

    assert "AUTHORIZED DONOR / UI PROTOTYPE / EXPERIMENT SOURCE" in donor
    assert PUBLIC_DONOR_SHA in donor
    assert "Shimmer may therefore contribute **code, UI structure and workflow implementations**" in donor
    assert "It is not imported as a second product or a second source of runtime truth." in donor
    assert "Do not keep a parallel Shimmer production server" in donor


def test_supercombine_keeps_genre_test_as_single_product_truth() -> None:
    architecture = _read(ARCHITECTURE)

    assert "`Genre_test` is the product." in architecture
    assert "Project | Analyze | Catalog | Search | Repair | Stems | Master | Compare | Delivery | Settings" in architecture
    assert "Genre_test workstation web UI" in architecture
    assert "Local workstation API / job facade" in architecture
    assert "Existing `Genre_test` contracts take precedence over donor implementation choices." in _read(DONOR)


def test_ozone_core_is_reused_without_duplicate_import() -> None:
    donor = _read(DONOR)
    architecture = _read(ARCHITECTURE)

    for text in (donor, architecture):
        assert OZONE_CORE_SHA256 in text

    assert "do not add another Universal Core copy" in architecture
    assert "src/genre_test/mastering/ozone12/" in architecture
    assert "The historical `OZONE12_MASTERING_LAB` is not revived." in architecture


def test_detector_evasion_is_not_a_production_objective() -> None:
    donor = _read(DONOR)
    architecture = _read(ARCHITECTURE)
    todo = _read(TODO)

    assert "That objective is outside Genre_test" in donor
    assert "detector-score optimization loops" in architecture
    assert "reject detector-score minimization" in todo
    assert "audible defect" in donor
    assert "BYPASS" in architecture


def test_migration_backlog_covers_complete_workstation_path() -> None:
    todo = _read(TODO)

    for stage in (
        "P1 — workstation shell",
        "P2 — current Genre_test capabilities in workstation",
        "P3 — common transport, preview and comparison",
        "P4 — resource HUD",
        "P5 — Repair UI (#50)",
        "P6 — Stems / Vocal (#51 / #52)",
        "P7 — Mastering workstation (#v0.7)",
        "P8 — Project / Vault / Delivery",
    ):
        assert stage in todo


def test_supercombine_workstation_is_discoverable_from_cold_start() -> None:
    cold_start = _read(COLD_START)

    assert "docs/SUPERCOMBINE_UI_ARCHITECTURE.md" in cold_start
    assert "docs/SUPERCOMBINE_SHIMMER_DONOR_TODO.md" in cold_start
    assert "P3 common #54-compatible A/B/X/Delta transport" in cold_start
    assert cold_start.index("P3 common #54-compatible A/B/X/Delta transport") < cold_start.index(
        "P5 Repair UI"
    )
    assert cold_start.index("P5 Repair UI") < cold_start.index("P7 Mastering UI")
