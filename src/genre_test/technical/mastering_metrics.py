"""Backend-neutral source/candidate mastering comparison metrics.

Migrated from the project-owned OZONE12_MASTERING_LAB mastering meter so Ozone,
repair, A/B/X and future backends share one versioned implementation.
"""
from __future__ import annotations

import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.integrate import trapezoid
from scipy.io import wavfile
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, correlate, correlation_lags, find_peaks, resample_poly, sosfilt, welch

ALGORITHM_ID = "genre_test.technical.mastering_metrics:v1"
STATUS_RANK = {"NOT_APPLICABLE": 0, "MEASURED": 0, "PASS": 0, "WARN": 1, "FAIL": 2}
CODEC_SPECS: dict[str, dict[str, Any]] = {
    "mp3_320": {"extension": ".mp3", "label": "MP3 320 kbps", "encode_args": ["-c:a", "libmp3lame", "-b:a", "320k"]},
    "aac_256": {"extension": ".m4a", "label": "AAC 256 kbps", "encode_args": ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart"]},
    "aac_192": {"extension": ".m4a", "label": "AAC 192 kbps stress test", "encode_args": ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]},
}
MONO_BANDS = [
    ("low_20_120", 20.0, 120.0),
    ("low_mid_120_500", 120.0, 500.0),
    ("presence_500_4000", 500.0, 4000.0),
    ("high_4000_18000", 4000.0, 18000.0),
]


def _channels(audio: np.ndarray) -> np.ndarray:
    data = np.asarray(audio, dtype=np.float32)
    if data.ndim == 1:
        data = data[:, None]
    if data.ndim != 2 or not data.shape[1] or not np.all(np.isfinite(data)):
        raise ValueError("Audio must be finite samples x channels")
    return data


def _mono(audio: np.ndarray) -> np.ndarray:
    data = _channels(audio)
    return data[:, 0] if data.shape[1] == 1 else 0.5 * (data[:, 0] + data[:, 1])


def _db_amplitude(value: float) -> float:
    return -300.0 if value <= 0.0 or not np.isfinite(value) else float(20.0 * math.log10(value))


def _rms(audio: np.ndarray) -> float:
    data = np.asarray(audio, dtype=np.float64)
    return 0.0 if not data.size else float(np.sqrt(np.mean(data * data)))


def load_wav(path: Path) -> tuple[int, np.ndarray, str]:
    try:
        sample_rate, data = wavfile.read(str(path), mmap=True)
        backend = "scipy.io.wavfile:mmap"
    except (ValueError, OSError):
        sample_rate, data = wavfile.read(str(path), mmap=False)
        backend = "scipy.io.wavfile"
    data = np.asarray(data)
    if np.issubdtype(data.dtype, np.integer):
        info = np.iinfo(data.dtype)
        data = data.astype(np.float32) / float(max(abs(info.min), info.max))
    else:
        data = data.astype(np.float32, copy=False)
    return int(sample_rate), _channels(data), backend


