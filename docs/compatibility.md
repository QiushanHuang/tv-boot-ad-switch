# 兼容性与证据

自动修改必须匹配系统型号、设备代号、Android 版本、固件和原机桌面版本。匹配不代表所有广告路径都可关闭；修改后请通过实际重启验证。不同地区、更新后的固件和其他尺寸不能仅凭名称推断兼容。

## REDMI 电视 X55 2026

- `MiTV-MFTR0` / `freeguy`；Android 14；固件 `OS3.0.107.0.UFTMATV`；`com.mitv.tvhome` 4.8.413。
- 项目本机实测：原开关不存在；设置为 `0` 后，用户报告一次重启没有商业视频广告，重连后读回仍为 `0`。未验证其他固件、后续系统升级或更长时间的效果。

## 小米电视 L43M7-EA

- `MiTV-ANTL0` / `starwars`；Android 5.1.1；固件 `23.2.4.2225`；桌面 3.38.1017。
- [社区设备记录](https://github.com/Gathin23/cleanyourtv/blob/main/docs/devices/xiaomi-l43m7-ea-antl0.md)：修改开关后完整重启，用户报告广告消失；系统标志动画仍存在。广告授权界面可能改回开关，升级和恢复出厂未测试。

## REDMI 电视 MiTV-MFTP0

- `MiTV-MFTP0` / `alita`；Android 9；固件 `23.2.10.6129`；桌面 3.49.1601。
- [社区设备记录](https://github.com/Gathin23/cleanyourtv/blob/main/examples/redmi-mitv-mftp0/debloat.txt)：修改开关后完整重启，用户报告无开机广告；另有其他组件调整，因此不是独立受控实验。

## REDMI 电视 L65R6-A

- `MiTV-MTTP0` / `hugo`；Android 9；构建 `21.4.9.2585`（incremental `2585`）；桌面 3.50.1621。
- [社区报告](https://github.com/Gathin23/cleanyourtv/issues/1063)：开关读回 `0`，用户报告一次关开机后没有广告；完整重启、升级后持久性和长期使用尚未验证。

## 未匹配的设备

即使同一机型有类似固件，只要关键版本不匹配，工具仍保持只读。欢迎依据 [贡献指南](../CONTRIBUTING.md)提供无敏感信息的验证报告。
