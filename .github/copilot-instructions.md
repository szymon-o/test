# Market Arbitrage Analyzer - Copilot Instructions

## Project Overview
This application identifies arbitrage opportunities across **three prediction market platforms**: **Polymarket**, **predict.fun**, and **Opinion.trade**. It compares prices for the same markets across all platforms and generates comprehensive reports showing profitable betting strategies where users can guarantee profits regardless of outcome by betting opposite sides on different platforms.

The analyzer performs three types of cross-platform arbitrage analysis:
1. **Polymarket vs predict.fun** - Traditional two-platform arbitrage
2. **Polymarket vs Opinion.trade** - Matches markets using category slug + title
3. **Opinion.trade vs predict.fun** - Cross-matches using Polymarket as intermediary

## Tech Stack
- **Language**: Python 3.x
- **Key Dependencies**:
  - `requests>=2.31.0` - HTTP requests to all platform APIs
  - `openpyxl>=3.1.0` - Excel report generation with multi-sheet support
  - `python-dotenv>=1.0.0` - Environment variable management
- **APIs**: 
  - Polymarket Gamma API (events endpoint, no auth required)
  - Polymarket CLOB API (orderbook endpoint, no auth required)
  - predict.fun REST API (requires `PREDICT_DOT_FUN_API_KEY` in `.env`)
  - Opinion.trade OpenAPI (requires `OPINION_API_KEY` in `.env`)
- **Data Sources**: Real-time data from all three platforms via APIs

## Project Structure
```
market_compare/
├── .github/
│   └── copilot-instructions.md    # This file
├── src/
│   ├── main.py                    # Main orchestration script
│   ├── config.py                  # Centralized configuration (market slugs, API URLs)
│   ├── polymarket.py              # Polymarket API integration (events + orderbooks)
│   ├── predict_dot_fun.py         # predict.fun API integration
│   ├── opinion.py                 # Opinion.trade API integration
│   ├── report_generation.py       # Excel report creation (3 sheets)
│   ├── capital_allocator.py       # Capital allocation strategies (unused currently)
│   └── test_conn.py               # Connection testing utility
├── assets/
│   ├── polymarket_data.json       # Example Polymarket market data
│   ├── polymarket_orderbook.json  # Example Polymarket orderbook response
│   ├── opinion_market_data.json   # Example Opinion.trade market data
│   ├── opinion_token_data.json    # Example Opinion.trade token price data
│   └── pedict_dot_fun_example_category_slug_request.json  # API response example
├── results/                       # Generated reports (gitignored)
│   └── arbitrage_report.xlsx      # Excel report with 3 sheets
├── .env                           # API keys (gitignored, user creates)
├── .gitignore
└── requirements.txt
```

## Key Architecture Patterns

### Data Flow
1. **Fetch Polymarket**: Query Polymarket Gamma API for events using configured category slugs
2. **Extract Markets**: Parse Polymarket response to extract market info (conditionId, title, slug, prices, clobTokenIds)
3. **Fetch predict.fun**: For each category slug, query predict.fun API for markets and orderbooks (parallel)
4. **Fetch Opinion.trade**: For configured market IDs, fetch market data and token prices (parallel)
5. **Match Markets**: 
   - Polymarket ↔ predict.fun: Match by conditionId
   - Polymarket ↔ Opinion: Match by category_slug + title (composite key)
   - Opinion ↔ predict.fun: Cross-match using Polymarket as intermediary
6. **Calculate Arbitrage**: For each match, check if combined opposite prices < 1.0
7. **Fetch Orderbooks**: For top 5 ROI opportunities, fetch Polymarket CLOB orderbooks (parallel)
8. **Extract Depth**: Extract bid/ask prices and sizes from orderbooks
9. **Generate Report**: Create Excel file with 3 sheets, sorted by ROI

### Module Responsibilities
- **main.py**: Orchestrates workflow, calculates arbitrage, coordinates all modules
- **config.py**: Centralized configuration with `MARKET_CONFIGS` dict (slug → Opinion market ID), API URLs
- **polymarket.py**: Fetches Polymarket events, extracts market info, fetches orderbooks (parallel), extracts depth
- **predict_dot_fun.py**: API client for predict.fun, fetches categories and orderbooks (parallel), calculates prices
- **opinion.py**: API client for Opinion.trade, fetches market data (parallel), fetches token prices (parallel)
- **report_generation.py**: Creates multi-sheet Excel reports with color-coded ROI and orderbook depth
- **capital_allocator.py**: Capital allocation strategies (equal weight, Kelly criterion) - **currently unused**

