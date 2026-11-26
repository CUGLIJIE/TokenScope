# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · **Deutsch** · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

TokenScope zeigt den Token-Verbrauch mehrerer Codex- und Claude-Code-Konten unter Windows. Das Dashboard läuft auf dem eigenen Rechner. Die Oberfläche ist auf vereinfachtem Chinesisch verfügbar.

- **Codex-Kontodaten.** Der installierte Codex-Client ruft über die ChatGPT-Anmeldung den Gesamtverbrauch und, soweit verfügbar, Tageswerte ab.
- **Lokale Daten.** Sitzungsprotokolle und JSON-/CSV-Importe liefern Eingabe-, Ausgabe- und Cache-Tokens pro Modell. Das Dashboard wertet lokale Daten und Cloud-Daten getrennt aus, um Doppelzählungen zu vermeiden.

## Schnellstart

Python 3.10 oder neuer unter Windows installieren und im Projektordner folgenden PowerShell-Befehl ausführen:

```powershell
.\start.cmd
```

Das Dashboard öffnet sich unter `http://127.0.0.1:8765`. Fehlt der Codex-Client, erscheint ein Link zur ChatGPT-Desktop-App. Die Nutzungsdaten liegen in einer lokalen SQLite-Datenbank.

Zum Ausprobieren ohne Anmeldung [usage.json](../../examples/usage.json) unter **账号与数据** (Konten und Daten) importieren. Unter **本地与导入** (Lokale und importierte Daten) den Zeitraum **全部日期** (Alle Tage) wählen.

## Tests und Build

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

Die ausführbare Windows-Datei liegt anschließend unter `dist\TokenScope.exe`.

[MIT-Lizenz](../../LICENSE)

