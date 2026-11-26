# TokenScope

**English** · [简体中文](docs/readme/README.zh-CN.md) · [繁體中文](docs/readme/README.zh-TW.md) · [Español](docs/readme/README.es.md) · [Français](docs/readme/README.fr.md) · [Deutsch](docs/readme/README.de.md) · [Português (Brasil)](docs/readme/README.pt-BR.md)  
[Italiano](docs/readme/README.it.md) · [日本語](docs/readme/README.ja.md) · [한국어](docs/readme/README.ko.md) · [Русский](docs/readme/README.ru.md) · [العربية](docs/readme/README.ar.md) · [हिन्दी](docs/readme/README.hi.md) · [Bahasa Indonesia](docs/readme/README.id.md)

Track Codex and Claude Code token usage across accounts on Windows. The dashboard runs locally and its interface is in Simplified Chinese.

- **Codex cloud** shows account totals and daily usage when available. Sync uses the installed Codex client and your ChatGPT sign-in.
- **Local usage** shows input, output, and cached tokens by model from session logs or JSON/CSV imports. Cloud and local totals are kept separate to avoid double-counting.

## Quick start

Install Python 3.10+ on Windows and run this command in PowerShell from the project folder:

```powershell
.\start.cmd
```

The dashboard opens at `http://127.0.0.1:8765`. If the Codex client is missing, the dashboard links to the ChatGPT desktop installer. Usage is stored in SQLite on your PC.

To try it without signing in, import [usage.json](examples/usage.json) under **账号与数据** (Accounts & data), then select **本地与导入 → 全部日期** (Local & imported → All dates).

## Test and build

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

The build produces `dist\TokenScope.exe`, a standalone Windows executable.

[MIT License](LICENSE)

