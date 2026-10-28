# 电视开机助手

在局域网中连接小米 / REDMI 电视，检测经过验证的固件，并关闭相应的开机广告开关。提供 macOS 和 Windows 桌面版本，支持恢复本工具修改前的设置。

> 本项目是独立社区工具，与小米公司无关。支持范围取决于型号、固件和原机桌面版本；它不处理应用内广告或所有其他广告形式。

## 下载与使用

从 [Releases](https://github.com/QiushanHuang/tv-boot-ad-switch/releases) 下载适合电脑的版本，解压后打开。发布包自带 ADB，无需安装 Python 或 ADB。

1. 电视和电脑连接同一局域网。在电视「设置 → 关于」中连续按「产品型号」约 7 次，再到「设置 → 账号与安全」允许 ADB 调试。
2. 打开工具，搜索电视或输入电视 IP，点击「连接电视」。电视出现电脑调试授权提示时选择允许，再根据提示重新连接。
3. 核对型号和固件，点击「关闭开机广告」。重启电视，确认广告是否消失；完成后建议在电视设置中关闭 ADB 调试。

macOS 可能要求允许本地网络访问；如果系统阻止未签名或未公证应用，请在确认下载来源后按系统提示处理。Windows 版本需要 Microsoft Edge WebView2 运行时；如果电脑没有该运行时，可从 [Microsoft 官方页面](https://developer.microsoft.com/microsoft-edge/webview2/)安装。

## 兼容性

| 型号 | 固件 / 原机桌面 | 证据 |
| --- | --- | --- |
| REDMI 电视 X55 2026（MiTV-MFTR0） | OS3.0.107.0.UFTMATV / 4.8.413 | 项目实机：重启后用户确认无开机视频广告，开关仍关闭 |
| 小米电视 L43M7-EA（MiTV-ANTL0） | 23.2.4.2225 / 3.38.1017 | 社区报告：完整重启后广告消失 |
| REDMI 电视 MiTV-MFTP0 | 23.2.10.6129 / 3.49.1601 | 社区报告：完整重启后广告消失 |
| REDMI 电视 L65R6-A（MiTV-MTTP0） | 21.4.9.2585 / 3.50.1621 | 社区报告：一次关开机后广告消失，完整重启未独立验证 |

详细来源和匹配条件见 [兼容性与证据](docs/compatibility.md)。其他版本只进行只读检测；请不要因为型号相似就假定适用。

## 恢复和隐私

修改前，工具将原开关值保存到这台电脑；只有匹配同一电视、固件和原机桌面时才提供「恢复原设置」。如果开关本来已关闭，工具不会伪造一份恢复记录。恢复文件丢失、电视身份变化或固件升级后，自动恢复可能不可用。

工具仅在用户发起操作时搜索和连接局域网设备，不上传电视信息。恢复匹配使用本机密钥对设备标识做 HMAC；不会在恢复记录中保存原始标识。官方 ADB 使用电脑用户目录中的标准调试密钥，电视可能保留已授权电脑记录；关闭调试或撤销授权可在电视设置中完成。

## 从源码运行

需要 Python 3.12、Node.js（仅用于界面状态测试）和网络连接以准备官方 ADB。Windows 需要 WebView2。

```sh
python -m venv .venv
# 激活虚拟环境后：
python -m pip install -r requirements.txt
python scripts/prepare_adb.py --platform macos --output build/adb
python scripts/run_tests.py
node --test tests/ui-state.test.js
python main.py
```

Windows 将 `--platform macos` 改为 `--platform windows`。构建发布包可运行 `python -m PyInstaller --noconfirm TVBootAdSwitch.spec`。本地界面模拟测试使用 `python tests/preview_ui.py`，不会连接电视。

## 参与贡献

欢迎提交具体型号的验证结果；请先阅读 [贡献指南](CONTRIBUTING.md)，不要上传电视序列号、MAC 地址、账户信息、家庭 IP、调试密钥或电视系统 APK。

代码以 [MIT License](LICENSE) 开源。发布包包含 Android ADB 等第三方组件，其版权和许可见包内说明。
