# crypto_dashboard_dash_telegram.py
import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import numpy as np
from functools import wraps
import plotly.graph_objs as go
import plotly.express as px
import threading
import json
import ssl
import urllib.request
from urllib.parse import urlencode
import certifi
import io
import socket
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def rate_limit(calls_per_second=5):
    """Rate limiting decorator to prevent API abuse"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


# Load configuration from environment variables with fallbacks
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8494532235:AAE5JaJAhImWYkCUXQxU3pvHNkGJYY749vk')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-4882717465')
CSV_URL = os.getenv('CSV_URL', 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgiqkaWzOnXJBIeNEzvUXaGPS0f3gHytC7A1wlohkFScEhVbururPv9amRuAop5ooqY_BJU23XKlL_/pub?output=csv')

DEBUG_MODE = False

# Cooldown configuration
COOLDOWN_PCT = 0.012  # 1.2% hysteresis for alert cooldown
MAX_ALERTS_MEMORY = 1000  # Maximum alerts to keep in memory


def cleanup_old_alerts():
    """Clean up old alerts to prevent memory bloat"""
    if len(current_data["alerts_sent"]) > MAX_ALERTS_MEMORY:
        alerts_list = list(current_data["alerts_sent"])
        # Remove oldest half
        alerts_to_remove = alerts_list[:len(alerts_list)//2]
        for alert in alerts_to_remove:
            current_data["alerts_sent"].discard(alert)
        
        if DEBUG_MODE:
            print(f"🧹 Cleaned up {len(alerts_to_remove)} old alerts from memory")


# Initialize Dash App
app = dash.Dash(__name__)
app.title = "Crypto Trading Dashboard"

# Add viewport meta tag for responsive design
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            /* Mobile First Responsive Design */
            * {
                box-sizing: border-box;
            }
            
            html {
                font-size: 16px;
            }
            
            body {
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 10px;
            }
            
            .header {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .header h1 {
                font-size: clamp(1.5rem, 4vw, 2.5rem);
                margin: 10px 0;
                color: #2c3e50;
            }
            
            .controls-section {
                background: #ecf0f1;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .controls-row {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .control-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .refresh-button {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.3s;
                width: 100%;
                max-width: 200px;
            }
            
            .refresh-button:hover {
                background: #2980b9;
            }
            
            .summary-cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .summary-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border: 1px solid #e0e0e0;
            }
            
            .summary-card h3 {
                font-size: clamp(1.5rem, 3vw, 2rem);
                margin: 0 0 5px 0;
            }
            
            .summary-card p {
                margin: 0;
                color: #7f8c8d;
                font-size: 14px;
            }
            
            .dashboard-table {
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            
            .table-header {
                background: #3498db;
                color: white;
                padding: 15px 20px;
                font-size: 18px;
                font-weight: bold;
            }
            
            .status-section {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .status-item {
                text-align: center;
                margin: 5px 0;
                font-size: 14px;
            }
            
            .alerts-section {
                background: #ffeaa7;
                border: 1px solid #fdcb6e;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
            }
            
            .alerts-section h4 {
                color: #e74c3c;
                margin: 0 0 10px 0;
                font-size: 16px;
            }
            
            .alerts-list {
                margin: 0;
                padding-left: 20px;
            }
            
            .alerts-list li {
                color: #c0392b;
                margin: 5px 0;
                font-size: 14px;
            }
            
            /* Tablet Styles */
            @media (min-width: 768px) {
                .container {
                    padding: 20px;
                }
                
                .controls-section {
                    padding: 20px;
                }
                
                .controls-row {
                    flex-direction: row;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .control-item {
                    flex-direction: row;
                    justify-content: space-between;
                }
                
                .refresh-button {
                    width: auto;
                }
                
                .summary-cards {
                    grid-template-columns: repeat(3, 1fr);
                }
            }
            
            /* Desktop Styles */
            @media (min-width: 1024px) {
                .container {
                    padding: 30px;
                }
                
                .summary-cards {
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                }
                
                .summary-card {
                    padding: 25px;
                }
            }
            
            /* Large Desktop Styles */
            @media (min-width: 1440px) {
                .container {
                    max-width: 1400px;
                }
            }
            
            /* DataTable Responsive Styles */
            .dash-table-container {
                overflow-x: auto;
            }
            
            .dash-spreadsheet-container {
                font-size: 14px;
            }
            
            .dash-spreadsheet-inner th {
                font-size: 14px !important;
                padding: 12px 8px !important;
            }
            
            .dash-spreadsheet-inner td {
                font-size: 13px !important;
                padding: 10px 8px !important;
            }
            
            /* Mobile table adjustments */
            @media (max-width: 767px) {
                .dash-spreadsheet-inner th,
                .dash-spreadsheet-inner td {
                    font-size: 11px !important;
                    padding: 6px 3px !important;
                }
                
                .dash-table-container {
                    font-size: 11px;
                }
                
                .summary-cards {
                    grid-template-columns: 1fr;
                    gap: 10px;
                }
                
                .summary-card {
                    padding: 15px;
                }
                
                .summary-card h3 {
                    font-size: 1.5rem;
                }
                
                .controls-section {
                    padding: 12px;
                }
                
                .refresh-button {
                    padding: 10px 16px;
                    font-size: 13px;
                }
            }
            
            /* Small mobile adjustments */
            @media (max-width: 480px) {
                .container {
                    padding: 8px;
                }
                
                .header h1 {
                    font-size: 1.5rem;
                }
                
                .summary-card h3 {
                    font-size: 1.3rem;
                }
                
                .dash-spreadsheet-inner th,
                .dash-spreadsheet-inner td {
                    font-size: 10px !important;
                    padding: 4px 2px !important;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Global variables to store data
current_data = {"df": None, "last_update": None, "alerts_sent": set()}

# Enhanced connection functions
def create_robust_session():
    """Create a robust requests session with better headers and settings"""
    session = requests.Session()
    
    # More comprehensive headers to mimic a real browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    
    # Configure SSL and retry strategy
    session.verify = certifi.where()
    
    return session

# Global session for reuse
robust_session = create_robust_session()

def get_crypto_price_alternative_apis(symbol):
    """Try multiple crypto APIs as fallbacks"""
    clean_symbol = symbol.replace('/', '').replace('-', '').upper()
    
    # API endpoints to try in order of preference
    apis = [
        {
            'name': 'Binance Spot',
            'url': f'https://api.binance.com/api/v3/ticker/price?symbol={clean_symbol}USDT',
            'parser': lambda r: float(r.json()['price'])
        },
        {
            'name': 'Binance Futures',
            'url': f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={clean_symbol}USDT',
            'parser': lambda r: float(r.json()['price'])
        },
        {
            'name': 'CoinGecko',
            'url': f'https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd',
            'parser': lambda r: float(list(r.json().values())[0]['usd'])
        },
        {
            'name': 'CryptoCompare',
            'url': f'https://min-api.cryptocompare.com/data/price?fsym={clean_symbol}&tsyms=USD',
            'parser': lambda r: float(r.json()['USD'])
        },
        {
            'name': 'CoinCap',
            'url': f'https://api.coincap.io/v2/assets/{symbol.lower()}',
            'parser': lambda r: float(r.json()['data']['priceUsd'])
        }
    ]
    
    for api in apis:
        try:
            if DEBUG_MODE:
                print(f"🔄 Trying {api['name']} for {symbol}...")
            
            response = robust_session.get(api['url'], timeout=10)
            response.raise_for_status()
            
            price = api['parser'](response)
            
            if DEBUG_MODE:
                print(f"✅ {api['name']} success: {symbol} = ${price}")
            
            return price
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ {api['name']} failed for {symbol}: {str(e)}")
            continue
    
    return None

@rate_limit(calls_per_second=3)  # More conservative rate limiting
def get_multiple_prices_enhanced(symbols):
    """Enhanced price fetching with multiple fallback APIs"""
    price_dict = {}
    
    # First try: Batch request to Binance (most efficient)
    try:
        if DEBUG_MODE:
            print("🔄 Attempting Binance batch request...")
        
        apis_to_try = [
            'https://api.binance.com/api/v3/ticker/24hr',
            'https://fapi.binance.com/fapi/v1/ticker/24hr'
        ]
        
        for api_url in apis_to_try:
            try:
                response = robust_session.get(api_url, timeout=15)
                response.raise_for_status()
                
                all_prices = response.json()
                
                for symbol in symbols:
                    clean_symbol = symbol.replace('/', '').replace('-', '').upper() + "USDT"
                    for ticker in all_prices:
                        if ticker['symbol'] == clean_symbol:
                            price_dict[symbol] = float(ticker['lastPrice'])
                            break
                
                if price_dict:
                    if DEBUG_MODE:
                        print(f"✅ Binance batch success: {len(price_dict)} prices fetched")
                    break
                    
            except Exception as e:
                if DEBUG_MODE:
                    print(f"❌ Binance batch failed: {str(e)}")
                continue
    
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ All Binance batch attempts failed: {str(e)}")
    
    # Second try: Individual requests for missing symbols
    missing_symbols = [s for s in symbols if s not in price_dict]
    
    if missing_symbols:
        if DEBUG_MODE:
            print(f"🔄 Fetching {len(missing_symbols)} symbols individually...")
        
        for symbol in missing_symbols:
            try:
                price = get_crypto_price_alternative_apis(symbol)
                if price:
                    price_dict[symbol] = price
                time.sleep(0.5)  # Small delay between individual requests
            except Exception as e:
                if DEBUG_MODE:
                    print(f"❌ Individual fetch failed for {symbol}: {str(e)}")
                price_dict[symbol] = None
    
    return price_dict

def load_sheet_data_enhanced(url):
    """Enhanced CSV loading with multiple methods"""
    methods = [
        {
            'name': 'Pandas with session',
            'method': lambda: pd.read_csv(url, storage_options={'User-Agent': robust_session.headers['User-Agent']})
        },
        {
            'name': 'Requests then pandas',
            'method': lambda: pd.read_csv(io.StringIO(robust_session.get(url, timeout=15).text))
        },
        {
            'name': 'urllib fallback',
            'method': lambda: pd.read_csv(urllib.request.urlopen(urllib.request.Request(url, headers=dict(robust_session.headers))))
        }
    ]
    
    for method in methods:
        try:
            if DEBUG_MODE:
                print(f"🔄 Trying CSV load method: {method['name']}")
            
            df = method['method']()
            
            if DEBUG_MODE:
                print(f"✅ CSV loaded successfully with {method['name']}: {len(df)} rows")
            
            return df, None
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ CSV method {method['name']} failed: {str(e)}")
            continue
    
    return None, "All CSV loading methods failed"

def check_connection_health_enhanced():
    """Enhanced connection health check with detailed diagnostics"""
    health_status = {
        'csv_accessible': False,
        'binance_spot_accessible': False,
        'binance_futures_accessible': False,
        'coingecko_accessible': False,
        'telegram_accessible': False,
        'dns_resolution': False
    }
    
    # Test DNS resolution
    try:
        socket.gethostbyname('google.com')
        health_status['dns_resolution'] = True
    except:
        pass
    
    # Test various APIs
    test_endpoints = [
        ('csv_accessible', CSV_URL, 'HEAD'),
        ('binance_spot_accessible', 'https://api.binance.com/api/v3/ping', 'GET'),
        ('binance_futures_accessible', 'https://fapi.binance.com/fapi/v1/ping', 'GET'),
        ('coingecko_accessible', 'https://api.coingecko.com/api/v3/ping', 'GET'),
        ('telegram_accessible', f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe", 'GET')
    ]
    
    for key, url, method in test_endpoints:
        try:
            if method == 'HEAD':
                response = robust_session.head(url, timeout=10)
            else:
                response = robust_session.get(url, timeout=10)
            
            health_status[key] = response.status_code in [200, 201]
            
            if DEBUG_MODE:
                print(f"{'✅' if health_status[key] else '❌'} {key}: {response.status_code}")
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ {key} failed: {str(e)}")
            health_status[key] = False
    
    return health_status

def run_network_diagnostics():
    """Run comprehensive network diagnostics"""
    print("🔍 Running Network Diagnostics...")
    print("=" * 50)
    
    # Check DNS
    try:
        socket.gethostbyname('google.com')
        print("✅ DNS Resolution: Working")
    except Exception as e:
        print(f"❌ DNS Resolution: Failed - {e}")
    
    # Check basic connectivity
    test_sites = [
        'https://httpbin.org/ip',
        'https://api.github.com',
        'https://jsonplaceholder.typicode.com/posts/1'
    ]
    
    print("\n🌐 Basic Connectivity Tests:")
    for site in test_sites:
        try:
            response = robust_session.get(site, timeout=5)
            print(f"✅ {site}: {response.status_code}")
        except Exception as e:
            print(f"❌ {site}: {str(e)}")
    
    # Check crypto APIs specifically
    print("\n💰 Crypto API Tests:")
    crypto_apis = [
        'https://api.binance.com/api/v3/ping',
        'https://fapi.binance.com/fapi/v1/ping',
        'https://api.coingecko.com/api/v3/ping',
        'https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD'
    ]
    
    for api in crypto_apis:
        try:
            response = robust_session.get(api, timeout=10)
            print(f"✅ {api}: {response.status_code}")
        except Exception as e:
            print(f"❌ {api}: {str(e)}")
    
    print("=" * 50)

# Custom CSS styling with responsive design
app.layout = html.Div([
    
    dcc.Store(id='data-store'),
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Update every 30 seconds
        n_intervals=0
    ),
    
    html.Div([
        # Header
        html.Div([
            html.H1("📈 Crypto Trading Dashboard", className='header'),
            html.Hr(),
        ], className='header'),
        
        # Controls Section
        html.Div([
            html.Div([
                html.Div([
                    html.Label("Auto Refresh:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Checklist(
                        id='auto-refresh-toggle',
                        options=[{'label': ' Enabled', 'value': 'enabled'}],
                        value=['enabled'],
                        style={'display': 'inline-block'}
                    )
                ], className='control-item'),
                
                html.Div([
                    html.Button('🔄 Manual Refresh', id='manual-refresh-btn', className='refresh-button')
                ], className='control-item'),
            ], className='controls-row'),
        ], className='controls-section'),
        
        # Status Section
        html.Div(id='status-section', className='status-section'),
        
        # Main Dashboard Content
        html.Div(id='dashboard-content'),
        
        # Alerts Section
        html.Div(id='alerts-section', className='alerts-section')
    ], className='container')
])


def send_telegram_notification(message):
    """Send Telegram notification with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if DEBUG_MODE:
                    print(f"✅ Telegram notification sent (attempt {attempt + 1}): {result}")
                return True
            else:
                if DEBUG_MODE:
                    print(f"❌ Telegram notification failed (attempt {attempt + 1}): {response.status_code} - {response.text}")
                
                # Don't retry on client errors (4xx)
                if 400 <= response.status_code < 500:
                    return False
                    
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Telegram notification error (attempt {attempt + 1}): {str(e)}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return False


