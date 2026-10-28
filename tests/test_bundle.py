import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tvboot.app import find_adb
from tvboot.core import OperationError


class BundleTests(unittest.TestCase):
    def test_packaged_app_does_not_fall_back_to_adb_from_path(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", temp, create=True), patch("tvboot.app.shutil.which", return_value="/some/other/adb"):
                with self.assertRaises(OperationError):
                    find_adb()

    def test_packaged_adb_requires_its_notice(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "adb"
            root.mkdir()
            (root / ("adb.exe" if sys.platform == "win32" else "adb")).write_bytes(b"fake executable")
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", temp, create=True):
                with self.assertRaises(OperationError):
                    find_adb()


if __name__ == "__main__":
    unittest.main()
