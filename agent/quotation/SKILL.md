---
name: tof-quotation-generator
description: "TOF Project Assistant - Quotation Generator. Membuat dokumen quotation (penawaran harga) berdasarkan project plan dan rate card yang sudah disetujui. Menghasilkan file .docx berdasarkan template quotation yang bisa di-review oleh user, dan jika disetujui dapat dikirim via email. Trigger words: buat quotation, penawaran harga, quotation dokumen, kirim penawaran, generate quotation, buat penawaran, kirim email quotation."
agent_created: true
---

# TOF Project Assistant - Quotation Generator

## Role

Quotation Generator bertugas membuat dokumen quotation (penawaran harga) profesional berdasarkan:
- **Project plan** yang sudah divalidasi dan disetujui
- **Rate card** dari `data/rate-card.md`
- **Template quotation** dari `data/templates/Quotation_Template_Dummy.docx`

Dokumen quotation dihasilkan sebagai file .docx yang bisa di-review oleh user sebelum dikirim.

## Input

Quotation Generator menerima input dari Orchestrator:
- **Project plan** — dari `state/projects/{project-id}/plan.json`
- **Client information** — dari brief dan clarifications
- **Rate card** — dari `data/rate-card.md`
- **Company info** — nama perusahaan, kontak, logo (TOF Solusi Digital)

## Output

File `.docx` quotation yang disimpan di:
`state/projects/{project-id}/quotation/Quotation_{client-name}_{date}.docx`

## Template Structure

Template quotation (`data/templates/Quotation_Template_Dummy.docx`) memiliki struktur:

### 1. Header (Table 1: 1 row × 2 cols)
- Cell 1: [Image] — Logo perusahaan
- Cell 2: Company name (e.g., "TOF Solusi Digital")

### 2. Title Section
- "QUOTATION" (large text)
- Quote number: `{seq}/QUO/TSD/{roman-month}/{year}`
- Project name

### 3. Quotation Info (Table 2: 3 rows × 2 cols)
| Field | Value |
|-------|-------|
| Tanggal | {current date} |
| Masa berlaku | 7 hari sejak tanggal quotation |
| Disiapkan oleh | TOF Solusi Digital |

### 4. Client Info (Table 3: 3 rows × 2 cols)
| Field | Value |
|-------|-------|
| Kepada | {client organization name} |
| Telepon | {client phone} |
| PIC | {client contact person} |

### 5. Opening Letter
```
Dengan hormat,

Terima kasih atas kesempatan yang diberikan. Berikut kami sampaikan penawaran harga untuk {project name}.
```

### 6. Work Scope Table (Table 4: variable rows × 4 cols)
Columns: No | Item | Keterangan | Biaya

Items dikelompokkan by phase/category:
```
A. {Category 1} ({url/notes})
  1. {Item name} | {Description} | {Cost}
  2. {Item name} | {Description} | {Cost}

B. {Category 2} ({url/notes})
  3. {Item name} | {Description} | {Cost}

C. Bonus
  N. {Bonus item} | {Description} | GRATIS
```

### 7. Total Investment (Table 5: 1 row × 2 cols)
| TOTAL INVESTASI | Rp{total amount} |

### 8. Terbilang
"{amount in words} rupiah"

### 9. Terms (Ketentuan) — Bullet list
- Harga berlaku untuk {scope summary}
- Estimasi pengerjaan {duration} sejak uang muka diterima
- {Testing terms}
- Revisi sudah termasuk {N} kali putaran
- Garansi perbaikan bug selama {N} hari setelah serah terima
- Tidak termasuk: {exclusions}
- Permintaan di luar daftar pekerjaan akan dikonfirmasi terpisah
- {Bonus terms if any}

### 10. Payment Schedule (Table 6: variable rows × 3 cols)
Columns: Tahap | Persentase | Nominal

Default:
| Uang muka saat quotation disetujui | 50% | Rp{50% of total} |
| Pelunasan saat serah terima final | 50% | Rp{50% of total} |

### 11. Approval Section
```
Persetujuan

Dengan menandatangani quotation ini, kedua pihak menyetujui ruang lingkup, harga, dan ketentuan yang tercantum.
```

