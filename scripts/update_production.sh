#!/bin/bash
# DentSignal Production Update Script
# Run this on the production server
# Usage: SERVER_IP=your.server.ip bash update_production.sh

set -e

echo "🚀 DentSignal Production Update"
echo "================================"

# Navigate to app directory
cd /root/dentsignal/dental_agent

# Pull latest code from GitHub
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Update DATABASE_URL to use Supabase PostgreSQL
echo "🗄️ Updating database configuration..."

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# SECURITY: Database credentials are read from environment variables or .env file.
# Never hardcode credentials in scripts. Set DATABASE_URL in the server's .env file.
# Example: DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@pooler.supabase.com:6543/postgres
echo "⚠️  Ensure DATABASE_URL is set in .env (do NOT hardcode credentials in scripts)"

# Update API_BASE_URL from the SERVER_IP environment variable
SERVER_IP="${SERVER_IP:?Set SERVER_IP environment variable}"
sed -i "s|API_BASE_URL=.*|API_BASE_URL=https://${SERVER_IP}:8000|" .env  # DevSkim: ignore DS137138
sed -i "s|WS_BASE_URL=.*|WS_BASE_URL=wss://${SERVER_IP}:8000|" .env

echo "✅ Environment updated"

# Restart the service
echo "🔄 Restarting DentSignal service..."
systemctl restart dentsignal

# Wait for service to start
sleep 3

# Check service status
echo "📊 Service status:"
systemctl status dentsignal --no-pager | head -15

echo ""
echo "✅ Update complete!"
echo ""
echo "Test commands:"
echo "  curl https://${SERVER_IP}:8000/health"
echo "  journalctl -u dentsignal -f"