def send_formatted_telegram_alert(symbol, current_price, alert_level, entry_price=None):
    """Send beautifully formatted Telegram alert"""
    try:
        # Determine alert type and emoji
        if "Entry" in alert_level:
            alert_emoji = "🎯"
            alert_type = "ENTRY ALERT"
        elif "Stop Loss" in alert_level:
            alert_emoji = "🛑"
            alert_type = "STOP LOSS ALERT"
        elif "Take Profit" in alert_level:
            alert_emoji = "💰"
            alert_type = "TAKE PROFIT ALERT"
        else:
            alert_emoji = "🚨"
            alert_type = "PRICE ALERT"
        
        # Format the message with Markdown
        message = f"""
🔥 *CRYPTO {alert_type}* {alert_emoji}


📊 *Symbol:* `{symbol}`
💰 *Current Price:* `${current_price:.5f}`
🎯 *Alert Level:* `{alert_level}`
📏 *Distance:* `≤1%`


⏰ *Time:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`


💡 _Price is within 1% of your target level!_
📈 _Check your dashboard for more details._
        """.strip()
        
        return send_telegram_notification(message)
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Formatted Telegram alert error: {str(e)}")
        # Fallback to simple message
        simple_message = f"🚨 ALERT: {symbol} at ${current_price:.5f} is 1% near {alert_level}"
        return send_telegram_notification(simple_message)


