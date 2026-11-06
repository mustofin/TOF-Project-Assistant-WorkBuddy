# TOF Project Assistant - Architecture Document

> Accountable AI Project Management Assistant untuk TOF Solusi Digital
> Dibangun di atas WorkBuddy AI Platform

---

## 1. Analisis Workspace & Environment

### 1.1 Workspace Aktif
- **Path**: `/Users/user/Documents/Github/TOF-Project-Assistant-WorkBuddy/`
- **Status**: Fresh workspace (hanya README.md + git init)
- **Memory directory**: `.workbuddy-ai/memory/` sudah dibuat

### 1.2 WorkBuddy Version & Build
- **Version**: 5.9.4-wb.42593613.gfa0a0901.h1dfe572c384a
- **Platform**: macOS (darwin)
- **Install path**: `/Applications/WorkBuddy AI.app/`

---

## 2. Mekanisme Skills WorkBuddy (Terverifikasi)

### 2.1 Struktur Skill

```
skill-name/
├── SKILL.md              (WAJIB - YAML frontmatter + instructions)
├── .codebuddy-plugin/
│   └── plugin.json       (metadata plugin)
├── scripts/              (opsional - Python/Bash executable)
├── references/           (opsional - dokumentasi referensi)
└── assets/               (opsional - template, file output)
```

**SKILL.md frontmatter wajib:**
```yaml
---
name: skill-name           # hyphen-case, max 40 chars
description: ...           # jelaskan KAPAN skill digunakan
agent_created: true        # WAJIB untuk skill yang dibuat oleh AI
---
```

### 2.2 Lokasi Penyimpanan

| Type | Path | Scope |
|------|------|-------|
| User skill | `~/.workbuddy-ai/skills/skill-name/` | Semua project |
| Project skill | `{workspace}/.workbuddy-ai/skills/skill-name/` | Project ini saja |

### 2.3 Cara Pemanggilan Skill

- Skills **otomatis dipicu** oleh WorkBuddy berdasarkan konteks percakapan
- Matching dilakukan berdasarkan `name` dan `description` di frontmatter
- Skills yang disabled tidak akan dipicu
- Skills bisa juga dipanggil eksplisit via Skill tool

### 2.4 Pembuatan Skill

