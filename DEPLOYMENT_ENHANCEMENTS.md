# Railway Deployment Enhancements

## Overview
This document outlines the recent enhancements made to improve Railway deployment reliability and handle common deployment issues.

## Key Improvements

### 1. Railway-Specific Optimizations
- **Enhanced Headers**: Added proxy headers (`X-Forwarded-For`, `X-Real-IP`) to avoid IP blocking
- **Retry Strategy**: Implemented exponential backoff for failed requests
- **Rate Limiting**: More conservative rate limiting (2 calls/second) for Railway environment
- **API Prioritization**: Prioritizes CoinGecko and CryptoCompare over Binance APIs

### 2. Connection Health Monitoring
- **Comprehensive Diagnostics**: Tests all external services with detailed status reporting
- **IP Blocking Detection**: Specifically handles 451 status codes from Binance APIs
- **Fallback Mechanisms**: Multiple CSV loading methods and crypto API alternatives

### 3. Environment Detection
- **Automatic Detection**: Detects Railway environment automatically
- **Port Configuration**: Uses Railway's PORT environment variable
- **Production Mode**: Disables debug features in production

## Deployment Steps

### 1. Environment Variables
Set these in your Railway project:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
CSV_URL=your_google_sheets_csv_url_here
DEBUG_MODE=false
```

### 2. Railway Configuration
The `Procfile` is configured for Railway:
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 g:app.server
```

### 3. Dependencies
All required packages are in `requirements.txt`:
- `gunicorn==21.2.0` for production server
- Enhanced retry and connection handling libraries

## Troubleshooting

### Common Issues

#### 1. "Application failed to respond"
**Cause**: Usually due to external API blocking or connection issues
**Solution**: 
- Check Railway logs for specific error messages
- Verify environment variables are set correctly
- The app now has better fallback mechanisms

#### 2. Binance API 451 Errors
**Cause**: Railway IP addresses are blocked by Binance
**Solution**: 
- The app now prioritizes CoinGecko and CryptoCompare
- Enhanced headers attempt to bypass blocking
- Fallback to individual API calls if batch fails

#### 3. CSV Loading Failures
**Cause**: Google Sheets blocking Railway IPs
**Solution**:
- Multiple CSV loading methods with enhanced headers
- Automatic fallback between different approaches
- Increased timeout values

### Debug Mode
Enable debug mode to see detailed connection information:
```bash
DEBUG_MODE=true
```

### Health Check
Run the configuration checker:
```bash
python railway_config.py
```

## Monitoring

### Connection Status
The dashboard shows real-time connection status:
- ✅ Working services
- ❌ Failed services  
- 🚫 Blocked services (451 errors)

### Logs
Monitor Railway logs for:
- Connection attempts and failures
- API rate limiting
- Successful data loading
- Alert notifications

## Performance Optimizations

### For Railway
- **Single Worker**: Uses 1 gunicorn worker to avoid memory issues
- **Threading**: 2 threads for concurrent requests
- **Timeout**: 120-second timeout for long-running operations
- **Keep-alive**: 5-second keep-alive for connection reuse

### Rate Limiting
- **Conservative Limits**: 2 API calls per second
- **Exponential Backoff**: Automatic retry with increasing delays
- **Memory Management**: Automatic cleanup of old alert data

## Expected Behavior

### Startup Sequence
1. Railway environment detection
2. Connection health checks
3. Service availability assessment
4. Dashboard initialization
5. Auto-refresh setup

### Normal Operation
- Dashboard updates every 30 seconds
- Telegram alerts for price movements
- Automatic fallback between APIs
- Memory cleanup every 50 updates

### Error Handling
- Graceful degradation when APIs are blocked
- Continued operation with available services
- Detailed error logging for debugging
- Automatic retry mechanisms

## Support

If you encounter issues:
1. Check Railway logs for error messages
2. Verify environment variables are set
3. Enable debug mode for detailed information
4. Check the connection health status in the dashboard

The enhanced deployment should handle most Railway-specific issues automatically. 
