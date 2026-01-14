"""
Market Arbitrage Analyzer
This script compares prices from two different prediction markets and identifies arbitrage opportunities.
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


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
            for market in item['markets']:
                market_info = {
                    'id': market.get('id'),
                    'question': market.get('question'),
                    'outcomes': json.loads(market.get('outcomes', '[]')),
                    'outcomePrices': [float(p) for p in json.loads(market.get('outcomePrices', '[]'))],
                    'slug': market.get('slug'),
                    'active': market.get('active', False),
                    'closed': market.get('closed', False)
                }
                extracted_markets.append(market_info)

    return extracted_markets


def mock_api_call(market_id: str, question: str) -> Dict:
    """
    Mock API call to get prices from another market application.
    In a real scenario, this would make an actual HTTP request to another prediction market API.

    Returns a dict with 'yes' and 'no' prices that differ slightly from the original.
    """
    # Simulate varying prices from another market
    # For demonstration, we'll generate prices that sometimes create arbitrage opportunities

    random.seed(int(market_id) if market_id else 0)  # Consistent random values for same market

    # Generate prices that sum to approximately 1.0 but with some variation
    base_yes_price = random.uniform(0.1, 0.9)

    # Sometimes create arbitrage opportunities (prices don't sum to 1.0 accounting for fees)
    if random.random() < 0.3:  # 30% chance of arbitrage opportunity
        # Create inefficiency
        base_no_price = random.uniform(0.1, 0.9)
    else:
        # Normal market (prices sum to ~1.0)
        base_no_price = 1.0 - base_yes_price + random.uniform(-0.05, 0.05)

    # Ensure prices are in valid range
    yes_price = max(0.01, min(0.99, base_yes_price))
    no_price = max(0.01, min(0.99, base_no_price))

    return {
        'market_id': market_id,
        'source': 'Application_2_API',
        'yes_price': round(yes_price, 3),
        'no_price': round(no_price, 3),
        'timestamp': datetime.now().isoformat()
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


def analyze_markets(markets: List[Dict]) -> List[Dict]:
    """Analyze all markets for arbitrage opportunities."""
    opportunities = []

    for market in markets:
        # Skip closed markets or markets with invalid prices
        if market['closed'] or not market['outcomePrices']:
            continue

        # Get prices from second market (mock API call)
        market2_data = mock_api_call(market['id'], market['question'])

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


def generate_report(opportunities: List[Dict], output_path: str):
    """Generate a human-readable report of arbitrage opportunities."""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("ARBITRAGE OPPORTUNITIES REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")

        if not opportunities:
            f.write("No arbitrage opportunities found.\n")
            return

        f.write(f"Total Opportunities Found: {len(opportunities)}\n\n")

        # Sort opportunities by ROI (best first)
        sorted_opportunities = sorted(
            opportunities,
            key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0,
            reverse=True
        )

        for idx, opp in enumerate(sorted_opportunities, 1):
            market = opp['market']
            arb = opp['arbitrage']
            best = arb['best_strategy']

            if not best:
                continue

            f.write("-" * 100 + "\n")
            f.write(f"OPPORTUNITY #{idx}\n")
            f.write("-" * 100 + "\n\n")

            f.write(f"Question: {market['question']}\n")
            f.write(f"Market ID: {market['id']}\n")
            f.write(f"Slug: {market['slug']}\n\n")

            f.write("PRICE COMPARISON:\n")
            f.write(f"  Application 1 (JSON Data):\n")
            f.write(f"    - YES: ${arb['market1_yes']:.3f}\n")
            f.write(f"    - NO:  ${arb['market1_no']:.3f}\n")
            f.write(f"    - Sum: ${arb['market1_yes'] + arb['market1_no']:.3f}\n\n")

            f.write(f"  Application 2 (API Data):\n")
            f.write(f"    - YES: ${arb['market2_yes']:.3f}\n")
            f.write(f"    - NO:  ${arb['market2_no']:.3f}\n")
            f.write(f"    - Sum: ${arb['market2_yes'] + arb['market2_no']:.3f}\n\n")

            f.write("ARBITRAGE STRATEGY:\n")
            f.write(f"  Strategy Type: {best['type']}\n")
            f.write(f"  Total Cost: ${best['cost']:.3f}\n")
            f.write(f"  Guaranteed Profit: ${best['profit']:.3f}\n")
            f.write(f"  ROI: {best['roi_percent']:.2f}%\n\n")

            f.write("ACTION PLAN:\n")
            f.write(f"  1. On Application 1: {best['action_app1']}\n")
            f.write(f"  2. On Application 2: {best['action_app2']}\n")
            f.write(f"  3. Payout: $1.00 (regardless of outcome)\n")
            f.write(f"  4. Net Profit: ${best['profit']:.3f}\n\n")

            # Show both strategies for completeness
            f.write("ALTERNATIVE STRATEGIES:\n")
            f.write(f"  Strategy A ({arb['strategy1']['description']}):\n")
            f.write(f"    Cost: ${arb['strategy1']['cost']:.3f}, ")
            f.write(f"Profit: ${arb['strategy1']['profit']:.3f}, ")
            f.write(f"ROI: {arb['strategy1']['roi_percent']:.2f}%\n")

            f.write(f"  Strategy B ({arb['strategy2']['description']}):\n")
            f.write(f"    Cost: ${arb['strategy2']['cost']:.3f}, ")
            f.write(f"Profit: ${arb['strategy2']['profit']:.3f}, ")
            f.write(f"ROI: {arb['strategy2']['roi_percent']:.2f}%\n\n")

        f.write("=" * 100 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 100 + "\n")


def main():
    """Main execution function."""
    print("Market Arbitrage Analyzer")
    print("=" * 50)

    # Define paths
    base_dir = Path(__file__).parent
    json_path = base_dir / "assets" / "data.json"
    output_path = base_dir / "arbitrage_report.txt"
    json_output_path = base_dir / "arbitrage_report.json"

    # Load data
    print(f"\n1. Loading market data from: {json_path}")
    try:
        market_data = load_market_data(json_path)
        print(f"   ✓ Loaded {len(market_data)} market groups")
    except Exception as e:
        print(f"   ✗ Error loading data: {e}")
        return

    # Extract market information
    print("\n2. Extracting market information...")
    markets = extract_market_info(market_data)
    print(f"   ✓ Extracted {len(markets)} individual markets")

    # Analyze for arbitrage opportunities
    print("\n3. Analyzing markets for arbitrage opportunities...")
    print("   (Comparing with mock API data from Application 2)")
    opportunities = analyze_markets(markets)
    print(f"   ✓ Found {len(opportunities)} arbitrage opportunities")

    # Generate report
    print(f"\n4. Generating reports...")
    print(f"   Text report: {output_path}")
    generate_report(opportunities, output_path)
    print(f"   ✓ Text report saved")

    print(f"   JSON report: {json_output_path}")
    generate_json_report(opportunities, json_output_path)
    print(f"   ✓ JSON report saved")

    # Summary
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    print(f"Total markets analyzed: {len(markets)}")
    print(f"Arbitrage opportunities found: {len(opportunities)}")

    if opportunities:
        best_opp = max(
            opportunities,
            key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0
        )
        best_roi = best_opp['arbitrage']['best_strategy']['roi_percent']
        print(f"Best ROI opportunity: {best_roi:.2f}%")

    print(f"\nReports saved:")
    print(f"  - Text: {output_path}")
    print(f"  - JSON: {json_output_path}")
    print("\nNote: API data is mocked for demonstration purposes.")


if __name__ == '__main__':
    main()
