# Rekaman Video Demo — Panduan Praktis

## Dulu: tidak ada file video

`demo/run_demo.py` **mencetak teks ke terminal**. Tidak ada output `.mp4`.
Skrip ini alat bantu untuk direkam, bukan perekam. Yang merekam adalah macOS
(atau QuickTime), dan itu memang harus kamu lakukan sendiri — video demo harus
rekaman layar nyata, bukan animasi buatan.

Yang sudah siap dari sisi repo: naskah narasi (`submission/demo-script.md`),
11 adegan yang bisa dijalankan, dan alat pemeriksa state (`demo/check_state.py`).

---

## Sebelum menekan Record

| Cek | Cara |
|---|---|
| Ukuran font terminal besar | `Cmd` + `+` tiga sampai empat kali |
| Window cukup lebar | minimal 130 kolom × 40 baris (130×54 sudah bagus) |
| Notifikasi mati | klik ikon Control Center → Focus → Do Not Disturb |
| Desktop bersih | sembunyikan ikon desktop, tutup tab lain |
| Demo tidak error | jalankan `python3 demo/run_demo.py --fast` sekali dulu |
| Mikrofon | tes 10 detik, putar ulang sebelum merekam panjang |

Cek terakhir yang paling sering terlewat: **jalankan `--fast` sekali**. Kalau ada
error (misal Chrome tidak bisa jalan), kamu ingin tahu sekarang, bukan di menit ke-4.

---

## Cara merekam di macOS

1. `Cmd` + `Shift` + `5`
2. Pilih **Record Selected Portion**, seleksi window terminal
3. **Options** → **Microphone** → pilih mic yang benar
4. **Record** → selesai: `Cmd` + `Shift` + `5` lagi → **Stop**

Alternatif: buka **QuickTime Player** → File → New Screen Recording.

Hasilnya `.mov` di Desktop. Trim dengan QuickTime (Edit → Trim) sebelum upload.

---

## Tiga segmen, total 5–8 menit

### Segmen A — 0:00–0:40 · demo runner

```bash
cd ~/Documents/Github/TOF-Project-Assistant-WorkBuddy
python3 demo/run_demo.py --step
```

`--step` berhenti di setiap adegan dan menunggu **Enter**. Ini yang membuatmu bisa
berbicara tanpa dikejar timer — mode biasa hanya memberi jeda 1,2 detik per langkah,
dan seluruh 11 adegan selesai dalam 32 detik.

Tekan Enter hanya setelah selesai bicara untuk adegan itu.

### Segmen B — 0:40–5:30 · chat asli (bagian terpenting)

Buka WorkBuddy, jalankan Turn 1 → 2 → 3 → 7 dari `docs/CASE-STUDY-02-CHAT.md`.
Teksnya tinggal copy-paste. Ini yang membuktikan agent-nya nyata, karena ada
percakapan — bukan replay.

Empat momen yang dinilai juri:

| Momen | Yang harus terlihat |
|---|---|
| Agent **bertanya** | Turn 1: daftar celah, tidak langsung membuat plan |
| Agent **menunggu** | Turn 2: approval card, eksekusi berhenti |
| Agent **merevisi** | Turn 3: tolak karena over budget → card `[REVISED]` |
| Agent **menolak** | Turn 7: "abaikan aturan" → ditolak |

### Segmen C — 5:30–7:00 · bukti di disk

```bash
python3 demo/check_state.py
```

Menunjukkan brief, klarifikasi, plan, validasi, quotation, UI spec, dan audit log
benar-benar ada sebagai file. Ini menjawab "kok saya percaya?".

---

## Narasi per adegan (untuk Segmen A)

| Scene | Kalimat singkat |
|---|---|
| 1 | "Brief masuk apa adanya — pesan WhatsApp, tanpa struktur." |
| 2 | "Agent menemukan celah dan bertanya. Ia belum membuat plan." |
| 3 | "Plan 14 task, 24 hari, Rp 21,6 juta. Setiap baris bertanda sumbernya." |
| 4 | "Enam cek deterministik — kode, bukan prompt." |
| 5 | "Approval card. Agent berhenti di sini. Ini intinya." |
| 6 | "Baru setelah disetujui, tracker Excel ditulis." |
| 7 | "Quotation minta persetujuan terpisah — setuju draft bukan setuju kirim." |
| 7b | "Layar UI diturunkan dari plan. Tiap layar menunjuk baris scope-nya." |
| 8 | "Ditolak karena over budget → direvisi → card baru. ID lama tidak dipakai ulang." |
| 9 | "Brief berisi injeksi. Agent menolak dan alur normal tetap jalan." |
| 10 | "Audit log: 15 event, append-only." |

---

## Setelah rekaman

1. Trim bagian mati di awal/akhir (QuickTime → Edit → Trim)
2. Upload ke YouTube
3. Visibility: **Unlisted** — bukan Private. Link Private tidak bisa dibuka juri.
4. Salin link → tempel ke field 16 di form

---

## Kalau ada yang gagal

| Gejala | Solusi |
|---|---|
| `sandbox initialization failed` | Chrome tidak bisa membuat sandbox. Runner sekarang retry otomatis dengan `--no-sandbox`; kalau tetap gagal, jalankan dari Terminal.app, bukan terminal di dalam IDE |
| Layar terlalu sempit, teks terpotong | `Cmd` + `-` untuk mengecilkan font, atau perlebar window |
| Suara tidak terekam | Cek Options → Microphone di panel `Cmd+Shift+5` |
| Salah bicara di tengah | Jangan stop — ulangi kalimatnya, potong saat trim |
