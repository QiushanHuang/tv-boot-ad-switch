import unittest

from tvboot.core import DeviceInfo
from tvboot.presentation import view_state, same_connected_host, error_message


def info(firmware="OS3.0.107.0.UFTMATV", identity="serial:test-device"):
    return DeviceInfo("MiTV-MFTR0", "freeguy", "14", firmware, "", "4.8.413", identity)


class PresentationTests(unittest.TestCase):
    def test_unknown_firmware_has_no_action_buttons(self):
        result = view_state(info(firmware="unknown"), None, True)
        self.assertFalse(result.can_disable)
        self.assertFalse(result.can_restore)

    def test_supported_device_requires_backup_before_restore_is_available(self):
        result = view_state(info(), "1", False)
        self.assertTrue(result.can_disable)
        self.assertFalse(result.can_restore)

    def test_missing_identity_never_enables_a_write(self):
        result = view_state(info(identity=""), "1", False)
        self.assertFalse(result.can_disable)
        self.assertFalse(result.can_restore)

    def test_already_disabled_does_not_offer_another_write(self):
        result = view_state(info(), "0", True)
        self.assertFalse(result.can_disable)
        self.assertTrue(result.can_restore)

    def test_editing_ip_disables_actions_for_the_previous_connection(self):
        self.assertTrue(same_connected_host("192.168.8.2", "192.168.8.2"))
        self.assertFalse(same_connected_host("192.168.8.2", "192.168.8.3"))
        self.assertFalse(same_connected_host(None, "192.168.8.2"))

    def test_network_permission_denial_explains_what_to_check(self):
        self.assertIn("本地网络", error_message(PermissionError("denied")))

    def test_windows_network_permission_error_does_not_show_mac_settings(self):
        text = error_message(PermissionError("denied"), "win32")
        self.assertIn("防火墙", text)
        self.assertNotIn("隐私与安全性", text)


if __name__ == "__main__":
    unittest.main()
