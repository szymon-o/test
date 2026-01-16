"""
Market Arbitrage Analyzer
This script compares prices from two different prediction markets and identifies arbitrage opportunities.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from dotenv import load_dotenv
load_dotenv() 

from predict_dot_fun import get_predict_dot_fun_data
from report_generation import generate_excel_report
from capital_allocator import allocate_capital, AllocationStrategy, validate_allocations

BASE_DIR = Path(__file__).parent.parent
REPORT_DIR = BASE_DIR / "results"
POLYMARKET_DATA_PATH = BASE_DIR / "assets" / "polymarket_data.json"
JSON_OUTPUT_PATH = REPORT_DIR / "arbitrage_report.json"
EXCEL_OUTPUT_PATH = REPORT_DIR / "arbitrage_report.xlsx"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Market Arbitrage Analyzer - Identify arbitrage opportunities and calculate capital allocation'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=1500.0,
        help='Total available capital for allocation (default: $1500)'
    )
    parser.add_argument(
        '--allocation-strategy',
        type=str,
        choices=['equal', 'roi_weighted', 'kelly'],
        default='equal',
        help='Capital allocation strategy (default: equal)'
    )
    return parser.parse_args()


def load_market_data(json_path: str) -> List[Dict]:
    """Load market data from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def extract_market_info(market_data: List[Dict]) -> List[Dict]:
    """Extract relevant information from markets array."""
    extracted_markets = []

    for item in market_data:
        if 'markets' in item:
            category = {'slug': item['slug'], 'markets': []}
            for market in item['markets']:
                market_info = {
                    'id': market.get('id'),
                    'question': market.get('question'),
                    'title': market.get("groupItemTitle"),
                    'outcomes': json.loads(market.get('outcomes', '[]')),
                    'outcomePrices': [float(p) for p in json.loads(market.get('outcomePrices', '[]'))],
                    'slug': market.get('slug'),
                    'conditionId': market.get('conditionId'),
                    'active': market.get('active', False),
                    'closed': market.get('closed', False)
                }
                category['markets'].append(market_info)

            if category['markets']:
                extracted_markets.append(category)

    return extracted_markets


def get_predict_fun_price(market: Dict, predict_price_lookup: Dict[str, Dict]) -> Optional[Dict]:
    """Validate and return predict.fun prices for the given Polymarket market."""
    condition_id = market.get('conditionId')
    if not condition_id:
        return None

    lookup = predict_price_lookup.get(condition_id)
    if not lookup:
        return None

    yes_price = lookup.get('yes_price')
    no_price = lookup.get('no_price')

    if yes_price is None or no_price is None:
        return None

    return {
        'market_id': lookup.get('market_id') or market.get('id'),
        'source': lookup.get('source', 'predict.fun'),
        'yes_price': float(yes_price),
        'no_price': float(no_price),
        'timestamp': lookup.get('timestamp') or datetime.utcnow().isoformat()
    }


