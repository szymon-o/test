from typing import List, Dict, Optional

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def generate_excel_report(opportunities: List[Dict], output_path: str, allocation_result: Optional[Dict] = None):
    # Sort opportunities by ROI (best first)
    sorted_opportunities = sorted(
        opportunities,
        key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0,
        reverse=True
    )

    # Create allocation lookup if available
    allocation_lookup = {}
    if allocation_result and allocation_result.get('allocations'):
        for allocation in allocation_result['allocations']:
            market_id = allocation['opportunity']['market']['id']
            allocation_lookup[market_id] = allocation

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

    # Define headers with allocation columns
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

    # Add allocation columns if available
    if allocation_result:
        headers.extend([
            "Allocated Capital",
            "Bet on YES",
            "Platform YES",
            "Bet on NO",
            "Platform NO",
            "Expected Profit",
            "Allocation ROI %"
        ])

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
    action_highlight = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")

    # Fill data rows
    for idx, opp in enumerate(sorted_opportunities, 1):
        market = opp['market']
        arb = opp['arbitrage']
        best = arb['best_strategy']

        if not best:
            continue

        row = idx + 1

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

        # Add allocation columns if available
        if allocation_result:
            market_id = market['id']
            if market_id in allocation_lookup:
                allocation = allocation_lookup[market_id]
                bet_details = allocation['bet_details']

                # Allocated Capital
                cell = ws.cell(row=row, column=15, value=round(bet_details['allocated_capital'], 2))
                cell.alignment = currency_alignment
                cell.number_format = '$0.00'
                cell.border = border
                cell.fill = action_highlight

                # Bet on YES
                cell = ws.cell(row=row, column=16, value=round(bet_details['bet_yes'], 2))
                cell.alignment = currency_alignment
                cell.number_format = '$0.00'
                cell.border = border
                cell.fill = action_highlight

                # Platform YES
                cell = ws.cell(row=row, column=17, value=bet_details['platform_yes'])
                cell.alignment = center_alignment
                cell.border = border
                cell.fill = action_highlight

                # Bet on NO
                cell = ws.cell(row=row, column=18, value=round(bet_details['bet_no'], 2))
                cell.alignment = currency_alignment
                cell.number_format = '$0.00'
                cell.border = border
                cell.fill = action_highlight

                # Platform NO
                cell = ws.cell(row=row, column=19, value=bet_details['platform_no'])
                cell.alignment = center_alignment
                cell.border = border
                cell.fill = action_highlight

                # Expected Profit
                cell = ws.cell(row=row, column=20, value=round(bet_details['expected_profit'], 2))
                cell.alignment = currency_alignment
                cell.number_format = '$0.00'
                cell.border = border
                cell.fill = action_highlight

                # Allocation ROI %
                cell = ws.cell(row=row, column=21, value=round(bet_details['roi_percent'], 2))
                cell.alignment = currency_alignment
                cell.number_format = '0.00"%"'
                cell.border = border
                cell.fill = action_highlight
            else:
                # Empty cells for non-allocated opportunities
                for col in range(15, 22):
                    cell = ws.cell(row=row, column=col, value="")
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

    if allocation_result:
        column_widths.update({
            15: 15, # Allocated Capital
            16: 12, # Bet on YES
            17: 15, # Platform YES
            18: 12, # Bet on NO
            19: 15, # Platform NO
            20: 15, # Expected Profit
            21: 15  # Allocation ROI %
        })

    for col_num, width in column_widths.items():
        ws.column_dimensions[get_column_letter(col_num)].width = width

    # Freeze the header row
    ws.freeze_panes = "A2"

    # Add auto-filter to all columns
    ws.auto_filter.ref = ws.dimensions

    # Create Action Plan sheet if allocation exists
    if allocation_result and allocation_result.get('allocations'):
        _create_action_plan_sheet(wb, allocation_result)

    # Create Summary sheet if allocation exists
    if allocation_result:
        _create_summary_sheet(wb, allocation_result)

    # Save workbook
    wb.save(output_path)


