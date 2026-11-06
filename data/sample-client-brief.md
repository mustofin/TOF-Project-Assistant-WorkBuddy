# Sample Client Brief — Aplikasi Manajemen Bengkel

## Klien
**Nama**: SG Garage  
**Pemilik**: Budi Santoso  
**Lokasi**: Surabaya, Jawa Timur  
**Kontak**: +62 812-3456-7890  

## Latar Belakang

SG Garage adalah bengkel mobil umum di Surabaya yang menangani servis rutin hingga perbaikan kompleks. Saat ini pengelolaan bengkel masih manual menggunakan buku catatan dan WhatsApp. Pemilik ingin digitalisasi operasional bengkel.

## Kebutuhan Utama

Saya butuh aplikasi untuk mengelola bengkel saya. Aplikasi ini harus bisa:

1. Mencatat pelanggan dan kendaraan mereka
2. Mencatat transaksi servis (kerja jasa + suku cadang)
3. Mengelola inventory suku cadang dan oli
4. Mencetak nota servis/invoice
5. Melihat dashboard performa bengkel

## Informasi Teknis

- **Platform**: Web app (bisa dibuka di browser HP dan laptop)
- **Database**: Google Sheets (saya sudah punya struktur 6 sheet: Users, Customers, Vehicles, Inventory, Transactions, Transaction_Items)
- **Backend**: Google Apps Script (sudah familiar)
- **Frontend**: React (tim kami bisa React)
- **Pengguna**: Service Advisor, Kasir, Kepala Bengkel
- **Multi-cabang**: Untuk saat ini hanya 1 cabang (SG Garage Central HQ)

## Kendala

- **Budget**: Terbatas, ini adalah project pertama kami yang digital
- **Timeline**: Idealnya selesai dalam 3-4 minggu
- **Tim**: 1 developer full-stack (familiar dengan React dan Apps Script)

## Yang Sudah Ada

- Struktur database Google Sheets sudah dirancang (6 master tables)
- DeployApps Script dasar sudah ada (doGet/doPost router)
- Frontend React Vite sudah di-init

## Yang Belum Jelas

- Apakah perlu autentikasi dengan role berbeda? (Saya punya 3 jenis user)
- Apakah perlu notifikasi WhatsApp ke pelanggan?
- Apakah perlu laporan bulanan?
- Apakah perlu multi-cabang di masa depan?
