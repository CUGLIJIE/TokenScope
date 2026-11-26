# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · **한국어** · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

TokenScope는 여러 Codex 및 Claude Code 계정의 토큰 사용량을 확인하는 Windows용 로컬 대시보드입니다. 화면은 중국어 간체로 표시됩니다.

- **Codex 클라우드 사용량**은 설치된 Codex 클라이언트와 ChatGPT 로그인 정보를 이용해 계정 누적 사용량을 조회합니다. 서비스가 일별 데이터를 제공하면 날짜별 사용량도 표시합니다.
- **로컬 사용량**은 세션 로그나 JSON/CSV 파일에서 모델별 입력·출력·캐시 토큰을 집계합니다. 중복 계산을 방지하기 위해 클라우드와 로컬 사용량을 따로 표시합니다.

## 시작하기

Windows에 Python 3.10 이상을 설치한 뒤 프로젝트 폴더에서 PowerShell을 열고 다음 명령을 실행하세요.

```powershell
.\start.cmd
```

브라우저에서 `http://127.0.0.1:8765`가 열립니다. Codex 클라이언트가 없으면 ChatGPT 데스크톱 앱 설치 링크가 표시됩니다. 사용량 데이터는 컴퓨터의 SQLite 데이터베이스에 저장됩니다.

로그인 없이 사용해 보려면 **账号与数据**(계정 및 데이터)에서 [usage.json](../../examples/usage.json)을 가져온 뒤 **本地与导入**(로컬 및 가져온 데이터)에서 기간을 **全部日期**(전체 기간)로 설정하세요.

## 테스트 및 빌드

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

Windows 실행 파일은 `dist\TokenScope.exe`에 생성됩니다.

[MIT 라이선스](../../LICENSE)