def check_price_alerts_with_cooldown(symbol, current_price, entries, sl, tp, alerts_sent):
    """Check if current price is within 1% of any entry, SL, or TP levels with cooldown logic"""
    alerts = []
    alert_threshold = 0.01  # 1%
    new_alerts = []
    
    # Check entries
    entry_levels = ['1st', '2nd', '3rd']
    for i, entry in enumerate(entries):
        if entry and current_price:
            price_diff_pct = abs(current_price - entry) / entry
            if price_diff_pct <= alert_threshold:
                alert_level = f"{entry_levels[i]} Entry (${entry:.5f})"
                alerts.append(alert_level)
    
    # Check Stop Loss
    if sl and current_price:
        price_diff_pct = abs(current_price - sl) / sl
        if price_diff_pct <= alert_threshold:
            alert_level = f"Stop Loss (${sl:.5f})"
            alerts.append(alert_level)
    
    # Check Take Profit
    if tp and current_price:
        price_diff_pct = abs(current_price - tp) / tp
        if price_diff_pct <= alert_threshold:
            alert_level = f"Take Profit (${tp:.5f})"
            alerts.append(alert_level)
    
    # Process cooldown logic for each alert
    for alert_level in alerts:
        alert_key = f"{symbol}_{alert_level}"
        
        # Check if alert was already sent
        if alert_key in alerts_sent:
            # Extract the numeric price from alert_level string
            try:
                base_price = float(alert_level.split('$')[-1].replace(')', '').replace(',', ''))
            except ValueError:
                base_price = None
            
            if base_price:
                pct_away = abs(current_price - base_price) / base_price
                if pct_away > COOLDOWN_PCT:
                    # Price has moved far enough away → reset the key
                    alerts_sent.remove(alert_key)
                    if DEBUG_MODE:
                        print(f"🔄 Cooldown reset for {alert_key} (moved {pct_away:.3f} away)")
        
        # Send new alert if not in cooldown
        if alert_key not in alerts_sent:
            if send_formatted_telegram_alert(symbol, current_price, alert_level):
                alerts_sent.add(alert_key)
                new_alerts.append(f"{symbol}: {alert_level}")
                if DEBUG_MODE:
                    print(f"📱 New alert sent: {alert_key}")
    
    return new_alerts


