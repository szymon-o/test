from typing import Dict, Optional


# polymarket slug to opinion market ID mapping
MARKET_CONFIGS: Dict[str, Optional[int]] = {
    # these slugs appears in predict dot fun and opinion markets
    "metamask-fdv-above-one-day-after-launch": 189,
    "edgex-fdv-above-one-day-after-launch": 98,
    "opensea-fdv-above-one-day-after-launch": 173,
    "will-metamask-launch-a-token-in-2025": 118,
    "megaeth-market-cap-fdv-one-day-after-launch": 67,
    "opinion-fdv-above-one-day-after-launch": None,
    "based-fdv-above-one-day-after-launch": 97,
    "will-base-launch-a-token-in-2025-341": 119,
    "infinex-fdv-above-one-day-after-launch": 184,

    # these slugs appear only in opinion markets
    "rainbow-fdv-above-one-day-after-launch-676": 244,
    "backpack-fdv-above-one-day-after-launch": 95,
    "gensyn-fdv-above-one-day-after-launch": 194,
    "usdai-fdv-above-one-day-after-launch": 183,
    "standx-fdv-above-one-day-after-launch": 96,
}

POLYMARKET_API_EVENTS_URL = "https://gamma-api.polymarket.com/events"
OPINION_API_DATA_URL = "https://openapi.opinion.trade/openapi/market/categorical/{marketId}"
OPINION_TOKEN_URL = "https://openapi.opinion.trade/openapi/token/latest-price"
