#!/usr/bin/env python3
"""
Build script for TOF Project Tracker Excel file.
Generates a project tracker workbook with:
  1. Dashboard tab — multi-project summary with KPIs
  2. SG Garage-WMS tab — sample project task list
  3. Settings tab — reference data (statuses, priorities, phases)

Design patterns: plan.md (task list) + dashboard.md (KPI overview)
Color scheme: Fresh Green (#70AD47) — suitable for project/task/progress
"""

from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, NamedStyle
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from datetime import date

# ==================== COLOR SCHEME (Fresh Green) ====================
HEADER_BG = "70AD47"       # Green header background
HEADER_FG = "FFFFFF"       # White header text
INPUT_BG = "E2EFDA"        # Light green for input areas
SUMMARY_BG = "548235"      # Dark green for summary
SUMMARY_FG = "FFFFFF"      # White summary text
TITLE_FG = "375623"        # Dark green for titles
CALC_BG = "F2F2F2"         # Light gray for calculated cells

# Status colors
STATUS_DONE_BG = "C6EFCE"  # Green for completed
STATUS_DONE_FG = "006100"
STATUS_PROGRESS_BG = "FFEB9C"  # Yellow for in progress
STATUS_PROGRESS_FG = "9C6500"
STATUS_OVERDUE_BG = "FFC7CE"   # Red for overdue
STATUS_OVERDUE_FG = "9C0006"
STATUS_PENDING_BG = "D9E2F3"   # Blue for not started
STATUS_PENDING_FG = "1F4E79"

# Borders
thin_border = Border(
    left=Side(style='thin', color='B0B0B0'),
    right=Side(style='thin', color='B0B0B0'),
    top=Side(style='thin', color='B0B0B0'),
    bottom=Side(style='thin', color='B0B0B0')
)

# ==================== HELPER FUNCTIONS ====================

def style_header_row(ws, row, start_col, end_col):
    """Apply header styling to a row."""
    for col in range(start_col, end_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = Font(name='Calibri', bold=True, color=HEADER_FG, size=11)
        cell.fill = PatternFill(start_color=HEADER_BG, end_color=HEADER_BG, fill_type='solid')
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border

def style_title(ws, cell_ref, text, merge_range=None):
    """Apply title styling."""
    ws[cell_ref] = text
    ws[cell_ref].font = Font(name='Calibri', bold=True, color=TITLE_FG, size=14)
    ws[cell_ref].alignment = Alignment(horizontal='center', vertical='center')
    if merge_range:
        ws.merge_cells(merge_range)

def style_input_cell(cell):
    """Style an input cell."""
    cell.fill = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type='solid')
    cell.border = thin_border
    cell.alignment = Alignment(vertical='top', wrap_text=True)

def style_calc_cell(cell):
    """Style a calculated cell."""
    cell.fill = PatternFill(start_color=CALC_BG, end_color=CALC_BG, fill_type='solid')
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center', vertical='center')

def style_summary_cell(cell):
    """Style a summary cell."""
    cell.font = Font(name='Calibri', bold=True, color=SUMMARY_FG, size=11)
    cell.fill = PatternFill(start_color=SUMMARY_BG, end_color=SUMMARY_BG, fill_type='solid')
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center', vertical='center')

# ==================== BUILD WORKBOOK ====================

wb = Workbook()

# ---- Remove default sheet ----
wb.remove(wb.active)

# ============================================================
# SHEET 1: Dashboard — Multi-Project Summary
# ============================================================
ws_dash = wb.create_sheet("Dashboard")

# Layout anchors:
# Row 1: Title
# Row 2: (spacer)
# Row 3-4: KPI cards
# Row 5: (spacer)
# Row 6: Section header "Project Summary"
# Row 7: Table headers
# Row 8+: Project data rows
# Row 13: Totals row

# --- Title ---
style_title(ws_dash, "A1", "TOF Project Assistant — Project Tracker Dashboard", "A1:H1")
ws_dash.row_dimensions[1].height = 28

# --- KPI Cards (Row 3-4) ---
# Each KPI card spans 2 columns: Row 3 = label, Row 4 = value (large font)
kpi_labels = ["Total Projects", "Active Projects", "Total Tasks", "Completed Tasks"]

