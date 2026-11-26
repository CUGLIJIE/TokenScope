# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · **Español** · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

Consulta el consumo de tokens de varias cuentas de Codex y Claude Code en Windows. El panel se ejecuta en tu equipo y su interfaz está en chino simplificado.

- **Uso en la nube de Codex.** Muestra el total de la cuenta y, cuando están disponibles, los datos diarios. La sincronización usa el cliente de Codex instalado y tu sesión de ChatGPT.
- **Uso local.** Desglosa por modelo los tokens de entrada, de salida y de caché a partir de registros de sesión o archivos JSON/CSV. Los totales locales y los de la nube se muestran por separado para evitar duplicados.

## Inicio rápido

Instala Python 3.10 o posterior en Windows y ejecuta este comando en PowerShell desde la carpeta del proyecto:

```powershell
.\start.cmd
```

El panel se abre en `http://127.0.0.1:8765`. Si falta el cliente de Codex, encontrarás un enlace para instalar ChatGPT para Windows. Los datos de uso se guardan en SQLite en tu equipo.

Para probarlo sin iniciar sesión, importa [usage.json](../../examples/usage.json) en **账号与数据** (Cuentas y datos) y selecciona **本地与导入 → 全部日期** (Datos locales e importados → Todas las fechas).

## Pruebas y compilación

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

El ejecutable de Windows se crea en `dist\TokenScope.exe`.

[Licencia MIT](../../LICENSE)

