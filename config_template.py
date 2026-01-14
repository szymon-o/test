# Configuration Template for API Integration
# Copy this to config.py and add your actual values

# API Configuration for Application 2
API_CONFIG = {
    # Base URL for the API
    'base_url': 'https://api.example-market.com/v1',
    
    # Authentication
    'api_key': 'YOUR_API_KEY_HERE',
    'api_secret': 'YOUR_API_SECRET_HERE',
    
    # API endpoints
    'endpoints': {
        'market_prices': '/markets/{market_id}/prices',
        'market_search': '/markets/search',
        'market_details': '/markets/{market_id}'
    },
    
    # Request settings
    'timeout': 10,  # seconds
    'retry_attempts': 3,
    'rate_limit_delay': 0.5,  # seconds between requests
}

# Arbitrage Settings
ARBITRAGE_CONFIG = {
    # Minimum ROI to consider (percentage)
    'min_roi_percent': 5.0,
    
    # Trading fees (as decimal, e.g., 0.02 = 2%)
    'app1_fee': 0.02,
    'app2_fee': 0.02,
    
    # Minimum profit in dollars
    'min_profit_dollars': 5.0,
    
    # Maximum investment per opportunity
    'max_investment': 1000.0,
    
    # Skip closed or inactive markets
    'skip_inactive': True,
}

# Report Settings
REPORT_CONFIG = {
    # Output file name
    'output_file': 'arbitrage_report.txt',
    
    # Maximum opportunities to include
    'max_opportunities': 100,
    
    # Sort by: 'roi', 'profit', 'cost'
    'sort_by': 'roi',
    
    # Include low-profit opportunities
    'include_low_profit': False,
}

# Example usage in main.py:
"""
# At the top of main.py, add:
try:
    from config import API_CONFIG, ARBITRAGE_CONFIG, REPORT_CONFIG
except ImportError:
    # Use defaults if config.py doesn't exist
    API_CONFIG = {...}
    ARBITRAGE_CONFIG = {...}
    REPORT_CONFIG = {...}
"""

