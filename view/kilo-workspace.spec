# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

view = Path(SPECPATH)
icon = view / "static" / "icon.icns"

a = Analysis(
    [str(view / "app.py")],
    pathex=[str(view)],
    binaries=[],
    datas=[
        (str(view / "static"), "static"),
        (str(view / "VERSION"), "."),
    ],
    hiddenimports=[
        "serve",
        "webview",
        "webview.platforms.cocoa",
        "objc",
        "AppKit",
        "Foundation",
        "WebKit",
        "Quartz",
        "CoreFoundation",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Kilo",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon) if icon.is_file() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Kilo",
)
app = BUNDLE(
    coll,
    name="Kilo.app",
    icon=str(icon) if icon.is_file() else None,
    bundle_identifier="com.kl7sn.kilo",
    info_plist={
        "CFBundleName": "Kilo",
        "CFBundleDisplayName": "Kilo",
        "CFBundleShortVersionString": (view / "VERSION").read_text(encoding="utf-8").strip() or "0.0.1",
        "CFBundleVersion": (view / "VERSION").read_text(encoding="utf-8").strip() or "0.0.1",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "NSAppleEventsUsageDescription": "Kilo uses Apple Events to raise the Orca window.",
    },
)
