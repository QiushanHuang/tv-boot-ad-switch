"""Turn read-only TV state into a safe set of available UI actions."""

from dataclasses import dataclass
import sys

from .profiles import profile_for


@dataclass(frozen=True)
class ViewState:
    heading: str
    detail: str
    can_disable: bool
    can_restore: bool


def same_connected_host(connected, entered):
    return bool(connected) and connected == entered.strip()


def error_message(error, platform=None):
    platform = platform or sys.platform
    if isinstance(error, PermissionError):
        if platform == "win32":
            return "系统阻止了局域网访问；请检查防火墙和本地网络权限。"
        return "系统阻止了局域网访问；请在系统的「隐私与安全性 → 本地网络」中允许本应用。"
    if isinstance(error, OSError):
        return "网络搜索未完成；请检查本地网络权限，或手动输入电视 IP。"
    return "操作未完成，请检查连接后重试。"


def view_state(info, switch, has_backup):
    profile = profile_for(info)
    if profile is None:
        return ViewState("此固件尚未验证", "已完成只读检测，暂不提供修改。", False, False)
    if not info.identity:
        return ViewState("无法识别电视身份", "为了确保恢复时对应同一台电视，暂不提供修改。", False, False)
    if switch not in (None, "0", "1"):
        return ViewState("广告开关状态异常", "未识别的原值不会被修改。", False, False)
    evidence = profile.evidence
    if switch == "0":
        return ViewState("开机广告开关已关闭", evidence + " · 请通过重启确认实际播放效果。", False, bool(has_backup))
    return ViewState("可以处理开机广告", evidence + " · 修改前会保存原值。", not has_backup, bool(has_backup))