def calculate_arbitrage(market1_prices: List[float], market2_prices: Dict) -> Dict:
    """
    Calculate potential arbitrage opportunities between two markets.

    Arbitrage exists when you can bet on opposite outcomes in different markets
    and guarantee a profit regardless of the outcome.

    For a binary market (Yes/No):
    - If (price_yes_market1 + price_no_market2) < 1.0, there's an arbitrage opportunity
    - If (price_no_market1 + price_yes_market2) < 1.0, there's an arbitrage opportunity

    Returns dict with arbitrage analysis.
    """
    if len(market1_prices) < 2:
        return None

    yes_price_m1 = market1_prices[0]  # Yes price from market 1
    no_price_m1 = market1_prices[1]   # No price from market 1
    yes_price_m2 = market2_prices['yes_price']
    no_price_m2 = market2_prices['no_price']

    # Strategy 1: Buy Yes on Market 1, Buy No on Market 2
    cost_strategy1 = yes_price_m1 + no_price_m2
    profit_strategy1 = 1.0 - cost_strategy1
    roi_strategy1 = (profit_strategy1 / cost_strategy1 * 100) if cost_strategy1 > 0 else 0

    # Strategy 2: Buy No on Market 1, Buy Yes on Market 2
    cost_strategy2 = no_price_m1 + yes_price_m2
    profit_strategy2 = 1.0 - cost_strategy2
    roi_strategy2 = (profit_strategy2 / cost_strategy2 * 100) if cost_strategy2 > 0 else 0

    # Determine if there's an arbitrage opportunity
    arbitrage_exists = profit_strategy1 > 0 or profit_strategy2 > 0

    best_strategy = None
    if profit_strategy1 > profit_strategy2 and profit_strategy1 > 0:
        best_strategy = {
            'type': 'Yes on App1, No on App2',
            'cost': cost_strategy1,
            'profit': profit_strategy1,
            'roi_percent': roi_strategy1,
            'action_app1': f"Bet ${yes_price_m1:.3f} on YES",
            'action_app2': f"Bet ${no_price_m2:.3f} on NO"
        }
    elif profit_strategy2 > 0:
        best_strategy = {
            'type': 'No on App1, Yes on App2',
            'cost': cost_strategy2,
            'profit': profit_strategy2,
            'roi_percent': roi_strategy2,
            'action_app1': f"Bet ${no_price_m1:.3f} on NO",
            'action_app2': f"Bet ${yes_price_m2:.3f} on YES"
        }

    return {
        'arbitrage_exists': arbitrage_exists,
        'market1_yes': yes_price_m1,
        'market1_no': no_price_m1,
        'market2_yes': yes_price_m2,
        'market2_no': no_price_m2,
        'strategy1': {
            'description': 'Yes on App1, No on App2',
            'cost': cost_strategy1,
            'profit': profit_strategy1,
            'roi_percent': roi_strategy1
        },
        'strategy2': {
            'description': 'No on App1, Yes on App2',
            'cost': cost_strategy2,
            'profit': profit_strategy2,
            'roi_percent': roi_strategy2
        },
        'best_strategy': best_strategy
    }


def analyze_markets(markets: List[Dict], predict_price_lookup: Dict[str, Dict]) -> List[Dict]:
    """Analyze all markets for arbitrage opportunities."""
    opportunities = []

    for market in markets:
        # Skip closed markets or markets with invalid prices
        if market['closed'] or not market['outcomePrices']:
            continue

        # Get prices from predict.fun lookup
        market2_data = get_predict_fun_price(market, predict_price_lookup)

        if not market2_data:
            continue

        # Calculate arbitrage
        arbitrage_result = calculate_arbitrage(market['outcomePrices'], market2_data)

        if arbitrage_result and arbitrage_result['arbitrage_exists']:
            opportunities.append({
                'market': market,
                'market2_data': market2_data,
                'arbitrage': arbitrage_result
            })

    return opportunities


def generate_json_report(opportunities: List[Dict], output_path: str):
    """Generate a concise JSON report of arbitrage opportunities."""

    # Sort opportunities by ROI (best first)
    sorted_opportunities = sorted(
        opportunities,
        key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0,
        reverse=True
    )

    json_data = {
        'generated_at': datetime.now().isoformat(),
        'total_opportunities': len(opportunities),
        'opportunities': []
    }

    for opp in sorted_opportunities:
        market = opp['market']
        arb = opp['arbitrage']
        best = arb['best_strategy']

        if not best:
            continue

        opportunity = {
            'market_id': market['id'],
            'question': market['question'],
            'slug': market['slug'],
            'prices': {
                'app1': {
                    'yes': arb['market1_yes'],
                    'no': arb['market1_no']
                },
                'app2': {
                    'yes': arb['market2_yes'],
                    'no': arb['market2_no']
                }
            },
            'best_strategy': {
                'type': best['type'],
                'total_cost': round(best['cost'], 3),
                'profit': round(best['profit'], 3),
                'roi_percent': round(best['roi_percent'], 2),
                'actions': {
                    'app1': best['action_app1'],
                    'app2': best['action_app2']
                }
            }
        }

        json_data['opportunities'].append(opportunity)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


