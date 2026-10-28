"""Fetch the official, checksum-pinned ADB component for release builds."""

import argparse
import hashlib
import io
import os
import urllib.request
import zipfile
from pathlib import Path


ARCHIVES = {
    "macos": (
        "https://dl.google.com/android/repository/platform-tools_r37.0.1-darwin.zip",
        "ee39ad5967e95c2a07f04dbcbde96b1a0c916ba376096db5d2f498b7727a5d1d",
        ("adb", "NOTICE.txt"),
    ),
    "windows": (
        "https://dl.google.com/android/repository/platform-tools_r37.0.1-win.zip",
        "45f4d63113e895ebde0c90f194099a4676b6ac653bd28d54314a9e022bbc1a99",
        ("adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "NOTICE.txt"),
    ),
}


def extract_checked(data, platform, destination, expected_sha256):
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("官方 ADB 文件校验失败")
    names = ARCHIVES[platform][2]
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        content = {name: bundle.read("platform-tools/" + name) for name in names}
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in content.items():
        target = destination / name
        target.write_bytes(payload)
        if name == "adb":
            os.chmod(target, 0o755)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=ARCHIVES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    url, sha256, _ = ARCHIVES[args.platform]
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise ValueError("下载文件过大")
    extract_checked(data, args.platform, args.output, sha256)
    print("ADB prepared from Google Platform-Tools 37.0.1, SHA-256 verified.")


if __name__ == "__main__":
    main()
