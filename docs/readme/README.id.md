# TokenScope

[English](../../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)  
[Italiano](README.it.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Русский](README.ru.md) · [العربية](README.ar.md) · [हिन्दी](README.hi.md) · **Bahasa Indonesia**

Pantau penggunaan token di beberapa akun Codex dan Claude Code pada Windows. Dasbor lokal mengikuti preferensi bahasa peramban dan memakai bahasa Inggris jika tidak ada yang cocok. Pilihan pada menu **Bahasa** akan disimpan.

- **Penggunaan cloud Codex.** Klien Codex yang terpasang menggunakan sesi ChatGPT Anda untuk mengambil total penggunaan akun serta data harian jika tersedia.
- **Penggunaan lokal.** Lihat token input, output, dan cache per model dari log sesi atau berkas JSON/CSV yang diimpor. Statistik cloud dan lokal ditampilkan terpisah agar penggunaan yang sama tidak dihitung dua kali.

## Mulai menggunakan

Pasang Python 3.10 atau yang lebih baru di Windows. Buka PowerShell di folder proyek dan jalankan:

```powershell
.\start.cmd
```

Dasbor akan terbuka di `http://127.0.0.1:8765`. Jika klien Codex belum terpasang, dasbor menyediakan tautan untuk memasang aplikasi desktop ChatGPT. Data penggunaan tersimpan di basis data SQLite pada komputer Anda.

Untuk mencoba tanpa masuk, impor [usage.json](../../examples/usage.json) di **Akun dan data**, lalu pilih **Data lokal dan impor → Semua tanggal**.

## Pengujian dan pembuatan aplikasi

Paket sumber luring Windows x64 menyertakan Python dan alat build. Ekstrak dan jalankan skrip langsung tanpa instalasi atau unduhan.

```powershell
.\test.cmd
py -3 -m pip install PyInstaller==6.21.0
.\build.cmd
```

Berkas aplikasi Windows akan tersedia di `dist\TokenScope.exe`.

[Lisensi MIT](../../LICENSE)

