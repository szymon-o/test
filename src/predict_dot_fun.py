from typing import Optional, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import os
import time

import requests

BASE_URL = "https://api.predict.fun/v1"

PREDICT_DOT_FUN_API_KEY = os.environ.get('PREDICT_DOT_FUN_API_KEY')
JWT_TOKEN = ""

POLYMARKET_TO_PREDICT_DOT_FUN_CATEGORY_SLUGS = {
    "will-base-launch-a-token-in-2025-341": "will-base-launch-a-token-in-2026",
}


def get_headers():
    headers = {
        "Content-Type": "application/json",
    }
    
    if PREDICT_DOT_FUN_API_KEY:
        headers["x-api-key"] = PREDICT_DOT_FUN_API_KEY
    if JWT_TOKEN:
        headers["Authorization"] = f"Bearer {JWT_TOKEN}"
    
    return headers


def get_category_by_slug(slug: str):
    slug = POLYMARKET_TO_PREDICT_DOT_FUN_CATEGORY_SLUGS.get(slug, slug)
    endpoint = f"{BASE_URL}/categories/{slug}"
    
    headers = get_headers()
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    

def get_market_orderbook(market_id: int) -> Optional[dict]:
    endpoint = f"{BASE_URL}/markets/{market_id}/orderbook"
    
    try:
        time.sleep(0.1)
        response = requests.get(endpoint, headers=get_headers())
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching orderbook for market {market_id}: {e}")
        return None
    

def calculate_prices(orderbook: dict) -> Dict[str, Dict[str, Optional[float]]]:
    """
    The orderbook stores prices based on the 'Yes' outcome.
    - Yes Buy Price = lowest ask price (asks[0][0])
    - Yes Sell Price = highest bid price (bids[0][0])
    - No Buy Price = 1 - (highest bid price for Yes)
    - No Sell Price = 1 - (lowest ask price for Yes)
    """
    if not orderbook or not orderbook.get("success"):
        return {
            "yes": {"buy": None, "sell": None},
            "no": {"buy": None, "sell": None}
        }
    
    data = orderbook.get("data", {})
    bids = data.get("bids", [])
    asks = data.get("asks", [])
    
    prices = {
        "yes": {"buy": None, "sell": None},
        "no": {"buy": None, "sell": None}
    }
    
    # Yes prices
    if asks:
        prices["yes"]["buy"] = asks[0][0]  # Lowest ask to buy Yes
    if bids:
        prices["yes"]["sell"] = bids[0][0]  # Highest bid to sell Yes
    
    # No prices (calculated from Yes prices)
    if bids:
        prices["no"]["buy"] = round(1 - bids[0][0], 4)  # Buy No = 1 - highest Yes bid
    if asks:
        prices["no"]["sell"] = round(1 - asks[0][0], 4)  # Sell No = 1 - lowest Yes ask
    
    return prices


def fetch_market_prices(category_data: dict) -> List[Dict]:
    if not category_data or not category_data.get("success"):
        return []
    
    markets = category_data.get("data", {}).get("markets", [])
    
    print(f"\nFetching prices for {len(markets)} markets in parallel for {category_data.get('data', {}).get('title', 'unknown category')}...")
    
    def fetch_single_market(market):
        market_id = market.get("id")
        market_title = market.get("title")
        
        # Fetch orderbook for this market
        orderbook = get_market_orderbook(market_id)
        
        # Calculate prices
        prices = calculate_prices(orderbook)
        
        # Add prices to market data
        market_with_prices = {
            **market,
            "prices": prices,
            "updateTimestamp": None
        }
        
        if orderbook and orderbook.get("success"):
            market_with_prices["updateTimestamp"] = orderbook.get("data", {}).get("updateTimestampMs")
        
        return market_with_prices, market_title
    
    markets_with_prices = []
    
    # Use ThreadPoolExecutor to fetch orderbooks in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_market = {executor.submit(fetch_single_market, market): market for market in markets}
        
        # Process completed tasks as they finish
        completed = 0
        for future in as_completed(future_to_market):
            completed += 1
            try:
                market_with_prices, market_title = future.result()
                markets_with_prices.append(market_with_prices)
                print(f"  [{completed}/{len(markets)}] Fetched {market_title}... ✓")
            except Exception as e:
                market = future_to_market[future]
                print(f"  [{completed}/{len(markets)}] Error fetching {market.get('title')}: {e}")
    
    return markets_with_prices


def display_category_with_prices(category_data: dict, markets_with_prices: List[Dict]):
    if not category_data or not category_data.get("success"):
        print("Failed to fetch category data")
        return
    
    print(f"\n{'MARKETS (' + str(len(markets_with_prices)) + ')':^100}")
    print("="*100)
    
    for idx, market in enumerate(markets_with_prices, 1):
        prices = market.get("prices", {})
        yes_prices = prices.get("yes", {})
        no_prices = prices.get("no", {})
        
        print(f"\n[{idx}] {market.get('title')}")
        print(f"    ID: {market.get('id')} | Status: {market.get('status')}")
        print(f"    Question: {market.get('question')}")
        
        print(f"\n    YES PRICES:")
        print(f"      Buy (Lowest Ask):  {yes_prices.get('buy') or 'N/A'}")
        print(f"      Sell (Highest Bid): {yes_prices.get('sell') or 'N/A'}")
        
        print(f"\n    NO PRICES:")
        print(f"      Buy:  {no_prices.get('buy') or 'N/A'}")
        print(f"      Sell: {no_prices.get('sell') or 'N/A'}")
        
        print("-" * 100)


def get_predict_dot_fun_data(slugs: list):
    price_lookup: Dict[str, Dict] = {}

    for slug in slugs:
        category_data = get_category_by_slug(slug)

        if not (category_data and category_data.get("success")):
            print(f"Failed to retrieve category data for slug: {slug}")
            continue

        markets_with_prices = fetch_market_prices(category_data)

        for market in markets_with_prices:
            polymarket_condition_ids = market.get("polymarketConditionIds", [])
            prices = market.get("prices", {})
            yes_buy = prices.get("yes", {}).get("buy")
            no_buy = prices.get("no", {}).get("buy")

            if not polymarket_condition_ids or yes_buy is None or no_buy is None:
                continue

            # Use the first (and typically only) Polymarket conditionId as the key
            condition_id = polymarket_condition_ids[0]
            price_lookup[condition_id] = {
                "market_id": market.get("id"),
                "question": market.get("question"),
                "yes_price": float(yes_buy),
                "no_price": float(no_buy),
                "source": "predict.fun",
                "timestamp": datetime.utcnow().isoformat(),
                "category_slug": market.get("categorySlug"),
                "market_title": market.get("title")
            }

    return price_lookup



if __name__ == "__main__":
    category_slug = "metamask-fdv-above-one-day-after-launch"
    print(f"Fetching category: {category_slug}")
    
    category_data = get_category_by_slug(category_slug)
    
    if category_data and category_data.get("success"):
        # Fetch market prices
        markets_with_prices = fetch_market_prices(category_data)
        
        # Display formatted information
        display_category_with_prices(category_data, markets_with_prices)
    else:
        print("Failed to retrieve category data")
