import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def setup_railway_environment():
    """Railway-specific environment setup"""
    
    # Railway environment variables
    RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT')
    RAILWAY_PROJECT_ID = os.getenv('RAILWAY_PROJECT_ID')
    
    print(f"🚂 Railway Environment: {RAILWAY_ENVIRONMENT}")
    print(f"🚂 Railway Project ID: {RAILWAY_PROJECT_ID}")
    
    # Set up proxy if needed (Railway doesn't usually need this, but just in case)
    proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
    if proxy_url:
        print(f"🔄 Using proxy: {proxy_url}")
        return {'http': proxy_url, 'https': proxy_url}
    
    return None

def create_railway_session():
    """Create a session optimized for Railway deployment"""
    session = requests.Session()
    
    # Retry strategy for unreliable connections
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Railway-optimized headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Set proxy if available
    proxies = setup_railway_environment()
    if proxies:
        session.proxies.update(proxies)
    
    return session

# Alternative API Configuration
ALTERNATIVE_CRYPTO_APIS = {
    'primary': [
        {
            'name': 'Binance Spot',
            'base_url': 'https://api.binance.com/api/v3',
            'price_endpoint': '/ticker/price',
            'batch_endpoint': '/ticker/24hr'
        },
        {
            'name': 'Binance Futures', 
            'base_url': 'https://fapi.binance.com/fapi/v1',
            'price_endpoint': '/ticker/price',
            'batch_endpoint': '/ticker/24hr'
        }
    ],
    'fallback': [
        {
            'name': 'CoinGecko',
            'base_url': 'https://api.coingecko.com/api/v3',
            'supports_batch': False,
            'rate_limit': 50  # requests per minute
        },
        {
            'name': 'CryptoCompare',
            'base_url': 'https://min-api.cryptocompare.com/data',
            'supports_batch': True,
            'rate_limit': 100
        },
        {
            'name': 'CoinCap',
            'base_url': 'https://api.coincap.io/v2',
            'supports_batch': False,
            'rate_limit': 1000
        }
    ]
} 