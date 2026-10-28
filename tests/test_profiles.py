import unittest

from tvboot.core import DeviceInfo
from tvboot.profiles import profile_for


class ProfileTests(unittest.TestCase):
    def test_documented_community_reports_match_only_their_recorded_versions(self):
        samples = [
            (DeviceInfo("MiTV-ANTL0", "starwars", "5.1.1", "23.2.4.2225", "", "3.38.1017", "serial:one"), "antl0-2225"),
            (DeviceInfo("MiTV-MFTP0", "alita", "9", "23.2.10.6129", "", "3.49.1601", "serial:two"), "mftp0-6129"),
            (DeviceInfo("MiTV-MTTP0", "hugo", "9", "2585", "", "3.50.1621", "serial:three"), "mttp0-2585"),
        ]
        for info, key in samples:
            with self.subTest(model=info.model):
                self.assertEqual(profile_for(info).key, key)
                changed = DeviceInfo(info.model, info.codename, info.android, info.firmware, info.display, "unexpected", info.identity)
                self.assertIsNone(profile_for(changed))


if __name__ == "__main__":
    unittest.main()