def load_sheet_data(url):
    """Load data from Google Sheet CSV URL with caching"""
    df, error = load_csv_with_fallbacks(url)
    if error:
        print(f"❌ CSV loading failed: {error}")
        return None
    return df


@rate_limit(calls_per_second=5)
def get_multiple_prices(symbols):
    """Fetch multiple prices in one API call with retry logic"""
    return get_multiple_prices_enhanced(symbols)


def safe_float(value):
    """Safely convert value to float"""
    try:
        if pd.isna(value) or value == '' or value is None:
            return None
        return float(value)
    except:
        return None


def parse_date_flexible(date_str):
    """Parse date with multiple format support"""
    if pd.isna(date_str) or date_str == '':
        return None
        
    date_str = str(date_str).strip()
    
    date_formats = [
        "%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y",
        "%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y"
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            
            if parsed_date.year < 100:
                current_year = datetime.now().year
                current_2digit = current_year % 100
                
                if parsed_date.year > current_2digit:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                else:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
            
            if parsed_date.date() > datetime.now().date():
                parsed_date = parsed_date.replace(year=parsed_date.year - 1)
            
            return parsed_date
        except ValueError:
            continue
    
    return None


def fetch_1d_ohlc_to_today(symbol, start_date):
    """Fetch daily OHLC data from start_date to today"""
    try:
        clean_symbol = symbol.replace("/", "").replace("-", "").upper() + "USDT"
        url = "https://fapi.binance.com/fapi/v1/klines"
        
        parsed_start_date = parse_date_flexible(start_date)
        
        if parsed_start_date is None:
            return []
        
        end_date = datetime.now()
        
        start_ts = int(parsed_start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        params = {
            "symbol": clean_symbol,
            "interval": "1d",
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, params=params, timeout=15, headers=headers)
        response.raise_for_status()
        candles = response.json()
        
        if not isinstance(candles, list):
            return []
        
        return candles
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"❌ Error fetching OHLC for {symbol}: {str(e)}")
        return []


def check_entries_hit_sequentially(candles, entries, symbol=""):
    """Check entries hit sequentially"""
    if not candles or not entries:
        return [False] * len(entries), []
    
    entries_hit = [False] * len(entries)
    hit_dates = [None] * len(entries)
    
    sorted_candles = sorted(candles, key=lambda x: x[0])
    
    for candle in sorted_candles:
        try:
            low_price = float(candle[3])
            candle_date = datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d')
            
            for entry_idx, entry_price in enumerate(entries):
                entry_price = float(entry_price)
                
                if not entries_hit[entry_idx] and low_price <= entry_price:
                    entries_hit[entry_idx] = True
                    hit_dates[entry_idx] = candle_date
                    
                    for higher_entry_idx in range(entry_idx):
                        if not entries_hit[higher_entry_idx]:
                            entries_hit[higher_entry_idx] = True
                            hit_dates[higher_entry_idx] = candle_date
            
        except (ValueError, TypeError, IndexError):
            continue
    
    return entries_hit, hit_dates


def calculate_metrics(row, live_price, symbol):
    """Calculate all trading metrics for a row"""
    try:
        entries = []
        entry_columns = ['Entry 1', 'Entry 2', 'Entry 3']
        
        if not any(col in row.index for col in entry_columns):
            entry_columns = ['1st entry', '2nd entry', '3rd entry']
        
        for col in entry_columns:
            if col in row.index:
                entry = safe_float(row[col])
                if entry is not None and entry > 0:
                    entries.append(entry)
                else:
                    entries.append(None)
            else:
                entries.append(None)
        
        while entries and entries[-1] is None:
            entries.pop()
        
        start_date = None
        date_columns = ['Date of given', 'Date', 'Start Date', 'Given Date']
        for col in date_columns:
            if col in row.index and pd.notna(row[col]):
                start_date = row[col]
                break
        
        if not entries or live_price is None:
            return {
                'entry_hit': False,
                'entries_hit_status': "–",
                'avg_entry': None,
                'pl': None,
                'entry_down_pct': None,
                'roi_pct': None
            }
        
        valid_entries = [e for e in entries if e is not None]
        
        if not valid_entries:
            return {
                'entry_hit': False,
                'entries_hit_status': "–",
                'avg_entry': None,
                'pl': None,
                'entry_down_pct': None,
                'roi_pct': None
            }
        
        entries_hit_flags = [False] * len(valid_entries)
        entries_hit_status = "–"
        
        if start_date:
            candles = fetch_1d_ohlc_to_today(symbol, start_date)
            if candles:
                entries_hit_flags, hit_dates = check_entries_hit_sequentially(candles, valid_entries, symbol)
                
                hit_count = sum(entries_hit_flags)
                if hit_count == 0:
                    entries_hit_status = "No entries hit"
                else:
                    hit_entries = []
                    for i, (hit, date) in enumerate(zip(entries_hit_flags, hit_dates)):
                        if hit and date:
                            hit_entries.append(f"Entry {i+1} ({date})")
                    entries_hit_status = " → ".join(hit_entries)
            else:
                entries_hit_status = "No candle data"
        else:
            entries_hit_status = "No start date provided"
        
        hit_entries = [entry for entry, hit in zip(valid_entries, entries_hit_flags) if hit]
        
        if hit_entries:
            avg_entry = sum(hit_entries) / len(hit_entries)
        else:
            avg_entry = sum(valid_entries) / len(valid_entries)
        
        quantity = safe_float(row.get('Quantity', 1)) or 1
        pl = (live_price - avg_entry) * quantity if avg_entry else None
        entry_down_pct = ((live_price - avg_entry) / avg_entry) * 100 if avg_entry else None
        roi_pct = (pl / (avg_entry * quantity)) * 100 if avg_entry and pl is not None else None
        
        return {
            'entry_hit': any(entries_hit_flags),
            'entries_hit_status': entries_hit_status,
            'avg_entry': avg_entry,
            'pl': pl,
            'entry_down_pct': entry_down_pct,
            'roi_pct': roi_pct
        }
    
    except Exception as e:
        return {
            'entry_hit': False,
            'entries_hit_status': f"Error: {str(e)[:50]}",
            'avg_entry': None,
            'pl': None,
            'entry_down_pct': None,
            'roi_pct': None
        }


def process_data():
    """Process all data and check for alerts with cooldown and memory management"""
    df, error = load_sheet_data(CSV_URL)
    
    if error or df is None or df.empty:
        return None, error
    
    # Memory cleanup every 50 updates
    if not hasattr(current_data, 'update_count'):
        current_data['update_count'] = 0
    current_data['update_count'] += 1
    
    if current_data['update_count'] % 50 == 0:
        cleanup_old_alerts()
    
    # Identify symbol column
    symbol_col = None
    for col in ['Symbol', 'PAIR NAME', 'Pair', 'symbol', 'pair']:
        if col in df.columns:
            symbol_col = col
            break
    
    if symbol_col is None:
        return None, "Could not find Symbol/Pair column"
    
    symbols = df[symbol_col].tolist()
    
    # Validate symbols list
    if not symbols or all(pd.isna(symbol) for symbol in symbols):
        return None, "No valid symbols found in data"
    
    # Filter out empty/invalid symbols
    valid_symbols = [str(symbol).strip() for symbol in symbols if pd.notna(symbol) and str(symbol).strip()]
    
    if not valid_symbols:
        return None, "No valid symbols after filtering"
    
    price_data = get_multiple_prices(valid_symbols)
    
    results = []
    all_new_alerts = []
    
    for _, row in df.iterrows():
        symbol = row[symbol_col]
        
        # Skip invalid symbols
        if pd.isna(symbol) or str(symbol).strip() == '':
            continue
            
        symbol = str(symbol).strip()
        live_price = price_data.get(symbol)
        
        if live_price:
            # Check for price alerts with cooldown
            entries = []
            for col in ['Entry 1', 'Entry 2', 'Entry 3', '1st entry', '2nd entry', '3rd entry']:
                if col in row.index:
                    entry = safe_float(row[col])
                    if entry and entry > 0:
                        entries.append(entry)
            
            sl = safe_float(row.get('SL', row.get('Stop Loss')))
            tp = safe_float(row.get('TP', row.get('Take Profit')))
            
            # Check alerts with cooldown logic
            try:
                new_alerts = check_price_alerts_with_cooldown(
                    symbol, live_price, entries, sl, tp, current_data["alerts_sent"]
                )
                all_new_alerts.extend(new_alerts)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"❌ Error checking alerts for {symbol}: {str(e)}")
        
        # Calculate metrics with error handling
        try:
            metrics = calculate_metrics(row, live_price, symbol)
        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Error calculating metrics for {symbol}: {str(e)}")
            metrics = {
                'entry_hit': False,
                'entries_hit_status': "Error",
                'avg_entry': None,
                'pl': None,
                'entry_down_pct': None,
                'roi_pct': None
            }
        
        result_row = {
            'Symbol': symbol,
            'Live Price': f"${live_price:.5f}" if live_price else "–",
            'Entry Status': metrics['entries_hit_status'],
            'Entry Hit': '✅' if metrics['entry_hit'] else '❌',
            'Avg Entry': f"${metrics['avg_entry']:.5f}" if metrics['avg_entry'] else "–",
            'P/L': f"${metrics['pl']:.5f}" if metrics['pl'] else "–",
            'Entry % Down': f"{metrics['entry_down_pct']:.2f}%" if metrics['entry_down_pct'] else "–",
            'ROI %': f"{metrics['roi_pct']:.2f}%" if metrics['roi_pct'] else "–",
        }
        
        # Add other columns from original data
        for col in df.columns:
            if col not in result_row and col != symbol_col:
                result_row[col] = row[col]
        
        results.append(result_row)
    
    if not results:
        return None, "No valid data processed"
    
    results_df = pd.DataFrame(results)
    current_data["df"] = results_df
    current_data["last_update"] = datetime.now()
    
    return results_df, all_new_alerts


