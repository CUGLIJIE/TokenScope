# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · **繁體中文** · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

TokenScope 是 Windows 上的本機 Token 用量儀表板，支援多個 Codex 與 Claude Code 帳號。預設跟隨瀏覽器的語言偏好，無法對應時使用英文。可在頁首的「語言」選單切換並儲存選擇。

- **雲端用量**顯示 Codex 帳號的累計用量，以及服務提供的每日用量。同步時會透過本機的 Codex 用戶端與 ChatGPT 登入狀態取得資料。
- **本機用量**可從工作階段紀錄或匯入的 JSON/CSV 檔案，依模型查看輸入、輸出與快取 Token。雲端與本機用量分開計算，避免重複加總。

## 快速開始

在 Windows 安裝 Python 3.10 或更新版本，於專案資料夾開啟 PowerShell 並執行：

```powershell
.\start.cmd
```

瀏覽器會開啟 `http://127.0.0.1:8765`。找不到 Codex 用戶端時，頁面會提供 ChatGPT 桌面版安裝連結。統計資料儲存在本機 SQLite 資料庫。

免登入試用：在「帳號與資料」匯入 [usage.json](../../examples/usage.json)，然後在「本機與匯入」將日期範圍設為「全部日期」。

## 測試與建置

Windows x64 離線原始碼套件內含 Python 與建置工具，解壓縮後可直接執行啟動、測試或建置指令，無須安裝或連線。

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

建置完成後，Windows 單檔執行檔位於 `dist\TokenScope.exe`。

[MIT 授權條款](../../LICENSE)