Gunakan `init_skill.py` dari skill-creator:
```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

---

## 3. Tools & Integrasi yang Tersedia

### 3.1 MCP Tools Aktif (6 Providers, 43 Tools)

| Provider | Tools | Fungsi |
|----------|-------|-------|
| **SheetAgent** | 9 | Excel/spreadsheet lokal manipulation |
| **Google Drive** | 2 | Read file metadata, export CSV (first worksheet only) |
| **WeixinPay** | 4 | WeChat payment integration |
| **Miora** | 8 | Image/video generation canvas |
| **Library** | 2 | Document library search & export |
| **TDrive** | 10 | File management (upload/download/search/delete) |

### 3.2 Google Drive Connector (TERHUBUNG)

- **Status**: Connected dengan encrypted bearer token
- **Tools tersedia**:
  - `mcp__google-drive__read_file` - Read metadata atau export sebagai CSV (first worksheet only)
  - `mcp__google-drive__search_files` - Search files by name atau full_text
- **KETERBATASAN KRITIS**:
  - Hanya bisa **READ** (metadata + CSV export first worksheet)
  - **TIDAK BISA WRITE** ke Google Sheets (no cell update, no row append)
  - CSV export hanya first worksheet, bukan seluruh workbook
  - Tidak ada akses ke Google Sheets API v4 (cells.values.batchUpdate)

### 3.3 SheetAgent (Excel Lokal)

- **9 MCP tools** untuk manipulasi file Excel/xlsx lokal
- Bisa: resolve, read_table, get/set_cell_range, run_command, search_data, calculate_formulas, fill_formula
- **HANYA untuk file lokal** — tidak bisa membuka Google Sheets langsung
- `resolve_local_excel` menerima `local_path` (absolute path ke file .xlsx di disk)

### 3.4 Connectors Lain yang Aktif

| Connector | Scope |
|-----------|-------|
| Gmail | Email send/read |
| Slack | Message read/send |

### 3.5 Audit Log System (BUILT-IN)

WorkBuddy sudah memiliki audit log system di `~/.workbuddy-ai/audit-log/`:
- Format: JSONL (JSON Lines), hash-chained, immutable
- Mencatat: file operations, command execution, config changes
- Categories: `file-safety`, `command-safety`, `config`

### 3.6 Automation System

- One-time, recurring (daily/weekly/monthly/yearly), interval (per N hours)
- Configuration via `automation_update` tool

---

## 4. Arsitektur Hybrid Storage (REVISED)

### 4.1 Design Principles

1. **Accountable**: Setiap keputusan AI tercatat dengan trace yang dapat diaudit
2. **Human-in-the-loop**: Approval gate untuk semua aksi berisiko
3. **Skill-based**: Modular, setiap komponen adalah WorkBuddy skill
4. **Dual source of truth**: Local JSON untuk agent state, Google Sheets untuk human tracker
5. **Transparent**: User selalu tahu apa yang sedang terjadi dan mengapa
6. **No silent overwrite**: Agent tidak menimpa perubahan manual user tanpa persetujuan

### 4.2 Storage Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  TOF Project Assistant                    │
│                                                          │
│  ┌──────────────┐     ┌───────────────────────────────┐ │
│  │  LOCAL JSON   │     │    GOOGLE SHEETS (REMOTE)     │ │
│  │  (Agent State)│     │   (Human-Facing Tracker)      │ │
│  │                │     │                               │ │
│  │ - Project      │     │ - Project dashboard           │ │
│  │   state        │     │ - Task list & WBS             │ │
│  │ - Pending      │     │ - Dependencies                │ │
│  │   approvals    │     │ - Assignee, priority          │ │
│  │ - Approval     │◄───►│ - Dates, status, progress     │ │
│  │   history      │     │ - Risks & blockers            │ │
│  │ - Audit log    │     │                               │ │
│  │ - Execution    │     │ Workbook: Project Tracker     │ │
│  │   history      │     │   (Gemini)                    │ │
│  │                │     │ ID: 12BeLPdhOC0oxh...         │ │
│  └──────────────┘     └───────────────────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │  CLOUD SERVICE DB — DITUNDA UNTUK MVP                ││
│  │  Dipertimbangkan jika: multi-user, akses terkontrol,  ││
│  │  skalabilitas sudah benar-benar diperlukan            ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 4.3 Local JSON State Structure

```
state/
├── projects/
│   └── {project-id}.json          # Project metadata & workflow status
├── pending-approvals/
│   └── {approval-id}.json         # Pending approval requests
├── approval-history/
│   └── {project-id}.json          # All approval decisions for a project
├── audit-log/
│   └── YYYY-MM-DD.jsonl           # Daily audit events (append-only)
└── execution-history/
    └── {project-id}.json          # Agent execution log per project
```

### 4.4 Source of Truth Rules

| Data | Source of Truth | Direction |
|------|-----------------|-----------|
| Approval state | Local JSON | Agent reads/writes locally |
| Workflow state | Local JSON | Agent internal status |
| Task list & WBS | Google Sheets | Human-facing, agent syncs to |
| Task status | Google Sheets | PM/dev updates, agent reads back |
| Audit trail | Local JSONL | Append-only, agent writes |
| Project dashboard | Google Sheets | Auto-calculated via formulas |

**Conflict resolution**:
- Jika local JSON dan Google Sheets tidak sinkron, tampilkan konflik dan minta keputusan user
- Agent TIDAK boleh diam-diam menimpa perubahan manual user di Google Sheets
- Sync bersifat **bidirectional dengan approval gate**

### 4.5 Komponen Utama

#### A. Orchestrator (Skill: `tof-orchestrator`)
- Entry point dan coordinator
- Menerima user input, menentukan jenis task
- Mendelegasikan ke Planner, Validator, atau Executor
- Mengelola lifecycle task via local JSON state
- Sinkronisasi dengan Google Sheets (dengan approval)

#### B. Planner (Skill: `tof-planner`)
- Task decomposition & scheduling
- Generate WBS dari project brief
- Output: structured task plan (JSON + proposal untuk Google Sheets)

#### C. Validator (Skill: `tof-validator`)
- Risk assessment & feasibility check
- Classify risk: low/medium/high
- Flag tasks yang memerlukan human approval
- Define approval criteria

#### D. Executor (Skill: `tof-executor`)
- Execute approved tasks
- Panggil tools/skills yang relevan
- Generate deliverables
- Sync results ke Google Sheets (dengan approval)
- Verify results dengan read-back

### 4.6 Data Flow

```
User Input
    │
    ▼
