import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tvboot.adb import AdbSession
from tvboot.core import OperationError


class FakeRunner:
    def __init__(self, device_state="device"):
        self.state = device_state
        self.android_id = "null"
        self.transport_id = "7"
        self.system_settings = "other_setting=1\n"
        self.calls = []
        self.environments = []
        self.properties = {
            "ro.product.model": "MiTV-MFTR0",
            "ro.product.device": "freeguy",
            "ro.build.version.release": "14",
            "ro.build.version.incremental": "OS3.0.107.0.UFTMATV",
            "ro.build.display.id": "some-build",
            "ro.serialno": "synthetic-serial",
        }

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        self.environments.append(kwargs.get("env", {}))
        if "start-server" in args:
            return SimpleNamespace(returncode=0, stdout="", stderr="* daemon started successfully")
        if "connect" in args:
            return SimpleNamespace(returncode=0, stdout="connected to 192.168.4.8:5555", stderr="")
        if "devices" in args:
            suffix = " transport_id:" + self.transport_id if self.transport_id else ""
            return SimpleNamespace(returncode=0, stdout="List of devices attached\n192.168.4.8:5555\t" + self.state + suffix + "\n", stderr="")
        if "getprop" in args:
            return SimpleNamespace(returncode=0, stdout=self.properties[args[-1]], stderr="")
        if "dumpsys" in args:
            return SimpleNamespace(returncode=0, stdout="Packages:\n versionName=4.8.413\nHidden:\n versionName=4.2.56.6\n", stderr="")
        if args[-4:] == ["settings", "get", "secure", "android_id"]:
            return SimpleNamespace(returncode=0, stdout=self.android_id, stderr="")
        if args[-3:] == ["settings", "list", "system"]:
            return SimpleNamespace(returncode=0, stdout=self.system_settings, stderr="")
        if "get" in args:
            return SimpleNamespace(returncode=0, stdout="null\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")


class AdbTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runner = FakeRunner()
        self.session = AdbSession(Path("adb"), Path(self.temp.name), port=55123, runner=self.runner)

    def test_rejects_non_private_or_injected_host_before_starting_adb(self):
        for host in ("8.8.8.8", "192.168.1.1;reboot", "example.com"):
            with self.assertRaises(OperationError):
                self.session.connect(host)
        self.assertEqual(self.runner.calls, [])

    def test_unauthorized_tv_does_not_allow_device_queries(self):
        self.runner.state = "unauthorized"
        with self.assertRaises(OperationError):
            self.session.connect("192.168.4.8")
        with self.assertRaises(OperationError):
            self.session.device_info()
        self.assertFalse(any("getprop" in call for call in self.runner.calls))

    def test_authorized_device_identity_and_current_launcher_are_read(self):
        self.session.connect("192.168.4.8")
        info = self.session.device_info()
        self.assertEqual((info.model, info.codename, info.android, info.launcher),
                         ("MiTV-MFTR0", "freeguy", "14", "4.8.413"))
        self.assertEqual(info.identity, "serial:synthetic-serial")
        self.assertNotIn("synthetic-serial", repr(info))

    def test_only_known_setting_values_can_be_written(self):
        self.session.connect("192.168.4.8")
        with self.assertRaises(OperationError):
            self.session.write_switch("1; reboot")
        self.session.write_switch(None)
        self.assertTrue(any(call[-4:] == ["settings", "delete", "system", "boot_ad_switch"] for call in self.runner.calls))
        self.assertFalse(any("reboot" in " ".join(call) for call in self.runner.calls))

    def test_shutdown_only_uses_the_isolated_server_port(self):
        self.session.connect("192.168.4.8")
        self.session.close()
        self.assertIn(["adb", "-P", "55123", "kill-server"], self.runner.calls)

    def test_existing_adb_server_overrides_do_not_redirect_our_session(self):
        with patch.dict(os.environ, {"ADB_SERVER_SOCKET": "tcp:localhost:5037", "ANDROID_ADB_SERVER_PORT": "5037"}):
            isolated = AdbSession(Path("adb"), Path(self.temp.name), port=55123, runner=self.runner)
        self.assertFalse("ADB_SERVER_SOCKET" in isolated.env)
        self.assertFalse("ANDROID_ADB_SERVER_PORT" in isolated.env)

    def test_two_televisions_with_same_serial_but_different_android_ids_do_not_share_identity(self):
        self.session.connect("192.168.4.8")
        self.runner.android_id = "abcd1234abcd1234"
        first = self.session.device_info().identity
        self.runner.android_id = "9999abcd9999abcd"
        second = self.session.device_info().identity
        self.assertNotEqual(first, second)

    def test_device_commands_are_bound_to_the_authorized_transport(self):
        self.session.connect("192.168.4.8")
        self.session.read_switch()
        call = next(call for call in self.runner.calls if "settings" in call)
        self.assertIn("-t", call)
        self.assertEqual(call[call.index("-t") + 1], "7")
        self.assertNotIn("-s", call)

    def test_missing_transport_id_never_allows_tv_commands(self):
        self.runner.transport_id = ""
        with self.assertRaises(OperationError):
            self.session.connect("192.168.4.8")
        with self.assertRaises(OperationError):
            self.session.read_switch()

    def test_private_adb_server_does_not_autoconnect_other_devices(self):
        self.session.connect("192.168.4.8")
        env = self.runner.environments[0]
        for name in ("ADB_MDNS_AUTO_CONNECT", "ADB_MDNS", "ADB_USB", "ADB_EMU"):
            self.assertEqual(env.get(name), "0")

    def test_absent_switch_and_literal_null_are_not_confused(self):
        self.session.connect("192.168.4.8")
        self.runner.system_settings = "other=0\n"
        self.assertIsNone(self.session.read_switch())
        self.runner.system_settings = "boot_ad_switch=null\n"
        self.assertEqual(self.session.read_switch(), "null")

    def test_empty_settings_response_does_not_claim_switch_is_absent(self):
        self.session.connect("192.168.4.8")
        self.runner.system_settings = ""
        with self.assertRaises(OperationError):
            self.session.read_switch()
        self.runner.system_settings = "Error: unknown command"
        with self.assertRaises(OperationError):
            self.session.read_switch()


if __name__ == "__main__":
    unittest.main()
