"""Use a private local ADB server and target exactly one authorised TV."""

import os
import re
import socket
import subprocess
from pathlib import Path

from .core import DeviceInfo, OperationError
from .discovery import valid_ipv4


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _usable_identifier(value):
    value = value.strip()
    return bool(value and value.lower() not in {
        "null", "unknown", "none", "0", "0000000000000000", "0123456789abcdef"
    } and len(value) >= 6 and set(value) != {"0"})


class AdbSession:
    def __init__(self, executable, directory, port=None, runner=None):
        self.executable = str(executable)
        self.directory = Path(directory)
        self.port = port if port is not None else _free_port()
        self.runner = runner or subprocess.run
        self.serial = None
        self.transport_id = None
        self.owns_server = False
        self.env = os.environ.copy()
        for key in ("ADB_SERVER_SOCKET", "ANDROID_ADB_SERVER_PORT", "ANDROID_SERIAL",
                    "ADB_VENDOR_KEYS", "ADB_MDNS_AUTO_CONNECT", "ADB_TRACE"):
            self.env.pop(key, None)
        for key in ("ADB_MDNS_AUTO_CONNECT", "ADB_MDNS", "ADB_USB", "ADB_EMU"):
            self.env[key] = "0"

    def _run(self, *arguments, timeout=10):
        args = [self.executable, "-P", str(self.port)] + list(arguments)
        options = dict(capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, env=self.env)
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        try:
            result = self.runner(args, **options)
        except (OSError, subprocess.SubprocessError) as exc:
            raise OperationError("ADB 工具不可用或连接超时。") from exc
        if result.returncode != 0:
            raise OperationError("电视连接或 ADB 命令失败，请检查调试授权。")
        return result

    def _start(self):
        if self.owns_server:
            return
        try:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as exc:
            raise OperationError("无法创建本机调试配置目录。") from exc
        result = self._run("start-server", timeout=15)
        text = (result.stdout + result.stderr).lower()
        if "daemon started successfully" not in text:
            raise OperationError("无法确认独立 ADB 服务的所有权，请重试。")
        self.owns_server = True

    def connect(self, host):
        if not valid_ipv4(host):
            raise OperationError("请输入电视的局域网 IPv4 地址。")
        self.serial = None
        self.transport_id = None
        self._start()
        target = host + ":5555"
        self._run("connect", target, timeout=12)
        devices = self._run("devices", "-l").stdout
        status = None
        transport = None
        for line in devices.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[0] == target:
                status = fields[1]
                ids = [item.split(":", 1)[1] for item in fields[2:] if item.startswith("transport_id:")]
                transport = ids[0] if len(ids) == 1 and ids[0].isdigit() and int(ids[0]) > 0 else None
                break
        if status == "unauthorized":
            raise OperationError("请在电视屏幕上允许此电脑调试，然后再次连接。")
        if status != "device":
            raise OperationError("未连接到电视；请确认电视开机、地址正确且 ADB 调试已允许。")
        if transport is None:
            raise OperationError("无法确认本次电视连接，请重新连接。")
        self.serial = target
        self.transport_id = transport

    def _shell(self, *args):
        if not self.serial or not self.transport_id:
            raise OperationError("电视尚未连接并授权。")
        result = self._run("-t", self.transport_id, "shell", *args)
        text = result.stdout.strip()
        diagnostics = (text + "\n" + result.stderr).lower()
        if "securityexception" in diagnostics or "permission denied" in diagnostics:
            raise OperationError("电视拒绝了该操作。")
        return text

    def device_info(self):
        values = [self._shell("getprop", key) for key in (
            "ro.product.model", "ro.product.device", "ro.build.version.release",
            "ro.build.version.incremental", "ro.build.display.id",
        )]
        dump = self._shell("dumpsys", "package", "com.mitv.tvhome")
        match = re.search(r"(?m)^\s*versionName=([^\s]+)", dump)
        launcher = match.group(1) if match else ""
        serial = self._shell("getprop", "ro.serialno")
        try:
            android_id = self._shell("settings", "get", "secure", "android_id")
        except OperationError:
            android_id = ""
        components = []
        if _usable_identifier(serial):
            components.append("serial:" + serial)
        if _usable_identifier(android_id):
            components.append("android_id:" + android_id)
        identity = "|".join(components)
        return DeviceInfo(*values, launcher, identity)

    def read_switch(self):
        output = self._shell("settings", "list", "system")
        if not output or not any("=" in line and line.split("=", 1)[0] for line in output.splitlines()):
            raise OperationError("无法读取电视设置，未进行修改。")
        prefix = "boot_ad_switch="
        values = [line[len(prefix):] for line in output.splitlines() if line.startswith(prefix)]
        if len(values) > 1:
            raise OperationError("广告开关存在重复记录，未进行修改。")
        return values[0] if values else None

    def write_switch(self, value):
        if value is None:
            self._shell("settings", "delete", "system", "boot_ad_switch")
        elif value in ("0", "1"):
            self._shell("settings", "put", "system", "boot_ad_switch", value)
        else:
            raise OperationError("无效的广告开关值。")

    def close(self):
        self.serial = None
        self.transport_id = None
        if self.owns_server:
            try:
                self._run("kill-server", timeout=5)
            except OperationError:
                pass
            self.owns_server = False