## Arbitrage Logic

### Calculation Method
For binary markets, arbitrage exists when you can bet opposite outcomes on different platforms and guarantee profit:

**Strategy 1**: Buy YES on Platform1, Buy NO on Platform2
- Cost: `price_yes_p1 + price_no_p2`
- Profit: `1.0 - cost`
- ROI: `(profit / cost) * 100`

**Strategy 2**: Buy NO on Platform1, Buy YES on Platform2
- Cost: `price_no_p1 + price_yes_p2`
- Profit: `1.0 - cost`
- ROI: `(profit / cost) * 100`

Arbitrage exists if either profit > 0. The system selects the best strategy with highest ROI.

### Share Calculation
For a given capital allocation (default $1500 per opportunity):
- Bet is split proportionally to prices to minimize exposure
- `bet_app1 = capital * (price_app1 / total_cost)`
- `bet_app2 = capital * (price_app2 / total_cost)`
- `shares = bet_amount / price`

### Market Matching Strategies

#### Polymarket ↔ predict.fun
- **Key**: Polymarket `conditionId`
- **Lookup**: `predict_price_lookup[conditionId]`
- **Source**: predict.fun provides `polymarketConditionIds` array

#### Polymarket ↔ Opinion.trade
- **Key**: Composite `"{category_slug}||{market_title}"`
- **Lookup**: `opinion_price_lookup[composite_key]`
- **Reason**: Opinion.trade uses different conditionIds, so match by slug+title
- **Matching**: Exact string match on both slug and title

#### Opinion.trade ↔ predict.fun
- **Method**: Three-way matching using Polymarket as intermediary
- **Process**:
  1. Iterate through Polymarket markets
  2. Check if market exists in Opinion (by slug+title)
  3. Check if market exists in predict.fun (by conditionId)
  4. If both exist, create match pair

## Performance Optimizations

### Parallel API Fetching
- **Opinion Markets**: ThreadPoolExecutor with max_workers=10 for market data
- **Opinion Token Prices**: ThreadPoolExecutor with max_workers=20 (read-heavy)
- **predict.fun Orderbooks**: ThreadPoolExecutor with max_workers=10
- **Polymarket Orderbooks**: ThreadPoolExecutor with max_workers=10

### Rate Limiting
- **Opinion Token Prices**: 0.1s sleep per request (within thread)
- **predict.fun Orderbooks**: 0.1s sleep per request (within thread)
- **Polymarket**: No rate limiting (batch endpoint + no auth restrictions)

### Orderbook Optimization
- Only fetch Polymarket orderbooks for **top 5 ROI opportunities** per comparison type
- Batch token IDs from multiple opportunities into single API call
- Extract only bid1, bid2, ask1, ask2 (not full orderbook depth)

## Coding Guidelines

### Style
- Follow PEP 8 conventions
- Use type hints for function parameters and returns
- Keep functions focused on single responsibilities

### Error Handling
- Wrap API calls in try-except blocks
- Continue processing other markets if one fails
- Print informative error messages with context
- Use `Optional` type hints when values may be None

### Data Validation
- Check for required fields before accessing (use `.get()` for dicts)
- Validate prices exist before calculating arbitrage
- Skip closed/inactive markets explicitly
- Verify conditionId exists before lookups

### Constants
- Define paths using `Path(__file__).parent` for portability
- Use UPPER_CASE for module-level constants
- Store API URLs as constants at module top

### Testing
- Do not write any tests

### Documentation
- Do not add docstrings to functions
- Do not create any .md document until explicitly requested

## Environment Setup

### First-Time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with both API keys
echo PREDICT_DOT_FUN_API_KEY=your_predict_key_here > .env
echo OPINION_API_KEY=your_opinion_key_here >> .env

