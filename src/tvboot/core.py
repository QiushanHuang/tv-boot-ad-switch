"""Read, save, change, and restore one narrowly scoped system setting."""

import hashlib
import hmac
import json
import os
import secrets
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .profiles import profile_for


class OperationError(Exception):
    """An operation was stopped or could not be verified."""


@dataclass(frozen=True)
class DeviceInfo:
    model: str
    codename: str
    android: str
    firmware: str
    display: str
    launcher: str
    identity: str = field(repr=False)

    def public_fields(self):
        return {
            "model": self.model, "codename": self.codename,
            "android": self.android, "firmware": self.firmware,
            "display": self.display, "launcher": self.launcher,
        }


class BackupStore:
    """Private local records; raw device identifiers are never written."""

    def __init__(self, directory):
        self.directory = Path(directory)

    def _ensure_directory(self):
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self.directory.is_dir():
            raise OSError("backup path is not a directory")

    def _secret(self):
        self._ensure_directory()
        path = self.directory / "device-key"
        try:
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            key = path.read_bytes()
        else:
            key = secrets.token_bytes(32)
            with os.fdopen(fd, "wb") as handle:
                handle.write(key)
                handle.flush()
                os.fsync(handle.fileno())
        if len(key) != 32:
            raise OSError("invalid local identity key")
        return key

    def _path_for(self, info):
        if not info.identity or info.identity.lower() in {
            "unknown", "null", "none", "serial:unknown", "serial:null", "android_id:null"
        }:
            raise OperationError("电视没有可用于恢复的稳定标识，未进行修改。")
        token = hmac.new(self._secret(), info.identity.encode("utf-8"), hashlib.sha256).hexdigest()
        return self.directory / (token + ".json")

    def read(self, info):
        try:
            path = self._path_for(info)
            if not path.exists():
                return None
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict) or record.get("schema") != 1:
                raise ValueError("unsupported backup format")
            return record
        except OperationError:
            raise
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            raise OperationError("无法读取本地恢复记录，未进行修改。") from exc

    def write(self, info, record):
        temp_path = None
        try:
            path = self._path_for(info)
            data = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
            fd, temp_path = tempfile.mkstemp(prefix=".tvboot-", dir=str(self.directory))
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
            temp_path = None
        except OperationError:
            raise
        except (OSError, ValueError, TypeError) as exc:
            raise OperationError("无法保存本地恢复记录，未继续修改。") from exc
        finally:
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass


class AdController:
    def __init__(self, device, backups, expected_info=None):
        self.device = device
        self.backups = backups
        self.expected_info = expected_info

    def _supported(self):
        info = self.device.device_info()
        if self.expected_info is not None and (
            not info.identity or info.identity != self.expected_info.identity
            or info.public_fields() != self.expected_info.public_fields()
        ):
            raise OperationError("电视身份或系统版本已变化，请重新连接并检测。")
        profile = profile_for(info)
        if profile is None:
            raise OperationError("此型号或固件尚未验证；只进行检测，不进行修改。")
        return info, profile

    def disable(self):
        info, profile = self._supported()
        current = self.device.read_switch()
        if current not in (None, "0", "1"):
            raise OperationError("开关原值无法识别，未进行修改。")
        if current == "0":
            return "already_off"
        prior = self.backups.read(info)
        if prior and prior.get("active"):
            raise OperationError("已有未恢复的记录，但电视状态已变化；未覆盖原始备份。")
        record = {
            "schema": 1, "active": True, "profile": profile.key,
            "device": info.public_fields(), "original": current,
        }
        self.backups.write(info, record)
        self.device.write_switch("0")
        if self.device.read_switch() != "0":
            raise OperationError("写入后未能确认关闭；恢复记录已保存在本机。")
        return "changed"

    def restore(self):
        info, profile = self._supported()
        record = self.backups.read(info)
        if not record or record.get("active") is not True:
            raise OperationError("没有这台电视可用的恢复记录。")
        if record.get("profile") != profile.key or record.get("device") != info.public_fields():
            raise OperationError("电视固件或桌面版本已变化，未自动恢复。")
        if "original" not in record:
            raise OperationError("恢复记录不完整，未进行修改。")
        original = record["original"]
        if original not in (None, "1"):
            raise OperationError("恢复记录的原值无效，未进行修改。")
        current = self.device.read_switch()
        if current == original:
            record["active"] = False
            self.backups.write(info, record)
            return "restored"
        if current != "0":
            raise OperationError("电视当前状态已被其他操作改变，未覆盖。")
        self.device.write_switch(original)
        if self.device.read_switch() != original:
            raise OperationError("未能确认恢复结果；恢复记录仍保存在本机。")
        record["active"] = False
        self.backups.write(info, record)
        return "restored"