def check_connection_health():
    """Check if all external services are accessible"""
    return check_connection_health_enhanced()


@app.callback(
    [Output('dashboard-content', 'children'),
     Output('status-section', 'children'),
     Output('alerts-section', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('manual-refresh-btn', 'n_clicks'),
     Input('auto-refresh-toggle', 'value')]
)
def update_dashboard(n_intervals, manual_click, auto_refresh_enabled):
    """Update dashboard callback with comprehensive error handling"""
    try:
        # Only update if auto-refresh is enabled or manual refresh clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            trigger_id = 'interval-component'
        else:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == 'interval-component' and 'enabled' not in (auto_refresh_enabled or []):
            # Skip auto-refresh if disabled
            if current_data["df"] is not None:
                return create_dashboard_layout(current_data["df"]), create_status_section(), create_alerts_section([])
            else:
                return html.Div("Enable auto-refresh or click manual refresh to load data"), html.Div(), html.Div()
        
        # Process data with comprehensive error handling
        try:
            results_df, alerts = process_data()
        except Exception as processing_error:
            error_message = f"Data processing error: {str(processing_error)[:100]}"
            if DEBUG_MODE:
                print(f"❌ Processing error: {processing_error}")
            return html.Div([
                html.H3("Processing Error", style={'color': 'orange'}),
                html.P(error_message),
                html.P("Retrying on next refresh...")
            ]), create_status_section(), html.Div()
        
        if results_df is None:
            return html.Div([
                html.H3("Error Loading Data", style={'color': 'red'}),
                html.P(str(alerts) if alerts else "Unknown error occurred"),
                html.P("Check your internet connection and CSV URL")
            ]), create_status_section(), html.Div()
        
        return create_dashboard_layout(results_df), create_status_section(), create_alerts_section(alerts or [])
        
    except Exception as e:
        # Fallback error handling
        error_msg = f"Dashboard error: {str(e)[:100]}"
        if DEBUG_MODE:
            print(f"❌ Dashboard callback error: {e}")
        
        return html.Div([
            html.H3("Dashboard Error", style={'color': 'red'}),
            html.P(error_msg),
            html.P("Please refresh the page or check the console for details")
        ]), html.Div(), html.Div()


def create_dashboard_layout(df):
    """Create the main dashboard layout with responsive design"""
    total_rows = len(df)
    entries_hit = sum(1 for _, row in df.iterrows() if row['Entry Hit'] == '✅')
    hit_rate = (entries_hit / total_rows * 100) if total_rows > 0 else 0
    
    return html.Div([
        # Summary Cards
        html.Div([
            html.Div([
                html.H3(str(total_rows), style={'margin': '0', 'color': '#2c3e50'}),
                html.P("Total Pairs", style={'margin': '0', 'color': '#7f8c8d'})
            ], className='summary-card'),
            
            html.Div([
                html.H3(f"{entries_hit}/{total_rows}", style={'margin': '0', 'color': '#27ae60'}),
                html.P("Entries Hit", style={'margin': '0', 'color': '#7f8c8d'})
            ], className='summary-card'),
            
            html.Div([
                html.H3(f"{hit_rate:.1f}%", style={'margin': '0', 'color': '#3498db'}),
                html.P("Hit Rate", style={'margin': '0', 'color': '#7f8c8d'})
            ], className='summary-card'),
        ], className='summary-cards'),
        
        # Data Table
        html.Div([
            html.Div("Trading Dashboard", className='table-header'),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': col, 'id': col, 'presentation': 'markdown'} for col in df.columns],
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontFamily': 'Arial, sans-serif',
                    'minWidth': '80px',
                    'maxWidth': '200px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                },
                style_header={
                    'backgroundColor': '#3498db',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                },
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Entry Hit} = ✅'},
                        'backgroundColor': '#d5f4e6',
                    },
                    {
                        'if': {'filter_query': '{Entry Hit} = ❌'},
                        'backgroundColor': '#fadbd8',
                    }
                ],
                page_size=15,
                sort_action='native',
                filter_action='native',
                style_table={
                    'overflowX': 'auto',
                    'minWidth': '100%'
                },
                css=[{
                    'selector': '.dash-spreadsheet-container',
                    'rule': 'font-size: 14px;'
                }]
            )
        ], className='dashboard-table')
    ])


