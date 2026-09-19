import soundfile as sf

from .lufs import measure_lufs

ebu_loudness_tests = [
    ("seq-3341-1-16bit.wav", -23.0, 0.1),
    ("seq-3341-2-16bit.wav", -33.0, 0.1),
    ("seq-3341-3-16bit-v02.wav", -23.0, 0.1),
    ("seq-3341-4-16bit-v02.wav", -23.0, 0.1),
    ("seq-3341-5-16bit-v02.wav", -23.0, 0.1),
]


def validate(test_dir):
    results = {}
    for filename, expected, tol in ebu_loudness_tests:
        path = test_dir / filename
        if not path.exists():
            results[filename] = {"error": f"file not found: {path}"}
            continue

        audio, sr = sf.read(path)
        measured = measure_lufs(audio, sr)
        error = measured - expected

        results[filename] = {
            "expected_lufs": expected,
            "measured_lufs": measured,
            "error_lu": round(error, 3),
            "tol": tol,
            "passed": abs(error) <= tol,
        }

    return results


def print_validate_report(test_dir):
    results = validate(test_dir)
    all_passed = True
    n_run = 0
    for name, r in results.items():
        n_run += 1
        status = "PASS" if r["passed"] else "FAIL"
        if not r["passed"]:
            all_passed = False
        print(
            f"  {status}  {name}: "
            f"expected {r['expected_lufs']:+.1f}, "
            f"got {r['measured_lufs']:+.2f}, "
            f"error {r['error_lu']:+.3f} LU "
            f"(allowed +/-{r['tol']:.1f})"
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
    print_validate_report(test_dir)