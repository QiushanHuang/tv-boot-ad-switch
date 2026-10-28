"""Local GUI smoke test with a simulated television; no network or TV writes."""

import tempfile
import sys
from pathlib import Path

import webview

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tvboot.bridge import Bridge
from tvboot.core import BackupStore, DeviceInfo
from tvboot.discovery import Candidate


class SimulatedTV:
    def __init__(self):
        self.value = None

    def connect(self, host):
        return None

    def device_info(self):
        return DeviceInfo("MiTV-MFTR0", "freeguy", "14", "OS3.0.107.0.UFTMATV", "", "4.8.413", "serial:simulated-tv")

    def read_switch(self):
        return self.value

    def write_switch(self, value):
        self.value = value

    def close(self):
        return None


with tempfile.TemporaryDirectory(prefix="tvboot-preview-") as temp:
    bridge = Bridge(SimulatedTV, BackupStore(Path(temp)), lambda: [Candidate("192.168.1.20", "客厅电视（模拟）")])
    page = (Path(__file__).resolve().parents[1] / "ui" / "index.html").as_uri()
    window = webview.create_window("电视开机助手 · 模拟测试", page, js_api=bridge, width=800, height=640, min_size=(560, 500))
    window.events.closing += bridge._close
    webview.start()