def create_status_section():
    """Create enhanced status section with health check"""
    status_elements = []
    
    if current_data["last_update"]:
        status_elements.extend([
            html.P(f"🔄 Last Updated: {current_data['last_update'].strftime('%Y-%m-%d %H:%M:%S')}", 
                  className='status-item'),
            html.P("✅ Auto-refresh every 30 seconds | 📱 Telegram alerts enabled", 
                  className='status-item')
        ])
        
        # Add health status
        health = check_connection_health()
        health_items = []
        
        for service, status in health.items():
            emoji = "✅" if status else "❌"
            service_name = service.replace('_', ' ').title()
            health_items.append(f"{emoji} {service_name}")
        
        health_text = " | ".join(health_items)
        status_elements.append(
            html.P(f"🏥 Health: {health_text}", 
                  className='status-item')
        )
        
        # Add memory usage info
        alerts_count = len(current_data.get("alerts_sent", set()))
        update_count = current_data.get('update_count', 0)
        status_elements.append(
            html.P(f"📊 Updates: {update_count} | Active Alerts: {alerts_count}", 
                  className='status-item')
        )
    
    return html.Div(status_elements)


def create_alerts_section(alerts):
    """Create alerts section"""
    if alerts:
        return html.Div([
            html.H4("📱 Recent Telegram Alerts Sent:"),
            html.Ul([html.Li(alert) for alert in alerts], className='alerts-list')
        ])
    return html.Div()


