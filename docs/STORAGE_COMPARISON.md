# Perbandingan Alternatif Storage untuk TOF Project Assistant

> Analisis komparatif: Cloud Service DB vs JSON/Markdown vs Excel vs Google Sheets
> Tanggal: 2026-11-06

---

## 1. Alternatif yang Dibandingkan

| # | Alternatif | Deskripsi |
|---|-----------|-----------|
| A | **Cloud Service DB (PostgreSQL)** | Database managed WorkBuddy via MCP tools |
| B | **JSON/Markdown files** | Local file storage di workspace |
| C | **Excel (.xlsx)** | Spreadsheet lokal via sheetagent MCP |
| D | **Google Sheets** | Spreadsheet online, contoh: link yang diberikan |

---

## 2. Matrix Perbandingan

### 2.1 Kapabilitas Teknis

| Kriteria | Cloud Service DB | JSON/Markdown | Excel (.xlsx) | Google Sheets |
|----------|:---:|:---:|:---:|:---:|
| **Query capability** | SQL penuh (WHERE, JOIN, ORDER, LIMIT) | Read all, filter manual | Search via MCP, terbatas | Apps Script, terbatas |
| **Concurrent write** | Ya (ACID, RLS) | Tidak (race condition) | Tidak (file lock) | Ya (Google backend) |
| **Data integrity** | Schema enforcement, constraints | Tidak ada validasi | Format bebas, mudah rusak | Format bebas |
| **Relational data** | Ya (foreign keys, JOIN) | Tidak (flat) | Tidak (sheet terpisah) | Tidak (sheet terpisah) |
| **Indexing** | Ya | Tidak | Tidak | Tidak |
| **Audit trail** | Queryable via SQL (timestamp, filter) | Manual parsing | Manual parsing | Manual / version history |
| **Scalability** | Ribuan record, no problem | Lambat >100 record | OK untuk ratusan | OK untuk ribuan |
| **Programmatic access** | MCP tools langsung dari AI | Read/Write tools | MCP sheetagent | Butuh API/Apps Script |

### 2.2 Integrasi dengan WorkBuddy

| Kriteria | Cloud Service DB | JSON/Markdown | Excel (.xlsx) | Google Sheets |
|----------|:---:|:---:|:---:|:---:|
| **MCP tool tersedia** | 5 tools (list, describe, exec SQL, RLS, users) | Read/Write/Edit tools | 9 tools sheetagent | Tidak ada MCP native |
| **AI bisa query langsung** | Ya, via `exec_sql` | Ya, via Read | Ya, via `read_table` | Tidak, butuh connector |
| **AI bisa write langsung** | Ya, via `exec_sql` (write mode) | Ya, via Write/Edit | Ya, via `set_cell_range` | Tidak langsung |
| **Butuh aktivasi** | Ya (activate via UI) | Tidak | Tidak | Tidak (butuh Google account) |
| **Connector tersedia** | Built-in | N/A | Built-in (sheetagent) | Tidak ada connector WorkBuddy |

### 2.3 Fitur untuk Project Management

| Kriteria | Cloud Service DB | JSON/Markdown | Excel (.xlsx) | Google Sheets |
|----------|:---:|:---:|:---:|:---:|
| **Task tracking** | Structured, queryable | Unstructured | Tabular, terbatas | Tabular, online |
| **Approval records** | Relational (FK ke tasks) | Flat JSON | Sheet terpisah | Sheet terpisah |
| **Audit log** | Dedicated table, queryable | Manual append | Manual append | Version history |
| **Project state** | Persistent across sessions | Persistent (local) | Persistent (local) | Persistent (cloud) |
| **Reporting** | SQL aggregate queries | Manual parsing | Pivot via MCP | Built-in charts |
| **Multi-project** | Table per type, filter by project_id | File per project | Sheet/tab per project | Tab per project |
| **History per task** | Query by task_id, ORDER BY timestamp | Parse entire file | Hard to track | Version history (limited) |

### 2.4 Kelebihan & Kekurangan

#### A. Cloud Service DB (PostgreSQL)

**Kelebihan:**
- Query paling powerful: `SELECT * FROM tof_tasks WHERE project_id = X AND status = 'pending' ORDER BY priority`
- ACID compliance: tidak ada data corrupt/half-written
- Row Level Security (RLS): bisa isolate data per user
- Relational: tasks → approvals → audit_log dengan foreign keys
- MCP tools siap pakai: `exec_sql` untuk semua operasi
- AI bisa langsung query kompleks dalam satu tool call
- Scalable: ribuan tasks tanpa performance issue
- Immutable audit trail via SQL queries

**Kekurangan:**
- Perlu aktivasi environment (UI confirmation, mungkin ada quota/billing)
- One app = one environment (tidak bisa multi-DB)
- Tidak bisa diakses di luar WorkBuddy ecosystem
- Kurva belajar: perlu define schema upfront

