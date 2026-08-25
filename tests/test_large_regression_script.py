"""Regression contract for the large-corpus Windows runner."""


def test_large_regression_validates_before_persisting_batch() -> None:
    with open("scripts/run-large-regression.ps1", encoding="utf-8") as handle:
        script = handle.read()
    validation = "& $genre validate $Source"
    batch = "& $genre batch $Source"
    assert validation in script
    assert batch in script
    assert script.index(validation) < script.index(batch)
    assert "--filter old_versions" in script
    assert "Pre-batch stale/missing history recheck" in script
