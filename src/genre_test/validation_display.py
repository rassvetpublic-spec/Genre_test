from __future__ import annotations

DRIFT_LEVELS = ("STABLE", "MINOR", "SIGNIFICANT", "CRITICAL")
DRIFT_LEGEND = (
    "DRIFT = изменение результата относительно history/другого режима; "
    "это не confidence классификатора."
)


def label_drift_output(text: str) -> str:
    output = text.replace("Overall severity:", "Overall drift severity:")
    for severity in DRIFT_LEVELS:
        output = output.replace(f"\n[{severity}] ", f"\n[DRIFT: {severity}] ")
    marker = "Overall drift severity:"
    if marker in output and DRIFT_LEGEND not in output:
        output = output.replace(marker, f"{DRIFT_LEGEND}\n\n{marker}", 1)
    return output


def install_validation_display_labels() -> None:
    from . import validation, validation_gui

    original = validation.format_validation_session
    if getattr(original, "_genre_test_drift_labels", False):
        validation_gui.format_validation_session = original
        return

    def wrapped(result):
        return label_drift_output(original(result))

    wrapped._genre_test_drift_labels = True  # type: ignore[attr-defined]
    validation.format_validation_session = wrapped
    validation_gui.format_validation_session = wrapped
