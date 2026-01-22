"""
Market Arbitrage Analyzer
This script compares prices from two different prediction markets and identifies arbitrage opportunities.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from dotenv import load_dotenv
load_dotenv() 

from predict_dot_fun import get_predict_dot_fun_data
from opinion import get_opinion_data
from report_generation import generate_excel_report
from polymarket import fetch_polymarket_events, extract_market_info, fetch_polymarket_orderbooks, extract_orderbook_depth

BASE_DIR = Path(__file__).parent.parent
REPORT_DIR = BASE_DIR / "results"
EXCEL_OUTPUT_PATH = REPORT_DIR / "arbitrage_report.xlsx"


def get_price_from_lookup(market: Dict, price_lookup: Dict[str, Dict], match_by_slug: bool = False) -> Optional[Dict]:
    """Validate and return prices for the given Polymarket market from any price lookup."""
    
    if match_by_slug:
        # For Opinion.trade: match by category_slug + title since condition IDs differ
        category_slug = market.get('category_slug', '')
        market_title = market.get('title', '')
        
        # Try exact match first
        market_key = f"{category_slug}||{market_title}"
        lookup = price_lookup.get(market_key)
        
        if not lookup:
            # Try fuzzy matching by searching for markets with same slug and title
            for key, value in price_lookup.items():
                stored_slug, stored_title = key.split('||', 1)
                if stored_slug == category_slug and stored_title == market_title:
                    lookup = value
                    break
        
        if not lookup:
            return None
    else:
        # For predict.fun: match by condition ID
        condition_id = market.get('conditionId')
        if not condition_id:
            return None
        
        lookup = price_lookup.get(condition_id)
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
        shares_yes = 1.0 / yes_price_m1 if yes_price_m1 > 0 else 0
        shares_no = 1.0 / no_price_m2 if no_price_m2 > 0 else 0
        best_strategy = {
            'type': 'Yes on App1, No on App2',
            'cost': cost_strategy1,
            'profit': profit_strategy1,
            'roi_percent': roi_strategy1,
            'action_app1': f"Buy {shares_yes:.2f} shares of YES @ ${yes_price_m1:.3f}",
            'action_app2': f"Buy {shares_no:.2f} shares of NO @ ${no_price_m2:.3f}"
        }
    elif profit_strategy2 > 0:
        shares_no = 1.0 / no_price_m1 if no_price_m1 > 0 else 0
        shares_yes = 1.0 / yes_price_m2 if yes_price_m2 > 0 else 0
        best_strategy = {
            'type': 'No on App1, Yes on App2',
            'cost': cost_strategy2,
            'profit': profit_strategy2,
            'roi_percent': roi_strategy2,
            'action_app1': f"Buy {shares_no:.2f} shares of NO @ ${no_price_m1:.3f}",
            'action_app2': f"Buy {shares_yes:.2f} shares of YES @ ${yes_price_m2:.3f}"
        }

    return {
        'arbitrage_exists': arbitrage_exists,
        'market1_yes': yes_price_m1,
        'market1_no': no_price_m1,
        'market2_yes': yes_price_m2,
        'market2_no': no_price_m2,
        'best_strategy': best_strategy
    }


def calculate_orderbook_roi(strategy_type: str, market2_prices: Dict, orderbook_data: Dict) -> Optional[float]:
    if not orderbook_data:
        return None

    yes_price_m2 = market2_prices['yes_price']
    no_price_m2 = market2_prices['no_price']

    if 'Yes on App1, No on App2' in strategy_type:
        yes_ask1 = orderbook_data.get('yes_ask1_price')
        if yes_ask1 is None:
            return None
        cost = yes_ask1 + no_price_m2
    else:
        no_ask1 = orderbook_data.get('no_ask1_price')
        if no_ask1 is None:
            return None
        cost = no_ask1 + yes_price_m2

    if cost <= 0:
        return None

    profit = 1.0 - cost
    roi = (profit / cost * 100)
    return roi


def calculate_orderbook_roi_ask2(strategy_type: str, market2_prices: Dict, orderbook_data: Dict) -> Optional[float]:
    if not orderbook_data:
        return None

    yes_price_m2 = market2_prices['yes_price']
    no_price_m2 = market2_prices['no_price']

    if 'Yes on App1, No on App2' in strategy_type:
        yes_ask2 = orderbook_data.get('yes_ask2_price')
        if yes_ask2 is None:
            return None
        cost = yes_ask2 + no_price_m2
    else:
        no_ask2 = orderbook_data.get('no_ask2_price')
        if no_ask2 is None:
            return None
        cost = no_ask2 + yes_price_m2

    if cost <= 0:
        return None

    profit = 1.0 - cost
    roi = (profit / cost * 100)
    return roi


def calculate_orderbook_roi_combined_ask1(strategy_type: str, platform1_orderbook: Optional[Dict], platform2_orderbook: Optional[Dict], platform1_prices: Dict, platform2_prices: Dict) -> Optional[float]:
    yes_price_p1 = platform1_prices.get('yes_price')
    no_price_p1 = platform1_prices.get('no_price')
    yes_price_p2 = platform2_prices.get('yes_price')
    no_price_p2 = platform2_prices.get('no_price')

    if 'Yes on App1, No on App2' in strategy_type:
        # Use Ask1 price from platform1 if available, else fallback to midpoint
        if platform1_orderbook and platform1_orderbook.get('yes_ask1_price') is not None:
            price_p1 = platform1_orderbook['yes_ask1_price']
        else:
            price_p1 = yes_price_p1
        
        # Use Ask1 price from platform2 if available, else fallback to midpoint
        if platform2_orderbook and platform2_orderbook.get('no_ask1_price') is not None:
            price_p2 = platform2_orderbook['no_ask1_price']
        else:
            price_p2 = no_price_p2
    else:  # 'No on App1, Yes on App2'
        # Use Ask1 price from platform1 if available, else fallback to midpoint
        if platform1_orderbook and platform1_orderbook.get('no_ask1_price') is not None:
            price_p1 = platform1_orderbook['no_ask1_price']
        else:
            price_p1 = no_price_p1
        
        # Use Ask1 price from platform2 if available, else fallback to midpoint
        if platform2_orderbook and platform2_orderbook.get('yes_ask1_price') is not None:
            price_p2 = platform2_orderbook['yes_ask1_price']
        else:
            price_p2 = yes_price_p2

    cost = price_p1 + price_p2
    if cost <= 0:
        return None

    profit = 1.0 - cost
    roi = (profit / cost * 100)
    return roi


def calculate_orderbook_roi_combined_ask2(strategy_type: str, platform1_orderbook: Optional[Dict], platform2_orderbook: Optional[Dict], platform1_prices: Dict, platform2_prices: Dict) -> Optional[float]:
    yes_price_p1 = platform1_prices.get('yes_price')
    no_price_p1 = platform1_prices.get('no_price')
    yes_price_p2 = platform2_prices.get('yes_price')
    no_price_p2 = platform2_prices.get('no_price')

    if 'Yes on App1, No on App2' in strategy_type:
        # Use Ask2 price from platform1 if available, else fallback to midpoint
        if platform1_orderbook and platform1_orderbook.get('yes_ask2_price') is not None:
            price_p1 = platform1_orderbook['yes_ask2_price']
        else:
            price_p1 = yes_price_p1
        
        # Use Ask2 price from platform2 if available, else fallback to midpoint
        if platform2_orderbook and platform2_orderbook.get('no_ask2_price') is not None:
            price_p2 = platform2_orderbook['no_ask2_price']
        else:
            price_p2 = no_price_p2
    else:  # 'No on App1, Yes on App2'
        # Use Ask2 price from platform1 if available, else fallback to midpoint
        if platform1_orderbook and platform1_orderbook.get('no_ask2_price') is not None:
            price_p1 = platform1_orderbook['no_ask2_price']
        else:
            price_p1 = no_price_p1
        
        # Use Ask2 price from platform2 if available, else fallback to midpoint
        if platform2_orderbook and platform2_orderbook.get('yes_ask2_price') is not None:
            price_p2 = platform2_orderbook['yes_ask2_price']
        else:
            price_p2 = yes_price_p2

    cost = price_p1 + price_p2
    if cost <= 0:
        return None

    profit = 1.0 - cost
    roi = (profit / cost * 100)
    return roi


def find_opinion_predict_matches(opinion_price_lookup: Dict[str, Dict], predict_price_lookup: Dict[str, Dict], polymarket_markets: List[Dict]) -> List[Dict]:
    """
    Match Opinion markets with predict.fun markets using Polymarket data as intermediary.
    For each Polymarket market, check if it exists in both Opinion and predict.fun.
    Returns list of match pairs with price data from both platforms.
    """
    matches = []
    
    # Build lookup for predict.fun by conditionId
    predict_by_condition_id = {}
    for condition_id, predict_data in predict_price_lookup.items():
        predict_by_condition_id[condition_id] = predict_data
    
    # Build lookup for Opinion by slug||title
    opinion_by_slug_title = {}
    for opinion_key, opinion_data in opinion_price_lookup.items():
        opinion_by_slug_title[opinion_key] = opinion_data
    
    # Go through each Polymarket category and its markets
    for category in polymarket_markets:
        category_slug = category['slug']
        for market in category.get('markets', []):
            if market.get('closed'):
                continue
            
            condition_id = market.get('conditionId')
            market_title = market.get('title')
            
            if not condition_id or not market_title:
                continue
            
            # Check if this market exists in predict.fun
            predict_data = predict_by_condition_id.get(condition_id)
            if not predict_data:
                continue
            
            # Check if this market exists in Opinion
            opinion_key = f"{category_slug}||{market_title}"
            opinion_data = opinion_by_slug_title.get(opinion_key)
            if not opinion_data:
                continue
            
            # Both exist - create match
            matches.append({
                'opinion': opinion_data,
                'predict': predict_data,
                'polymarket_slug': category_slug,
                'market_title': market_title,
                'market_question': market.get('question')
            })
    
    return matches


def analyze_markets(markets: List[Dict], price_lookup: Dict[str, Dict], match_by_slug: bool = False) -> List[Dict]:
    """Analyze all markets for arbitrage opportunities."""
    opportunities = []

    for market in markets:
        # Skip closed markets or markets with invalid prices
        if market['closed'] or not market['outcomePrices']:
            continue

        # Get prices from lookup
        market2_data = get_price_from_lookup(market, price_lookup, match_by_slug)

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


def main():
    # Check if Excel file is open
    if EXCEL_OUTPUT_PATH.exists():
        try:
            with open(EXCEL_OUTPUT_PATH, 'r+b') as f:
                pass
        except PermissionError:
            print("\n" + "=" * 50)
            print("ERROR: Excel file is currently open!")
            print("=" * 50)
            print(f"Please close the file: {EXCEL_OUTPUT_PATH}")
            print("Then run the script again.")
            return

    print("Market Arbitrage Analyzer")
    print("=" * 50)

    # Fetch Polymarket data via API
    print(f"\n1. Fetching Polymarket data via API...")
    try:
        market_data = fetch_polymarket_events()
        print(f"   ✓ Fetched {len(market_data)} market events")
    except Exception as e:
        print(f"   ✗ Error fetching data: {e}")
        return

    # Extract market information
    print("\n2. Extracting Polymarket information...")
    poly_cat_with_markets = extract_market_info(market_data)
    print(f"   ✓ Extracted {len(poly_cat_with_markets)} Polymarket categories")

    category_slugs = [cat['slug'] for cat in poly_cat_with_markets]
    
    print("\n3. Fetching predict.fun prices...")
    predict_price_lookup = get_predict_dot_fun_data(category_slugs)
    print(f"   ✓ Retrieved prices for {len(predict_price_lookup)} predict.fun markets")

    print("\n4. Loading Opinion.trade data...")
    opinion_price_lookup = get_opinion_data()
    print(f"   ✓ Retrieved data for {len(opinion_price_lookup)} Opinion.trade markets")

    all_opportunities = []
    all_opinion_opportunities = []
    total_markets = 0

    print("\n5. Analyzing markets for arbitrage opportunities...")
    print("\n   Polymarket vs predict.fun:")
    for idx, polymarket_category in enumerate(poly_cat_with_markets, 1):
        markets = polymarket_category.get('markets', [])
        total_markets += len(markets)
        print(f"   - Category {idx}/{len(poly_cat_with_markets)}: {polymarket_category['slug']} ({len(markets)} markets)")
        category_opportunities = analyze_markets(markets, predict_price_lookup)
        all_opportunities.extend(category_opportunities)

    opportunities = all_opportunities
    print(f"   ✓ Found {len(opportunities)} predict.fun arbitrage opportunities across {total_markets} markets")

    print("\n   Polymarket vs Opinion.trade:")
    opinion_total_markets = 0
    for idx, polymarket_category in enumerate(poly_cat_with_markets, 1):
        markets = polymarket_category.get('markets', [])
        opinion_total_markets += len(markets)
        
        # Add category slug to each market for Opinion matching
        category_slug = polymarket_category['slug']
        for market in markets:
            market['category_slug'] = category_slug
        
        print(f"   - Category {idx}/{len(poly_cat_with_markets)}: {category_slug} ({len(markets)} markets)")
        category_opportunities = analyze_markets(markets, opinion_price_lookup, match_by_slug=True)
        all_opinion_opportunities.extend(category_opportunities)

    opinion_opportunities = all_opinion_opportunities
    print(f"   ✓ Found {len(opinion_opportunities)} Opinion.trade arbitrage opportunities across {opinion_total_markets} markets")

    print("\n   Opinion.trade vs predict.fun:")
    matched_pairs = find_opinion_predict_matches(opinion_price_lookup, predict_price_lookup, poly_cat_with_markets)
    print(f"   - Found {len(matched_pairs)} matched markets")
    
    opinion_vs_predict_opportunities = []
    for match in matched_pairs:
        opinion_data = match['opinion']
        predict_data = match['predict']
        
        # Calculate arbitrage with Opinion as market1 and predict.fun as market2
        opinion_prices = [opinion_data['yes_price'], opinion_data['no_price']]
        arbitrage_result = calculate_arbitrage(opinion_prices, predict_data)
        
        if arbitrage_result and arbitrage_result['arbitrage_exists']:
            opinion_vs_predict_opportunities.append({
                'market': {
                    'id': f"{match['polymarket_slug']}||{match['market_title']}",
                    'question': f"{match['polymarket_slug']} - {match['market_title']}",
                    'title': match['market_title'],
                    'outcomePrices': opinion_prices,
                    'closed': False
                },
                'market2_data': predict_data,
                'arbitrage': arbitrage_result
            })
    
    print(f"   ✓ Found {len(opinion_vs_predict_opportunities)} Opinion vs predict.fun arbitrage opportunities")

    # Fetch orderbooks for top 5 ROI opportunities
    print(f"\n6. Fetching Polymarket orderbooks for top 5 ROI opportunities...")
    
    # Sort and get top 5 from Polymarket vs predict.fun
    top5_polymarket_predict = sorted(
        opportunities,
        key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0,
        reverse=True
    )[:5]
    
    # Sort and get top 5 from Polymarket vs Opinion
    top5_polymarket_opinion = sorted(
        opinion_opportunities,
        key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0,
        reverse=True
    )[:5]
    
    # Collect all unique token IDs needed
    token_ids_to_fetch = set()
    for opp in top5_polymarket_predict + top5_polymarket_opinion:
        clob_tokens = opp['market'].get('clobTokenIds', [])
        token_ids_to_fetch.update(clob_tokens)
    
    # Fetch all orderbooks in one call
    orderbook_lookup = {}
    if token_ids_to_fetch:
        orderbook_lookup = fetch_polymarket_orderbooks(list(token_ids_to_fetch))
        print(f"   ✓ Fetched {len(orderbook_lookup)} orderbooks")
    
    # Attach orderbook data to opportunities
    for opp in top5_polymarket_predict:
        clob_tokens = opp['market'].get('clobTokenIds', [])
        if clob_tokens and len(clob_tokens) >= 2:
            yes_price = opp['market']['outcomePrices'][0]
            no_price = opp['market']['outcomePrices'][1]
            
            orderbook_data = {}
            
            # Get YES token orderbook
            yes_token_id = clob_tokens[0]
            if yes_token_id in orderbook_lookup:
                yes_orderbook = orderbook_lookup[yes_token_id]
                yes_depth = extract_orderbook_depth(yes_orderbook, yes_price)
                if yes_depth:
                    # Prefix with 'yes_'
                    orderbook_data.update({f'yes_{k}': v for k, v in yes_depth.items()})
            
            # Get NO token orderbook
            no_token_id = clob_tokens[1]
            if no_token_id in orderbook_lookup:
                no_orderbook = orderbook_lookup[no_token_id]
                no_depth = extract_orderbook_depth(no_orderbook, no_price)
                if no_depth:
                    # Prefix with 'no_'
                    orderbook_data.update({f'no_{k}': v for k, v in no_depth.items()})
            
            if orderbook_data:
                opp['polymarket_orderbook'] = orderbook_data
        
        # Attach predict.fun orderbook depth
        condition_id = opp['market'].get('conditionId')
        predict_orderbook = None
        if condition_id and condition_id in predict_price_lookup:
            predict_orderbook = predict_price_lookup[condition_id].get('orderbook_depth')
            if predict_orderbook:
                opp['predict_orderbook'] = predict_orderbook
        
        # Calculate combined orderbook-based ROI using both platforms' orderbooks
        strategy_type = opp['arbitrage']['best_strategy']['type']
        polymarket_orderbook = opp.get('polymarket_orderbook')
        
        # Build platform price dicts for combined ROI calculation
        platform1_prices = {
            'yes_price': opp['market']['outcomePrices'][0],
            'no_price': opp['market']['outcomePrices'][1]
        }
        platform2_prices = opp['market2_data']
        
        orderbook_roi = calculate_orderbook_roi_combined_ask1(
            strategy_type, polymarket_orderbook, predict_orderbook, 
            platform1_prices, platform2_prices
        )
        if orderbook_roi is not None:
            opp['orderbook_roi_percent'] = orderbook_roi

        # Calculate orderbook-based ROI using Ask2
        orderbook_roi_ask2 = calculate_orderbook_roi_combined_ask2(
            strategy_type, polymarket_orderbook, predict_orderbook,
            platform1_prices, platform2_prices
        )
        if orderbook_roi_ask2 is not None:
            opp['orderbook_roi_ask2_percent'] = orderbook_roi_ask2

    for opp in top5_polymarket_opinion:
        clob_tokens = opp['market'].get('clobTokenIds', [])
        if clob_tokens and len(clob_tokens) >= 2:
            yes_price = opp['market']['outcomePrices'][0]
            no_price = opp['market']['outcomePrices'][1]
            
            orderbook_data = {}
            
            yes_token_id = clob_tokens[0]
            if yes_token_id in orderbook_lookup:
                yes_orderbook = orderbook_lookup[yes_token_id]
                yes_depth = extract_orderbook_depth(yes_orderbook, yes_price)
                if yes_depth:
                    orderbook_data.update({f'yes_{k}': v for k, v in yes_depth.items()})
            
            no_token_id = clob_tokens[1]
            if no_token_id in orderbook_lookup:
                no_orderbook = orderbook_lookup[no_token_id]
                no_depth = extract_orderbook_depth(no_orderbook, no_price)
                if no_depth:
                    orderbook_data.update({f'no_{k}': v for k, v in no_depth.items()})
            
            if orderbook_data:
                opp['polymarket_orderbook'] = orderbook_data
        
        # Extract Opinion orderbook depth
        category_slug = opp['market'].get('category_slug', '')
        market_title = opp['market'].get('title', '')
        opinion_key = f"{category_slug}||{market_title}"
        
        opinion_orderbook = None
        if opinion_key in opinion_price_lookup:
            opinion_orderbook = opinion_price_lookup[opinion_key].get('orderbook_depth')
            if opinion_orderbook:
                opp['opinion_orderbook'] = opinion_orderbook
        
        # Calculate combined orderbook-based ROI using both platforms' orderbooks
        strategy_type = opp['arbitrage']['best_strategy']['type']
        polymarket_orderbook = opp.get('polymarket_orderbook')
        
        # Build platform price dicts for combined ROI calculation
        platform1_prices = {
            'yes_price': opp['market']['outcomePrices'][0],
            'no_price': opp['market']['outcomePrices'][1]
        }
        platform2_prices = opp['market2_data']
        
        orderbook_roi = calculate_orderbook_roi_combined_ask1(
            strategy_type, polymarket_orderbook, opinion_orderbook,
            platform1_prices, platform2_prices
        )
        if orderbook_roi is not None:
            opp['orderbook_roi_percent'] = orderbook_roi

        # Calculate orderbook-based ROI using Ask2
        orderbook_roi_ask2 = calculate_orderbook_roi_combined_ask2(
            strategy_type, polymarket_orderbook, opinion_orderbook,
            platform1_prices, platform2_prices
        )
        if orderbook_roi_ask2 is not None:
            opp['orderbook_roi_ask2_percent'] = orderbook_roi_ask2

    # Handle Opinion vs predict.fun top 5 opportunities
    top5_opinion_predict = sorted(
        opinion_vs_predict_opportunities,
        key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0,
        reverse=True
    )[:5]
    
    for opp in top5_opinion_predict:
        # Extract predict.fun orderbook depth from market2_data
        market_id = opp['market2_data'].get('market_id')
        predict_orderbook = opp['market2_data'].get('orderbook_depth')
        
        if predict_orderbook:
            opp['predict_orderbook'] = predict_orderbook
        
        # Calculate combined orderbook-based ROI
        # Opinion has no orderbook, so only use predict.fun orderbook
        strategy_type = opp['arbitrage']['best_strategy']['type']
        
        # Build platform price dicts
        platform1_prices = {
            'yes_price': opp['market']['outcomePrices'][0],
            'no_price': opp['market']['outcomePrices'][1]
        }
        platform2_prices = opp['market2_data']
        
        orderbook_roi = calculate_orderbook_roi_combined_ask1(
            strategy_type, None, predict_orderbook,
            platform1_prices, platform2_prices
        )
        if orderbook_roi is not None:
            opp['orderbook_roi_percent'] = orderbook_roi

        # Calculate orderbook-based ROI using Ask2
        orderbook_roi_ask2 = calculate_orderbook_roi_combined_ask2(
            strategy_type, None, predict_orderbook,
            platform1_prices, platform2_prices
        )
        if orderbook_roi_ask2 is not None:
            opp['orderbook_roi_ask2_percent'] = orderbook_roi_ask2

    # Generate report
    print(f"\n7. Generating Excel report...")
    print(f"   Excel report: {EXCEL_OUTPUT_PATH}")
    generate_excel_report(
        opportunities, 
        EXCEL_OUTPUT_PATH, 
        opinion_opportunities,
        opinion_vs_predict_opportunities
    )
    print(f"   ✓ Excel report saved")

    # Summary
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    print(f"Total markets analyzed: {total_markets}")
    print(f"\nPredict.fun arbitrage opportunities: {len(opportunities)}")

    if opportunities:
        best_opp = max(
            opportunities,
            key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0
        )
        best_roi = best_opp['arbitrage']['best_strategy']['roi_percent']
        print(f"  Best ROI: {best_roi:.2f}%")

    print(f"\nOpinion.trade arbitrage opportunities: {len(opinion_opportunities)}")

    if opinion_opportunities:
        best_opp_opinion = max(
            opinion_opportunities,
            key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0
        )
        best_roi_opinion = best_opp_opinion['arbitrage']['best_strategy']['roi_percent']
        print(f"  Best ROI: {best_roi_opinion:.2f}%")

    print(f"\nOpinion vs predict.fun arbitrage opportunities: {len(opinion_vs_predict_opportunities)}")

    if opinion_vs_predict_opportunities:
        best_opp_opinion_predict = max(
            opinion_vs_predict_opportunities,
            key=lambda x: x['arbitrage']['best_strategy']['roi_percent'] if x['arbitrage']['best_strategy'] else 0
        )
        best_roi_opinion_predict = best_opp_opinion_predict['arbitrage']['best_strategy']['roi_percent']
        print(f"  Best ROI: {best_roi_opinion_predict:.2f}%")

    print(f"\nReport saved:")
    print(f"  - Excel: {EXCEL_OUTPUT_PATH}")


if __name__ == '__main__':
    main()
