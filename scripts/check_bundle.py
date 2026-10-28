"""Smoke-test the built application without opening a window or a TV."""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if sys.platform == "darwin":
    executable = root / "dist" / "TVBootAdSwitch.app" / "Contents" / "MacOS" / "TVBootAdSwitch"
elif sys.platform == "win32":
    executable = root / "dist" / "TVBootAdSwitch" / "TVBootAdSwitch.exe"
else:
    raise SystemExit("Only macOS and Windows release bundles are supported")
if not executable.is_file():
    raise SystemExit("Bundle executable is missing")
result = subprocess.run([str(executable), "--self-test"], capture_output=True, text=True, timeout=40)
if result.returncode:
    print(result.stdout, result.stderr, file=sys.stderr)
    raise SystemExit("Bundle self-test failed")
print("Bundle self-test passed")
