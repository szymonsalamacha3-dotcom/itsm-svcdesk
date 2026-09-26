import re
import subprocess
import sys


def main() -> int:
    command = [sys.executable, "-m", "pytest", "-q", "/app/tests"]
    result = subprocess.run(command, capture_output=True, text=True, cwd="/app")

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)

    summary = (result.stdout or "").strip().splitlines()[-1] if (result.stdout or "").strip() else ""
    passed_match = re.search(r"(\d+) passed", summary)
    failed_match = re.search(r"(\d+) failed", summary)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    emit = f"ITSMLAB-TESTS: passed={passed} failed={failed}"
    print(emit)
    return 0 if result.returncode == 0 and failed == 0 else result.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