# Create results directory (if not exists)
mkdir results
```

### Running the Application
```bash
# From src directory
cd src
python main.py
```

**Expected Output**: 
- Console progress with parallel fetch indicators
- Excel report in `results/arbitrage_report.xlsx` with 3 sheets
- Summary statistics for all three arbitrage types

## API Integration Notes

### Polymarket APIs

#### Gamma API (Events)
- **Base URL**: `https://gamma-api.polymarket.com`
- **Authentication**: None required
- **Key Endpoints**:
  - `GET /events?slug={slugs}` - Get events by category slugs (supports multiple)
- **Response**: Array of events with nested markets containing conditionId, prices, clobTokenIds

#### CLOB API (Orderbooks)
- **Base URL**: `https://clob.polymarket.com`
- **Authentication**: None required
- **Key Endpoints**:
  - `POST /books` - Get orderbooks for token IDs (batch endpoint)
- **Request Body**: `[{"token_id": "0x..."}, ...]`
- **Response**: Array of orderbooks with bids/asks sorted by price
- **Implementation**: Parallel fetching with ThreadPoolExecutor (max_workers=10)

### predict.fun API
- **Base URL**: `https://api.predict.fun/v1`
- **Authentication**: API key via `x-api-key` header (from `PREDICT_DOT_FUN_API_KEY` env var)
- **Key Endpoints**:
  - `GET /categories/{slug}` - Get category with markets
  - `GET /markets/{id}/orderbook` - Get market orderbook
- **Rate Limiting**: Unknown - implemented 0.1s delay + parallel fetching (max_workers=10)
- **Data Mapping**: Markets linked via `polymarketConditionIds` array
- **Slug Mapping**: Some slugs differ from Polymarket (defined in `config.py`)

#### Price Interpretation
predict.fun orderbooks are based on "Yes" outcome:
- **Yes Buy Price**: Lowest ask (asks[0][0])
- **Yes Sell Price**: Highest bid (bids[0][0])
- **No Buy Price**: 1 - Yes Sell Price
- **No Sell Price**: 1 - Yes Buy Price

Use **Buy prices** for arbitrage (cost to enter position).

### Opinion.trade API
- **Base URL**: `https://openapi.opinion.trade/openapi`
- **Authentication**: API key via `apikey` header (from `OPINION_API_KEY` env var)
- **Key Endpoints**:
  - `GET /market/categorical/{marketId}` - Get categorical market with child markets
  - `GET /token/latest-price?token_id={tokenId}` - Get latest token price
- **Rate Limiting**: Implemented 0.1s delay + parallel fetching (max_workers=20)
- **Data Mapping**: 
  - Markets matched by category_slug + marketTitle (composite key format: `{slug}||{title}`)
  - Each market has yesTokenId and noTokenId for price lookups
  - Only status=2 (active) markets are processed
- **Market Status**: 
  - Status enum 2 = Active/Trading
  - ConditionIds are prefixed with `0x` if missing
- **Implementation**: Two-phase parallel fetching (markets then token prices)

## Configuration Management

### Market Configuration
Markets are managed in `config.py` via the `MARKET_CONFIGS` dictionary:
```python
MARKET_CONFIGS: Dict[str, Optional[int]] = {
    "polymarket-slug": opinion_market_id,  # Opinion market ID (int) or None
    # None means market exists on Polymarket/predict.fun but not Opinion
}
```

**Adding New Markets**:
1. Add Polymarket category slug as key
2. If market exists on Opinion.trade, add its market ID as value
3. If market only exists on Polymarket/predict.fun, use `None` as value
4. The system will automatically fetch data for all configured slugs

### API URLs
All API URLs are centralized in `config.py`:
- `POLYMARKET_API_EVENTS_URL`
- `OPINION_API_DATA_URL` (parameterized with `{marketId}`)
- `OPINION_TOKEN_URL`

## Excel Report Structure

### Three Sheets Generated
1. **"Polymarket vs predict.fun"**: Traditional arbitrage opportunities
2. **"Polymarket vs Opinion"**: Polymarket-Opinion arbitrage
3. **"Opinion vs predict.fun"**: Cross-platform arbitrage

### Columns (All Sheets)
- **Rank**: Sorted by ROI descending
- **Question**: Market question/title
- **ROI %**: Return on investment percentage
- **Bet YES on**: Platform to bet YES (highlighted)
- **Bet NO on**: Platform to bet NO (highlighted)
- **Platform YES/NO**: Current prices for both outcomes on each platform (used prices highlighted)
- **Shares Platform1/2**: Calculated shares to purchase