for i, label in enumerate(kpi_labels):
    col_start = 1 + i * 2  # A=1, C=3, E=5, G=7
    col_end = col_start + 1

    # Label cell (row 3)
    label_cell = ws_dash.cell(row=3, column=col_start, value=label)
    label_cell.font = Font(name='Calibri', size=9, color="808080", bold=True)
    label_cell.alignment = Alignment(horizontal='center', vertical='center')
    label_cell.fill = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type='solid')
    ws_dash.merge_cells(start_row=3, start_column=col_start, end_row=3, end_column=col_end)

    # Style the merged-over cell
    ws_dash.cell(row=3, column=col_end).fill = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type='solid')

    # Value cell (row 4) — will hold formula
    val_cell = ws_dash.cell(row=4, column=col_start)
    val_cell.font = Font(name='Calibri', size=18, bold=True, color=TITLE_FG)
    val_cell.alignment = Alignment(horizontal='center', vertical='center')
    val_cell.fill = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type='solid')
    ws_dash.merge_cells(start_row=4, start_column=col_start, end_row=4, end_column=col_end)

    # Style the merged-over cell
    ws_dash.cell(row=4, column=col_end).fill = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type='solid')

ws_dash.row_dimensions[3].height = 18
ws_dash.row_dimensions[4].height = 30

# KPI formulas (will reference the project summary table below)
# Total Projects = COUNTA of project names in A8:A12
# Active Projects = COUNTIF status = Active
# Total Tasks = SUM of task count column
# Completed Tasks = SUM of completed tasks column
ws_dash["A4"] = "=COUNTA(A8:A12)"
ws_dash["C4"] = '=COUNTIF(F8:F12,"Active")'
ws_dash["E4"] = "=SUM(D8:D12)"
ws_dash["G4"] = "=SUM(E8:E12)"

# --- Section Header (Row 6) ---
ws_dash["A6"] = "Project Summary"
ws_dash["A6"].font = Font(name='Calibri', bold=True, size=12, color=TITLE_FG)
ws_dash.merge_cells("A6:H6")
ws_dash["A6"].alignment = Alignment(horizontal='left', vertical='center')

# --- Project Summary Table Headers (Row 7) ---
# Anchors: header at row 7, data rows 8-12, total at row 13
headers_dash = [
    "Project ID", "Project Name", "Client", "Total Tasks",
    "Completed Tasks", "Status", "Start Date", "Target End Date"
]
for i, h in enumerate(headers_dash, 1):
    ws_dash.cell(row=7, column=i, value=h)
style_header_row(ws_dash, 7, 1, 8)

# --- Sample project data (Row 8-12) ---
# Only one sample project (SG Garage), rest empty for future projects
sample_projects = [
    ["PRJ-SGG-001", "SG Garage - Workshop Management System", "SG Garage (Budi Santoso)",
     0, 0, "Active", date(2026, 11, 6), date(2026, 12, 4)],
    # Rows 9-12 left empty for future projects
]

for row_idx, proj in enumerate(sample_projects, 8):
    for col_idx, val in enumerate(proj, 1):
        cell = ws_dash.cell(row=row_idx, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(vertical='center', wrap_text=True)
        if col_idx in (4, 5):
            cell.alignment = Alignment(horizontal='center', vertical='center')
        if col_idx in (7, 8):
            cell.number_format = 'YYYY-MM-DD'
        if col_idx == 6:
            cell.alignment = Alignment(horizontal='center', vertical='center')

# Style empty rows (9-12) with borders
for row in range(9, 13):
    for col in range(1, 9):
        cell = ws_dash.cell(row=row, column=col)
        cell.border = thin_border
        cell.fill = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type='solid')

# --- Total Row (Row 13) ---
ws_dash["A13"] = "TOTAL"
ws_dash.merge_cells("A13:C13")
style_summary_cell(ws_dash["A13"])
ws_dash["A13"].alignment = Alignment(horizontal='center', vertical='center')

