#!/usr/bin/env python3
"""Build unsigned Kilo.app on macOS."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "kilo-workspace.spec"
DIST = HERE / "dist"
APP = DIST / "Kilo.app"


def main() -> int:
    if sys.platform != "darwin":
        sys.stderr.write("pack.py only builds a macOS .app\n")
        return 2
    if not SPEC.is_file():
        sys.stderr.write(f"missing spec: {SPEC}\n")
        return 2
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "missing pyinstaller. Install with:\n"
            "  pip install -r view/requirements-pack.txt\n"
        )
        return 2

    os.chdir(HERE)
    for leftover in (HERE / "build", DIST):
        if leftover.exists():
            shutil.rmtree(leftover)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC),
    ]
    print(" ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=HERE)
    if r.returncode != 0:
        return r.returncode
    if not APP.is_dir():
        sys.stderr.write(f"pyinstaller finished but missing {APP}\n")
        return 1

    sign = subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(APP)],
        capture_output=True,
        text=True,
    )
    if sign.returncode != 0:
        sys.stderr.write(sign.stderr or "codesign failed (ad-hoc)\n")
        # still a usable local .app
    print(f"built {APP}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
