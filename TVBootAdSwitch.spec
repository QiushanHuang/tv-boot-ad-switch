# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[(str(root / "build" / "adb"), "adb"), (str(root / "ui"), "ui"),
           (str(root / "licenses"), "licenses"), (str(root / "LICENSE"), ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="TVBootAdSwitch", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="TVBootAdSwitch")
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="TVBootAdSwitch.app",
        bundle_identifier="org.qiushan.tvbootadswitch",
        info_plist={
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "1",
            "NSLocalNetworkUsageDescription": "用于查找并连接您选择的局域网电视，检查和设置开机广告开关。",
        },
    )
