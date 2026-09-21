#!/usr/bin/env python3
"""Native window around the read-only kilo workspace board."""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _pick_folder() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(title="选择 kilo workspace（含 Projects/ 的目录）")
        root.destroy()
        return path or ""
    except Exception:
        return ""


def main() -> None:
    try:
        import webview
    except ImportError:
        sys.stderr.write(
            "missing pywebview. Install with:\n"
            "  pip install -r view/requirements.txt\n"
        )
        sys.exit(2)

    p = argparse.ArgumentParser(description="kilo workspace desktop viewer")
    p.add_argument("--root", default=os.environ.get("KILO_WORKSPACE", ""))
    p.add_argument("--port", type=int, default=0)
    args = p.parse_args()
    root = args.root
    if not root:
        root = _pick_folder()
    if not root:
        sys.stderr.write("set --root or KILO_WORKSPACE, or pick a folder\n")
        sys.exit(2)
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        sys.stderr.write(f"root not a directory: {root_path}\n")
        sys.exit(2)

    port = args.port or _free_port()

    import serve as board

    board.ROOT = root_path

    class BoundHandler(board.Handler):
        pass

    from http.server import ThreadingHTTPServer

    httpd = ThreadingHTTPServer(("127.0.0.1", port), BoundHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/"
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)

    webview.create_window(
        "kilo workspace",
        url,
        width=1100,
        height=740,
        min_size=(720, 480),
        text_select=True,
    )
    webview.start()
    httpd.shutdown()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