### Additional Columns (Top 5 ROI with Polymarket)
For top 5 opportunities involving Polymarket, orderbook depth is added:
- **YES Bid 1/2**: Best and second-best bid prices for YES token
- **YES Bid 1/2 Size $**: USD value of bid sizes (highlighted if YES is bought)
- **YES Ask 1/2**: Best and second-best ask prices for YES token
- **YES Ask 1/2 Size $**: USD value of ask sizes (highlighted if YES is bought)
- **NO Bid 1/2**: Best and second-best bid prices for NO token
- **NO Bid 1/2 Size $**: USD value of bid sizes (highlighted if NO is bought)
- **NO Ask 1/2**: Best and second-best ask prices for NO token
- **NO Ask 1/2 Size $**: USD value of ask sizes (highlighted if NO is bought)

### Formatting
- Headers: Blue background, white bold text, centered
- Price cells: Right-aligned, currency format ($0.000)
- Active strategy prices: Green highlight
- Orderbook sizes used in strategy: Light green highlight
- Auto-filter enabled on all columns
- Frozen header row

## Testing Approach
No formal test suite exists. Manual testing workflow:
1. Ensure both API keys are in `.env` file
2. Run `python main.py` from src directory
3. Verify console shows:
   - Polymarket events fetched count
   - predict.fun markets fetched (with parallel progress)
   - Opinion.trade markets and token prices fetched (with parallel progress)
   - Three arbitrage opportunity counts
   - Top 5 orderbook fetching progress
4. Check `results/arbitrage_report.xlsx` exists
5. Open Excel, verify:
   - Three sheets exist with correct names
   - All sheets have data sorted by ROI descending
   - Filters work on all columns
   - Price highlighting matches strategy type
   - Orderbook columns appear on top 5 Polymarket opportunities
6. Validate arbitrage calculation manually for a sample opportunity

## File Naming Conventions
- Python files: snake_case.py
- JSON data: descriptive_name.json
- Generated reports: arbitrage_report.xlsx

## Known Limitations & Notes

### Capital Allocator Module
- `capital_allocator.py` exists but is **not currently integrated** into main workflow
- Contains equal-weight allocation strategy and bet sizing calculations
- Platform minimum bet: $5.00 per side
- Future feature: Will enable portfolio optimization across multiple opportunities

### Slug Mapping
- Some category slugs differ between Polymarket and predict.fun
- Mappings defined in `POLYMARKET_TO_PREDICT_DOT_FUN_CATEGORY_SLUGS` dict
- Example: `"will-base-launch-a-token-in-2025-341"` → `"will-base-launch-a-token-in-2026"`

### Orderbook Depth
- Polymarket bids/asks are pre-sorted by API (descending for bids, ascending for asks)
- We extract from end of arrays: `bids[-1]` = best bid, `asks[-1]` = best ask
- Size values converted to USD: `price * size`

### Error Handling Philosophy
- Continue processing remaining markets if one fails
- Print warnings but don't stop execution
- Missing prices/data = skip that market silently
- API errors logged with context but workflow continues

### Price Update Frequency
- All prices fetched in real-time on each run
- No caching between runs
- Typical run time: 30-60 seconds depending on market count
- Opinion.trade token price fetching is the slowest step (many serial API calls)

## Future Enhancements (Not Implemented)

### Potential Features
1. **Capital Allocation Integration**: Use `capital_allocator.py` to optimize portfolio
2. **Historical Tracking**: Store arbitrage opportunities over time in database
3. **Alerting System**: Notify when ROI exceeds threshold
4. **Automated Trading**: Execute trades via platform APIs
5. **Liquidity Analysis**: Factor in orderbook depth before recommending opportunities
6. **Multi-Currency Support**: Handle USDC, USDT, etc. conversions
7. **Gas Fee Estimation**: Include transaction costs in profit calculations

### Code Improvements
1. **Async/Await**: Replace ThreadPoolExecutor with asyncio for better performance
2. **Retry Logic**: Add exponential backoff for failed API calls
3. **Logging**: Replace print statements with proper logging framework
4. **Config File**: Move from hardcoded dict to JSON/YAML configuration
5. **CLI Arguments**: Accept capital amount, market filters, output path as args
