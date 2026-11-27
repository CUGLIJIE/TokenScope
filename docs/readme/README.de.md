# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · **Deutsch** · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

TokenScope zeigt die Token-Nutzung mehrerer Codex- und Claude-Code-Konten unter Windows. Das lokale Dashboard übernimmt die bevorzugte Browsersprache und verwendet sonst Englisch. Unter **Sprache** lässt sich eine andere Auswahl speichern.

- **Codex-Kontodaten.** Der installierte Codex-Client ruft über die ChatGPT-Anmeldung den Gesamtverbrauch und, soweit verfügbar, Tageswerte ab.
- **Lokale Daten.** Sitzungsprotokolle und JSON-/CSV-Importe liefern Eingabe-, Ausgabe- und Cache-Tokens pro Modell. Das Dashboard wertet lokale Daten und Cloud-Daten getrennt aus, um Doppelzählungen zu vermeiden.

## Schnellstart

Python 3.10 oder neuer unter Windows installieren und im Projektordner folgenden PowerShell-Befehl ausführen:

```powershell
.\start.cmd
```

Das Dashboard öffnet sich unter `http://127.0.0.1:8765`. Fehlt der Codex-Client, erscheint ein Link zur ChatGPT-Desktop-App. Die Nutzungsdaten liegen in einer lokalen SQLite-Datenbank.

Zum Ausprobieren ohne Anmeldung [usage.json](../../examples/usage.json) unter **Konten und Daten** importieren. Unter **Lokal und importiert** den Zeitraum **Alle Daten** wählen.

## Tests und Build

Das Offline-Quellpaket für Windows x64 enthält Python und die Build-Werkzeuge. Nach dem Entpacken lassen sich die Skripte ohne Installation oder Download starten.

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

Die ausführbare Windows-Datei liegt anschließend unter `dist\TokenScope.exe`.

[MIT-Lizenz](../../LICENSE)

