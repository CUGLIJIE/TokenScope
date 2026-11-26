# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · **العربية** · [हिन्दी](README.hi.md) · [Bahasa Indonesia](README.id.md)

يتيح لك TokenScope متابعة استهلاك الرموز (tokens) لعدة حسابات في Codex وClaude Code على Windows. تعمل لوحة المعلومات على جهازك، وواجهتها بالصينية المبسّطة.

- **استخدام Codex السحابي:** يستعين البرنامج بعميل Codex المثبّت على جهازك وبتسجيل دخولك إلى ChatGPT لعرض إجمالي استهلاك الحساب والاستهلاك اليومي عند توفّر بياناته.
- **الاستخدام المحلي:** تعرض اللوحة رموز الإدخال والإخراج والرموز المخزّنة مؤقتًا لكل نموذج، اعتمادًا على سجلات الجلسات أو ملفات JSON وCSV المستوردة. تُعرض الإحصاءات المحلية والسحابية بشكل منفصل لتجنّب العدّ المزدوج.

## التشغيل السريع

ثبّت Python 3.10 أو إصدارًا أحدث على Windows، ثم افتح PowerShell في مجلد المشروع ونفّذ الأمر التالي:

```powershell
.\start.cmd
```

تُفتح اللوحة على `http://127.0.0.1:8765`. إذا لم تجد عميل Codex، فستعرض رابطًا لتثبيت تطبيق ChatGPT لسطح المكتب. تُحفظ بيانات الاستخدام في قاعدة SQLite على جهازك.

للتجربة دون تسجيل الدخول، استورد [usage.json](../../examples/usage.json) من **账号与数据** (الحسابات والبيانات)، ثم افتح **本地与导入** (البيانات المحلية والمستوردة) واختر **全部日期** (كل التواريخ).

## الاختبار وبناء البرنامج

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

يُنشأ ملف Windows التنفيذي في `dist\TokenScope.exe`.

[ترخيص MIT](../../LICENSE)

