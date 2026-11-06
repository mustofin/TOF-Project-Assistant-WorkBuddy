# Google Sheets Integration Analysis

> Analisis mendalam kemampuan, keterbatasan, dan strategi integrasi
> dengan Google Sheets workbook "Project Tracker (Gemini)"

---

## 1. Workbook Summary

| Field | Value |
|-------|-------|
| **Name** | Project Tracker (Gemini) |
| **File ID** | `12BeLPdhOC0oxhvlQZB5KvduwTj-UBb8u7ELbxVqX4Fg` |
| **URL** | https://docs.google.com/spreadsheets/d/12BeLPdhOC0oxhvlQZB5KvduwTj-UBb8u7ELbxVqX4Fg/edit |
| **Last modified** | 2026-11-01 |
| **Size** | 15,557 bytes |
| **MIME type** | application/vnd.google-apps.spreadsheet |

### Tabs Identified

| # | Tab Name | GID | Content |
|---|----------|-----|---------|
| 1 | Dashboard | 293709883 | Multi-project summary, metrics, navigation links |
| 2 | SG Garage - WMS | 0 | 34 tasks across 7 fasa, WBS untuk SG Garage project |
| 3 | Database Architecture | (via gviz) | 6 master table schemas (Users, Customers, Vehicles, Inventory, Transactions, Transaction_Items) |

---

## 2. Tab Detail: Dashboard

### Layout
- Row 1-3: Title header ("MULTI-PROJECT TRACKER & PORTFOLIO MANAGEMENT")
- Row 4-6: Summary metrics (Total Projects, Total Tasks, In Progress, Completed, Not Started, Completion Rate)
- Row 7+: Project table

### Project Table Columns

| Column | Header | Description |
|--------|--------|-------------|
| B | Project ID | PRJ-01 s/d PRJ-06 |
| C | Nama Project | Project name |
| D | Nama Sheet | Tab name for detail tasks |
| E | TOTAL TASKS | Count formula |
| F | IN PROGRESS | Count formula |
| G | COMPLETED | Count formula |
| H | NOT STARTED | Count formula |
| I | COMPLETION RATE | Percentage formula |
| J | PROGRESS CHART | Visual indicator |
| K | LINK DETAIL TASK | Hyperlink to detail sheet |

### Current Data
- PRJ-01: SG Garage - WMS (34 tasks, 0% completion)
- PRJ-02 s/d PRJ-06: Empty slots

### Formulas (Inferred)
- Metrics dihitung otomatis dari sheet detail (COUNTIF berdasarkan status)
- Panduan add project tersedia (4 steps: duplikasi sheet, update task, daftarkan di dashboard, otomatisasi metrik)

---

## 3. Tab Detail: SG Garage - WMS

### Columns (9)

| Col | Header | Type | Example |
|-----|--------|------|---------|
| A | Task ID | String | T-01 |
| B | Fase / Urutan | String | Fase 1: Core Arch & Auth |
| C | Kategori | Enum | Backend / Frontend / QA / Deployment |
| D | Deskripsi Task | Text | Setup struktur 6 sheet... |
| E | Alasan Teknis & Dependency | Text | Fondasi skema database... |
| F | Prioritas | Enum | P0-P3 |
| G | Estimasi Waktu (Hari) | String | Hari 1 - 2 |
| H | Waktu Aktual (Hari) | String | 0.5 hari |
| I | Status | Enum | Done / In Progress / Not Started |

### Task Breakdown (34 tasks)

| Fase | Tasks | Priority | Status |
|------|-------|----------|--------|
| Fase 1: Core Arch & Auth | T-01 to T-05 | P0 - Kritis | T-01 Done, rest Not Started |
| Fase 2: Manajemen Inventory | T-06 to T-12 | P1 - Tinggi | All Not Started |
| Fase 3: Data Pelanggan | T-13 to T-17 | P1 - Tinggi | All Not Started |
| Fase 4: Input Transaksi Servis | T-18 to T-23 | P0 - Kritis | All Not Started |
| Fase 5: Riwayat Servis & Cetak | T-24 to T-29 | P2 - Menengah | All Not Started |
| Fase 6: Dashboard & Optimasi | T-30 to T-32 | P2 - Menengah | All Not Started |
| Fase 7: QA (UAT) & Deploy | T-33 to T-34 | P3 - Finalisasi | All Not Started |

---

## 4. Tab Detail: Database Architecture

### 6 Master Tables

| Table | PK | FK | Volume |
|-------|----|----|--------|
| Users | user_id | - | Low (master karyawan) |
| Customers | customer_id | - | Medium (~500-2000) |
| Vehicles | vehicle_id | customer_id → Customers | Medium (1-3 per customer) |
| Inventory | part_id | - | Medium (~200-500 SKU) |
| Transactions | trx_id | customer_id, license_plate → Vehicles | High (~300-1000/month) |
| Transaction_Items | item_id | trx_id → Transactions, part_id → Inventory | Very High (3-7 per trx) |