def resample_audio(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    data = _channels(audio)
    if source_rate == target_rate:
        return data
    divisor = math.gcd(source_rate, target_rate)
    return np.asarray(resample_poly(data, target_rate // divisor, source_rate // divisor, axis=0), dtype=np.float32)


def estimate_alignment(reference: np.ndarray, candidate: np.ndarray, sample_rate: int, max_lag_seconds: float = 2.0) -> dict[str, Any]:
    analysis_rate = 1000
    def envelope(audio: np.ndarray) -> np.ndarray:
        x = np.abs(_mono(audio)).astype(np.float64)
        divisor = math.gcd(sample_rate, analysis_rate)
        x = resample_poly(x, analysis_rate // divisor, sample_rate // divisor)
        x = uniform_filter1d(x, size=max(1, int(0.020 * analysis_rate)), mode="nearest")
        x -= np.mean(x)
        scale = float(np.std(x))
        return np.asarray(x / scale if scale > 0.0 else x, dtype=np.float32)
    ref, cand = envelope(reference), envelope(candidate)
    corr = correlate(cand, ref, mode="full", method="fft")
    lags = correlation_lags(cand.size, ref.size, mode="full")
    valid = np.abs(lags) <= int(round(max_lag_seconds * analysis_rate))
    if not np.any(valid):
        lag_ds, confidence = 0, 0.0
    else:
        vc, vl = corr[valid], lags[valid]
        index = int(np.argmax(vc))
        lag_ds = int(vl[index])
        denominator = float(np.linalg.norm(ref) * np.linalg.norm(cand))
        confidence = float(vc[index] / denominator) if denominator > 0.0 else 0.0
    lag_samples = int(round(lag_ds * sample_rate / analysis_rate))
    return {"candidate_lag_samples": lag_samples, "candidate_lag_ms": 1000.0 * lag_samples / sample_rate, "envelope_correlation": confidence}


def align_pair(reference: np.ndarray, candidate: np.ndarray, lag_samples: int) -> tuple[np.ndarray, np.ndarray]:
    reference, candidate = _channels(reference), _channels(candidate)
    ref_start, cand_start = (0, lag_samples) if lag_samples >= 0 else (-lag_samples, 0)
    count = min(reference.shape[0] - ref_start, candidate.shape[0] - cand_start)
    if count <= 0:
        raise ValueError("No overlapping audio after alignment")
    channels = min(reference.shape[1], candidate.shape[1])
    return reference[ref_start:ref_start + count, :channels], candidate[cand_start:cand_start + count, :channels]


def level_match(reference: np.ndarray, candidate: np.ndarray, sample_rate: int) -> tuple[np.ndarray, float]:
    def active_rms(audio: np.ndarray) -> float:
        x = _mono(audio).astype(np.float64)
        frame, hop = max(1, int(0.400 * sample_rate)), max(1, int(0.200 * sample_rate))
        values = [_rms(x[i:i + frame]) for i in range(0, max(1, x.size - frame + 1), hop)]
        arr = np.asarray(values or [_rms(x)])
        floor = float(np.max(arr)) * 10.0 ** (-30.0 / 20.0)
        active = arr[arr >= floor]
        return float(np.sqrt(np.mean(active * active))) if active.size else _rms(x)
    ref_rms, cand_rms = active_rms(reference), active_rms(candidate)
    if ref_rms <= 0.0 or cand_rms <= 0.0:
        return _channels(candidate), 0.0
    gain = ref_rms / cand_rms
    return np.asarray(_channels(candidate) * gain, dtype=np.float32), _db_amplitude(gain)


def detect_transient_events(reference: np.ndarray, sample_rate: int, max_events: int = 64) -> tuple[list[int], dict[str, Any]]:
    analysis_rate = min(4000, sample_rate)
    x = _mono(reference).astype(np.float64)
    high = min(12000.0, sample_rate * 0.45)
    if high <= 40.0:
        raise ValueError("Sample rate too low for transient analysis")
    filtered = sosfilt(butter(3, [35.0, high], btype="bandpass", fs=sample_rate, output="sos"), x)
    divisor = math.gcd(sample_rate, analysis_rate)
    y = resample_poly(filtered, analysis_rate // divisor, sample_rate // divisor)
    energy = y * y
    fast = np.sqrt(np.maximum(uniform_filter1d(energy, size=max(1, int(0.008 * analysis_rate))), 1e-18))
    slow = np.sqrt(np.maximum(uniform_filter1d(energy, size=max(2, int(0.080 * analysis_rate))), 1e-18))
    fast_db = 20.0 * np.log10(fast + 1e-12)
    ratio = 20.0 * np.log10((fast + 1e-12) / (slow + 1e-12))
    rise_n = max(1, int(0.016 * analysis_rate))
    earlier = np.roll(fast_db, rise_n)
    earlier[:rise_n] = fast_db[:rise_n]
    score = ratio + 0.35 * np.maximum(0.0, fast_db - earlier)
    finite = np.isfinite(score) & np.isfinite(fast_db)
    if not np.any(finite):
        return [], {"events_detected": 0, "events_used": 0, "algorithm_id": ALGORITHM_ID}
    floor = max(float(np.percentile(fast_db[finite], 55.0)), float(np.max(fast_db[finite])) - 38.0)
    height = max(1.0, float(np.percentile(score[finite], 70.0)))
    peaks, _ = find_peaks(score, distance=max(1, int(0.085 * analysis_rate)), height=height, prominence=0.75)
    peaks = peaks[fast_db[peaks] >= floor]
    margin = int(0.180 * analysis_rate)
    peaks = peaks[(peaks >= margin) & (peaks < score.size - margin)]
    ranked = sorted(peaks.tolist(), key=lambda i: (float(score[i]), float(fast_db[i])), reverse=True)[:max_events]
    selected = sorted(ranked)
    events = [max(0, int(round(i * sample_rate / analysis_rate - 0.004 * sample_rate))) for i in selected]
    return events, {"events_detected": int(peaks.size), "events_used": len(events), "analysis_rate_hz": analysis_rate, "detection_band_hz": [35.0, high], "selected_detector_scores_db": [float(score[i]) for i in selected], "proxy_note": "Strong broad-band full-master onsets; not drum-stem separation.", "algorithm_id": ALGORITHM_ID}


def measure_transient_retention(reference: np.ndarray, candidate: np.ndarray, sample_rate: int, events: Sequence[int], detector: dict[str, Any] | None = None, warn_db: float = -0.75, fail_db: float = -1.5) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    reference, candidate, detector = _channels(reference), _channels(candidate), dict(detector or {})
    rows, rms_deltas, contrast_deltas = [], [], []
    for number, event in enumerate(events, 1):
        a0, a1 = event - int(0.005 * sample_rate), event + int(0.035 * sample_rate)
        s0, s1 = event + int(0.045 * sample_rate), event + int(0.145 * sample_rate)
        if a0 < 0 or s1 > reference.shape[0]:
            continue
        rp, cp = _db_amplitude(float(np.max(np.abs(reference[a0:a1])))), _db_amplitude(float(np.max(np.abs(candidate[a0:a1]))))
        rr, cr = _db_amplitude(_rms(reference[a0:a1])), _db_amplitude(_rms(candidate[a0:a1]))
        rs, cs = _db_amplitude(_rms(reference[s0:s1])), _db_amplitude(_rms(candidate[s0:s1]))
        rms_delta, contrast_delta = cr - rr, (cp - cs) - (rp - rs)
        rms_deltas.append(rms_delta)
        contrast_deltas.append(contrast_delta)
        rows.append({"event": number, "time_sec": event / sample_rate, "attack_peak_delta_db": cp - rp, "attack_rms_delta_db": rms_delta, "attack_to_sustain_delta_db": contrast_delta})
    median_rms = float(np.median(rms_deltas)) if rms_deltas else None
    median_contrast = float(np.median(contrast_deltas)) if contrast_deltas else None
    guard = min(v for v in (median_rms, median_contrast) if v is not None) if rows else None
    status = "FAIL" if guard is None or guard < fail_db else "WARN" if guard < warn_db else "PASS"
    return {"status": status, "events_detected": detector.get("events_detected", len(events)), "events_used": len(rows), "attack_guard_delta_db": guard, "median_attack_rms_delta_db": median_rms, "median_attack_to_sustain_delta_db": median_contrast, "warning_threshold_db": warn_db, "fail_threshold_db": fail_db, "windows_ms": {"attack": [-5, 35], "sustain": [45, 145]}, "interpretation": "Negative delta means less event attack after active-RMS matching.", "algorithm_id": ALGORITHM_ID}, rows


def _mono_retention(left_power: float, right_power: float, mid_power: float) -> float | None:
    stereo = 0.5 * (left_power + right_power)
    return None if stereo <= 0.0 else 10.0 * math.log10(max(mid_power, 1e-30) / stereo)


def overall_mono_retention(audio: np.ndarray) -> float | None:
    data = _channels(audio)
    if data.shape[1] < 2:
        return None
    left, right = data[:, 0].astype(np.float64), data[:, 1].astype(np.float64)
    mid = 0.5 * (left + right)
    return _mono_retention(float(np.mean(left * left)), float(np.mean(right * right)), float(np.mean(mid * mid)))


def correlation_lr(audio: np.ndarray) -> float | None:
    data = _channels(audio)
    if data.shape[1] < 2:
        return None
    left, right = data[:, 0].astype(np.float64), data[:, 1].astype(np.float64)
    denominator = float(np.sqrt(np.sum(left * left) * np.sum(right * right)))
    return float(np.sum(left * right) / denominator) if denominator > 0.0 else None


def _band_retention(audio: np.ndarray, sample_rate: int) -> dict[str, float | None]:
    data = _channels(audio)
    if data.shape[1] < 2:
        return {}
    left, right = data[:, 0].astype(np.float64), data[:, 1].astype(np.float64)
    mid = 0.5 * (left + right)
    nperseg = min(32768, max(4096, int(sample_rate * 0.68)))
    f, lp = welch(left, fs=sample_rate, nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
    _, rp = welch(right, fs=sample_rate, nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
    _, mp = welch(mid, fs=sample_rate, nperseg=nperseg, noverlap=nperseg // 2, detrend=False)
    out = {}
    for name, low, high in MONO_BANDS:
        mask = (f >= low) & (f < min(high, sample_rate * 0.5))
        if np.any(mask):
            out[name] = _mono_retention(float(trapezoid(lp[mask], f[mask])), float(trapezoid(rp[mask], f[mask])), float(trapezoid(mp[mask], f[mask])))
    return out


def measure_mono_loss(reference: np.ndarray, candidate: np.ndarray, sample_rate: int, event_samples: Sequence[int] = (), warn_db: float = -0.5, fail_db: float = -1.5) -> dict[str, Any]:
    reference, candidate = _channels(reference), _channels(candidate)
    if reference.shape[1] < 2 or candidate.shape[1] < 2:
        return {"status": "NOT_APPLICABLE", "algorithm_id": ALGORITHM_ID}
    ref_overall, cand_overall = overall_mono_retention(reference), overall_mono_retention(candidate)
    overall_delta = None if ref_overall is None or cand_overall is None else cand_overall - ref_overall
    ref_bands, cand_bands = _band_retention(reference, sample_rate), _band_retention(candidate, sample_rate)
    bands, deltas = {}, []
    if overall_delta is not None:
        deltas.append(("overall", overall_delta))
    for name, low, high in MONO_BANDS:
        if name in ref_bands and name in cand_bands and ref_bands[name] is not None and cand_bands[name] is not None:
            delta = float(cand_bands[name] - ref_bands[name])
            deltas.append((name, delta))
            bands[name] = {"low_hz": low, "high_hz": min(high, sample_rate * 0.5), "reference_mono_retention_db": ref_bands[name], "candidate_mono_retention_db": cand_bands[name], "candidate_minus_reference_db": delta}
    worst_scope, worst = min(deltas, key=lambda x: x[1]) if deltas else (None, None)
    status = "NOT_APPLICABLE" if worst is None else "FAIL" if worst < fail_db else "WARN" if worst < warn_db else "PASS"
    return {"status": status, "definition": "10*log10(power((L+R)/2) / mean(power(L), power(R)))", "overall": {"reference_mono_retention_db": ref_overall, "candidate_mono_retention_db": cand_overall, "candidate_minus_reference_db": overall_delta, "reference_lr_correlation": correlation_lr(reference), "candidate_lr_correlation": correlation_lr(candidate)}, "bands": bands, "events_considered": len(event_samples), "worst_scope": worst_scope, "worst_candidate_minus_reference_db": worst, "warning_threshold_db": warn_db, "fail_threshold_db": fail_db, "interpretation": "Negative candidate-minus-reference means extra loss on mono collapse.", "algorithm_id": ALGORITHM_ID}


def _run(command: Sequence[str], timeout: int = 600) -> tuple[str, str]:
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
    if process.returncode:
        raise RuntimeError((process.stderr or process.stdout).strip()[-2000:])
    return process.stdout, process.stderr


def _true_peak(path: Path) -> dict[str, float | None]:
    _, err = _run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"])
    peaks = re.findall(r"Peak:\s*([-+]?\d+(?:\.\d+)?)\s*dBFS", err)
    loudness = re.findall(r"I:\s*([-+]?\d+(?:\.\d+)?)\s*LUFS", err)
    return {"true_peak_dbtp": float(peaks[-1]) if peaks else None, "integrated_lufs": float(loudness[-1]) if loudness else None}


def measure_codecs(candidate_path: Path, codecs: Sequence[str], *, target_dbtp: float | None = None, safety_margin_db: float = 0.1) -> dict[str, Any]:
    if not codecs:
        return {"status": "NOT_APPLICABLE", "results": [], "algorithm_id": ALGORITHM_ID}
    unknown = sorted(set(codecs) - set(CODEC_SPECS))
    if unknown:
        raise ValueError(f"Unknown codec profiles: {', '.join(unknown)}")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for codec preview")
    rows = []
    with tempfile.TemporaryDirectory(prefix="genre_test_codec_") as tmp:
        work = Path(tmp)
        for name in codecs:
            spec = CODEC_SPECS[name]
            encoded = work / f"candidate.{name}{spec['extension']}"
            decoded = work / f"candidate.{name}.wav"
            _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(candidate_path), "-map_metadata", "-1", *spec["encode_args"], str(encoded)])
            _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(encoded), "-c:a", "pcm_f32le", str(decoded)])
            stats = _true_peak(decoded)
            peak = stats["true_peak_dbtp"]
            trim = None if target_dbtp is None or peak is None else max(0.0, peak - target_dbtp + safety_margin_db)
            status = "MEASURED" if target_dbtp is None and peak is not None else "FAIL" if peak is None or (trim or 0.0) > 0.0 else "PASS"
            rows.append({"codec": name, "label": spec["label"], "status": status, "decoded_true_peak_dbtp": peak, "decoded_integrated_lufs": stats["integrated_lufs"], "target_dbtp": target_dbtp, "recommended_source_trim_db": trim, "algorithm_id": ALGORITHM_ID})
    return {"status": max((r["status"] for r in rows), key=lambda s: STATUS_RANK.get(s, 0)), "results": rows, "algorithm_id": ALGORITHM_ID}


def compare_mastering_arrays(reference: np.ndarray, candidate: np.ndarray, sample_rate: int, *, max_lag_seconds: float = 2.0, max_events: int = 64, attack_warn_db: float = -0.75, attack_fail_db: float = -1.5, mono_warn_db: float = -0.5, mono_fail_db: float = -1.5) -> dict[str, Any]:
    alignment = estimate_alignment(reference, candidate, sample_rate, max_lag_seconds)
    ref, cand = align_pair(reference, candidate, int(alignment["candidate_lag_samples"]))
    cand, gain_db = level_match(ref, cand, sample_rate)
    events, detector = detect_transient_events(ref, sample_rate, max_events)
    transient, event_rows = measure_transient_retention(ref, cand, sample_rate, events, detector, attack_warn_db, attack_fail_db)
    mono_loss = measure_mono_loss(ref, cand, sample_rate, events, mono_warn_db, mono_fail_db)
    overall = max((transient["status"], mono_loss["status"]), key=lambda s: STATUS_RANK.get(s, 0))
    return {"schema": "MasteringComparisonMetricsV1", "algorithm_id": ALGORITHM_ID, "sample_rate": sample_rate, "alignment": alignment, "level_match_gain_db": gain_db, "transient_retention": transient, "transient_events": event_rows, "mono_loss": mono_loss, "overall_status": overall}


def compare_mastering_files(reference_path: Path, candidate_path: Path, *, codecs: Sequence[str] = (), target_dbtp: float | None = None, codec_safety_margin_db: float = 0.1, **kwargs: Any) -> dict[str, Any]:
    ref_rate, reference, ref_backend = load_wav(reference_path)
    cand_rate, candidate, cand_backend = load_wav(candidate_path)
    if cand_rate != ref_rate:
        candidate = resample_audio(candidate, cand_rate, ref_rate)
    result = compare_mastering_arrays(reference, candidate, ref_rate, **kwargs)
    result["reference"] = {"path": str(reference_path), "sample_rate": ref_rate, "channels": int(reference.shape[1]), "load_backend": ref_backend}
    result["candidate"] = {"path": str(candidate_path), "source_sample_rate": cand_rate, "analysis_sample_rate": ref_rate, "channels": int(candidate.shape[1]), "load_backend": cand_backend}
    codec = measure_codecs(candidate_path, codecs, target_dbtp=target_dbtp, safety_margin_db=codec_safety_margin_db)
    result["codec_preview"] = codec
    result["overall_status"] = max((result["overall_status"], codec["status"]), key=lambda s: STATUS_RANK.get(s, 0))
    return result
