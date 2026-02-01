#!/bin/bash
# DentSignal Production Update Script
# Run this on the DigitalOcean server (159.89.247.86)

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

# Update DATABASE_URL in .env (URL-encoded password: DentSignal2026Prod)
sed -i 's|DATABASE_URL=sqlite:///./prod.db|DATABASE_URL=postgresql://postgres.movpukmfuelqctixfbcz:DentSignal2026Prod@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres|' .env

# Also update API_BASE_URL if needed
sed -i 's|API_BASE_URL=.*|API_BASE_URL=http://159.89.247.86:8000|' .env
sed -i 's|WS_BASE_URL=.*|WS_BASE_URL=ws://159.89.247.86:8000|' .env

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
echo "  curl http://159.89.247.86:8000/health"
echo "  journalctl -u dentsignal -f"
