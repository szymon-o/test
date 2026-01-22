from typing import Dict, List, Optional, Tuple
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MARKET_CONFIGS, OPINION_API_DATA_URL, OPINION_TOKEN_URL, OPINION_ORDERBOOK_URL


API_KEY = os.getenv('OPINION_API_KEY')
HEADERS = {
    "apikey": API_KEY,
    "Accept": "*/*"
}

def fetch_opinion_market_data(slug: str, market_id: int) -> Tuple[str, Optional[Dict]]:
    url = OPINION_API_DATA_URL.format(marketId=market_id)
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return (slug, response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Opinion market {market_id}: {e}")
        return (slug, None)


def extract_opinion_orderbook_depth(sorted_bids: List[Dict], sorted_asks: List[Dict]) -> Optional[Dict]:
    if not sorted_asks:
        return None
    
    result = {}
    
    # Extract Bid 1 (highest bid)
    if len(sorted_bids) > 0:
        bid1_price = float(sorted_bids[0]['price'])
        bid1_size = float(sorted_bids[0]['size'])
        result['bid1_price'] = bid1_price
        result['bid1_size_usd'] = bid1_price * bid1_size
    
    # Extract Bid 2 (second-highest bid)
    if len(sorted_bids) > 1:
        bid2_price = float(sorted_bids[1]['price'])
        bid2_size = float(sorted_bids[1]['size'])
        result['bid2_price'] = bid2_price
        result['bid2_size_usd'] = bid2_price * bid2_size
    
    # Extract Ask 1 (lowest ask)
    if len(sorted_asks) > 0:
        ask1_price = float(sorted_asks[0]['price'])
        ask1_size = float(sorted_asks[0]['size'])
        result['ask1_price'] = ask1_price
        result['ask1_size_usd'] = ask1_price * ask1_size
    
    # Extract Ask 2 (second-lowest ask)
    if len(sorted_asks) > 1:
        ask2_price = float(sorted_asks[1]['price'])
        ask2_size = float(sorted_asks[1]['size'])
        result['ask2_price'] = ask2_price
        result['ask2_size_usd'] = ask2_price * ask2_size
    
    return result if result else None


def fetch_token_orderbook(token_id: str, token_type: str) -> Tuple[str, str, Optional[Dict]]:
    time.sleep(0.1)
    try:
        response = requests.get(OPINION_ORDERBOOK_URL, headers=HEADERS, 
                                params={"token_id": token_id})
        response.raise_for_status()
        data = response.json()
        
        errno = data.get('errno')
        if errno != 0:
            return (token_id, token_type, None)
        
        result = data.get('result', {})
        bids = result.get('bids', [])
        asks = result.get('asks', [])
        
        # Sort orderbooks (Opinion returns unsorted data)
        sorted_bids = sorted(bids, key=lambda x: float(x['price']), reverse=True)
        sorted_asks = sorted(asks, key=lambda x: float(x['price']))
        
        # Extract orderbook depth
        orderbook_depth = extract_opinion_orderbook_depth(sorted_bids, sorted_asks)
        
        return (token_id, token_type, orderbook_depth)
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        print(f"Error fetching orderbook for {token_id}: {e}")
        return (token_id, token_type, None)


def extract_opinion_markets() -> List[Dict]:
    all_markets = []
    
    opinion_markets = {slug: market_id for slug, market_id in MARKET_CONFIGS.items() if market_id is not None}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_market = {
            executor.submit(fetch_opinion_market_data, slug, market_id): (slug, market_id)
            for slug, market_id in opinion_markets.items()
        }
        
        for future in as_completed(future_to_market):
            slug, market_id = future_to_market[future]
            try:
                slug, market_data = future.result()
                
                if not market_data:
                    continue
                
                result = market_data.get('result', {})
                data = result.get('data', {})
                
                parent_market_title = data.get('marketTitle', '')
                child_markets = data.get('childMarkets', [])
                
                for market in child_markets:
                    status = market.get('status')
                    
                    if status != 2:
                        continue
                    
                    condition_id = market.get('conditionId')
                    if not condition_id:
                        continue
                    
                    if not condition_id.startswith('0x'):
                        condition_id = f"0x{condition_id}"
                    
                    yes_token_id = market.get('yesTokenId')
                    no_token_id = market.get('noTokenId')
                    
                    if not yes_token_id or not no_token_id:
                        continue
                    
                    volume = market.get('volume', '0')
                    try:
                        volume_float = float(volume)
                    except (ValueError, TypeError):
                        volume_float = 0.0
                    
                    market_info = {
                        'polymarket_slug': slug,
                        'market_id': market.get('marketId'),
                        'market_title': market.get('marketTitle', ''),
                        'parent_title': parent_market_title,
                        'status': status,
                        'status_enum': market.get('statusEnum', ''),
                        'condition_id': condition_id,
                        'yes_token_id': yes_token_id,
                        'no_token_id': no_token_id,
                        'volume': volume_float,
                        'quote_token': market.get('quoteToken'),
                        'chain_id': market.get('chainId'),
                        'created_at': market.get('createdAt'),
                    }
                    
                    all_markets.append(market_info)
                
                print(f"Fetched Opinion market: {slug} (ID: {market_id})")
                
            except Exception as e:
                print(f"Error processing market {slug} ({market_id}): {e}")
    
    return all_markets


def get_opinion_price_lookup(opinion_markets: List[Dict]) -> Dict[str, Dict]:
    price_lookup = {}
    
    token_requests = []
    for market in opinion_markets:
        yes_token_id = market.get('yes_token_id')
        no_token_id = market.get('no_token_id')
        if yes_token_id and no_token_id:
            token_requests.append((market, yes_token_id, 'yes'))
            token_requests.append((market, no_token_id, 'no'))
    
    prices_map = {}
    print(f"\nFetching prices for {len(token_requests)} tokens in parallel...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_token = {
            executor.submit(fetch_token_orderbook, token_id, token_type): (market, token_id, token_type)
            for market, token_id, token_type in token_requests
        }
        
        completed = 0
        for future in as_completed(future_to_token):
            completed += 1
            market, token_id, token_type = future_to_token[future]
            try:
                token_id, token_type, orderbook_depth = future.result()
                if orderbook_depth is not None:
                    prices_map[token_id] = orderbook_depth
                    print(f"  [{completed}/{len(token_requests)}] Fetched {token_type} token for {market.get('market_title')}... ✓")
                else:
                    print(f"  [{completed}/{len(token_requests)}] Failed to fetch {token_type} token for {market.get('market_title')}")
            except Exception as e:
                print(f"  [{completed}/{len(token_requests)}] Error processing {token_type} token for {market.get('market_title')}: {e}")
    
    for market in opinion_markets:
        yes_token_id = market.get('yes_token_id')
        no_token_id = market.get('no_token_id')
        
        yes_orderbook = prices_map.get(yes_token_id)
        no_orderbook = prices_map.get(no_token_id)
        
        # Require at least ask1 for both YES and NO
        if yes_orderbook is None or no_orderbook is None:
            print(f"Warning: Could not fetch orderbooks for market {market.get('market_title')}")
            continue
        
        yes_ask1 = yes_orderbook.get('ask1_price')
        no_ask1 = no_orderbook.get('ask1_price')
        
        if yes_ask1 is None or no_ask1 is None:
            print(f"Warning: Missing ask1 prices for market {market.get('market_title')}")
            continue
        
        # Combine YES and NO orderbook depths with prefixes
        orderbook_depth = {}
        for key, value in yes_orderbook.items():
            orderbook_depth[f'yes_{key}'] = value
        for key, value in no_orderbook.items():
            orderbook_depth[f'no_{key}'] = value
        
        # Use composite key: slug + market_title for matching
        market_key = f"{market.get('polymarket_slug')}||{market.get('market_title')}"
        
        price_lookup[market_key] = {
            'market_id': market.get('market_id'),
            'market_title': market.get('market_title'),
            'polymarket_slug': market.get('polymarket_slug'),
            'source': 'opinion.trade',
            'yes_price': yes_ask1,
            'no_price': no_ask1,
            'volume': market.get('volume'),
            'status': market.get('status_enum'),
            'orderbook_depth': orderbook_depth
        }
    
    return price_lookup


def get_opinion_data() -> Dict[str, Dict]:
    opinion_markets = extract_opinion_markets()
    
    print(f"\nLoaded {len(opinion_markets)} active Opinion markets")
    
    price_lookup = get_opinion_price_lookup(opinion_markets)
    
    return price_lookup