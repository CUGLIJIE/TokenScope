<h1 align="center">🔭 TokenScope</h1>

<p align="center">A local Windows dashboard for tracking token usage across Codex and Claude Code accounts.</p>

<div align="center">

<a href="https://github.com/CUGLIJIE/TokenScope/releases">Releases</a> · [Sample data](examples/usage.json) · [MIT License](LICENSE)

</div>

🌐 **README languages**

**English** · [简体中文](docs/readme/README.zh-CN.md) · [繁體中文](docs/readme/README.zh-TW.md) · [Español](docs/readme/README.es.md) · [Français](docs/readme/README.fr.md) · [Deutsch](docs/readme/README.de.md) · [Português (Brasil)](docs/readme/README.pt-BR.md)<br>
[Italiano](docs/readme/README.it.md) · [日本語](docs/readme/README.ja.md) · [한국어](docs/readme/README.ko.md) · [Русский](docs/readme/README.ru.md) · [العربية](docs/readme/README.ar.md) · [हिन्दी](docs/readme/README.hi.md) · [Bahasa Indonesia](docs/readme/README.id.md)

## 📊 What you can track

| View | Data source | What you can see |
| --- | --- | --- |
| **Account cloud usage** | Installed Codex client, signed in with ChatGPT | Account totals and daily usage when available |
| **Local & imported** | Codex and Claude Code session logs, or JSON/CSV imports | Input, output, and cached tokens by account and model |

TokenScope keeps cloud and local totals separate to avoid double-counting. Usage is stored in SQLite on your PC.

## 🚀 Quick start

**Windows executable.** Open `TokenScope.exe`. It includes Python.

**From source.** Install Python 3.10+ or extract the Windows x64 offline source package, which includes Python and the build tools. Run the startup script from the project folder.

```powershell
.\start.cmd
```

The dashboard opens at `http://127.0.0.1:8765`. It follows your browser’s preferred language and falls back to English. Use **Language** to save a different choice. If the Codex client is missing, the dashboard links to the ChatGPT desktop installer.

**Try it without signing in.** In **Accounts & data**, import [usage.json](examples/usage.json). Then open **Local & imported** and select **All dates**.

## 🛠️ Test and build

For a regular source checkout, install the build tool with `py -3 -m pip install PyInstaller==6.21.0`. The offline source package already includes it. Run the tests and build the executable from the project folder.

```powershell
.\test.cmd
.\build.cmd
```

The standalone Windows executable is written to `dist\TokenScope.exe`.
