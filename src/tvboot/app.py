"""Native desktop window with a local, accessible interface."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .adb import AdbSession
from .bridge import Bridge
from .core import BackupStore, OperationError
from .discovery import discover


def data_directory():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "TVBootAdSwitch"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")) / "TVBootAdSwitch"
    return Path.home() / ".local" / "share" / "TVBootAdSwitch"


def resource_directory():
    return Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]


def find_adb():
    executable = "adb.exe" if os.name == "nt" else "adb"
    root = resource_directory()
    candidate = root / "adb" / executable if getattr(sys, "frozen", False) else root / "build" / "adb" / executable
    if getattr(sys, "frozen", False):
        if candidate.is_file() and (root / "adb" / "NOTICE.txt").is_file():
            return candidate
        raise OperationError("程序包中的 ADB 或许可说明缺失，请重新下载完整发布包。")
    if candidate.is_file():
        return candidate
    path = shutil.which(executable)
    if path:
        return Path(path)
    raise OperationError("没有找到 ADB 工具。请使用完整发布包，或按开发说明准备 ADB。")


def self_test():
    try:
        import webview  # noqa: F401 -- ensures the packaged UI runtime exists
        if sys.platform == "darwin":
            import webview.platforms.cocoa  # noqa: F401
        elif os.name == "nt":
            import webview.platforms.edgechromium  # noqa: F401
        root = resource_directory()
        if not all((root / "ui" / name).is_file() for name in ("index.html", "app.js", "state.js", "app.css")):
            return 1
        if getattr(sys, "frozen", False) and not (root / "licenses" / "THIRD-PARTY.md").is_file():
            return 1
        options = dict(capture_output=True, text=True, timeout=10)
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run([str(find_adb()), "version"], **options)
        return 0 if result.returncode == 0 and "Android Debug Bridge" in result.stdout else 1
    except (ImportError, OperationError, OSError, subprocess.SubprocessError):
        return 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    if "--diagnose-network" in sys.argv:
        try:
            print("Local TV discovery completed; candidates:", len(discover(timeout=2)))
            return 0
        except OSError as exc:
            print("Local TV discovery failed:", type(exc).__name__, str(exc), file=sys.stderr)
            return 1

    import webview

    folder = data_directory()
    bridge = Bridge(lambda: AdbSession(find_adb(), folder), BackupStore(folder / "backups"), discover)
    window = webview.create_window(
        "电视开机助手", (resource_directory() / "ui" / "index.html").as_uri(), js_api=bridge,
        width=800, height=640, min_size=(560, 500), background_color="#f5f7fb",
        text_select=True, zoomable=True,
    )
    window.events.closing += bridge._close
    webview.start(gui="edgechromium" if os.name == "nt" else None, private_mode=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
