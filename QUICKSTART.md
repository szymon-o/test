# Quick Start Guide

## Running the Arbitrage Analyzer

### 1. Basic Usage
```bash
python main.py
```

This will:
- Read market data from `assets/data.json`
- Compare prices with mock API data (Application 2)
- Generate `arbitrage_report.txt` with all opportunities

### 2. View Results
Open `arbitrage_report.txt` to see:
- All arbitrage opportunities found
- Sorted by ROI (best opportunities first)
- Detailed action plans for each opportunity

### 3. Understand the Output

**Example Opportunity:**
```
Question: Will Team X win?

App 1 Prices:  YES: $0.40, NO: $0.60
App 2 Prices:  YES: $0.45, NO: $0.40

Strategy: Buy YES on App1 ($0.40) + Buy NO on App2 ($0.40)
Total Cost: $0.80
Payout: $1.00 (guaranteed)
Profit: $0.20
ROI: 25%
```

**Why This Works:**
- You spend $0.80 total
- If outcome is YES: You win $1.00 from App1 (profit from YES bet)
- If outcome is NO: You win $1.00 from App2 (profit from NO bet)
- Either way, you get $1.00 back
- Net profit: $1.00 - $0.80 = $0.20

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Main script - run this! |
| `assets/data.json` | Market data from Application 1 |
| `arbitrage_report.txt` | Generated report with opportunities |
| `README.md` | Full documentation |
| `api_examples.py` | Examples for real API integration |

## Next Steps

### For Testing (Current Setup)
- Script uses mock API data
- Good for understanding how arbitrage works
- Run multiple times to see different opportunities

### For Production Use
1. Edit `main.py`
2. Replace `mock_api_call()` function with real API
3. See `api_examples.py` for integration examples
4. Install requests: `pip install requests`
5. Add your API credentials
6. Test with small amounts first!

## Important Notes

⚠️ **Current Limitations:**
- Uses MOCK data for Application 2
- In production, you need real API integration
- Always account for trading fees
- Check market liquidity before trading
- Verify both markets have matching resolution criteria

✅ **What the Script Does Well:**
- Identifies price discrepancies
- Calculates optimal strategies
- Accounts for all possible outcomes
- Generates clear action plans
- Sorts by profitability

## Understanding ROI

**ROI (Return on Investment)** = (Profit / Cost) × 100%

Examples:
- Cost $0.80, Profit $0.20 → ROI = 25%
- Cost $0.90, Profit $0.10 → ROI = 11.1%
- Cost $0.50, Profit $0.50 → ROI = 100%

**Rule of Thumb:**
- ROI > 10%: Excellent opportunity (after fees)
- ROI 5-10%: Good opportunity (check fees)
- ROI < 5%: May not cover fees and execution risk

## Troubleshooting

**"No opportunities found"**
- Market prices are efficient (no arbitrage available)
- Adjust the mock_api_call to create more variation
- In production, this is actually good news for market efficiency!

**"File not found error"**
- Ensure `assets/data.json` exists
- Run from the correct directory

**"Import error"**
- Script uses only standard library (no installs needed)
- For real APIs, install: `pip install requests`

## Contact & Support

For questions or improvements:
1. Check the full `README.md`
2. Review `api_examples.py` for API integration
3. Examine `main.py` code comments

## Example Session

```
C:\market_compare> python main.py

Market Arbitrage Analyzer
==================================================

1. Loading market data from: assets/data.json
   ✓ Loaded 2 market groups

2. Extracting market information...
   ✓ Extracted 161 individual markets

3. Analyzing markets for arbitrage opportunities...
   ✓ Found 38 arbitrage opportunities

4. Generating report: arbitrage_report.txt
   ✓ Report saved successfully

==================================================
ANALYSIS COMPLETE
==================================================
Total markets analyzed: 161
Arbitrage opportunities found: 38
Best ROI opportunity: 592.04%

C:\market_compare> type arbitrage_report.txt
[View detailed report...]
```

Happy arbitraging! 🎯💰