def _create_action_plan_sheet(wb: Workbook, allocation_result: Dict):
    ws = wb.create_sheet("Action Plan")

    # Header styles
    title_font = Font(bold=True, size=16, color="FFFFFF")
    title_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    step_font = Font(bold=True, size=11)
    action_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Title
    ws.merge_cells('A1:E1')
    cell = ws.cell(row=1, column=1, value="CAPITAL ALLOCATION ACTION PLAN")
    cell.font = title_font
    cell.fill = title_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = border
    ws.row_dimensions[1].height = 30

    # Summary info
    row = 3
    ws.cell(row=row, column=1, value="Total Capital:").font = Font(bold=True)
    ws.cell(row=row, column=2, value=f"${allocation_result['total_capital']:.2f}")

    row += 1
    ws.cell(row=row, column=1, value="Deployed:").font = Font(bold=True)
    ws.cell(row=row, column=2, value=f"${allocation_result['total_deployed']:.2f}")

    row += 1
    ws.cell(row=row, column=1, value="Expected Profit:").font = Font(bold=True)
    ws.cell(row=row, column=2, value=f"${allocation_result['total_expected_profit']:.2f}")

    row += 1
    ws.cell(row=row, column=1, value="Overall ROI:").font = Font(bold=True)
    ws.cell(row=row, column=2, value=f"{allocation_result['overall_roi_percent']:.2f}%")

    row += 1
    ws.cell(row=row, column=1, value="Strategy:").font = Font(bold=True)
    ws.cell(row=row, column=2, value=allocation_result['strategy'])

    # Action steps
    row += 2
    ws.cell(row=row, column=1, value="Step-by-Step Betting Instructions:").font = Font(bold=True, size=14)

    row += 1
    headers = ["Step", "Market Question", "Action", "Platform", "Amount"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    step_num = 1
    for allocation in allocation_result['allocations']:
        market = allocation['opportunity']['market']
        bet_details = allocation['bet_details']

        # YES bet
        row += 1
        ws.cell(row=row, column=1, value=step_num).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=2, value=market['question']).alignment = Alignment(horizontal="left", wrap_text=True)
        ws.cell(row=row, column=3, value=f"Bet on YES").alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=4, value=bet_details['platform_yes']).alignment = Alignment(horizontal="center")
        cell = ws.cell(row=row, column=5, value=round(bet_details['bet_yes'], 2))
        cell.alignment = Alignment(horizontal="right")
        cell.number_format = '$0.00'

        for col in range(1, 6):
            ws.cell(row=row, column=col).fill = action_fill
            ws.cell(row=row, column=col).border = border

        step_num += 1

        # NO bet
        row += 1
        ws.cell(row=row, column=1, value=step_num).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=2, value=market['question']).alignment = Alignment(horizontal="left", wrap_text=True)
        ws.cell(row=row, column=3, value=f"Bet on NO").alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=4, value=bet_details['platform_no']).alignment = Alignment(horizontal="center")
        cell = ws.cell(row=row, column=5, value=round(bet_details['bet_no'], 2))
        cell.alignment = Alignment(horizontal="right")
        cell.number_format = '$0.00'

        for col in range(1, 6):
            ws.cell(row=row, column=col).fill = action_fill
            ws.cell(row=row, column=col).border = border

        step_num += 1

    # Column widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 60
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 15


def _create_summary_sheet(wb: Workbook, allocation_result: Dict):
    ws = wb.create_sheet("Summary", 0)

    # Header styles
    title_font = Font(bold=True, size=18, color="FFFFFF")
    title_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    label_font = Font(bold=True, size=12)
    value_font = Font(size=12)
    border = Border(
        left=Side(style='medium'),
        right=Side(style='medium'),
        top=Side(style='medium'),
        bottom=Side(style='medium')
    )

    # Title
    ws.merge_cells('A1:C1')
    cell = ws.cell(row=1, column=1, value="CAPITAL ALLOCATION SUMMARY")
    cell.font = title_font
    cell.fill = title_fill
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = border
    ws.row_dimensions[1].height = 35

    # Summary table
    row = 3
    summary_data = [
        ("Total Capital Available", f"${allocation_result['total_capital']:.2f}"),
        ("Capital Deployed", f"${allocation_result['total_deployed']:.2f}"),
        ("Unallocated Capital", f"${allocation_result['total_unallocated']:.2f}"),
        ("", ""),
        ("Number of Opportunities", str(allocation_result['num_opportunities'])),
        ("", ""),
        ("Total Expected Profit", f"${allocation_result['total_expected_profit']:.2f}"),
        ("Overall ROI", f"{allocation_result['overall_roi_percent']:.2f}%"),
        ("", ""),
        ("Allocation Strategy", allocation_result['strategy'].replace('_', ' ').title()),
    ]

    for label, value in summary_data:
        if label == "":
            row += 1
            continue

        cell = ws.cell(row=row, column=1, value=label)
        cell.font = label_font
        cell.alignment = Alignment(horizontal="left", vertical="center")

        cell = ws.cell(row=row, column=2, value=value)
        cell.font = value_font
        cell.alignment = Alignment(horizontal="right", vertical="center")

        # Highlight profit row
        if "Profit" in label or "ROI" in label:
            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")

        row += 1

    # Column widths
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 10