Orchestrator ────► reads/writes local JSON state
    │
    ├──► Planner ──────► generates task plan (JSON)
    │         │
    │         ▼
    ├──► Validator ────► assesses risk
    │         │
    │         ▼
    │    [Risk = low?] ─── yes ──► auto-execute (local only)
    │         │
    │         no (medium/high)
    │         │
    │         ▼
    │    Human Approval Gate (AskUserQuestion)
    │    Shows: what will change in Google Sheets
    │         │
    │    ┌────┴────┐
    │    ▼         ▼
    │  approved  rejected
    │    │         │
    │    ▼         └──► log rejection, stop
    ├──► Executor
    │    ├──► write to Google Sheets (if approved)
    │    ├──► verify by reading back
    │    └──► log to local audit
    │
    └──► Audit Log (local JSONL)
```

---

## 5. Human Approval Mechanism

### 5.1 Risk Classification

| Level | Criteria | Action |
|-------|----------|--------|
| **Low** | Read-only, info query, internal JSON write | Auto-execute |
| **Medium** | Google Sheets write, new task row, status update | Show diff, confirm |
| **High** | Delete data, overwrite formula, bulk changes, external action | Explicit approval + show exact cells |

### 5.2 Approval Flow untuk Google Sheets Operations

1. Agent menyiapkan proposed changes (which sheet, which cells, what values)
2. Validator menilai risk level
3. Orchestrator menampilkan **approval card** dengan detail:
   - Sheet name dan target cells
   - Current value vs proposed value
   - Reason for change
4. User approve/reject/modify via `AskUserQuestion`
5. Jika approved: Executor write + verify read-back
6. Jika rejected: log rejection reason, preserve local state
7. **Approval scoped per-operation**: approval untuk satu plan TIDAK otomatis mengizinkan operasi berikutnya

### 5.3 Approval Record Schema (Local JSON)

```json
{
  "approvalId": "uuid",
  "projectId": "project-id",
  "taskId": "task-id",
  "operation": "google_sheets_write|local_state_update|...",
  "riskLevel": "low|medium|high",
  "riskReasons": ["..."],
  "proposedChanges": {
    "sheet": "SG Garage - WMS",
    "cells": [{"range": "H5", "current": "Not Started", "proposed": "In Progress"}]
  },
  "approvalStatus": "auto|approved|rejected|modified",
  "approver": "user|system",
  "approvedAt": "ISO8601",
  "modifications": "...",
  "verificationResult": "success|failed|pending"
}
```

---

## 6. Audit Log Mechanism

### 6.1 Dual-Layer Audit

**Layer 1 - Built-in WorkBuddy Audit** (sudah ada):
- Lokasi: `~/.workbuddy-ai/audit-log/`
- Format: JSONL, hash-chained, immutable
- Mencatat: file operations, command execution, config changes

**Layer 2 - TOF Custom Audit** (akan dibangun):
- Lokasi: `state/audit-log/YYYY-MM-DD.jsonl` (local workspace)
- Format: JSONL, append-only
- Mencatat: business logic events (task decisions, approvals, execution, sync)

### 6.2 TOF Audit Event Schema

```json
{
  "id": "uuid",
  "timestamp": "ISO8601",
  "projectId": "project-id",
  "taskId": "task-id",
  "eventType": "task_received|plan_created|risk_assessed|approval_requested|approval_granted|approval_rejected|execution_started|execution_completed|execution_failed|gsheets_sync_started|gsheets_sync_completed|gsheets_sync_failed|conflict_detected",
  "actor": "orchestrator|planner|validator|executor|user",
  "riskLevel": "low|medium|high|null",
  "description": "...",
  "metadata": {}
}
```

### 6.3 Audit Events

| Event | Actor | Description |
|-------|-------|-------------|
| `task_received` | orchestrator | User input diterima |
| `plan_created` | planner | Task plan dihasilkan |
| `risk_assessed` | validator | Risk assessment selesai |
| `approval_requested` | orchestrator | User diminta approval |
| `approval_granted` | user | User menyetujui |
| `approval_rejected` | user | User menolak |
| `execution_started` | executor | Task mulai dijalankan |
| `execution_completed` | executor | Task selesai |
| `execution_failed` | executor | Task gagal |
| `gsheets_sync_started` | executor | Mulai sync ke Google Sheets |
| `gsheets_sync_completed` | executor | Sync berhasil + verified |
| `gsheets_sync_failed` | executor | Sync gagal, local state preserved |
| `conflict_detected` | orchestrator | Konflik local vs Google Sheets |

---

## 7. Google Sheets Workbook — Project Tracker (Gemini)

### 7.1 Workbook Info

- **Name**: Project Tracker (Gemini)
- **ID**: `12BeLPdhOC0oxhvlQZB5KvduwTj-UBb8u7ELbxVqX4Fg`
- **URL**: https://docs.google.com/spreadsheets/d/12BeLPdhOC0oxhvlQZB5KvduwTj-UBb8u7ELbxVqX4Fg/edit
- **Last modified**: 2026-11-01
- **Parent folder**: ID `1QmKdqZ-TN3kAr-xG-U8N9qsz2u6m6GS8`

### 7.2 Tabs yang Ditemukan

| Tab | GID | Status | Konten |
|-----|-----|--------|--------|
| **Dashboard** | 293709883 | Active | Multi-project summary, metrics, navigation |
| **SG Garage - WMS** | 0 | Active | 34 tasks, WBS untuk project SG Garage |
| **Database Architecture** | (unknown) | Active | 6 master table schemas untuk SG Garage DB |

### 7.3 Tab: Dashboard

**Struktur**:
- Header: "MULTI-PROJECT TRACKER & PORTFOLIO MANAGEMENT"
- Summary metrics: Total Projects (1), Total Tasks (34), In Progress (0), Completed (0), Not Started (0), Completion Rate (0.0%)
- Project table: Project ID, Nama Project, Nama Sheet, TOTAL TASKS, IN PROGRESS, COMPLETED, NOT STARTED, COMPLETION RATE, PROGRESS CHART, LINK DETAIL TASK
- 6 project slots (PRJ-01 s/d PRJ-06), hanya PRJ-01 terisi
- Panduan add project (4 steps)
- Navigation shortcuts

### 7.4 Tab: SG Garage - WMS

**Kolom** (9 columns):
| Col | Header | Sample |
|-----|--------|--------|
| A | Task ID | T-01 |
| B | Fase / Urutan | Fase 1: Core Arch & Auth |
| C | Kategori | Backend / Frontend / QA |
| D | Deskripsi Task | Setup struktur 6 sheet... |
| E | Alasan Teknis & Dependency | Fondasi skema database... |
| F | Prioritas | P0 - Kritis / P1 - Tinggi / P2 - Menengah / P3 - Finalisasi |
| G | Estimasi Waktu (Hari) | Hari 1 - 2 |
| H | Waktu Aktual (Hari) | 0.5 hari / 2 jam |
| I | Status | Done / In Progress / Not Started |

**Data**: 34 tasks across 7 fasa (T-01 s/d T-34)
**Status breakdown**: Beberapa Done, sebagian besar Not Started

### 7.5 Tab: Database Architecture

**Konten**: Spesifikasi 6 master tabel database Google Sheets untuk SG Garage:
1. **Users** — Autentikasi (user_id, username, password_hash, full_name, role, branch)
2. **Customers** — Master pelanggan (customer_id, category, name, phone, email, address, created_at)
3. **Vehicles** — Master kendaraan (vehicle_id, customer_id FK, license_plate, model, vin, engine_no)
4. **Inventory** — Katalog sparepart (part_id, name, category, stock, min_stock, buy_price, sell_price, unit)
5. **Transactions** — Header transaksi (trx_id, pkb_no, date, customer_id FK, license_plate FK, km, complaint, cause, advice, costs, advisor_name)
6. **Transaction_Items** — Rincian biaya (item_id, trx_id FK, item_name, category, part_id FK, qty, unit_price, subtotal)

---

## 8. Kemampuan & Keterbatasan Integrasi Google Sheets

### 8.1 Yang BISA Dilakukan

| Operasi | Tool | Keterbatasan |
|---------|------|--------------|
| Read file metadata | `mcp__google-drive__read_file` (mode=metadata) | Hanya metadata (name, id, modified_time) |
| Export first worksheet CSV | `mcp__google-drive__read_file` (mode=media) | Hanya worksheet pertama, bukan semua tab |
| Search files | `mcp__google-drive__search_files` | By name atau full_text |
| Export specific tab via URL | `curl` ke export URL dengan gid | Perlu tahu gid, tidak semua gid accessible |
| Read via gviz API | `curl` ke gviz/tq endpoint | By sheet name, returns CSV |

### 8.2 Yang TIDAK BISA Dilakukan

| Operasi | Status | Alternatif |
|---------|--------|------------|
| Write/update cell | TIDAK ADA TOOL | Butuh Google Sheets API v4 atau Apps Script |
| Append row | TIDAK ADA TOOL | Same as above |
| Delete row | TIDAK ADA TOOL | Same as above |
| Read semua tabs sekaligus | TIDAK ADA TOOL | Fetch per-tab dengan gid |
| Update formula | TIDAK ADA TOOL | Same as above |
| Batch operations | TIDAK ADA TOOL | Same as above |

### 8.3 Strategi Mengatasi Keterbatasan Write

Karena Google Drive connector **tidak bisa write ke Google Sheets**, ada 3 strategi yang mungkin:

| Strategi | Cara | Trade-off |
|----------|------|-----------|
| **A. Download-Edit-Upload** | Download xlsx → edit lokal via SheetAgent → upload via TDrive/Drive | File tidak real-time sync, butuh manual upload |
| **B. Apps Script Web App** | Deploy Apps Script sebagai REST endpoint, agent call via curl | Perlu setup Apps Script, extra complexity |
| **C. Manual + Proposal** | Agent generate proposed changes, user apply manual di Sheets | Paling simple tapi tidak otomatis |

**Rekomendasi MVP**: Strategi **C (Manual + Proposal)** dengan evolusi ke **B (Apps Script)** di fase berikutnya. Lihat `docs/google-sheets-integration.md` untuk detail lengkap.

### 8.4 SheetAgent vs Google Sheets

| Aspek | SheetAgent | Google Sheets |
|-------|------------|---------------|
| Target | File Excel/xlsx lokal | Cloud spreadsheet |
| Read | Full support (9 tools) | Via Google Drive CSV export only |
| Write | Full support (set_cell_range, run_command) | TIDAK ADA write support |
| Concurrency | Single user (file lock) | Multi-user real-time |
| AI integration | Excellent (MCP tools) | Limited (read-only) |
| Format | .xlsx, .xls, .csv | Google Sheets native |

---

## 9. Struktur Folder Project

```
TOF-Project-Assistant-WorkBuddy/
├── README.md
├── ARCHITECTURE.md                    # Dokumen ini
├── IMPLEMENTATION_PLAN.md             # Roadmap detail
│
├── .workbuddy-ai/
│   ├── skills/
│   │   ├── tof-orchestrator/          # Entry point & coordinator
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   ├── state_manager.py   # Local JSON state operations
│   │   │   │   ├── audit_logger.py    # JSONL audit logging
│   │   │   │   └── gsheets_reader.py  # Read Google Sheets via export URL
│   │   │   └── references/
│   │   │       ├── workflow.md        # Orchestrator workflow
│   │   │       └── state_schema.md    # JSON state schema reference
│   │   │
│   │   ├── tof-planner/               # Task decomposition
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   └── wbs_generator.py   # Work breakdown structure
│   │   │   └── references/
│   │   │       ├── planning_rules.md
│   │   │       └── task_templates.md
│   │   │
│   │   ├── tof-validator/             # Risk assessment
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   └── risk_assessor.py
│   │   │   └── references/
│   │   │       ├── risk_matrix.md
│   │   │       └── approval_policy.md
│   │   │
│   │   └── tof-executor/              # Task execution
│   │       ├── SKILL.md
│   │       ├── scripts/
│   │       │   ├── task_runner.py
│   │       │   └── gsheets_sync.py    # Sync proposal to Google Sheets
│   │       └── references/
│   │           ├── execution_rules.md
│   │           └── tool_routing.md
│   │
│   ├── memory/                        # Workspace memory
│   │   ├── MEMORY.md
│   │   └── YYYY-MM-DD.md
│   │
│   └── state/                         # Agent state (runtime)
│       ├── projects/
│       ├── pending-approvals/
│       ├── approval-history/
│       ├── audit-log/
│       └── execution-history/
│
├── docs/                              # Project documentation
│   ├── google-sheets-integration.md   # GSheets integration analysis
│   └── guides/
│       └── usage.md
│
└── tests/
    └── workflows/
