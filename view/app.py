#!/usr/bin/env python3
"""Kilo — native window for the kilo board."""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import time
from pathlib import Path

def bundle_dir() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent


HERE = bundle_dir()


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _pick_folder() -> str:
    if sys.platform == "darwin":
        try:
            from AppKit import NSApplication, NSOpenPanel

            NSApplication.sharedApplication()
            panel = NSOpenPanel.openPanel()
            panel.setCanChooseFiles_(False)
            panel.setCanChooseDirectories_(True)
            panel.setAllowsMultipleSelection_(False)
            panel.setCanCreateDirectories_(False)
            panel.setTitle_("Kilo")
            panel.setMessage_("选择 Projects 文件夹")
            start = _pick_start()
            if start:
                from Foundation import NSURL

                panel.setDirectoryURL_(NSURL.fileURLWithPath_(start))
            if int(panel.runModal()) == 1:
                urls = panel.URLs()
                if urls:
                    return str(urls[0].path())
            return ""
        except Exception:
            pass
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(title="Kilo：选择 Projects 文件夹")
        root.destroy()
        return path or ""
    except Exception:
        return ""


def _pick_start() -> str:
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    try:
        import serve as board

        saved = board.saved_root()
        if saved and Path(saved).is_dir():
            return saved
    except Exception:
        pass
    cand = (
        Path.home()
        / "Library"
        / "Mobile Documents"
        / "iCloud~md~obsidian"
        / "Documents"
        / "cosmos"
        / "Projects"
    )
    if cand.is_dir():
        return str(cand)
    return str(Path.home())


def main() -> None:
    try:
        import webview
    except ImportError:
        sys.stderr.write(
            "missing pywebview. Install with:\n"
            "  pip install -r view/requirements.txt\n"
        )
        sys.exit(2)

    p = argparse.ArgumentParser(description="Kilo")
    p.add_argument("--root", default=os.environ.get("KILO_WORKSPACE", ""))
    p.add_argument("--port", type=int, default=0)
    args = p.parse_args()
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import serve as board

    root = args.root or board.saved_root()
    if not root:
        root = _pick_folder()
    if not root:
        sys.stderr.write("set --root or KILO_WORKSPACE, or pick a folder\n")
        sys.exit(2)
    got = board.set_workspace(root)
    if not got.get("ok"):
        sys.stderr.write(got.get("error") or "bad workspace\n")
        sys.exit(2)
    root_path = Path(got["root"])

    port = args.port or _free_port()

    class BoundHandler(board.Handler):
        pass

    from http.server import ThreadingHTTPServer

    httpd = ThreadingHTTPServer(("127.0.0.1", port), BoundHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    board.start_code_watch()
    url = f"http://127.0.0.1:{port}/"
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)

    def _style_window(_win=None) -> None:
        # Slack / Linear / VS Code: hide the window title, draw content under
        # the traffic lights, keep the bar the same #f4f4f4 as the sidebar.
        try:
            from AppKit import NSApp, NSColor, NSImage

            try:
                from AppKit import NSFullSizeContentViewWindowMask, NSWindowTitleHidden
            except ImportError:
                NSFullSizeContentViewWindowMask = 1 << 15
                NSWindowTitleHidden = 1
            c = NSColor.colorWithSRGBRed_green_blue_alpha_(
                244 / 255.0, 244 / 255.0, 244 / 255.0, 1.0
            )
            native = getattr(_win, "native", None) if _win is not None else None
            windows = [native] if native is not None else []
            if not windows:
                windows = list(NSApp.windows() or [])
            for w in windows:
                if w is None:
                    continue
                try:
                    w.setTitlebarAppearsTransparent_(True)
                except Exception:
                    pass
                try:
                    w.setTitleVisibility_(NSWindowTitleHidden)
                except Exception:
                    try:
                        w.setTitleVisibility_(1)
                    except Exception:
                        pass
                try:
                    w.setStyleMask_(int(w.styleMask()) | int(NSFullSizeContentViewWindowMask))
                except Exception:
                    pass
                try:
                    w.setBackgroundColor_(c)
                except Exception:
                    pass
                try:
                    w.setTitle_("")
                except Exception:
                    pass
                try:
                    w.setTitlebarSeparatorStyle_(0)
                except Exception:
                    pass
            icns = HERE / "static" / "icon.icns"
            png = HERE / "static" / "icon.png"
            icon = icns if icns.is_file() else png
            if icon.is_file():
                img = NSImage.alloc().initWithContentsOfFile_(str(icon))
                if img:
                    NSApp.setApplicationIconImage_(img)
        except Exception:
            pass

    class BoardApi:
        def pick_folder(self) -> str:
            start = str(root_path) if root_path.is_dir() else str(Path.home())
            chosen = win.create_file_dialog(
                webview.FileDialog.FOLDER,
                directory=start,
            )
            if not chosen:
                return ""
            if isinstance(chosen, (list, tuple)):
                return str(chosen[0]) if chosen else ""
            return str(chosen)

    win = webview.create_window(
        "Kilo",
        url,
        width=1100,
        height=740,
        min_size=(720, 480),
        text_select=True,
        background_color="#F4F4F4",
        js_api=BoardApi(),
    )
    def _on_window(*args) -> None:
        w = args[0] if args else win
        _style_window(w)
        threading.Timer(0.05, lambda: _style_window(win)).start()

    shown = getattr(win.events, "shown", None)
    if shown is not None:
        shown += _on_window
    before = getattr(win.events, "before_show", None)
    if before is not None:
        before += _on_window
    webview.start()
    httpd.shutdown()


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    main()
