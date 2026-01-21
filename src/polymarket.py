import requests
import json
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MARKET_CONFIGS, POLYMARKET_API_EVENTS_URL

POLYMARKET_ORDERBOOK_URL = "https://clob.polymarket.com/books"


def fetch_polymarket_events() -> List[Dict]:
    try:
        params = {"slug": list(MARKET_CONFIGS.keys())}
        response = requests.get(POLYMARKET_API_EVENTS_URL, params=params)
        response.raise_for_status()
        
        events = response.json()
        
        print(f"Fetched Polymarket events")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Polymarket events: {e}")
    
    return events


def extract_market_info(market_data: List[Dict]) -> List[Dict]:
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
                    'clobTokenIds': json.loads(market.get('clobTokenIds', '[]')),
                    'active': market.get('active', False),
                    'closed': market.get('closed', False)
                }
                category['markets'].append(market_info)

            if category['markets']:
                extracted_markets.append(category)

    return extracted_markets


def fetch_polymarket_orderbooks(clob_token_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch orderbooks for multiple Polymarket token IDs using threading.
    Returns dict mapping token_id to orderbook data with bids/asks.
    """
    if not clob_token_ids:
        return {}
    
    orderbook_lookup = {}
    
    def fetch_single_orderbook(token_id: str) -> Optional[Dict]:
        """Fetch orderbook for a single token ID."""
        try:
            payload = [{"token_id": token_id}]
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(POLYMARKET_ORDERBOOK_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            orderbooks = response.json()
            if orderbooks and len(orderbooks) > 0:
                return orderbooks[0]
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"   Warning: Failed to fetch orderbook for token {token_id[:16]}...: {e}")
            return None
    
    # Use ThreadPoolExecutor to fetch orderbooks in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all fetch tasks
        future_to_token = {executor.submit(fetch_single_orderbook, token_id): token_id for token_id in clob_token_ids}
        
        # Collect results as they complete
        for future in as_completed(future_to_token):
            token_id = future_to_token[future]
            try:
                orderbook = future.result()
                if orderbook:
                    asset_id = orderbook.get('asset_id')
                    if asset_id:
                        orderbook_lookup[asset_id] = orderbook
            except Exception as e:
                print(f"   Warning: Error processing orderbook for token {token_id[:16]}...: {e}")
    
    return orderbook_lookup


def extract_orderbook_depth(orderbook: Dict, target_price: float) -> Optional[Dict]:
    """
    Extract best and second-best bid/ask prices with sizes in USD (price * size).
    Returns dict with top 2 bid/ask prices and their USD values.
    """
    if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
        return None
    
    bids = orderbook.get('bids', [])
    asks = orderbook.get('asks', [])
    
    result = {}
    
    # Get best bid (highest buy price) - first element in descending sorted list
    if bids and len(bids) > 0:
        bid_price = float(bids[-1]['price']) if bids[-1].get('price') else None
        bid_size = float(bids[-1]['size']) if bids[-1].get('size') else None
        
        if bid_price is not None:
            result['bid1_price'] = bid_price
            if bid_size is not None:
                result['bid1_size_usd'] = bid_price * bid_size
    
    # Get second-best bid
    if bids and len(bids) > 1:
        bid_price = float(bids[-2]['price']) if bids[-2].get('price') else None
        bid_size = float(bids[-2]['size']) if bids[-2].get('size') else None
        
        if bid_price is not None:
            result['bid2_price'] = bid_price
            if bid_size is not None:
                result['bid2_size_usd'] = bid_price * bid_size
    
    # Get best ask (lowest sell price) - first element in ascending sorted list
    if asks and len(asks) > 0:
        ask_price = float(asks[-1]['price']) if asks[-1].get('price') else None
        ask_size = float(asks[-1]['size']) if asks[-1].get('size') else None
        
        if ask_price is not None:
            result['ask1_price'] = ask_price
            if ask_size is not None:
                result['ask1_size_usd'] = ask_price * ask_size
    
    # Get second-best ask
    if asks and len(asks) > 1:
        ask_price = float(asks[-2]['price']) if asks[-2].get('price') else None
        ask_size = float(asks[-2]['size']) if asks[-2].get('size') else None
        
        if ask_price is not None:
            result['ask2_price'] = ask_price
            if ask_size is not None:
                result['ask2_size_usd'] = ask_price * ask_size
    
    return result if result else None
