"""Narrow JSON interface between the local UI and the TV controller."""

import threading

from .core import AdController, OperationError
from .discovery import valid_ipv4
from .presentation import error_message, view_state
from .profiles import profile_for


class Bridge:
    def __init__(self, session_factory, backups, discovery):
        self._session_factory = session_factory
        self._backups = backups
        self._discovery = discovery
        self._session = None
        self._connected_host = None
        self._connected_info = None
        self._lock = threading.Lock()

    def _run(self, operation):
        if not self._lock.acquire(blocking=False):
            return {"ok": False, "error": "操作正在进行，请稍候。"}
        try:
            return {"ok": True, **operation()}
        except OperationError as exc:
            return {"ok": False, "error": str(exc)}
        except Exception as exc:
            return {"ok": False, "error": error_message(exc)}
        finally:
            self._lock.release()

    def discover(self):
        return self._run(lambda: {"devices": [{"ip": c.ip, "name": c.name} for c in self._discovery()]})

    def connect(self, host):
        def operation():
            self._connected_host = None
            self._connected_info = None
            if not isinstance(host, str) or not valid_ipv4(host.strip()):
                raise OperationError("请输入电视的局域网 IPv4 地址。")
            host_value = host.strip()
            if self._session is None:
                self._session = self._session_factory()
            self._session.connect(host_value)
            info = self._session.device_info()
            result = self._status(info)
            self._connected_host = host_value
            self._connected_info = info
            return result
        return self._run(operation)

    def _status(self, info=None):
        info = info or self._session.device_info()
        if self._connected_info is not None and (
            info.identity != self._connected_info.identity
            or info.public_fields() != self._connected_info.public_fields()
        ):
            self._connected_host = None
            self._connected_info = None
            raise OperationError("电视身份或系统版本已变化，请重新连接并检测。")
        switch = self._session.read_switch()
        profile = profile_for(info)
        record = self._backups.read(info) if profile and info.identity else None
        has_backup = bool(record and record.get("active") is True
                          and record.get("profile") == profile.key
                          and record.get("device") == info.public_fields())
        view = view_state(info, switch, has_backup)
        return {
            "view": {
                "heading": view.heading, "detail": view.detail,
                "can_disable": view.can_disable, "can_restore": view.can_restore,
                "state": "unsupported" if profile is None else ("off" if switch == "0" else "ready"),
                "evidence": profile.evidence if profile else "",
            },
            "device": info.public_fields(),
        }

    def _require_host(self, host):
        if not isinstance(host, str) or not self._connected_host or not self._connected_info or host.strip() != self._connected_host:
            raise OperationError("电视地址已更改，请重新连接并检测。")

    def disable(self, host):
        def operation():
            self._require_host(host)
            outcome = AdController(self._session, self._backups, self._connected_info).disable()
            return {"outcome": outcome, **self._status()}
        return self._run(operation)

    def restore(self, host):
        def operation():
            self._require_host(host)
            outcome = AdController(self._session, self._backups, self._connected_info).restore()
            return {"outcome": outcome, **self._status()}
        return self._run(operation)

    def _close(self):
        if not self._lock.acquire(blocking=False):
            return False
        try:
            if self._session:
                self._session.close()
            return True
        finally:
            self._lock.release()
