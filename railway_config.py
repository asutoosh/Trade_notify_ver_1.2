#!/usr/bin/env python3
"""
Railway deployment configuration helper
"""

import os
import sys

def check_railway_environment():
    """Check if running in Railway environment"""
    railway_vars = [
        'RAILWAY_ENVIRONMENT',
        'RAILWAY_PROJECT_ID',
        'RAILWAY_SERVICE_ID',
        'PORT'
    ]
    
    railway_detected = any(os.getenv(var) for var in railway_vars)
    
    print("🔍 Railway Environment Check:")
    print(f"   Railway detected: {'✅ Yes' if railway_detected else '❌ No'}")
    
    for var in railway_vars:
        value = os.getenv(var, 'Not set')
        print(f"   {var}: {value}")
    
    return railway_detected

def validate_required_vars():
    """Validate required environment variables"""
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Telegram bot token for notifications',
        'TELEGRAM_CHAT_ID': 'Telegram chat ID for notifications',
        'CSV_URL': 'Google Sheets CSV URL for trading data'
    }
    
    print("\n🔍 Required Environment Variables:")
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'TOKEN' in var or 'CHAT_ID' in var:
                masked_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Missing - {description}")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def main():
    """Main configuration check"""
    print("🚂 Railway Configuration Checker")
    print("=" * 40)
    
    railway_ok = check_railway_environment()
    vars_ok = validate_required_vars()
    
    print("\n📊 Summary:")
    print(f"   Railway Environment: {'✅ Ready' if railway_ok else '⚠️  Not Railway'}")
    print(f"   Environment Variables: {'✅ Complete' if vars_ok else '❌ Missing'}")
    
    if railway_ok and vars_ok:
        print("\n🎉 Railway deployment should work correctly!")
        return 0
    elif not railway_ok:
        print("\n💡 Not running in Railway - this is normal for local development")
        return 0
    else:
        print("\n❌ Missing required environment variables")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 