---

## 5. Tool Capability Analysis

### 5.1 Google Drive MCP Connector

| Capability | Available | Method |
|------------|-----------|--------|
| Read file metadata | YES | `mcp__google-drive__read_file` (mode=metadata) |
| Export first worksheet as CSV | YES | `mcp__google-drive__read_file` (mode=media) |
| Search files by name | YES | `mcp__google-drive__search_files` (match=name) |
| Search files by content | YES | `mcp__google-drive__search_files` (match=full_text) |
| Read specific worksheet (non-first) | PARTIAL | Via `curl` ke export URL dengan gid parameter |
| Read via gviz API | PARTIAL | Via `curl` ke `gviz/tq?tqx=out:csv&sheet=SheetName` |
| Write cell value | **NO** | Tidak ada tool MCP untuk Google Sheets write |
| Append row | **NO** | Same as above |
| Update formula | **NO** | Same as above |
| Delete row | **NO** | Same as above |
| Create new worksheet | **NO** | Same as above |
| Batch operations | **NO** | Same as above |

### 5.2 SheetAgent (Excel Lokal)

| Capability | Available | Target |
|------------|-----------|--------|
| Resolve local Excel file | YES | `.xlsx` / `.xls` / `.csv` di disk lokal |
| Read table data | YES | Structured grid with auto-detection |
| Get/set cell ranges | YES | A1 notation, batch support |
| Run Apps Script style JS | YES | SpreadsheetApp runtime |
| Search data | YES | Text search with regex support |
| Calculate formulas | YES | Dry-run without modifying document |
| Fill formula | YES | R1C1 relative reference fill-down |
| **Google Sheets direct** | **NO** | SheetAgent only works with LOCAL files |

### 5.3 curl-Based Google Sheets Export

Google Sheets mendukung public CSV export via URL pattern:

```
https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv&gid={GID}
https://docs.google.com/spreadsheets/d/{FILE_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}
```

**Limitations**:
- Requires the sheet to be shared (view access minimum)
- Does not work for private sheets without authentication
- Returns CSV only (no formatting, no formulas, no cell colors)
- One worksheet per request

### 5.4 Authentication & Access

| Aspect | Detail |
|--------|--------|
| **Connector** | Google Drive MCP (connected via WorkBuddy) |
| **Auth method** | OAuth bearer token (encrypted in connector config) |
| **Scope** | drive.file or drive.readonly (read-only confirmed) |
| **Sheets API v4** | NOT available (would need `spreadsheets.values` scope) |
| **Write capability** | NOT available via current connector |

---

## 6. Write Strategy Analysis

Since the Google Drive connector **cannot write to Google Sheets**, we need an alternative strategy.

### Strategy A: Manual + Proposal (RECOMMENDED for MVP)

**How it works**:
1. Agent generates a **proposed changes document** (Markdown table showing: sheet, cell, current value, proposed value)
2. Agent displays this to user via `AskUserQuestion`
3. User reviews and approves
4. User manually applies changes in Google Sheets (or agent provides copy-paste ready commands)
5. Agent verifies by reading back the sheet

**Pros**:
- Zero setup, works immediately
- Full human control — nothing changes without explicit action
- No external dependencies
- Transparent audit trail

**Cons**:
- Not automated — user must manually apply
- Slower workflow

**Implementation**:
```
Agent → generate_proposal.md → AskUserQuestion → User applies manually → Agent reads back → verify
```

### Strategy B: Apps Script Web App (FUTURE)

**How it works**:
1. Deploy a Google Apps Script as a Web App (REST endpoint)
2. Script receives POST requests with cell update instructions
3. Agent calls the endpoint via `curl`
4. Script applies changes and returns confirmation

**Pros**:
- Fully automated write
- Real-time sync
- No manual intervention needed

**Cons**:
- Requires Apps Script deployment (extra setup)
- Security considerations (endpoint must be secured)
- Rate limits (Apps Script quotas)
- Additional complexity

**Implementation**:
```
Agent → curl POST to Apps Script URL → Script writes to Sheet → Returns JSON → Agent verifies
```

### Strategy C: Download-Edit-Upload (NOT RECOMMENDED)

**How it works**:
1. Download workbook as `.xlsx` via Google Drive
2. Edit locally via SheetAgent
3. Upload modified `.xlsx` back to Google Drive

**Cons**:
- Overwrites entire workbook (formulas, formatting may be lost)
- Not real-time
- Version conflict risk
- Google Sheets native features (Apps Script, formulas) may break

