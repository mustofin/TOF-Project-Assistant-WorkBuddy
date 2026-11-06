# Approval Policy — TOF Project Assistant

## When Approval is Required

### Always Requires Approval (Medium-High Risk)

| Action | Risk Level | Reason |
|--------|-----------|--------|
| Write to Excel tracker | Medium | Modifies shared data |
| Create new tasks in tracker | Medium | Changes project scope visible to team |
| Update task status | Medium | Affects progress reporting |
| Delete data | High | Irreversible |
| Overwrite existing formula | High | Can break calculations |
| Bulk operations (>5 cells) | High | Large impact |
| Sync local state to tracker | Medium | Propagates changes |
| Generate BAST draft | High | Legal document |
| Mark UAT as passed | High | Project closure decision |

### Auto-Execute Allowed (Low Risk)

| Action | Risk Level | Reason |
|--------|-----------|--------|
| Read project brief | Low | Read-only |
| Read Excel tracker | Low | Read-only |
| Read local state | Low | Internal |
| Write to local state (JSON) | Low | Agent internal |
| Write to audit log | Low | Append-only, internal |
| Generate analysis/report | Low | Output only, no external change |
| Ask clarification questions | Low | Communication only |

## Approval Card Required Fields

```
Action ID:       ACT-{YYYYMMDDHHMMSS}-{seq}
Action Type:     {type}
Project Name:    {project}
Target:          {what will be changed}
Detail Changes:  {specific changes}
Sources:         {brief/clarification/assumption/ai}
Assumptions:     {assumptions used}
Expected Impact: {anticipated impact}
Approval Status: DRAFT → PENDING_APPROVAL → APPROVED/REJECTED → EXECUTED → (FAILED)
```

## Approval State Machine

```
DRAFT ──► PENDING_APPROVAL ──► APPROVED ──► EXECUTED
                        │              │
                        └──► REJECTED  └──► FAILED
```

### Valid Transitions

| From | To | Trigger |
|------|----|---------| 
| DRAFT | PENDING_APPROVAL | Agent displays card to user |
| PENDING_APPROVAL | APPROVED | User approves |
| PENDING_APPROVAL | REJECTED | User rejects |
| APPROVED | EXECUTED | Agent executes successfully |
| APPROVED | FAILED | Execution failed |
| REJECTED | DRAFT | Agent revises and resubmits (new approval needed if details change) |

### Invalid Transitions

| From | To | Why |
|------|----|-----|
| PENDING_APPROVAL | EXECUTED | Cannot skip approval |
| REJECTED | EXECUTED | Rejected = no execution |
| FAILED | EXECUTED | Must get new approval for retry |

## Scoping Rules

- Approval berlaku HANYA untuk tindakan dan detail yang ditampilkan.
- Jika detail tindakan berubah, minta approval baru.
- Approval untuk project plan TIDAK otomatis mengizinkan eksekusi task.
- Approval untuk satu task TIDAK otomatis mengizinkan task berikutnya.
- Setiap tindakan eksternal mendapat approval card terpisah.

## Remediation Loop (Reject -> Revise -> Resubmit)

Ketika approval DITOLAK (REJECTED), agent harus:

1. **Accept feedback** — Catat alasan penolakan dari user
2. **Store feedback** — Simpan di `state/projects/{project-id}/rejection-feedback.json`
3. **Revise** — Ubah plan/tindakan berdasarkan feedback:
   - Hapus atau modifikasi item yang ditolak
   - Sesuaikan scope, timeline, atau cost
   - Tandai perubahan dengan `[REVISED]` tag
4. **New approval** — Generate approval card BARU dengan:
   - Action ID baru
   - Catatan: "Revised based on feedback: {reason}"
   - Reference ke action ID sebelumnya (untuk traceability)
5. **State transition**: REJECTED -> DRAFT -> PENDING_APPROVAL (new)

**Aturan remediation:**
- Loop dapat berulang beberapa kali (tidak terbatas)
- User dapat explicitly stop loop kapan saja
- Setiap rejection dan resubmission dicatat di audit log
- Revision tidak boleh mengabaikan feedback user
- Jika feedback kontradiktif dengan brief, tanyakan klarifikasi tambahan

## Approver Identity

Jika identitas dan timestamp tersedia:
- Catat siapa yang menyetujui (username/account)
- Catat kapan persetujuan diberikan (ISO8601)

Jika tidak tersedia:
- Catat sebagai "user" dengan timestamp dari sistem
- Tetap valid untuk audit purposes

## Multiple Approvals

Jika satu operasi memerlukan multiple changes:
- Bisa digabung dalam satu approval card (jika related)
- Atau dipisah per change type
- Prioritaskan clarity untuk user
