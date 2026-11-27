# TokenScope

[English](../../README.md) · **简体中文** · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

TokenScope 是 Windows 上的本地 Token 用量仪表盘，支持多个 Codex 和 Claude Code 账号。默认按浏览器的语言偏好显示，无法匹配时使用英文。可在页面顶部的「语言」菜单切换并记住选择。

- **账号云端**显示 Codex 账号历史累计和服务端提供的每日用量，通过本机 Codex 客户端和 ChatGPT 登录同步。
- **本地与导入**从会话日志或 JSON/CSV 文件按模型统计输入、输出和缓存 Token。云端与本地分别统计，避免重复计数。

## 快速开始

在 Windows 安装 Python 3.10 或更新版本，然后在项目目录打开 PowerShell 并运行：

```powershell
.\start.cmd
```

浏览器会打开 `http://127.0.0.1:8765`。缺少 Codex 客户端时，页面会提供 ChatGPT 桌面版安装入口。统计数据保存在本机 SQLite 数据库。

想先看效果，可在「账号与数据」导入 [usage.json](../../examples/usage.json)，再到「本地与导入」选择「全部日期」，无需登录。

## 测试与构建

Windows x64 离线源码包已包含 Python 和打包工具，解压后可直接运行启动、测试或打包脚本，无需安装或联网。

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

生成的 Windows 单文件程序位于 `dist\TokenScope.exe`。

[MIT 许可证](../../LICENSE)