```

---

## 10. Keterbatasan Teknis & Risiko

### 10.1 Keterbatasan Teridentifikasi

| Keterbatasan | Impact | Mitigasi |
|--------------|--------|----------|
| Google Drive connector READ-ONLY | Tidak bisa write ke Google Sheets via MCP | Strategi proposal + manual apply, atau Apps Script endpoint |
| CSV export hanya first worksheet | Tidak bisa baca semua tab sekaligus | Fetch per-tab dengan gid via curl |
| Skills dipicu otomatis oleh context matching | Kontrol kapan skill dipicu tidak sempurna | Description spesifik di SKILL.md |
| Local JSON tidak support concurrent write | Race condition risk | Single-writer pattern via Orchestrator |
| Tidak ada real-time sync | Google Sheets bisa outdated vs local | Periodic sync + conflict detection |

### 10.2 Risiko & Mitigasi

| Risiko | Probability | Impact | Mitigasi |
|--------|-------------|--------|----------|
| Google Sheets tidak bisa di-write otomatis | **Pasti** | High | Proposal-based approach + future Apps Script |
| Local JSON corrupt | Low | High | Backup + JSON validation + atomic writes |
| Sync conflict (local vs Sheets) | Medium | Medium | Conflict detection + user resolution |
| Skill tidak terpicu dengan benar | Medium | High | Description spesifik + testing iteratif |
| User approval bottleneck | Medium | Medium | Batch approval untuk low-risk operations |

---

## 11. Next Steps

1. **Review dokumen ini** — pastikan arsitektur hybrid sesuai visi
2. **Review `docs/google-sheets-integration.md`** — pahami keterbatasan write
3. **Review `IMPLEMENTATION_PLAN.md`** — setujui rencana milestone
4. **Pilih strategi write** — Manual+Proposal (MVP) atau Apps Script (advanced)
5. **Approve Milestone 1** — berikan persetujuan untuk mulai setup fondasi

---

_Dokumen ini akan diupdate seiring progress implementasi._
_Tanggal: 2026-11-06_
_Versi: 2.0 — Hybrid Storage Architecture_
