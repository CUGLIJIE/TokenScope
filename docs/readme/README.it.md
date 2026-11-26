# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
**Italiano** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

Monitora il consumo di token di più account Codex e Claude Code su Windows. Il pannello funziona sul tuo computer e l’interfaccia è in cinese semplificato.

- **Dati cloud di Codex.** Il client Codex installato utilizza la tua sessione ChatGPT per recuperare il totale dell’account e, quando disponibili, i dati giornalieri.
- **Dati locali.** I registri delle sessioni e i file JSON/CSV consentono di consultare i token di input, output e cache per modello. I totali locali e quelli del cloud sono calcolati separatamente per evitare doppi conteggi.

## Avvio rapido

Installa Python 3.10 o successivo su Windows ed esegui questo comando in PowerShell dalla cartella del progetto:

```powershell
.\start.cmd
```

Il pannello si apre su `http://127.0.0.1:8765`. Se manca il client Codex, trovi un collegamento per installare l’app desktop di ChatGPT. I dati di utilizzo sono salvati in un database SQLite locale.

Per provarlo senza accedere, importa [usage.json](../../examples/usage.json) in **账号与数据** (Account e dati) e scegli **本地与导入 → 全部日期** (Dati locali e importati → Tutte le date).

## Test e compilazione

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

Il file eseguibile per Windows viene creato in `dist\TokenScope.exe`.

[Licenza MIT](../../LICENSE)

