import numpy as np
import soundfile as sf

from capture.recorder import find_capture_device, record
from .true_peak import true_peak_dbtp

ebu_tp_tests = [
    ("seq-3341-15-24bit.wav", -6.0, -0.4, 0.2),
    ("seq-3341-16-24bit.wav", -6.0, -0.4, 0.2),
    ("seq-3341-17-24bit.wav", -6.0, -0.4, 0.2),
    ("seq-3341-18-24bit.wav", -6.0, -0.4, 0.2),
    ("seq-3341-19-24bit.wav", 3.0, -0.4, 0.2),
    ("seq-3341-20-24bit.wav", 0.0, -0.4, 0.2),
    ("seq-3341-21-24bit.wav", 0.0, -0.4, 0.2),
    ("seq-3341-22-24bit.wav", 0.0, -0.4, 0.2),
    ("seq-3341-23-24bit.wav", 0.0, -0.4, 0.2),
]


def capture_signal(path, device, buffer_s=2.0):
    signal, sr = sf.read(path)
    if signal.ndim == 1:
        signal = signal[:, np.newaxis]
    duration_s = len(signal) / sr
    input(f"Start {path.name} then press Enter")
    audio = record(duration_s + buffer_s, sample_rate=sr, device=device)
    return audio


def validate_capture(test_dir, device=None, buffer_s=2.0):
    if device is None:
        device = find_capture_device("BlackHole 2ch")

    results = {}
    for filename, expected, tol_low, tol_high in ebu_tp_tests:
        path = test_dir / filename
        if not path.exists():
            results[filename] = {"error": f"file not found: {path}"}
            continue

        audio = capture_signal(path, device, buffer_s)
        measured = max(true_peak_dbtp(audio[:, ch]) for ch in range(audio.shape[1]))
        peak_sample = float(np.max(np.abs(audio)))
        error = measured - expected

        leading_silence = 0
        for i in range(len(audio)):
            if np.max(np.abs(audio[i])) > 1e-4:
                leading_silence = i
                break

        results[filename] = {
            "expected_dbtp": expected,
            "measured_dbtp": round(measured, 3),
            "error_db": round(error, 3),
            "peak_sample": round(peak_sample, 4),
            "leading_silence": leading_silence,
            "tol_low": tol_low,
            "tol_high": tol_high,
            "passed": tol_low <= error <= tol_high,
        }

    return results


def print_capture_report(test_dir, device=None, buffer_s=2.0):
    results = validate_capture(test_dir, device, buffer_s)
    all_passed = True
    n_run = 0
    for name, r in results.items():
        n_run += 1
        status = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_passed = False
        print(
            f"  {status}  {name}: "
            f"expected {r['expected_dbtp']:+.1f}, "
            f"got {r['measured_dbtp']:+.3f}, "
            f"error {r['error_db']:+.3f} dB "
            f"(allowed {r['tol_low']:+.1f} / {r['tol_high']:+.1f}), "
            f"peak {r['peak_sample']:.4f}, "
            f"lead {r['leading_silence']}"
        )

    if n_run == 0:
        print("\nNo tests ran.")
    elif all_passed:
        print("\nAll tests passed.")
    else:
        print("\nSome tests failed.")

if __name__ == "__main__":
    from pathlib import Path
    test_dir = Path(__file__).parent.parent / "ebu_tests"
    print_capture_report(test_dir)