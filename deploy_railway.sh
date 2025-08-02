#!/bin/bash

echo "🚂 Preparing Railway deployment..."

# Install Railway CLI if not present
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    curl -fsSL https://railway.app/install.sh | sh
fi

# Login to Railway (you'll need to do this manually)
echo "Please login to Railway if not already logged in:"
echo "railway login"

# Set environment variables
echo "Setting up environment variables..."
railway variables set TELEGRAM_BOT_TOKEN="your_bot_token_here"
railway variables set TELEGRAM_CHAT_ID="your_chat_id_here" 
railway variables set CSV_URL="your_csv_url_here"
railway variables set DEBUG_MODE="True"

# Deploy
echo "Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "Check your Railway dashboard for the deployment URL" 