from typing import List, Dict

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def generate_excel_report(opportunities: List[Dict], output_path: str):
    """Generate an Excel report with filterable columns for easy analysis."""

    # Sort opportunities by ROI (best first)
    sorted_opportunities = sorted(
        opportunities,
        key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0,
        reverse=True
    )

    # Create workbook and worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Arbitrage Opportunities"

    # Define header styles
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Define headers
    headers = [
        "Rank",
        "Market ID",
        "Question",
        "Strategy Type",
        "ROI %",
        "Profit $",
        "Total Cost $",
        "App1 YES",
        "App1 NO",
        "App2 YES",
        "App2 NO",
        "Action App1",
        "Action App2",
        "Slug"
    ]

    # Write headers
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border

    # Define data alignment and formats
    center_alignment = Alignment(horizontal="center", vertical="center")
    left_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    currency_alignment = Alignment(horizontal="right", vertical="center")

    # Fill data rows
    for idx, opp in enumerate(sorted_opportunities, 1):
        market = opp['market']
        arb = opp['arbitrage']
        best = arb['best_strategy']

        if not best:
            continue

        row = idx + 1  # +1 because row 1 is headers

        # Rank
        cell = ws.cell(row=row, column=1, value=idx)
        cell.alignment = center_alignment
        cell.border = border

        # Market ID
        cell = ws.cell(row=row, column=2, value=market['id'])
        cell.alignment = center_alignment
        cell.border = border

        # Question
        cell = ws.cell(row=row, column=3, value=market['question'])
        cell.alignment = left_alignment
        cell.border = border

        # Strategy Type
        cell = ws.cell(row=row, column=4, value=best['type'])
        cell.alignment = center_alignment
        cell.border = border

        # ROI %
        cell = ws.cell(row=row, column=5, value=round(best['roi_percent'], 2))
        cell.alignment = currency_alignment
        cell.number_format = '0.00"%"'
        cell.border = border
        # Color code: Green if > 50%, Yellow if > 10%, default otherwise
        if best['roi_percent'] > 50:
            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        elif best['roi_percent'] > 10:
            cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

        # Profit $
        cell = ws.cell(row=row, column=6, value=round(best['profit'], 3))
        cell.alignment = currency_alignment
        cell.number_format = '$0.000'
        cell.border = border

        # Total Cost $
        cell = ws.cell(row=row, column=7, value=round(best['cost'], 3))
        cell.alignment = currency_alignment
        cell.number_format = '$0.000'
        cell.border = border

        # App1 YES
        cell = ws.cell(row=row, column=8, value=round(arb['market1_yes'], 3))
        cell.alignment = currency_alignment
        cell.number_format = '$0.000'
        cell.border = border

        # App1 NO
        cell = ws.cell(row=row, column=9, value=round(arb['market1_no'], 3))
        cell.alignment = currency_alignment
        cell.number_format = '$0.000'
        cell.border = border

        # App2 YES
        cell = ws.cell(row=row, column=10, value=round(arb['market2_yes'], 3))
        cell.alignment = currency_alignment
        cell.number_format = '$0.000'
        cell.border = border

        # App2 NO
        cell = ws.cell(row=row, column=11, value=round(arb['market2_no'], 3))
        cell.alignment = currency_alignment
        cell.number_format = '$0.000'
        cell.border = border

        # Action App1
        cell = ws.cell(row=row, column=12, value=best['action_app1'])
        cell.alignment = left_alignment
        cell.border = border

        # Action App2
        cell = ws.cell(row=row, column=13, value=best['action_app2'])
        cell.alignment = left_alignment
        cell.border = border

        # Slug
        cell = ws.cell(row=row, column=14, value=market['slug'])
        cell.alignment = left_alignment
        cell.border = border

    # Auto-adjust column widths
    column_widths = {
        1: 6,   # Rank
        2: 10,  # Market ID
        3: 50,  # Question
        4: 20,  # Strategy Type
        5: 10,  # ROI %
        6: 10,  # Profit $
        7: 12,  # Total Cost $
        8: 10,  # App1 YES
        9: 10,  # App1 NO
        10: 10, # App2 YES
        11: 10, # App2 NO
        12: 25, # Action App1
        13: 25, # Action App2
        14: 40  # Slug
    }

    for col_num, width in column_widths.items():
        ws.column_dimensions[get_column_letter(col_num)].width = width

    # Freeze the header row
    ws.freeze_panes = "A2"

    # Add auto-filter to all columns
    ws.auto_filter.ref = ws.dimensions


    # Save workbook
    wb.save(output_path)