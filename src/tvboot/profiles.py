"""Evidence-backed profiles; a model name alone is never sufficient."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Profile:
    key: str
    name: str
    model: str
    codename: str
    android: str
    firmwares: tuple
    launcher: str
    evidence: str
    source: str


PROFILES = (
    Profile(
        "mftr0-os3-107", "REDMI 电视 X55 2026", "MiTV-MFTR0", "freeguy",
        "14", ("OS3.0.107.0.UFTMATV",), "4.8.413", "本项目实机验证",
        "docs/compatibility.md#redmi-电视-x55-2026",
    ),
    Profile(
        "antl0-2225", "小米电视 L43M7-EA", "MiTV-ANTL0", "starwars",
        "5.1.1", ("23.2.4.2225",), "3.38.1017", "社区实机报告",
        "https://github.com/Gathin23/cleanyourtv/blob/main/docs/devices/xiaomi-l43m7-ea-antl0.md",
    ),
    Profile(
        "mftp0-6129", "REDMI 电视 MiTV-MFTP0", "MiTV-MFTP0", "alita",
        "9", ("23.2.10.6129",), "3.49.1601", "社区实机报告",
        "https://github.com/Gathin23/cleanyourtv/blob/main/examples/redmi-mitv-mftp0/debloat.txt",
    ),
    Profile(
        "mttp0-2585", "REDMI 电视 L65R6-A", "MiTV-MTTP0", "hugo",
        "9", ("21.4.9.2585", "2585"), "3.50.1621", "社区单次开关机报告",
        "https://github.com/Gathin23/cleanyourtv/issues/1063",
    ),
)


def profile_for(info) -> Optional[Profile]:
    for profile in PROFILES:
        if (
            info.model == profile.model
            and info.codename == profile.codename
            and info.android == profile.android
            and (info.firmware in profile.firmwares or info.display in profile.firmwares)
            and info.launcher == profile.launcher
        ):
            return profile
    return None
