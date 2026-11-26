# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · **हिन्दी** · [Bahasa Indonesia](README.id.md)

TokenScope की मदद से आप Windows पर Codex और Claude Code के कई खातों में टोकन की खपत देख सकते हैं। डैशबोर्ड आपके कंप्यूटर पर चलता है और इसका इंटरफ़ेस सरलीकृत चीनी में है।

- **Codex क्लाउड:** इंस्टॉल किया गया Codex क्लाइंट आपके ChatGPT लॉगिन से खाते की कुल खपत दिखाता है। दैनिक आँकड़े उपलब्ध होने पर वे भी दिखाई देते हैं।
- **स्थानीय उपयोग:** सेशन लॉग या आयात की गई JSON/CSV फ़ाइलों से हर मॉडल के इनपुट, आउटपुट और कैश टोकन देखे जा सकते हैं। दोहरी गिनती से बचने के लिए क्लाउड और स्थानीय आँकड़े अलग रखे जाते हैं।

## शुरुआत करें

Windows पर Python 3.10 या नया संस्करण इंस्टॉल करें। प्रोजेक्ट फ़ोल्डर में PowerShell खोलें और यह कमांड चलाएँ:

```powershell
.\start.cmd
```

डैशबोर्ड `http://127.0.0.1:8765` पर खुलता है। अगर Codex क्लाइंट नहीं मिलता, तो ChatGPT डेस्कटॉप ऐप इंस्टॉल करने का लिंक दिखता है। उपयोग के आँकड़े आपके कंप्यूटर पर SQLite डेटाबेस में सहेजे जाते हैं।

बिना लॉगिन किए आज़माने के लिए **账号与数据** (खाते और डेटा) में [usage.json](../../examples/usage.json) आयात करें। फिर **本地与导入** (स्थानीय और आयातित डेटा) में **全部日期** (सभी तारीखें) चुनें।

## टेस्ट और बिल्ड

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

बिल्ड पूरा होने पर Windows की एक्ज़ीक्यूटेबल फ़ाइल `dist\TokenScope.exe` पर मिलेगी।

[MIT लाइसेंस](../../LICENSE)