ws_dash["D13"] = "=SUM(D8:D12)"
ws_dash["E13"] = "=SUM(E8:E12)"
for col in ["D", "E"]:
    style_summary_cell(ws_dash[f"{col}13"])
    ws_dash[f"{col}13"].alignment = Alignment(horizontal='center', vertical='center')

for col in range(6, 9):
    cell = ws_dash.cell(row=13, column=col)
    cell.fill = PatternFill(start_color=SUMMARY_BG, end_color=SUMMARY_BG, fill_type='solid')
    cell.border = thin_border

# --- Column widths for Dashboard ---
col_widths_dash = {
    'A': 16, 'B': 36, 'C': 28, 'D': 12, 'E': 15, 'F': 12, 'G': 14, 'H': 14
}
for col, w in col_widths_dash.items():
    ws_dash.column_dimensions[col].width = w

# --- Freeze panes ---
ws_dash.freeze_panes = "A8"

# --- Data validation for Status column ---
dv_status_dash = DataValidation(
    type="list",
    formula1='"Active,On Hold,Completed,Cancelled"',
    allow_blank=True
)
dv_status_dash.add("F8:F12")
ws_dash.add_data_validation(dv_status_dash)

# --- Conditional formatting for Status column ---
ws_dash.conditional_formatting.add(
    "F8:F12",
    CellIsRule(operator='equal', formula=['"Active"'],
               fill=PatternFill(start_color=STATUS_PROGRESS_BG, end_color=STATUS_PROGRESS_BG, fill_type='solid'),
               font=Font(color=STATUS_PROGRESS_FG))
)
ws_dash.conditional_formatting.add(
    "F8:F12",
    CellIsRule(operator='equal', formula=['"Completed"'],
               fill=PatternFill(start_color=STATUS_DONE_BG, end_color=STATUS_DONE_BG, fill_type='solid'),
               font=Font(color=STATUS_DONE_FG))
)
ws_dash.conditional_formatting.add(
    "F8:F12",
    CellIsRule(operator='equal', formula=['"On Hold"'],
               fill=PatternFill(start_color=STATUS_PENDING_BG, end_color=STATUS_PENDING_BG, fill_type='solid'),
               font=Font(color=STATUS_PENDING_FG))
)
ws_dash.conditional_formatting.add(
    "F8:F12",
    CellIsRule(operator='equal', formula=['"Cancelled"'],
               fill=PatternFill(start_color=STATUS_OVERDUE_BG, end_color=STATUS_OVERDUE_BG, fill_type='solid'),
               font=Font(color=STATUS_OVERDUE_FG))
)

# ============================================================
# SHEET 2: SG Garage-WMS — Project Task List
# ============================================================
ws_proj = wb.create_sheet("SG Garage-WMS")

# Layout anchors:
# Row 1: Title
# Row 2: Project info (ID, Client, Status)
# Row 3: (spacer)
# Row 4: Table headers
# Row 5+: Task data rows (15 sample tasks + 5 empty input rows = rows 5-24)
# Row 25: Totals/summary

# --- Title ---
style_title(ws_proj, "A1", "SG Garage — Workshop Management System (WMS)", "A1:J1")
ws_proj.row_dimensions[1].height = 28

# --- Project Info (Row 2) ---
ws_proj["A2"] = "Project ID:"
ws_proj["A2"].font = Font(bold=True, size=10)
ws_proj["B2"] = "PRJ-SGG-001"
ws_proj["D2"] = "Client:"
ws_proj["D2"].font = Font(bold=True, size=10)
ws_proj["E2"] = "SG Garage (Budi Santoso)"
ws_proj["G2"] = "Overall Status:"
ws_proj["G2"].font = Font(bold=True, size=10)
ws_proj["H2"] = "Active"
ws_proj.merge_cells("E2:F2")

# --- Table Headers (Row 4) ---
# Columns: Task ID, Phase, Category, Task Description, Technical Reason,
#           Priority, Est. Time (days), Actual Time (days), Status, Notes
headers_proj = [
    "Task ID", "Phase", "Category", "Task Description", "Technical Reason",
    "Priority", "Est. Time (days)", "Actual Time (days)", "Status", "Notes"
]
for i, h in enumerate(headers_proj, 1):
    ws_proj.cell(row=4, column=i, value=h)
