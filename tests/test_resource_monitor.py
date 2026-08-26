from __future__ import annotations

import pytest

from genre_test.resource_monitor import GpuResourceSnapshot, parse_nvidia_smi_csv


def test_parse_nvidia_smi_csv_full_row() -> None:
    snapshot = parse_nvidia_smi_csv(
        "0, NVIDIA GeForce RTX 5070 Ti, 73, 8192, 16303, 64, 211.5, 300.0\n"
    )

    assert snapshot == GpuResourceSnapshot(
        index=0,
        name="NVIDIA GeForce RTX 5070 Ti",
        utilization_percent=73.0,
        memory_used_mib=8192.0,
        memory_total_mib=16303.0,
        temperature_c=64.0,
        power_draw_w=211.5,
        power_limit_w=300.0,
    )
    assert snapshot.memory_free_mib == pytest.approx(8111.0)
    assert snapshot.memory_percent == pytest.approx(50.2484, rel=1e-4)


def test_parse_nvidia_smi_csv_accepts_optional_na_fields() -> None:
    snapshot = parse_nvidia_smi_csv(
        "0, NVIDIA GPU, 5, 512, 4096, N/A, [N/A], Not Supported\n"
    )

    assert snapshot is not None
    assert snapshot.temperature_c is None
    assert snapshot.power_draw_w is None
    assert snapshot.power_limit_w is None
    assert snapshot.memory_free_mib == 3584.0


def test_parse_nvidia_smi_csv_rejects_malformed_rows() -> None:
    assert parse_nvidia_smi_csv("") is None
    assert parse_nvidia_smi_csv("garbage") is None
    assert parse_nvidia_smi_csv("x, GPU, 10, 10, 20, 50, 100, 200") is None