def main():
    args = parse_arguments()

    print("Market Arbitrage Analyzer")
    print("=" * 50)
    print(f"Capital: ${args.capital:.2f}")
    print(f"Allocation Strategy: {args.allocation_strategy}")
    print("=" * 50)

    # Load data
    print(f"\n1. Loading Polymarket data from: {POLYMARKET_DATA_PATH}")
    try:
        market_data = load_market_data(POLYMARKET_DATA_PATH)
        print(f"   ✓ Loaded {len(market_data)} market groups")
    except Exception as e:
        print(f"   ✗ Error loading data: {e}")
        return

    # Extract market information
    print("\n2. Extracting Polymarket information...")
    poly_cat_with_markets = extract_market_info(market_data)
    print(f"   ✓ Extracted {len(poly_cat_with_markets)} Polymarket categories")

    category_slugs = [cat['slug'] for cat in poly_cat_with_markets]
    print("\n3. Fetching predict.fun prices...")
    predict_price_lookup = get_predict_dot_fun_data(category_slugs)
    print(f"   ✓ Retrieved prices for {len(predict_price_lookup)} predict.fun markets")

    all_opportunities = []
    total_markets = 0

    print("\n4. Analyzing markets for arbitrage opportunities...")
    for idx, polymarket_category in enumerate(poly_cat_with_markets, 1):
        markets = polymarket_category.get('markets', [])
        total_markets += len(markets)
        print(f"   - Category {idx}/{len(poly_cat_with_markets)}: {polymarket_category['slug']} ({len(markets)} markets)")
        category_opportunities = analyze_markets(markets, predict_price_lookup)
        all_opportunities.extend(category_opportunities)

    opportunities = all_opportunities
    print(f"   ✓ Found {len(opportunities)} arbitrage opportunities across {total_markets} markets")

    # Calculate capital allocation
    allocation_result = None
    if opportunities and args.capital > 0:
        print(f"\n5. Calculating capital allocation...")
        strategy_map = {
            'equal': AllocationStrategy.EQUAL,
            'roi_weighted': AllocationStrategy.ROI_WEIGHTED,
            'kelly': AllocationStrategy.KELLY
        }
        strategy = strategy_map.get(args.allocation_strategy, AllocationStrategy.EQUAL)

        allocation_result = allocate_capital(opportunities, args.capital, strategy)
        print(f"   ✓ Allocated ${allocation_result['total_deployed']:.2f} across {allocation_result['num_opportunities']} opportunities")
        print(f"   ✓ Expected total profit: ${allocation_result['total_expected_profit']:.2f}")
        print(f"   ✓ Overall ROI: {allocation_result['overall_roi_percent']:.2f}%")

        if allocation_result['total_unallocated'] > 0:
            print(f"   ⚠ Unallocated capital: ${allocation_result['total_unallocated']:.2f}")

        warnings = validate_allocations(allocation_result)
        if warnings:
            print("\n   Warnings:")
            for warning in warnings:
                print(f"   ⚠ {warning}")

    # Generate report
    print(f"\n6. Generating reports...")
    print(f"   JSON report: {JSON_OUTPUT_PATH}")
    generate_json_report(opportunities, JSON_OUTPUT_PATH)
    print(f"   ✓ JSON report saved")

    print(f"   Excel report: {EXCEL_OUTPUT_PATH}")
    generate_excel_report(opportunities, EXCEL_OUTPUT_PATH, allocation_result)
    print(f"   ✓ Excel report saved")

    # Summary
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    print(f"Total markets analyzed: {total_markets}")
    print(f"Arbitrage opportunities found: {len(opportunities)}")

    if opportunities:
        best_opp = max(
            opportunities,
            key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0
        )
        best_roi = best_opp['arbitrage']['best_strategy']['roi_percent']
        print(f"Best ROI opportunity: {best_roi:.2f}%")

    if allocation_result:
        print(f"\nCapital Allocation Summary:")
        print(f"  Total capital: ${allocation_result['total_capital']:.2f}")
        print(f"  Deployed: ${allocation_result['total_deployed']:.2f}")
        print(f"  Expected profit: ${allocation_result['total_expected_profit']:.2f}")
        print(f"  Overall ROI: {allocation_result['overall_roi_percent']:.2f}%")

    print(f"\nReports saved:")
    print(f"  - JSON: {JSON_OUTPUT_PATH}")
    print(f"  - Excel: {EXCEL_OUTPUT_PATH}")


if __name__ == '__main__':
    main()
