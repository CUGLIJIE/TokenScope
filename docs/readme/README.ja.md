# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · **日本語** · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

TokenScope は、複数の Codex・Claude Code アカウントのトークン使用量を Windows 上で確認できるローカルダッシュボードです。画面の表示言語は簡体字中国語です。

- **Codex のクラウド使用量**：インストール済みの Codex クライアントと ChatGPT のログイン情報を使って、アカウントの累計使用量と、取得可能な場合は日別の使用量を表示します。
- **ローカル使用量**：セッションログや JSON・CSV ファイルから、入力・出力・キャッシュのトークン数をモデル別に集計します。二重計上を避けるため、クラウドとローカルの集計は分けて表示します。

## 起動方法

Windows に Python 3.10 以降をインストールし、プロジェクトフォルダーで PowerShell を開いて実行します。

```powershell
.\start.cmd
```

ブラウザーで `http://127.0.0.1:8765` が開きます。Codex クライアントが見つからない場合は、ChatGPT デスクトップアプリのインストール先が表示されます。使用量は端末内の SQLite に保存します。

ログインせずに試すには、「账号与数据」で [usage.json](../../examples/usage.json) を読み込み、「本地与导入」で期間を「全部日期」に切り替えてください。

## テストとビルド

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

Windows 用の実行ファイルが `dist\TokenScope.exe` に生成されます。

[MIT ライセンス](../../LICENSE)

