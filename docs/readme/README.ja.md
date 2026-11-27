# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · **日本語** · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

TokenScope は Windows で複数の Codex・Claude Code アカウントのトークン使用量を確認できるローカルダッシュボードです。ブラウザーの優先言語を使い、対応する言語がない場合は英語で表示します。「言語」で選択を変更して保存できます。

- **Codex のクラウド使用量**：インストール済みの Codex クライアントと ChatGPT のログイン情報を使って、アカウントの累計使用量と、取得可能な場合は日別の使用量を表示します。
- **ローカル使用量**：セッションログや JSON・CSV ファイルから、入力・出力・キャッシュのトークン数をモデル別に集計します。二重計上を避けるため、クラウドとローカルの集計は分けて表示します。

## 起動方法

Windows に Python 3.10 以降をインストールし、プロジェクトフォルダーで PowerShell を開いて実行します。

```powershell
.\start.cmd
```

ブラウザーで `http://127.0.0.1:8765` が開きます。Codex クライアントが見つからない場合は、ChatGPT デスクトップアプリのインストール先が表示されます。使用量は端末内の SQLite に保存します。

ログインせずに試すには、「アカウントとデータ」で [usage.json](../../examples/usage.json) を取り込み、「ローカル・インポート」で「全期間」を選んでください。

## テストとビルド

Windows x64 用のオフラインソースパッケージには Python とビルドツールが含まれます。展開後は追加のインストールやダウンロードなしで各スクリプトを実行できます。

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

Windows 用の実行ファイルが `dist\TokenScope.exe` に生成されます。

[MIT ライセンス](../../LICENSE)

