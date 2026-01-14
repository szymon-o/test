# Market Arbitrage Analyzer

A Python script that analyzes prediction market data to identify arbitrage opportunities between two different market applications.

## Overview

This tool compares prices from two prediction markets and identifies opportunities where you can place opposite bets on different platforms to guarantee a profit regardless of the outcome.

## How It Works

### 1. Data Input
- Reads market data from `assets/data.json`
- Extracts relevant information: question, outcomes, and outcome prices
- Each market contains binary outcomes (Yes/No) with associated prices

### 2. Price Comparison
- **Application 1**: Prices from the JSON file (your current market data)
- **Application 2**: Prices from a mock API call (simulating another prediction market)
  - In production, replace `mock_api_call()` with actual API requests

### 3. Arbitrage Detection

Arbitrage exists when the sum of prices for opposite outcomes across two markets is less than 1.0:

**Strategy A**: Buy YES on App1 + Buy NO on App2
- Cost = price_yes_app1 + price_no_app2
- If cost < $1.00, you make a profit!

**Strategy B**: Buy NO on App1 + Buy YES on App2
- Cost = price_no_app1 + price_yes_app2
- If cost < $1.00, you make a profit!

### Example

```
Market Question: "Will Team X win the championship?"

Application 1:     Application 2:
YES: $0.40        YES: $0.45
NO:  $0.60        NO:  $0.40

Strategy: Buy YES on App1 ($0.40) + Buy NO on App2 ($0.40)
Total Cost: $0.80
Payout: $1.00 (guaranteed, regardless of outcome)
Profit: $0.20
ROI: 25%
```

## Installation

No external dependencies required! Uses only Python standard library:
- `json` - Parse JSON data
- `random` - Generate mock API responses
- `pathlib` - Handle file paths
- `datetime` - Timestamp reports
- `typing` - Type hints

## Usage

### Run the Script

```bash
python main.py
```

### Output

The script generates `arbitrage_report.txt` with:
- Total opportunities found
- Detailed analysis for each opportunity
- Price comparisons between both applications
- Recommended arbitrage strategy
- Expected ROI and profit calculations
- Step-by-step action plan

### Report Structure

For each opportunity, the report includes:

1. **Market Information**
   - Question
   - Market ID and slug

2. **Price Comparison**
   - Prices from both applications
   - Price sums (helps identify inefficiencies)

3. **Arbitrage Strategy**
   - Best strategy type
   - Total cost
   - Guaranteed profit
   - ROI percentage

4. **Action Plan**
   - Specific bets to place on each application
   - Expected payout
   - Net profit

5. **Alternative Strategies**
   - Both possible strategies with their metrics

## Customization

### Integrate Real API

Replace the `mock_api_call()` function with actual API requests:

```python
def mock_api_call(market_id: str, question: str) -> Dict:
    # Replace with actual API call
    import requests
    
    response = requests.get(f"https://api.market2.com/markets/{market_id}")
    data = response.json()
    
    return {
        'market_id': market_id,
        'source': 'Real_API',
        'yes_price': data['yes_price'],
        'no_price': data['no_price'],
        'timestamp': datetime.now().isoformat()
    }
```

### Adjust Thresholds

Modify the arbitrage calculation to account for:
- Trading fees
- Minimum profit thresholds
- Risk tolerance

```python
def calculate_arbitrage(market1_prices, market2_prices, fee_rate=0.02):
    # Account for 2% trading fees
    cost_with_fees = (price1 + price2) * (1 + fee_rate)
    profit = 1.0 - cost_with_fees
    # ... rest of calculation
```

### Filter Markets

Add filters in `analyze_markets()`:

```python
def analyze_markets(markets: List[Dict]) -> List[Dict]:
    opportunities = []
    
    for market in markets:
        # Skip if market volume too low
        if market.get('volume', 0) < 10000:
            continue
            
        # Skip if not active
        if market['closed'] or not market['active']:
            continue
            
        # ... rest of analysis
```

## Understanding the Output

### Key Metrics

- **ROI (Return on Investment)**: Percentage profit relative to capital invested
- **Profit**: Absolute dollar amount of guaranteed profit
- **Cost**: Total capital required to execute the arbitrage
- **Price Sum**: Sum of YES + NO prices (should be ~1.0 in efficient markets)

### When to Act

Look for opportunities with:
- ✅ High ROI (> 5% after fees)
- ✅ Reasonable profit amount
- ✅ Both markets have sufficient liquidity
- ✅ Both markets are still accepting bets

### Risk Considerations

- **Execution Risk**: Prices change before you place both bets
- **Liquidity Risk**: Can't place full bet size
- **Settlement Risk**: Different resolution criteria
- **Fee Impact**: Trading fees reduce profit margins
- **Account Limits**: Betting limits per market

## File Structure

```
market_compare/
├── main.py                    # Main arbitrage analyzer script
├── assets/
│   └── data.json             # Market data from Application 1
├── arbitrage_report.txt      # Generated opportunities report
└── README.md                 # This file
```

## Example Console Output

```
Market Arbitrage Analyzer
==================================================

1. Loading market data from: ./assets/data.json
   ✓ Loaded 2 market groups

2. Extracting market information...
   ✓ Extracted 161 individual markets

3. Analyzing markets for arbitrage opportunities...
   (Comparing with mock API data from Application 2)
   ✓ Found 38 arbitrage opportunities

4. Generating report: ./arbitrage_report.txt
   ✓ Report saved successfully

==================================================
ANALYSIS COMPLETE
==================================================
Total markets analyzed: 161
Arbitrage opportunities found: 38
Best ROI opportunity: 592.04%

Detailed report saved to: ./arbitrage_report.txt
```

## Notes

- The current implementation uses **mock API data** for demonstration
- Mock data is seeded by market ID for consistency
- In production, replace with real API calls to another prediction market
- Always verify market rules and resolution criteria match
- Account for all fees before executing trades
- Consider market liquidity and bet limits

## Next Steps

1. **Integrate Real API**: Connect to actual prediction market APIs
2. **Add Fee Calculations**: Factor in trading fees and withdrawal costs
3. **Real-time Monitoring**: Set up continuous monitoring for new opportunities
4. **Automated Execution**: Build bot to automatically place arbitrage bets
5. **Alert System**: Get notified when high-ROI opportunities appear
6. **Historical Analysis**: Track opportunity frequency and profitability

## License

Free to use and modify for personal or commercial purposes.

## Disclaimer

This tool is for educational and research purposes. Always:
- Verify market rules and terms of service
- Check if arbitrage betting is allowed on both platforms
- Understand the risks involved in prediction market trading
- Only invest what you can afford to lose

