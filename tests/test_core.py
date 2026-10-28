import tempfile
import unittest
from pathlib import Path

from tvboot.core import AdController, BackupStore, DeviceInfo, OperationError


class FakeTV:
    def __init__(self, info, value=None):
        self.info = info
        self.value = value
        self.writes = []
        self.fail_readback = False

    def device_info(self):
        return self.info

    def read_switch(self):
        if self.fail_readback and self.writes:
            raise OperationError("断开连接")
        return self.value

    def write_switch(self, value):
        self.writes.append(value)
        self.value = value


def supported(identity="serial:example-one", firmware="OS3.0.107.0.UFTMATV"):
    return DeviceInfo("MiTV-MFTR0", "freeguy", "14", firmware, "", "4.8.413", identity)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = BackupStore(Path(self.temp.name))

    def test_disable_records_absent_original_and_restore_removes_key(self):
        tv = FakeTV(supported(), None)
        controller = AdController(tv, self.store)
        self.assertEqual(controller.disable(), "changed")
        self.assertEqual(tv.value, "0")
        self.assertEqual(controller.restore(), "restored")
        self.assertIsNone(tv.value)

    def test_disable_preserves_explicit_enabled_value(self):
        tv = FakeTV(supported(), "1")
        controller = AdController(tv, self.store)
        controller.disable()
        controller.restore()
        self.assertEqual(tv.value, "1")

    def test_unknown_firmware_never_writes(self):
        tv = FakeTV(supported(firmware="OS3.0.108.0.UFTMATV"), None)
        with self.assertRaises(OperationError):
            AdController(tv, self.store).disable()
        self.assertEqual(tv.writes, [])

    def test_missing_identity_never_writes(self):
        tv = FakeTV(supported(identity=""), None)
        with self.assertRaises(OperationError):
            AdController(tv, self.store).disable()
        self.assertEqual(tv.writes, [])

    def test_unexpected_existing_value_never_writes(self):
        tv = FakeTV(supported(), "unexpected")
        with self.assertRaises(OperationError):
            AdController(tv, self.store).disable()
        self.assertEqual(tv.writes, [])

    def test_already_off_does_not_create_a_fake_backup(self):
        tv = FakeTV(supported(), "0")
        controller = AdController(tv, self.store)
        self.assertEqual(controller.disable(), "already_off")
        with self.assertRaises(OperationError):
            controller.restore()
        self.assertEqual(tv.writes, [])

    def test_repeated_disable_keeps_original_backup(self):
        tv = FakeTV(supported(), "1")
        controller = AdController(tv, self.store)
        controller.disable()
        self.assertEqual(controller.disable(), "already_off")
        controller.restore()
        self.assertEqual(tv.value, "1")

    def test_restore_does_not_use_another_televisions_backup(self):
        one = FakeTV(supported("serial:one"), None)
        AdController(one, self.store).disable()
        two = FakeTV(supported("serial:two"), "0")
        with self.assertRaises(OperationError):
            AdController(two, self.store).restore()
        self.assertEqual(two.writes, [])

    def test_backup_failure_prevents_write(self):
        file_path = Path(self.temp.name) / "not-a-directory"
        file_path.write_text("file", encoding="utf-8")
        tv = FakeTV(supported(), None)
        with self.assertRaises(OperationError):
            AdController(tv, BackupStore(file_path)).disable()
        self.assertEqual(tv.writes, [])

    def test_failed_verification_leaves_recovery_record(self):
        tv = FakeTV(supported(), None)
        tv.fail_readback = True
        controller = AdController(tv, self.store)
        with self.assertRaises(OperationError):
            controller.disable()
        tv.fail_readback = False
        self.assertEqual(controller.restore(), "restored")
        self.assertIsNone(tv.value)

    def test_incomplete_backup_cannot_delete_a_setting(self):
        tv = FakeTV(supported(), "0")
        self.store.write(tv.info, {"schema": 1, "active": True, "profile": "mftr0-os3-107", "device": tv.info.public_fields()})
        with self.assertRaises(OperationError):
            AdController(tv, self.store).restore()
        self.assertEqual(tv.writes, [])


if __name__ == "__main__":
    unittest.main()