style_header_row(ws_proj, 4, 1, 10)

# --- Sample task data (Rows 5-19) — based on WBS from sample brief ---
# 15 tasks covering phases: Requirements, Design, Development, Testing, Deployment
sample_tasks = [
    # Task ID, Phase, Category, Description, Technical Reason, Priority, Est Days, Actual Days, Status, Notes
    ["TASK-001", "Requirements", "Analysis",
     "Review client brief and clarify requirements",
     "Ensure complete understanding before design phase",
     "High", 2, None, "Not Started", "[BRIEF] Need clarification on auth roles, WhatsApp notification, monthly reports"],

    ["TASK-002", "Requirements", "Analysis",
     "Define user roles and permissions (3 user types)",
     "Client has 3 user types: Service Advisor, Kasir, Kepala Bengkel",
     "High", 1, None, "Not Started", "[CLARIFIED] Need to confirm if role-based access is needed"],

    ["TASK-003", "Requirements", "Analysis",
     "Confirm scope: WhatsApp notification & monthly reports",
     "Client unsure about these features in brief",
     "Medium", 1, None, "Not Started", "[ASSUMPTION] Assume WhatsApp notification is P2, monthly report is P1"],

    ["TASK-004", "Design", "Architecture",
     "Design system architecture (React + Apps Script + Google Sheets)",
     "Client already has tech stack: React frontend, Apps Script backend, Google Sheets DB",
     "High", 2, None, "Not Started", "[BRIEF] Tech stack confirmed by client"],

    ["TASK-005", "Design", "Database",
     "Review existing Google Sheets database structure (6 master tables)",
     "Client has existing structure: Users, Customers, Vehicles, Inventory, Transactions, Transaction_Items",
     "High", 1, None, "Not Started", "[BRIEF] 6 sheets already designed"],

    ["TASK-006", "Design", "UI/UX",
     "Create wireframes for main modules (Customer, Vehicle, Service, Invoice, Dashboard)",
     "5 core modules identified from brief",
     "Medium", 3, None, "Not Started", ""],

    ["TASK-007", "Development", "Frontend",
     "Implement Customer & Vehicle management module (React)",
     "Core CRUD for customer and vehicle data",
     "High", 3, None, "Not Started", ""],

    ["TASK-008", "Development", "Frontend",
     "Implement Service transaction module (kerja jasa + suku cadang)",
     "Core business flow: service order with labor and parts",
     "High", 4, None, "Not Started", ""],

    ["TASK-009", "Development", "Frontend",
     "Implement Inventory management (suku cadang & oli)",
     "Stock tracking with auto-deduct on service completion",
     "Medium", 3, None, "Not Started", ""],

    ["TASK-010", "Development", "Frontend",
     "Implement Invoice/nota servis printing module",
     "Client needs printable invoice from service transaction",
     "Medium", 2, None, "Not Started", ""],

    ["TASK-011", "Development", "Frontend",
     "Implement Dashboard performa bengkel",
     "KPI display: revenue, service count, top services, inventory alerts",
     "Medium", 3, None, "Not Started", ""],

    ["TASK-012", "Development", "Backend",
     "Implement Apps Script API (doGet/doPost router for all modules)",
     "Client has basic router, needs full endpoint implementation",
     "High", 4, None, "Not Started", "[BRIEF] Basic doGet/doPost already exists"],

    ["TASK-013", "Testing", "QA",
     "Unit testing & integration testing",
     "Verify all modules work end-to-end",
     "High", 2, None, "Not Started", ""],

    ["TASK-014", "Testing", "UAT",
     "User Acceptance Testing with client",
     "Client validates the application meets requirements",
     "High", 2, None, "Not Started", ""],

    ["TASK-015", "Deployment", "Release",
     "Deploy to production & handover",
     "Final deployment and client handover",
     "High", 1, None, "Not Started", ""],
]

