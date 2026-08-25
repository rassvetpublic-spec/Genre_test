from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_large_regression_validates_before_persisting_batch() -> None:
    script = (ROOT / "scripts" / "run-large-regression.ps1").read_text(encoding="utf-8")
    validation = "& $genre validate $Source"
    batch = "& $genre batch $Source"
    assert validation in script
    assert batch in script
    assert script.index(validation) < script.index(batch)
    assert "--filter old_versions" in script
    assert "Pre-batch stale/missing history recheck" in script
