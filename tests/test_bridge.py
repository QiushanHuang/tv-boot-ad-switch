import tempfile
import unittest
from pathlib import Path

from tvboot.bridge import Bridge
from tvboot.core import BackupStore, DeviceInfo, OperationError
from tvboot.discovery import Candidate


class FakeSession:
    def __init__(self, firmware="OS3.0.107.0.UFTMATV", value=None):
        self.info = DeviceInfo("MiTV-MFTR0", "freeguy", "14", firmware, "", "4.8.413", "serial:private-synthetic")
        self.value = value
        self.writes = []
        self.connected = None

    def connect(self, host):
        self.connected = host

    def device_info(self):
        return self.info

    def read_switch(self):
        return self.value

    def write_switch(self, value):
        self.writes.append(value)
        self.value = value

    def close(self):
        pass


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.session = FakeSession()
        self.bridge = Bridge(lambda: self.session, BackupStore(Path(self.temp.name)),
                             lambda: [Candidate("192.168.8.2", "TV one")])

    def test_discovery_returns_only_display_information(self):
        result = self.bridge.discover()
        self.assertTrue(result["ok"])
        self.assertEqual(result["devices"], [{"ip": "192.168.8.2", "name": "TV one"}])

    def test_connect_never_exposes_raw_device_identifier_to_ui(self):
        result = self.bridge.connect("192.168.8.2")
        self.assertTrue(result["ok"])
        self.assertNotIn("private-synthetic", repr(result))
        self.assertTrue(result["view"]["can_disable"])

    def test_action_for_edited_address_cannot_write_to_old_device(self):
        self.bridge.connect("192.168.8.2")
        result = self.bridge.disable("192.168.8.3")
        self.assertFalse(result["ok"])
        self.assertEqual(self.session.writes, [])

    def test_unknown_firmware_remains_read_only(self):
        self.session.info = DeviceInfo("MiTV-MFTR0", "freeguy", "14", "other", "", "4.8.413", "serial:sample")
        result = self.bridge.connect("192.168.8.2")
        self.assertFalse(result["view"]["can_disable"])
        self.assertFalse(self.bridge.disable("192.168.8.2")["ok"])
        self.assertEqual(self.session.writes, [])

    def test_same_ip_reassigned_to_another_tv_cannot_be_modified(self):
        self.bridge.connect("192.168.8.2")
        self.session.info = DeviceInfo("MiTV-MFTR0", "freeguy", "14", "OS3.0.107.0.UFTMATV", "", "4.8.413", "serial:another-tv")
        result = self.bridge.disable("192.168.8.2")
        self.assertFalse(result["ok"])
        self.assertEqual(self.session.writes, [])

    def test_disable_and_restore_are_exposed_as_verified_states(self):
        self.bridge.connect("192.168.8.2")
        result = self.bridge.disable("192.168.8.2")
        self.assertTrue(result["ok"])
        self.assertFalse(result["view"]["can_disable"])
        self.assertTrue(result["view"]["can_restore"])
        result = self.bridge.restore("192.168.8.2")
        self.assertTrue(result["ok"])
        self.assertIsNone(self.session.value)


if __name__ == "__main__":
    unittest.main()
