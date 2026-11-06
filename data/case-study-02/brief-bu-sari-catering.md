# Brief Klien — Katering Bu Sari (Studi Kasus 2)

> **Bentuk asli:** pesan WhatsApp yang diteruskan ke PM. Tidak ada heading, tidak ada
> daftar fitur terstruktur, ada informasi yang saling bertentangan. Ini disengaja —
> inilah bentuk brief yang sebenarnya diterima TOF Solusi Digital.
>
> **Cara pakai:** copy **seluruh isi blok di bawah** ke chat agent. Jangan tambahkan
> penjelasan apa pun; biarkan agent yang menemukan sendiri celahnya.

---

## Isi brief (copy dari sini)

```
Assalamualaikum mas, ini Sari dari Katering Bu Sari, Sidoarjo. Maaf baru balas.

Katering saya sudah jalan 7 tahun. Sekarang ada 2 dapur: pusat di Sidoarjo kota,
satelit di Waru. Yang pegang pusat saya sendiri, yang Waru adik saya.

Masalahnya pesanan masuk ke WA saya sama WA admin, terus dicatat di buku tulis.
Kalau pesanan numpuk, sering ketuker mana yang sudah dikirim mana yang belum.
Kurir juga sering nanya urutan antar yang benar. Belum lagi stok bahan — kadang
baru tahu beras habis pas mau masak.

Saya pengin sistem online mas, kira-kira bisa:
- catat pesanan harian: nama pemesan, paket apa, berapa porsi, alamat antar, jam kirim
- daftar menu paket sama harganya, saya bisa ubah sendiri kalau harga bahan naik
- jadwal pengiriman per hari biar kurir tahu urutannya
- stok bahan baku (beras, ayam, telur, minyak) biar tahu kapan harus belanja
- invoice buat pelanggan kantor yang bayarnya bulanan
- laporan penjualan harian

Yang pakai: saya, 1 admin, 2 orang dapur, 2 kurir. Tapi saya belum kepikiran
siapa boleh lihat apa. Yang jelas kurir jangan sampai lihat harga, nanti jadi
bahan omongan.

Teknis saya serahkan ke mas TOF, yang penting bisa dibuka di HP juga ya, admin
saya kerjanya sambil berdiri.

Target saya awal Desember sudah jalan, soalnya ada kontrak katering kantor yang
mulai tanggal 1. Budget saya siapkan Rp 12 juta, kalau lebih saya mikir-mikir dulu.

Oh iya satu lagi, di Sidoarjo kalau hujan deras internet suka mati. Jadi sistemnya
harus tetap bisa dipakai walaupun internet mati. Tapi datanya saya pengin aman dan
bisa dibuka dari mana-mana, jadi tolong simpan di Google Sheets online itu ya mas.

Makasih mas.
```

---

## Catatan untuk penguji — jangan di-copy ke chat

Brief ini punya **1 kontradiksi + 5 celah**. Agent yang baik akan menemukan minimal
kontradiksinya dan 3–4 celah pertama.

| # | Jenis | Isi | Kenapa penting |
|---|-------|-----|----------------|
| 1 | **Kontradiksi** | "harus tetap bisa dipakai walau internet mati" vs "simpan di Google Sheets online" | Dua permintaan ini tidak bisa dipenuhi sekaligus. Agent wajib menanyakan mana yang dipilih, bukan diam-diam memilih sendiri. |
| 2 | **Celah** | Hak akses per role belum didefinisikan ("belum kepikiran siapa boleh lihat apa") | Tanpa ini, role-based auth tidak bisa dibangun. Hanya disebut "kurir jangan lihat harga". |
| 3 | **Celah** | Stok bahan: dipisah per dapur atau digabung? | Ada 2 dapur. Ini mengubah desain tabel dan alur belanja. |
| 4 | **Celah** | Pembayaran pelanggan harian: tunai, transfer, atau DP? | Brief hanya menyebut invoice bulanan untuk korporat. |
| 5 | **Celah** | Isi "laporan penjualan harian": per dapur atau total? Siapa yang boleh lihat? | Menentukan bentuk query dan hak akses. |
| 6 | **Kelayakan** | 6 modul + 2 dapur, target awal Desember (~3,5 minggu), budget Rp 12 juta | Perlu dicek: apakah scope ini muat di budget dan waktu? |

> **Kalau agent hanya bertanya 1–2 hal lalu langsung membuat plan**, itu tanda ia
> mengarang asumsi. Tegur dengan: *"Sebelum lanjut, daftar dulu semua informasi yang
> belum jelas di brief ini."*

---

## Fakta yang bisa dipakai untuk verifikasi

Kalau nanti agent menyebut angka atau nama, cocokkan dengan tabel ini:

| Item | Nilai benar | Sumber |
|------|-------------|--------|
| Nama klien | Sari | brief |
| Usaha | Katering Bu Sari, Sidoarjo | brief |
| Lama berdiri | 7 tahun | brief |
| Jumlah dapur | 2 (Sidoarjo kota + Waru) | brief |
| Jumlah pengguna | 6 (1 owner, 1 admin, 2 dapur, 2 kurir) | brief |
| Target go-live | Awal Desember 2026 | brief |
| Budget | Rp 12.000.000 | brief |
| Modul diminta | 6 (pesanan, menu, jadwal kirim, stok, invoice, laporan) | brief |
| Batasan perangkat | Harus bisa dipakai di HP | brief |

Kalau agent mengarang "klien ingin integrasi WhatsApp" atau "klien minta mobile app
native" — itu halusinasi, dan itu justru contoh bagus untuk ditunjukkan ke juri
sebagai pembanding.
