# Example: How to integrate a real API

"""
This file shows how to modify the mock_api_call function to work with a real API.
"""

import requests
from typing import Dict

# Example 1: Simple REST API integration
def real_api_call_example1(market_id: str, question: str) -> Dict:
    """
    Example: Calling a simple REST API that returns prices directly.
    """
    try:
        # Replace with your actual API endpoint
        api_url = f"https://api.example-market.com/v1/markets/{market_id}/prices"

        # Add authentication if needed
        headers = {
            'Authorization': 'Bearer YOUR_API_KEY_HERE',
            'Content-Type': 'application/json'
        }

        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            'market_id': market_id,
            'source': 'Real_API',
            'yes_price': float(data['outcomes']['yes']['price']),
            'no_price': float(data['outcomes']['no']['price']),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
    except Exception as e:
        print(f"Error fetching data for market {market_id}: {e}")
        return None


# Example 2: API with search/matching by question
def real_api_call_example2(market_id: str, question: str) -> Dict:
    """
    Example: When you need to search for markets by question text.
    """
    try:
        # Search for the market
        search_url = "https://api.example-market.com/v1/markets/search"
        params = {'q': question, 'limit': 1}

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()

        results = response.json()

        if not results or len(results['markets']) == 0:
            print(f"No matching market found for: {question}")
            return None

        market = results['markets'][0]

        return {
            'market_id': market['id'],
            'source': 'Real_API',
            'yes_price': float(market['yes_price']),
            'no_price': float(market['no_price']),
            'timestamp': market.get('timestamp', datetime.now().isoformat())
        }
    except Exception as e:
        print(f"Error searching for market: {e}")
        return None


# Example 3: GraphQL API integration
def real_api_call_example3(market_id: str, question: str) -> Dict:
    """
    Example: Using GraphQL API.
    """
    try:
        graphql_url = "https://api.example-market.com/graphql"

        query = """
        query GetMarketPrices($marketId: String!) {
            market(id: $marketId) {
                id
                outcomes {
                    name
                    price
                }
                lastUpdated
            }
        }
        """

        variables = {'marketId': market_id}

        response = requests.post(
            graphql_url,
            json={'query': query, 'variables': variables},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        market = data['data']['market']

        # Extract yes/no prices
        yes_price = next((o['price'] for o in market['outcomes'] if o['name'].lower() == 'yes'), None)
        no_price = next((o['price'] for o in market['outcomes'] if o['name'].lower() == 'no'), None)

        return {
            'market_id': market_id,
            'source': 'Real_API',
            'yes_price': float(yes_price),
            'no_price': float(no_price),
            'timestamp': market['lastUpdated']
        }
    except Exception as e:
        print(f"Error fetching GraphQL data: {e}")
        return None


# Example 4: With caching to avoid rate limits
from functools import lru_cache
from datetime import datetime, timedelta

# Cache for 5 minutes
@lru_cache(maxsize=1000)
def cached_api_call(market_id: str, cache_key: str) -> Dict:
    """
    Example: Caching API responses to avoid rate limits.
    cache_key includes timestamp rounded to 5-minute intervals.
    """
    try:
        api_url = f"https://api.example-market.com/v1/markets/{market_id}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def real_api_call_with_cache(market_id: str, question: str) -> Dict:
    """Uses cached API call."""
    # Create cache key with 5-minute buckets
    cache_time = datetime.now().replace(second=0, microsecond=0)
    cache_time = cache_time.replace(minute=(cache_time.minute // 5) * 5)
    cache_key = cache_time.isoformat()

    data = cached_api_call(market_id, cache_key)

    if not data:
        return None

    return {
        'market_id': market_id,
        'source': 'Real_API_Cached',
        'yes_price': float(data['yes_price']),
        'no_price': float(data['no_price']),
        'timestamp': data.get('timestamp', datetime.now().isoformat())
    }


# Example 5: Polymarket API (actual example)
def polymarket_api_call(market_id: str, question: str) -> Dict:
    """
    Example: Real Polymarket API integration.
    Note: Requires authentication for some endpoints.
    """
    try:
        # Polymarket CLOB API endpoint
        api_url = f"https://clob.polymarket.com/prices"

        # For market prices, you might need to query by token ID
        # This is a simplified example
        response = requests.get(
            f"https://gamma-api.polymarket.com/markets/{market_id}",
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        # Parse outcome prices
        outcomes = data.get('outcomes', [])
        yes_price = None
        no_price = None

        for outcome in outcomes:
            if outcome.lower() == 'yes':
                yes_price = float(data['outcomePrices'][outcomes.index(outcome)])
            elif outcome.lower() == 'no':
                no_price = float(data['outcomePrices'][outcomes.index(outcome)])

        return {
            'market_id': market_id,
            'source': 'Polymarket',
            'yes_price': yes_price or 0.5,
            'no_price': no_price or 0.5,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching Polymarket data: {e}")
        return None


# How to use in main.py:
# Simply replace the mock_api_call function with one of these examples
# Make sure to install requests: pip install requests

"""
Installation:
pip install requests

Then in main.py, replace:
    def mock_api_call(market_id: str, question: str) -> Dict:
        ...

With:
    from api_examples import real_api_call_example1 as mock_api_call
    # or whichever function you want to use
"""