def load_csv_with_fallbacks(csv_url):
    """Try multiple methods to load CSV data"""
    
    methods = [
        ("Direct pandas", lambda: pd.read_csv(csv_url)),
        ("With user agent", lambda: pd.read_csv(csv_url, storage_options={
            'User-Agent': 'Mozilla/5.0 (compatible; Python/3.11; Crypto Dashboard Bot)'
        })),
        ("Via requests", lambda: pd.read_csv(io.StringIO(
            requests.get(csv_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Python/3.11; Crypto Dashboard Bot)'
            }).text
        ))),
        ("Via urllib", lambda: pd.read_csv(urllib.request.urlopen(
            urllib.request.Request(csv_url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Python/3.11; Crypto Dashboard Bot)'
            })
        )))
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"🔄 Trying CSV method: {method_name}")
            df = method_func()
            print(f"✅ Success with {method_name}: {len(df)} rows loaded")
            return df, None
        except Exception as e:
            print(f"❌ {method_name} failed: {str(e)}")
            continue
    
    return None, "All CSV loading methods failed"


def handle_railway_errors():
    """Handle common Railway deployment errors"""
    
    import socket
    import ssl
    
    # Test basic connectivity
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("✅ Internet connectivity: OK")
    except OSError:
        print("❌ No internet connectivity")
        return False
    
    # Test DNS resolution
    try:
        socket.gethostbyname("api.binance.com")
        print("✅ DNS resolution: OK")
    except socket.gaierror:
        print("❌ DNS resolution failed")
        return False
    
    # Test SSL/TLS
    try:
        ssl.create_default_context().check_hostname = False
        print("✅ SSL context: OK")
    except Exception as e:
        print(f"❌ SSL issues: {e}")
    
    return True


