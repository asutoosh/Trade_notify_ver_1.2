#!/bin/bash

# Railway Deployment Script
# This script helps set up and deploy the Crypto Trading Dashboard to Railway

echo "🚂 Railway Deployment Script"
echo "============================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    
    # Install Railway CLI based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://railway.app/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install railway
    else
        echo "⚠️  Please install Railway CLI manually from https://railway.app/cli"
        exit 1
    fi
else
    echo "✅ Railway CLI found"
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
else
    echo "✅ Already logged in to Railway"
fi

# Create new project if needed
echo ""
echo "📁 Setting up Railway project..."
read -p "Do you want to create a new Railway project? (y/n): " create_new

if [[ $create_new == "y" || $create_new == "Y" ]]; then
    railway init
else
    echo "Using existing project"
fi

# Set environment variables
echo ""
echo "🔧 Setting up environment variables..."

# Check if .env file exists
if [ -f ".env" ]; then
    echo "📄 Found .env file, using values from it..."
    source .env
    
    # Set Railway variables from .env
    if [ ! -z "$TELEGRAM_BOT_TOKEN" ]; then
        railway variables set TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
        echo "✅ Set TELEGRAM_BOT_TOKEN"
    fi
    
    if [ ! -z "$TELEGRAM_CHAT_ID" ]; then
        railway variables set TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
        echo "✅ Set TELEGRAM_CHAT_ID"
    fi
    
    if [ ! -z "$CSV_URL" ]; then
        railway variables set CSV_URL="$CSV_URL"
        echo "✅ Set CSV_URL"
    fi
    
    if [ ! -z "$DEBUG_MODE" ]; then
        railway variables set DEBUG_MODE="$DEBUG_MODE"
        echo "✅ Set DEBUG_MODE"
    fi
else
    echo "📝 No .env file found. Please set environment variables manually:"
    echo ""
    echo "railway variables set TELEGRAM_BOT_TOKEN='your_bot_token'"
    echo "railway variables set TELEGRAM_CHAT_ID='your_chat_id'"
    echo "railway variables set CSV_URL='your_csv_url'"
    echo "railway variables set DEBUG_MODE='false'"
    echo ""
    read -p "Press Enter after setting the variables..."
fi

# Deploy to Railway
echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "🎉 Deployment complete!"
echo "📊 Your dashboard should be available at the Railway URL"
echo "🔍 Check the logs with: railway logs"
echo "🌐 Open the app with: railway open" 