#### B. JSON/Markdown Files

**Kelebihan:**
- Paling simple: langsung baca/tulis dengan Read/Write tools
- Tidak perpa aktivasi apa pun
- Human-readable: user bisa baca langsung
- Version control via git
- Tidak ada dependensi eksternal

**Kekurangan:**
- **Tidak ada query**: harus read entire file, filter di memory
- **Race condition**: concurrent writes bisa overwrite
- **Tidak ada schema**: data bisa inconsistent
- **Tidak relational**: semua flat, tidak ada JOIN
- **Performance**: >100 records mulai lambat
- **Audit trail manual**: harus append ke file, tidak queryable
- **Tidak scalable** untuk project management yang serius

#### C. Excel (.xlsx) Lokal

**Kelebihan:**
- Familiar untuk team: semua orang bisa buka Excel
- MCP sheetagent tersedia (9 tools)
- Visual: user bisa lihat data dalam grid
- Bisa charts dan pivot tables
- Tidak perlu aktivasi

**Kekurangan:**
- **File lock**: tidak bisa concurrent edit
- **Tidak relational**: setiap sheet terpisah, tidak ada JOIN
- **Mudah rusak**: user bisa accidentally delete/modify cell
- **Tidak ada constraints**: tidak ada data validation bawaan
- **Audit trail**: harus manual, tidak queryable
- **Query terbatas**: `search_data` MCP hanya text search, bukan SQL
- **Size limit**: file besar lambat
- **Tidak persistent across sessions** dengan baik: AI harus re-open setiap sesi

#### D. Google Sheets

**Kelebihan:**
- **Real-time collaboration**: multiple user edit bersamaan
- **Online access**: bisa diakses dari mana saja
- **Version history**: bawaan Google
- **Charts & reporting**: built-in
- **Apps Script**: programmable automation
- Familiar untuk team non-teknis

**Kekurangan:**
- **Tidak ada MCP tool native** di WorkBuddy
- **Tidak ada WorkBuddy connector** untuk Google Sheets (tidak ada di connector list)
- **AI tidak bisa query langsung**: butuh Google Sheets API atau manual copy
- **Rate limit**: Google API punya quota
- **Tidak relational**: same as Excel
- **Tidak ada ACID**: concurrent edit bisa conflict
- **Privacy**: data di Google server
- **Tidak terintegrasi** dengan WorkBuddy ecosystem

---

## 3. Analisis untuk Kebutuhan TOF Project Assistant

### 3.1 Kebutuhan Storage TOF

| Kebutuhan | Prioritas | Alternatif Terbaik |
|-----------|:---:|---------------------|
| Query task by status/project/priority | Critical | **DB** (SQL) |
| Relational: task → approval → audit | Critical | **DB** (foreign keys) |
| Concurrent read/write dari AI | High | **DB** (ACID) |
| Audit trail queryable | High | **DB** (SQL queries) |
| Persistent across sessions | High | **DB / JSON / Google Sheets** |
| AI akses langsung via MCP | High | **DB / Excel** |
| Multi-project support | Medium | **DB** (filter by project_id) |
| Human-readable backup | Medium | **JSON/Markdown** (sebagai backup) |
| Team collaboration visual | Low | **Google Sheets / Excel** |
| No activation/setup needed | Low | **JSON / Excel** |

### 3.2 Skenario Penggunaan

**Skenario 1: User bertanya "Status semua task yang pending di project X"**

| Alternatif | Cara | Kecepatan |
|-----------|------|-----------|
| Cloud DB | `SELECT * FROM tof_tasks WHERE project_id = X AND status = 'pending'` | 1 tool call |
| JSON | Read entire file → filter in memory | 2-3 tool calls |
| Excel | `search_data` → manual filter | 3-5 tool calls |
| Google Sheets | Tidak bisa langsung, butuh API | N/A tanpa connector |

**Skenario 2: Audit "Siapa yang approve task Y dan kapan?"**

| Alternatif | Cara | Kecepatan |
|-----------|------|-----------|
| Cloud DB | `SELECT * FROM tof_audit_log WHERE task_id = Y AND event_type = 'approval_granted'` | 1 tool call |
| JSON | Read file → scan semua entries | 2-3 tool calls |
| Excel | Search di sheet audit → manual scan | 3-5 tool calls |
| Google Sheets | Tidak bisa langsung | N/A |

**Skenario 3: "Berapa total task completed vs pending per project?"**

| Alternatif | Cara | Kecepatan |
|-----------|------|-----------|
| Cloud DB | `SELECT project_id, status, COUNT(*) FROM tof_tasks GROUP BY project_id, status` | 1 tool call |
| JSON | Read all → manual aggregate | 3-5 tool calls |
| Excel | Manual count atau pivot | 2-3 tool calls |
| Google Sheets | Built-in pivot table | Manual |

