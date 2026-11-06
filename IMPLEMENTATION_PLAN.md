# TOF Project Assistant - Implementation Plan

> Roadmap implementasi bertahap dengan Hybrid Storage Architecture
> Local JSON (agent state) + Google Sheets (human tracker)

---

## Overview

Implementasi dilakukan dalam **5 Milestone** yang berurutan. Setiap milestone menghasilkan deliverable yang dapat diuji sebelum lanjut ke berikutnya.

**Prinsip**: Jangan mengimplementasikan seluruh sistem sekaligus. Bangun fondasi, uji, lalu tambahkan lapisan berikutnya.

---

## Milestone 1: Foundation & State Management

**Tujuan**: Setup infrastruktur dasar, skill skeletons, dan local JSON state management.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 1.1 | Buat directory structure | `.workbuddy-ai/skills/`, `.workbuddy-ai/state/` dengan sub-directories |
| 1.2 | Init 4 skill skeletons | `tof-orchestrator`, `tof-planner`, `tof-validator`, `tof-executor` via `init_skill.py` |
| 1.3 | Tulis SKILL.md frontmatter | Name, description yang spesifik untuk auto-trigger |
| 1.4 | Implement `state_manager.py` | CRUD untuk local JSON: project state, approval records |
| 1.5 | Implement `audit_logger.py` | Append-only JSONL audit log dengan event schema |
| 1.6 | Implement `gsheets_reader.py` | Read Google Sheets via export URL (per-tab dengan gid) |
| 1.7 | Define JSON schemas | Project, task, approval, audit event schemas di `references/` |
| 1.8 | Test: state CRUD | Create project → update state → read back → audit logged |

### Deliverable
- 4 skill directories dengan SKILL.md
- `state_manager.py` berfungsi (create/read/update JSON state)
- `audit_logger.py` berfungsi (append JSONL events)
- `gsheets_reader.py` berfungsi (read tab dari Google Sheets)
- Local state directory dengan sample data

### Files yang Dibuat

```
.workbuddy-ai/
├── skills/
│   ├── tof-orchestrator/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── state_manager.py
│   │   │   ├── audit_logger.py
│   │   │   └── gsheets_reader.py
│   │   └── references/
│   │       ├── workflow.md
│   │       └── state_schema.md
│   ├── tof-planner/
│   │   └── SKILL.md (skeleton)
│   ├── tof-validator/
│   │   └── SKILL.md (skeleton)
│   └── tof-executor/
│       └── SKILL.md (skeleton)
└── state/
    ├── projects/
    ├── pending-approvals/
    ├── approval-history/
    ├── audit-log/
    └── execution-history/
```

---

## Milestone 2: Orchestrator & Planner

**Tujuan**: Orchestrator bisa menerima input, Planner menghasilkan WBS, hasil disimpan di local JSON.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 2.1 | Tulis SKILL.md `tof-orchestrator` | Workflow lengkap: receive → route → manage lifecycle |
| 2.2 | Tulis SKILL.md `tof-planner` | Decompose project brief → task list → dependencies |
| 2.3 | Implement `wbs_generator.py` | Parse brief, generate structured task plan |
| 2.4 | Define task templates | `references/task_templates.md` untuk project types umum |
| 2.5 | Test: end-to-end planning | Brief → Planner generates WBS → saved to local JSON → audit logged |

### Deliverable
- Orchestrator dapat menerima project brief
- Planner menghasilkan structured WBS (JSON)
- State tersimpan di `state/projects/{id}.json`
- Audit event `plan_created` tercatat

---

## Milestone 3: Validator & Approval Gate

**Tujuan**: Validator assess risk, approval gate berfungsi untuk Google Sheets operations.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 3.1 | Tulis SKILL.md `tof-validator` | Risk assessment workflow |
| 3.2 | Implement `risk_assessor.py` | Score risk berdasarkan operation type |
| 3.3 | Define risk matrix | `references/risk_matrix.md` dengan classification rules |
| 3.4 | Implement approval card | Show proposed changes (sheet, cells, current vs proposed) |
| 3.5 | Test: approval flow | High-risk task → AskUserQuestion → approved/rejected → logged |

### Deliverable
- Validator menghasilkan risk assessment per task
- Approval gate menampilkan diff yang jelas
- Approval decisions tercatat di `state/approval-history/`
- Audit events: `risk_assessed`, `approval_requested`, `approval_granted/rejected`

---

## Milestone 4: Executor & Google Sheets Sync

**Tujuan**: Executor menjalankan approved tasks, sinkronisasi ke Google Sheets dengan verification.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 4.1 | Tulis SKILL.md `tof-executor` | Execution workflow dengan sync |
| 4.2 | Implement `gsheets_sync.py` | Generate proposed changes, apply (via chosen strategy), verify |
| 4.3 | Implement read-back verification | Setelah write, read kembali untuk konfirmasi |
| 4.4 | Implement conflict detection | Compare local state vs Google Sheets, flag mismatches |
| 4.5 | Define tool routing | `references/tool_routing.md` — which skill for which task type |
| 4.6 | Test: sync flow | Approved plan → sync proposal → apply → verify → audit logged |

### Deliverable
- Executor dapat menjalankan approved tasks
- Google Sheets sync (dengan strategi yang dipilih dari `docs/google-sheets-integration.md`)
- Read-back verification
- Conflict detection dan reporting
- Audit events: `execution_*`, `gsheets_sync_*`, `conflict_detected`

---

## Milestone 5: Integration & Polish

**Tujuan**: Full workflow terintegrasi, error handling, documentation.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 5.1 | End-to-end testing | Brief → Plan → Validate → Approve → Execute → Sync → Verify |
| 5.2 | Error handling | JSON corrupt, Sheets unavailable, sync failure, conflict |
| 5.3 | Idempotency | Hindari duplikasi task saat sync diulang |
| 5.4 | Documentation | Usage guide, deployment guide |
| 5.5 | Iterate | Berdasarkan testing dan user feedback |

### Deliverable
- MVP lengkap dan teruji
- Dokumentasi penggunaan
- Error recovery procedures

---

## Dependency Graph

```
Milestone 1 (Foundation)
    │
    ├──► Milestone 2 (Orchestrator + Planner)
    │        │
    │        └──► Milestone 3 (Validator + Approval)
    │                 │
    │                 └──► Milestone 4 (Executor + Sync)
    │                          │
    │                          └──► Milestone 5 (Integration)
    │
    └──► docs/google-sheets-integration.md (parallel, ready after M1)
```

---

## Cloud Service DB — Postponed

Cloud Service DB (PostgreSQL) **ditunda** untuk MVP. Tidak ada:
- Aktivasi Cloud Service environment
- Pembuatan PostgreSQL tables
- Autentikasi dan storage setup

Cloud Service baru dipertimbangkan ketika:
- Multi-user concurrent access diperlukan
- Akses terkontrol (RLS) diperlukan
- Skalabilitas melebihi kapasitas local JSON
- Query komplek (JOIN, aggregate) diperlukan untuk reporting

---

_Tanggal: 2026-11-06_
_Versi: 2.0 — Hybrid Storage_