# Write sample task data
for row_idx, task in enumerate(sample_tasks, 5):
    for col_idx, val in enumerate(task, 1):
        cell = ws_proj.cell(row=row_idx, column=col_idx, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        if col_idx in (7, 8):  # Est/Actual time columns
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.number_format = '0.0'
        if col_idx == 6:  # Priority
            cell.alignment = Alignment(horizontal='center', vertical='center')
        if col_idx == 9:  # Status
            cell.alignment = Alignment(horizontal='center', vertical='center')

# --- Empty input rows (Rows 20-24) ---
for row in range(20, 25):
    for col in range(1, 11):
        cell = ws_proj.cell(row=row, column=col)
        cell.border = thin_border
        cell.fill = PatternFill(start_color=INPUT_BG, end_color=INPUT_BG, fill_type='solid')
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        if col in (7, 8, 6, 9):
            cell.alignment = Alignment(horizontal='center', vertical='center')
            if col in (7, 8):
                cell.number_format = '0.0'

# --- Summary Row (Row 25) ---
ws_proj["A25"] = "TOTAL"
ws_proj.merge_cells("A25:F25")
style_summary_cell(ws_proj["A25"])
ws_proj["A25"].alignment = Alignment(horizontal='center', vertical='center')

# Estimated time total
ws_proj["G25"] = "=SUM(G5:G24)"
style_summary_cell(ws_proj["G25"])

# Actual time total
ws_proj["H25"] = "=SUM(H5:H24)"
style_summary_cell(ws_proj["H25"])

# Completion percentage
ws_proj["I25"] = '=IF(OR(G25="",G25=0),"",H25/G25)'
style_summary_cell(ws_proj["I25"])
ws_proj["I25"].number_format = '0%'

ws_proj["J25"] = ""
cell_j25 = ws_proj.cell(row=25, column=10)
cell_j25.fill = PatternFill(start_color=SUMMARY_BG, end_color=SUMMARY_BG, fill_type='solid')
cell_j25.border = thin_border

# --- Column widths ---
col_widths_proj = {
    'A': 12,   # Task ID
    'B': 14,   # Phase
    'C': 14,   # Category
    'D': 36,   # Task Description (long text)
    'E': 32,   # Technical Reason (long text)
    'F': 10,   # Priority
    'G': 12,   # Est. Time
    'H': 12,   # Actual Time
    'I': 12,   # Status
    'J': 36,   # Notes (long text)
}
for col, w in col_widths_proj.items():
    ws_proj.column_dimensions[col].width = w

# --- Freeze panes (freeze header row + first column) ---
ws_proj.freeze_panes = "B5"

# --- Auto filter ---
ws_proj.auto_filter.ref = "A4:J24"

# --- Data validations ---
# Priority dropdown
dv_priority = DataValidation(
    type="list",
    formula1='"High,Medium,Low"',
    allow_blank=True
)
dv_priority.add("F5:F24")
ws_proj.add_data_validation(dv_priority)

# Status dropdown
dv_status = DataValidation(
    type="list",
    formula1='"Not Started,In Progress,Completed,Overdue,On Hold"',
    allow_blank=True
)
dv_status.add("I5:I24")
ws_proj.add_data_validation(dv_status)

# Phase dropdown
dv_phase = DataValidation(
    type="list",
    formula1='"Requirements,Design,Development,Testing,Deployment"',
    allow_blank=True
)
dv_phase.add("B5:B24")
ws_proj.add_data_validation(dv_phase)

# --- Conditional formatting ---
# Status column (I5:I24)
ws_proj.conditional_formatting.add(
    "I5:I24",
    CellIsRule(operator='equal', formula=['"Completed"'],
               fill=PatternFill(start_color=STATUS_DONE_BG, end_color=STATUS_DONE_BG, fill_type='solid'),
               font=Font(color=STATUS_DONE_FG, bold=True))
)
ws_proj.conditional_formatting.add(
    "I5:I24",
    CellIsRule(operator='equal', formula=['"In Progress"'],
               fill=PatternFill(start_color=STATUS_PROGRESS_BG, end_color=STATUS_PROGRESS_BG, fill_type='solid'),
               font=Font(color=STATUS_PROGRESS_FG))
)
ws_proj.conditional_formatting.add(
    "I5:I24",
    CellIsRule(operator='equal', formula=['"Overdue"'],
               fill=PatternFill(start_color=STATUS_OVERDUE_BG, end_color=STATUS_OVERDUE_BG, fill_type='solid'),
               font=Font(color=STATUS_OVERDUE_FG, bold=True))
)
ws_proj.conditional_formatting.add(
    "I5:I24",
    CellIsRule(operator='equal', formula=['"Not Started"'],
               fill=PatternFill(start_color=STATUS_PENDING_BG, end_color=STATUS_PENDING_BG, fill_type='solid'),
               font=Font(color=STATUS_PENDING_FG))
)

# Priority column (F5:F24) — High = red text
ws_proj.conditional_formatting.add(
    "F5:F24",
    CellIsRule(operator='equal', formula=['"High"'],
               fill=PatternFill(start_color=STATUS_OVERDUE_BG, end_color=STATUS_OVERDUE_BG, fill_type='solid'),
               font=Font(color=STATUS_OVERDUE_FG, bold=True))
)
ws_proj.conditional_formatting.add(
    "F5:F24",
    CellIsRule(operator='equal', formula=['"Medium"'],
               fill=PatternFill(start_color=STATUS_PROGRESS_BG, end_color=STATUS_PROGRESS_BG, fill_type='solid'),
               font=Font(color=STATUS_PROGRESS_FG))
)

# ============================================================
# SHEET 3: Settings — Reference Data
# ============================================================
ws_set = wb.create_sheet("Settings")

# Title
style_title(ws_set, "A1", "Settings & Reference Data", "A1:D1")
ws_set.row_dimensions[1].height = 24

# --- Status options ---
ws_set["A3"] = "Status Options"
ws_set["A3"].font = Font(bold=True, size=11, color=TITLE_FG)
status_options = ["Not Started", "In Progress", "Completed", "Overdue", "On Hold"]
for i, s in enumerate(status_options, 4):
    ws_set.cell(row=i, column=1, value=s).border = thin_border

# --- Priority options ---
ws_set["B3"] = "Priority Options"
ws_set["B3"].font = Font(bold=True, size=11, color=TITLE_FG)
priority_options = ["High", "Medium", "Low"]
for i, p in enumerate(priority_options, 4):
    ws_set.cell(row=i, column=2, value=p).border = thin_border

# --- Phase options ---
ws_set["C3"] = "Phase Options"
ws_set["C3"].font = Font(bold=True, size=11, color=TITLE_FG)
phase_options = ["Requirements", "Design", "Development", "Testing", "Deployment"]
for i, p in enumerate(phase_options, 4):
    ws_set.cell(row=i, column=3, value=p).border = thin_border

# --- Category options ---
ws_set["D3"] = "Category Options"
ws_set["D3"].font = Font(bold=True, size=11, color=TITLE_FG)
category_options = ["Analysis", "Architecture", "Database", "UI/UX", "Frontend", "Backend", "QA", "UAT", "Release"]
for i, c in enumerate(category_options, 4):
    ws_set.cell(row=i, column=4, value=c).border = thin_border

# --- Accountability tags reference ---
ws_set["A12"] = "Accountability Tags"
ws_set["A12"].font = Font(bold=True, size=11, color=TITLE_FG)
tags = [
    "[BRIEF] — Information from client brief",
    "[CLARIFIED] — Information from clarification with user",
    "[ASSUMPTION] — Assumption made by AI (needs confirmation)",
    "[AI RECOMMENDATION] — AI recommendation (not final decision)"
]
for i, t in enumerate(tags, 13):
    ws_set.cell(row=i, column=1, value=t).border = thin_border
    ws_set.cell(row=i, column=1).alignment = Alignment(wrap_text=True)
    ws_set.merge_cells(start_row=13+i, start_column=1, end_row=13+i, end_column=4)

# Column widths
ws_set.column_dimensions['A'].width = 20
ws_set.column_dimensions['B'].width = 20
ws_set.column_dimensions['C'].width = 20
ws_set.column_dimensions['D'].width = 20

# ============================================================
# SAVE WORKBOOK
# ============================================================
output_path = "/Users/user/Documents/Github/TOF-Project-Assistant-WorkBuddy/data/tof-project-tracker.xlsx"
wb.save(output_path)
print(f"Excel file created: {output_path}")
print(f"Sheets: {wb.sheetnames}")