---

## 4. Rekomendasi: Hybrid Approach

### 4.1 Primary: Cloud Service DB

**Untuk**: Project state, task records, approvals, audit log

**Alasan**:
- Kebutuhan inti TOF adalah **relational data** (task → approval → audit)
- Query kompleks adalah **daily operation** untuk PM assistant
- Audit trail harus **queryable**, bukan hanya append
- ACID compliance untuk **data integrity**
- MCP tools siap pakai, AI bisa operasi langsung

### 4.2 Secondary: Markdown/JSON (Read-only mirror)

**Untuk**: Human-readable project summary, weekly reports

**Alasan**:
- User bisa baca tanpa query DB
- Bisa di-version control via git
- Serve sebagai **backup** jika DB unavailable
- WorkBuddy workspace memory (`MEMORY.md`) sudah menggunakan format ini

### 4.3 Tertiary: Excel (Export/Reporting only)

**Untuk**: Export data untuk sharing, stakeholder reporting

**Alasan**:
- Stakeholder non-teknis familiar dengan Excel
- Bisa generate charts untuk reporting
- **Bukan untuk operational storage**, hanya export format
- WorkBuddy punya `workbuddy-sheet-generation` skill untuk generate Excel dari DB data

### 4.4 Google Sheets: Tidak Direkomendasikan

**Alasan**:
- **Tidak ada MCP tool atau connector** WorkBuddy untuk Google Sheets
- AI tidak bisa query/write langsung
- Untuk menggunakan, butuh manual copy atau custom API integration
- **Tidak terintegrasi** dengan WorkBuddy ecosystem
- Jika butuh online collaboration, lebih baik publish app via WorkBuddy Sites

---

## 5. Implementasi Hybrid

```
┌─────────────────────────────────────────────┐
│         TOF Project Assistant Storage        │
├─────────────────────────────────────────────┤
│                                              │
│  PRIMARY: Cloud Service DB (PostgreSQL)      │
│  ├── tof_projects (project metadata)         │
│  ├── tof_tasks (task records)                │
│  ├── tof_approvals (approval records)        │
│  └── tof_audit_log (audit trail)             │
│                                              │
│  SECONDARY: Markdown files (workspace)       │
│  ├── .workbuddy-ai/memory/MEMORY.md          │
│  ├── docs/reports/project-summary.md         │
│  └── (auto-generated from DB queries)        │
│                                              │
│  TERTIARY: Excel export (on-demand)          │
│  └── docs/exports/project-report.xlsx        │
│      (generated via sheet-generation skill)  │
│                                              │
└─────────────────────────────────────────────┘
```

### Flow:
1. **All writes** → Cloud Service DB (single source of truth)
2. **Weekly/Auto** → Generate Markdown summary dari DB
3. **On-demand** → Export ke Excel untuk stakeholder sharing
4. **Git tracking** → Markdown files di-version control

---

## 6. Google Sheet Link Analysis

Link yang diberikan: `https://docs.google.com/spreadsheets/d/12BeLPdhOC0oxhvlQZB5KvduwTj-UBb8u7ELbxVqX4Fg/edit?gid=293709883#gid=293709883`

**Status**: Tidak bisa diakses (memerlukan Google login)

**Jika tetap ingin menggunakan Google Sheets sebagai reference**:
- Bisa dijadikan **template reference** untuk struktur kolom
- Bisa di-copy struktur ke Excel lokal atau DB schema
- Tapi **tidak bisa diintegrasikan langsung** sebagai operational storage untuk AI

**Jika ingin Google Sheet sebagai read-only dashboard**:
- Export dari DB ke Google Sheets secara periodik (manual atau via automation)
- Tapi ini menambah complexity tanpa nilai tambah signifikan

---

## 7. Kesimpulan

| Pertanyaan | Jawaban |
|-----------|---------|
| Alternatif terbaik untuk operational storage? | **Cloud Service DB** |
| Alternatif terbaik untuk human-readable backup? | **Markdown/JSON** |
| Alternatif terbaik untuk stakeholder reporting? | **Excel export** |
| Google Sheets worth it? | **Tidak**, tidak ada integrasi WorkBuddy |
| Excel sebagai primary storage? | **Tidak**, terbatas untuk relational data |
| JSON sebagai primary storage? | **Tidak**, tidak ada query capability |

**Rekomendasi final**: **Cloud Service DB sebagai primary + Markdown sebagai secondary + Excel sebagai export format.** Google Sheet link yang diberikan bisa dipelajari strukturnya untuk inspirasi schema, tapi tidak digunakan sebagai storage.

---

_Tanggal: 2026-11-06_
_Versi: 1.0_