---

## 7. Recommended Integration Flow

### 7.1 Read Flow (Agent reads Google Sheets)

```
1. Agent needs to read project tracker
2. Call gsheets_reader.py with file_id and gid
3. gsheets_reader.py:
   a. Try mcp__google-drive__read_file (mode=media) for first worksheet
   b. OR curl export URL with specific gid for other worksheets
4. Parse CSV response
5. Return structured data (list of rows with headers)
6. Agent compares with local JSON state
7. If conflict: flag to user
```

### 7.2 Write Flow (Agent proposes changes to Google Sheets)

```
1. Agent prepares proposed changes (from Planner/Executor output)
2. Validator assesses risk level
3. If medium/high risk:
   a. Agent generates proposal document:
      - Sheet name
      - Target cells (A1 notation)
      - Current values (from last read)
      - Proposed values
      - Reason for change
   b. Agent displays via AskUserQuestion
   c. User approves/rejects/modifies
4. If approved:
   a. MVP: User applies manually, agent provides copy-paste guide
   b. FUTURE: Agent calls Apps Script endpoint
5. Agent reads back the sheet to verify changes applied
6. Agent logs result to audit log (success or failure)
7. If verification fails: report to user, preserve local state
```

### 7.3 Sync Flow (Bidirectional)

```
1. Trigger: user request OR periodic Automation
2. Read Google Sheets current state (via gsheets_reader.py)
3. Read local JSON state (via state_manager.py)
4. Compare:
   a. Tasks in local but not in Sheets → propose add
   b. Tasks in Sheets but not in local → flag for user review
   c. Status differs → propose update (with direction)
5. Generate sync proposal (diff report)
6. User approval gate
7. Apply approved changes
8. Verify read-back
9. Audit log: gsheets_sync_started, gsheets_sync_completed/failed
```

---

## 8. Conflict Resolution Rules

| Scenario | Rule |
|----------|------|
| Local has task, Sheets doesn't | Propose add to Sheets (with approval) |
| Sheets has task, local doesn't | Read into local, flag for user review |
| Status differs (local: Done, Sheets: Not Started) | **Do NOT auto-overwrite**. Show conflict, ask user |
| Cell modified by user manually | Detect via read-back mismatch, preserve Sheets value, update local |
| Formula in target cell | **Never overwrite formula**. Flag as protected, ask user |

---

## 9. Idempotency Rules

To prevent duplicate tasks when sync is repeated:

1. **Task ID matching**: Use Task ID (column A) as unique key
2. **Hash check**: Before writing, compare current cell value with last-known value
3. **Sync state tracking**: Record last-synced timestamp per task in local JSON
4. **Dry-run first**: Generate proposal without applying, show diff to user

---

## 10. Reusable Components from Existing Workbook

| Component | Reusable? | Notes |
|-----------|-----------|-------|
| Dashboard tab structure | YES | Multi-project summary works well, just add more projects |
| Project table (PRJ-01 to PRJ-06) | YES | Pattern works for registering new projects |
| Task columns (A-I) | YES | Good structure for WBS tracking |
| Auto-calculation formulas | YES | COUNTIF for status metrics works correctly |
| Database Architecture tab | YES (reference) | Keep as documentation for SG Garage project |
| Add project guide | YES | Keep as reference for PM |

### Components to Add for TOF Project Assistant

| Component | Purpose |
|-----------|---------|
| TOF-specific project sheet | New tab for TOF internal projects |
| Approval log tab | Track approval decisions (read-only mirror of local JSON) |
| Sync status column | Track last-synced timestamp per task |
| Risk level column | Show validator risk assessment |
| Agent reference column | Link to audit log entry |

---

## 11. Limitations Summary

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No write via MCP | Agent cannot update Sheets directly | Manual apply or Apps Script endpoint |
| CSV export = first worksheet only | Cannot read all tabs in one call | Fetch per-tab with gid |
| No real-time sync | Sheets can be outdated vs local | Periodic sync + conflict detection |
| No formula read | Cannot see formula behind cell value | Read computed values only |
| No cell formatting info | Cannot detect colors, borders, data validation | Structural data only via CSV |
| Rate limits on export URL | Too many requests may get throttled | Cache results, sync periodically |

---

## 12. Security Considerations

- Agent **MUST NOT** write to Google Sheets without explicit user approval
- Agent **MUST NOT** overwrite formulas or user-edited cells
- Agent **MUST** verify every write by reading back
- Agent **MUST** log all sync operations to audit log
- Agent **MUST** preserve local state if sync fails
- Agent **MUST NOT** claim success if verification fails

---

_Tanggal: 2026-11-06_
_Versi: 1.0_
