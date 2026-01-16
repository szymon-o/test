# Market Arbitrage Analyzer - Copilot Instructions

## Project Overview
This application identifies arbitrage opportunities between two prediction market platforms: **Polymarket** and **predict.fun**. It compares prices for the same markets across both platforms and generates reports showing profitable betting strategies where users can guarantee profits regardless of outcome by betting opposite sides on different platforms.

## Tech Stack
- **Language**: Python 3.x
- **Key Dependencies**:
  - `requests>=2.31.0` - HTTP requests to predict.fun API
  - `openpyxl>=3.1.0` - Excel report generation
  - `python-dotenv>=1.0.0` - Environment variable management
- **APIs**: predict.fun REST API (requires API key in `.env`)
- **Data Sources**: Polymarket data (JSON), predict.fun API

## Project Structure
```
market_compare/
├── .github/
│   └── copilot-instructions.md    # This file
├── src/
│   ├── main.py                    # Main orchestration script
│   ├── predict_dot_fun.py         # predict.fun API integration
│   └── report_generation.py       # Excel report creation
├── assets/
│   ├── polymarket_data.json       # Polymarket market data (input)
│   └── pedict_dot_fun_example_category_slug_request.json  # API response example
├── results/                       # Generated reports (gitignored)
│   ├── arbitrage_report.json      # JSON format
│   └── arbitrage_report.xlsx      # Excel format
├── .env                           # API keys (gitignored, user creates)
├── .gitignore
└── requirements.txt
```

## Key Architecture Patterns

### Data Flow
1. **Load**: Read Polymarket data from `assets/polymarket_data.json`
2. **Extract**: Parse market categories and extract conditionIds
3. **Fetch**: Query predict.fun API for each category slug
4. **Match**: Map markets using Polymarket conditionId ↔ predict.fun polymarketConditionIds
5. **Calculate**: Identify arbitrage (when combined opposite prices < 1.0)
6. **Report**: Generate JSON and Excel reports in `results/`

### Module Responsibilities
- **main.py**: Orchestrates workflow, loads data, calculates arbitrage, calls report generators
- **predict_dot_fun.py**: API client for predict.fun, handles authentication, fetches orderbooks
- **report_generation.py**: Creates formatted Excel reports with color-coded ROI

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

# Create .env file with API key
echo PREDICT_DOT_FUN_API_KEY=your_key_here > .env

# Create results directory
mkdir results
```

### Running the Application
```bash
# From project root
cd src
python main.py
```

**Expected Output**: Console progress, reports in `results/` directory

## API Integration Notes

### predict.fun API
- **Base URL**: `https://api.predict.fun/v1`
- **Authentication**: API key via `x-api-key` header (from env var)
- **Key Endpoints**:
  - `GET /categories/{slug}` - Get category with markets
  - `GET /markets/{id}/orderbook` - Get market prices
- **Rate Limiting**: Unknown - implemented sequential fetching to be safe
- **Data Mapping**: Markets linked via `polymarketConditionIds` array

### Price Interpretation
predict.fun orderbooks are based on "Yes" outcome:
- **Yes Buy Price**: Lowest ask (asks[0][0])
- **Yes Sell Price**: Highest bid (bids[0][0])
- **No Buy Price**: 1 - Yes Sell Price
- **No Sell Price**: 1 - Yes Buy Price

Use **Buy prices** for arbitrage (cost to enter position).

## Testing Approach
No formal test suite exists. Manual testing workflow:
1. Run main.py with known Polymarket data
2. Verify console shows category/market counts
3. Check results/ for both JSON and Excel files
4. Open Excel, verify filters work and ROI sorting correct
5. Validate opportunity calculations manually for sample market

## File Naming Conventions
- Python files: snake_case.py
- JSON data: descriptive_name.json
- Generated reports: arbitrage_report.{format}
