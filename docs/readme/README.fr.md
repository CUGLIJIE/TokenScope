# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · **Français** · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

Suivez la consommation de tokens de plusieurs comptes Codex et Claude Code sous Windows. Le tableau de bord fonctionne sur votre ordinateur et son interface est en chinois simplifié.

- **Données du compte Codex.** Le client Codex installé utilise votre session ChatGPT pour récupérer le total du compte et, lorsqu’elles sont disponibles, les données par jour.
- **Données locales.** Les journaux de session et les fichiers JSON/CSV permettent de ventiler les tokens d’entrée, de sortie et de cache par modèle. Les totaux locaux et distants restent séparés pour éviter les doubles comptes.

## Démarrage rapide

Installez Python 3.10 ou une version ultérieure sous Windows, puis lancez cette commande dans PowerShell depuis le dossier du projet :

```powershell
.\start.cmd
```

Le tableau de bord s’ouvre à l’adresse `http://127.0.0.1:8765`. Si le client Codex est absent, un lien permet d’installer l’application de bureau ChatGPT. Les statistiques sont conservées dans une base SQLite locale.

Pour essayer sans vous connecter, importez [usage.json](../../examples/usage.json) dans **账号与数据** (Comptes et données), puis choisissez **本地与导入 → 全部日期** (Données locales et importées → Toutes les dates).

## Tests et compilation

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

L’exécutable Windows est créé dans `dist\TokenScope.exe`.

[Licence MIT](../../LICENSE)

