import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.prepare_adb import extract_checked


def archive():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as bundle:
        for name, data in {
            "platform-tools/adb.exe": b"fake adb",
            "platform-tools/AdbWinApi.dll": b"fake dll 1",
            "platform-tools/AdbWinUsbApi.dll": b"fake dll 2",
            "platform-tools/NOTICE.txt": b"licenses",
            "../../escape": b"unwanted",
        }.items():
            bundle.writestr(name, data)
    return buf.getvalue()


class PrepareAdbTests(unittest.TestCase):
    def test_checksum_mismatch_produces_no_executable(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                extract_checked(archive(), "windows", Path(root), "0" * 64)
            self.assertFalse((Path(root) / "adb.exe").exists())

    def test_only_required_windows_files_and_notice_are_extracted(self):
        data = archive()
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "out"
            extract_checked(data, "windows", out, hashlib.sha256(data).hexdigest())
            self.assertEqual((out / "adb.exe").read_bytes(), b"fake adb")
            self.assertEqual((out / "NOTICE.txt").read_bytes(), b"licenses")
            self.assertEqual(set(p.name for p in out.iterdir()), {"adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "NOTICE.txt"})
            self.assertFalse((Path(root) / "escape").exists())


if __name__ == "__main__":
    unittest.main()
