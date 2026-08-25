from genre_test.runtime_health import RuntimeComponent, RuntimeHealth
from genre_test.runtime_health_gui import (
    _bounded_expert_parameters,
    _cuda_usable,
    _device_options,
    _is_device_selector_values,
)


def _health(cuda_status: str, cuda_value: str) -> RuntimeHealth:
    return RuntimeHealth(
        (
            RuntimeComponent(
                name="CUDA",
                status=cuda_status,
                value=cuda_value,
                category="Acceleration",
            ),
        )
    )


def test_cpu_only_gui_hides_cuda_device() -> None:
    health = _health("N/A", "not applicable")

    assert _cuda_usable(health) is False
    assert _device_options(health) == ("auto", "cpu")


def test_compatible_cuda_gui_exposes_cuda_device() -> None:
    health = _health("OK", "13.0")

    assert _cuda_usable(health) is True
    assert _device_options(health) == ("auto", "cuda", "cpu")


def test_failed_cuda_runtime_is_not_selectable() -> None:
    health = _health("FAIL", "12.8")

    assert _cuda_usable(health) is False
    assert _device_options(health) == ("auto", "cpu")


def test_device_selector_detection_covers_analysis_and_validation_states() -> None:
    assert _is_device_selector_values(("auto", "cuda", "cpu")) is True
    assert _is_device_selector_values(("auto", "cpu")) is True
    assert _is_device_selector_values(("Auto", "Fast", "Accurate")) is False


def test_expert_two_windows_remains_valid_but_top_k_two_is_raised_to_three() -> None:
    assert _bounded_expert_parameters(2, 2) == (2, 3)


def test_expert_parameter_bounds_are_enforced() -> None:
    assert _bounded_expert_parameters(0, 99) == (1, 50)
