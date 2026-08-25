from genre_test.validation_display import DRIFT_LEGEND, label_drift_output


def test_validation_output_labels_stability_as_drift() -> None:
    source = (
        "Overall severity:\n"
        "STABLE: 1\n"
        "MINOR: 0\n"
        "\n[STABLE] example.mp3\n"
        "  fast=Reggaeton\n"
        "\n[SIGNIFICANT] another.mp3\n"
        "  auto=Drum n Bass"
    )

    output = label_drift_output(source)

    assert "Overall drift severity:" in output
    assert DRIFT_LEGEND in output
    assert "[DRIFT: STABLE] example.mp3" in output
    assert "[DRIFT: SIGNIFICANT] another.mp3" in output
    assert "\n[STABLE] example.mp3" not in output
