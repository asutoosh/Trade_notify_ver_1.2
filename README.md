# 🚀 Enhanced Crypto Trading Dashboard

A responsive, real-time crypto trading dashboard with Telegram alerts, multiple API fallbacks, and comprehensive network diagnostics.

## ✨ Features

- **📊 Real-time Dashboard**: Live crypto price monitoring with Plotly Dash
- **📱 Telegram Alerts**: Instant notifications when prices hit target levels
- **🔄 Multiple API Fallbacks**: 5 different crypto APIs for maximum reliability
- **📱 Responsive Design**: Works perfectly on mobile, tablet, and desktop
- **🛡️ Enhanced Security**: Environment variables for sensitive data
- **🔧 Network Diagnostics**: Comprehensive connection health monitoring
- **⚡ Rate Limiting**: Intelligent API rate limiting to prevent blocks
- **🧹 Memory Management**: Automatic cleanup of old alerts

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# CSV Data Source
CSV_URL=your_google_sheets_csv_url_here

# Optional: Debug Mode
DEBUG_MODE=False
```

### 3. Get Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token to your `.env` file

### 4. Get Telegram Chat ID
1. Add your bot to a group or start a chat
2. Send a message to the bot
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find your chat ID in the response

### 5. Prepare Your CSV Data
Your Google Sheets should have these columns:
- **Symbol/Pair**: Crypto symbol (e.g., BTC, ETH)
- **Entry 1/2/3**: Entry price levels
- **SL**: Stop Loss price
- **TP**: Take Profit price
- **Date**: Start date for analysis

## 🚀 Running the Dashboard

### Local Development
```bash
python g.py
```

### Production Deployment
```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export CSV_URL="your_csv_url"

# Run the dashboard
python g.py
```

## 🌐 Deployment Options

### Heroku
1. Create a `Procfile`:
```
web: python g.py
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

### Railway
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard
3. Deploy automatically

### DigitalOcean App Platform
1. Connect your repository
2. Set environment variables
3. Deploy with automatic scaling

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8050

CMD ["python", "g.py"]
```

## 📱 Dashboard Features

### Real-time Monitoring
- Live price updates every 30 seconds
- Entry hit analysis with historical data
- P/L calculations and ROI tracking
- Responsive data tables with sorting/filtering

### Alert System
- **Entry Alerts**: When price approaches entry levels (≤1%)
- **Stop Loss Alerts**: When price nears stop loss
- **Take Profit Alerts**: When price approaches profit targets
- **Cooldown Logic**: Prevents spam with 1.2% hysteresis

### Network Reliability
- **5 API Fallbacks**: Binance Spot, Binance Futures, CoinGecko, CryptoCompare, CoinCap
- **Enhanced Headers**: Browser-like requests to avoid blocks
- **SSL Verification**: Proper certificate handling
- **Retry Logic**: Exponential backoff for failed requests

## 🔧 Configuration Options

### Rate Limiting
```python
# Adjust in g.py
@rate_limit(calls_per_second=3)  # More conservative
@rate_limit(calls_per_second=5)  # Default
@rate_limit(calls_per_second=10) # More aggressive
```

### Alert Thresholds
```python
# Adjust in g.py
alert_threshold = 0.01  # 1% alert distance
COOLDOWN_PCT = 0.012   # 1.2% cooldown hysteresis
```

### Update Intervals
```python
# Adjust in g.py
interval=30*1000  # 30 seconds (milliseconds)
```

## 🏥 Health Monitoring

The dashboard includes comprehensive health checks:
- **DNS Resolution**: Basic connectivity
- **API Accessibility**: All crypto APIs tested
- **CSV Loading**: Multiple fallback methods
- **Telegram Connectivity**: Bot communication
- **Memory Usage**: Alert cleanup monitoring

## 🛡️ Security Features

- **Environment Variables**: No hardcoded secrets
- **SSL Verification**: Proper certificate validation
- **Rate Limiting**: Prevents API abuse
- **Error Handling**: Graceful failure recovery
- **Input Validation**: Safe data processing

## 📊 Performance Optimizations

- **Batch API Requests**: Efficient price fetching
- **Memory Management**: Automatic cleanup
- **Caching**: Session reuse for requests
- **Lazy Loading**: Data loaded on demand
- **Responsive Design**: Optimized for all devices

## 🐛 Troubleshooting

### Common Issues

1. **"Telegram credentials not configured"**
   - Check your `.env` file
   - Verify bot token and chat ID

2. **"CSV URL not configured"**
   - Ensure your Google Sheets is published to web
   - Check the CSV export URL

3. **"No external services accessible"**
   - Check your internet connection
   - Verify firewall settings
   - Try running network diagnostics

4. **Dashboard not loading**
   - Check if port 8050 is available
   - Verify all dependencies are installed
   - Check console for error messages

### Debug Mode
Enable detailed logging by setting `DEBUG_MODE=True` in your `.env` file.

## 📈 Usage Tips

1. **Start Small**: Test with a few crypto pairs first
2. **Monitor Alerts**: Check Telegram for alert delivery
3. **Regular Updates**: Keep your CSV data current
4. **Health Checks**: Monitor the status section
5. **Backup Data**: Keep copies of your trading data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the console logs
3. Enable debug mode for detailed information
4. Create an issue with detailed error messages

---

**Happy Trading! 📈💰** 