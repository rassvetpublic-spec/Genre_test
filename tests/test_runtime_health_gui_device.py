from genre_test.runtime_health import RuntimeComponent, RuntimeHealth
from genre_test.runtime_health_gui import _cuda_usable, _device_options


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
    health = _health("WARN", "unavailable")

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
