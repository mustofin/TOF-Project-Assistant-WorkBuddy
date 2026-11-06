# Mock Client Brief 1 — Complete Brief (SG Garage WMS)

## Client Info
- **Name:** Budi Santoso
- **Company:** SG Garage
- **Location:** Surabaya, Indonesia
- **Phone:** 0812-3456-7890
- **Email:** budi@sggarage.com
- **PIC:** Budi Santoso (Owner)

## Background

SG Garage adalah bengkel mobil di Surabaya yang sudah berjalan 5 tahun. Saat ini pengelolaan service, customer, dan inventory masih manual menggunakan buku catatan dan Excel sederhana. Klien ingin digitalisasi dengan web app.

## Requirements

### Core Features
1. **Customer Management** — Data pelanggan (nama, kontak, kendaraan)
2. **Vehicle Management** — Data kendaraan pelanggan (merek, model, plat)
3. **Service Transactions** — Pencatatan service (jenis, status, biaya)
4. **Inventory Management** — Stok suku cadang
5. **Invoice Printing** — Cetak invoice dari transaksi service
6. **Dashboard** — Ringkasan operasional (omzet harian, service aktif)

### User Types
1. **Service Advisor** — Input transaksi service, manage customer
2. **Kasir** — Cetak invoice, manage pembayaran
3. **Kepala Bengkel** — Akses semua menu, laporan, dashboard

## Technical Info
- **Platform:** Web app
- **Frontend:** React (Vite) — sudah diinisialisasi
- **Backend:** Google Apps Script — sudah ada router dasar
- **Database:** Google Sheets — 6 tabel sudah ada (customer, vehicle, service, parts, invoice, users)
- **Hosting:** Google Sheets + Apps Script web app

## Constraints
- **Timeline:** 3-4 weeks
- **Budget:** Terjangkau (startup bengkel)
- **Team:** 1 full-stack developer
- **Platform:** Harus pakai React + Apps Script + Google Sheets

## Unclear Points
1. Autentikasi: Apakah masing-masing user punya akses berbeda?
2. Notifikasi WhatsApp: Apakah perlu untuk notifikasi service selesai?
3. Laporan bulanan: Apakah perlu untuk MVP?
4. Multi-cabang: Apakah akan ekspansi ke multiple cabang di masa depan?

## Existing Assets
- React Vite project initialized (folder `sg-garage-frontend`)
- Google Apps Script router (`Code.gs`) dengan endpoint dasar
- 6 Google Sheets tables (customer, vehicle, service, parts, invoice, users)
- Basic UI mockups (di kertas)
