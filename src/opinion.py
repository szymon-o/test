from typing import Dict, List, Optional, Tuple
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MARKET_CONFIGS, OPINION_API_DATA_URL, OPINION_TOKEN_URL


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


def fetch_token_price(token_id: str, token_type: str) -> Tuple[str, str, Optional[float]]:
    time.sleep(0.1)
    try:
        response = requests.get(OPINION_TOKEN_URL, headers=HEADERS, 
                                params={"token_id": token_id})
        response.raise_for_status()
        data = response.json()
        
        result = data.get('result', {})
        price = result.get('price')
        
        if price is not None:
            return (token_id, token_type, float(price))
        return (token_id, token_type, None)
    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        print(f"Error fetching token price for {token_id}: {e}")
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
            executor.submit(fetch_token_price, token_id, token_type): (market, token_id, token_type)
            for market, token_id, token_type in token_requests
        }
        
        completed = 0
        for future in as_completed(future_to_token):
            completed += 1
            market, token_id, token_type = future_to_token[future]
            try:
                token_id, token_type, price = future.result()
                if price is not None:
                    prices_map[token_id] = price
                    print(f"  [{completed}/{len(token_requests)}] Fetched {token_type} token for {market.get('market_title')}... ✓")
                else:
                    print(f"  [{completed}/{len(token_requests)}] Failed to fetch {token_type} token for {market.get('market_title')}")
            except Exception as e:
                print(f"  [{completed}/{len(token_requests)}] Error processing {token_type} token for {market.get('market_title')}: {e}")
    
    for market in opinion_markets:
        yes_token_id = market.get('yes_token_id')
        no_token_id = market.get('no_token_id')
        
        yes_price = prices_map.get(yes_token_id)
        no_price = prices_map.get(no_token_id)
        
        if yes_price is None or no_price is None:
            print(f"Warning: Could not fetch prices for market {market.get('market_title')}")
            continue
        
        # Use composite key: slug + market_title for matching
        market_key = f"{market.get('polymarket_slug')}||{market.get('market_title')}"
        
        price_lookup[market_key] = {
            'market_id': market.get('market_id'),
            'market_title': market.get('market_title'),
            'polymarket_slug': market.get('polymarket_slug'),
            'source': 'opinion.trade',
            'yes_price': yes_price,
            'no_price': no_price,
            'volume': market.get('volume'),
            'status': market.get('status_enum'),
        }
    
    return price_lookup


def get_opinion_data() -> Dict[str, Dict]:
    opinion_markets = extract_opinion_markets()
    
    print(f"\nLoaded {len(opinion_markets)} active Opinion markets")
    
    price_lookup = get_opinion_price_lookup(opinion_markets)
    
    return price_lookup