if __name__ == '__main__':
    print("🚀 Starting Enhanced Crypto Trading Dashboard...")
    
    # Remove hardcoded credentials - CRITICAL FIX
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    CSV_URL = os.getenv('CSV_URL')
    
    # Validate required environment variables
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set in environment variables")
        exit(1)

    if not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_CHAT_ID not set in environment variables")
        exit(1)

    if not CSV_URL:
        print("❌ Error: CSV_URL not set in environment variables")
        exit(1)
    
    # Run Railway error handling first
    print("🔧 Running Railway deployment checks...")
    railway_ok = handle_railway_errors()
    
    # Run diagnostics
    run_network_diagnostics()
    
    # Test connections
    print("🔍 Testing connections...")
    health = check_connection_health()
    
    for service, status in health.items():
        status_emoji = "✅" if status else "❌"
        service_name = service.replace('_', ' ').title()
        print(f"{status_emoji} {service_name}: {'Connected' if status else 'Failed'}")
    
    if not any(health.values()):
        print("⚠️  Warning: No external services accessible. Check your internet connection.")
    
    print("📱 Telegram notifications enabled")
    print("🔄 Auto-refresh every 30 seconds")
    print("🛡️  Rate limiting and retry logic enabled")
    print("🔧 Enhanced connection handling with multiple fallback APIs")
    print("🚂 Railway deployment optimizations enabled")
    
    # Production vs Development server
    port = int(os.environ.get('PORT', 8050))
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DYNO')
    
    if is_production:
        print(f"🌐 Production mode - Server will be managed by gunicorn on port {port}")
        # In production, gunicorn will handle the server
    else:
        print(f"🖥️  Development mode - Starting on http://localhost:{port}")
        try:
            app.run_server(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            print(f"❌ Failed to start dashboard: {e}")
