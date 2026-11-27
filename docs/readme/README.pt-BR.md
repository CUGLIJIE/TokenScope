# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Português (Brasil)**  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

Acompanhe o uso de tokens de várias contas do Codex e do Claude Code no Windows. O painel local segue os idiomas do navegador e usa inglês se nenhum for compatível. Use **Idioma** para salvar outra preferência.

- **Uso do Codex na nuvem.** O cliente Codex instalado usa sua sessão do ChatGPT para consultar o total da conta e os dados diários, quando disponíveis.
- **Uso local.** Consulte tokens de entrada, saída e cache por modelo a partir de registros de sessão ou arquivos JSON/CSV. Os totais locais e os da nuvem ficam separados para evitar contagem duplicada.

## Como começar

Instale o Python 3.10 ou superior no Windows e execute este comando no PowerShell, na pasta do projeto:

```powershell
.\start.cmd
```

O painel abre em `http://127.0.0.1:8765`. Se o cliente Codex não estiver instalado, o painel oferece um link para instalar o aplicativo do ChatGPT para Windows. Os dados de uso ficam em um banco SQLite local.

Para experimentar sem fazer login, importe [usage.json](../../examples/usage.json) em **Contas e dados** e selecione **Dados locais e importados → Todas as datas**.

## Testes e compilação

O pacote de código-fonte offline para Windows x64 inclui Python e as ferramentas de compilação. Extraia e execute os scripts diretamente, sem instalar ou baixar dependências.

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

O executável do Windows é gerado em `dist\TokenScope.exe`.

[Licença MIT](../../LICENSE)