Table 7: Signature table (1 row × 2 cols)
| Pihak Klien | Penyedia Jasa |

### 12. Attachment Note
"Lampiran: {attachment description}"

## Generation Process

### Step 1: Gather Data
Baca dari state:
- `plan.json` — WBS, effort estimation, cost estimation
- `brief.json` — client info, project name
- `clarifications.json` — any clarified scope items
- `data/rate-card.md` — rates for cost calculation

### Step 2: Calculate Costs
Untuk setiap task dalam WBS:
- Hitung cost = estimated_days × daily_rate (berdasarkan role/category)
- Kelompokkan by phase/category
- Hitung total

### Step 3: Generate Quote Number
Format: `{seq:03d}/QUO/TSD/{roman-month}/{year}`
Contoh: `001/QUO/TSD/XI/2026`

### Step 4: Generate Terbilang
Konversi total amount ke kata-kata dalam Bahasa Indonesia.
Contoh: Rp12.500.000 → "dua belas juta lima ratus ribu rupiah"

### Step 5: Create Document
Gunakan template `data/templates/Quotation_Template_Dummy.docx` sebagai base:
1. Copy template ke output path
2. Replace placeholder values:
   - Company name → "TOF Solusi Digital"
   - Quote number → generated number
   - Project name → from plan
   - Date → current date
   - Client info → from brief
   - Work scope items → from WBS
   - Total → calculated total
   - Terbilang → converted amount
   - Terms → generated from project specifics
   - Payment schedule → 50/50 default or custom

### Step 6: Save Output
Simpan ke: `state/projects/{project-id}/quotation/Quotation_{client}_{date}.docx`

## Email Integration

Setelah user review quotation dan menyetujui:

### Email Preparation
- **To**: Client email (dari brief atau clarifications)
- **Subject**: `Penawaran Harga - {Project Name} - TOF Solusi Digital`
- **Body**: Email template dengan ringkasan quotation
- **Attachment**: File .docx quotation

### Email Body Template
```
Yth. {PIC Name},
{Client Organization}

Dengan hormat,

Terima kasih atas kesempatan yang diberikan. Sehubungan dengan kebutuhan {project name}, kami sampaikan penawaran harga terlampir.

Ringkasan:
- Project: {project name}
- Total Investasi: Rp{total}
- Estimasi Pengerjaan: {duration}
- Masa berlaku penawaran: 7 hari

Quotation lengkap terlampir dalam email ini. Mohon konfirmasi jika ada pertanyaan atau yang perlu didiskusikan.

Hormat kami,
TOF Solusi Digital
```

### Sending Process
1. Agent prepares email draft dengan attachment
2. Tampilkan approval card untuk pengiriman email
3. Setelah disetujui, kirim email
4. Log ke audit trail: `QUOTATION_SENT`

## Approval Requirements

Quotation generation membutuhkan approval pada tahap-tahap berikut:

| Action | Approval Required | Risk Level |
|--------|-------------------|------------|
| Generate quotation draft | Yes — show planned content | Medium |
| Send quotation via email | Yes — show email content + recipient | High |

**Quotation TIDAK boleh dikirim tanpa:
1. User review dokumen .docx
2. Explicit approval untuk pengiriman email
3. Konfirmasi alamat email penerima

## Quality Rules

- Semua biaya harus dapat ditelusuri ke WBS dan rate card
- Terbilang harus akurat dan match dengan total
- Terms harus relevan dengan project (bukan generic copy-paste)
- Client info harus dari brief/clarification, bukan dikarang
- Template structure harus diikuti persis
- Quote number harus unique dan sequential

## Output Storage

```
state/projects/{project-id}/
└── quotation/
    ├── Quotation_{client}_{date}.docx    # Generated quotation
    ├── quotation-data.json                # Source data used
    └── email-draft.json                   # Email draft (if approved to send)
```

## References

- `data/templates/Quotation_Template_Dummy.docx` — Template quotation
- `data/rate-card.md` — Rate card untuk cost calculation
- `agent/orchestrator/SKILL.md` — Orchestrator workflow
- `agent/rules/approval-policy.md` — Approval rules
