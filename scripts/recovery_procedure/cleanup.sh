#!/bin/bash

echo "🧹 Starting complete system cleanup..."
echo "=================================="

# Stop all Docker containers
echo "📦 Stopping all Docker containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove all Docker containers
echo "🗑️  Removing all Docker containers..."
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Clean Docker system completely
echo "🐋 Cleaning Docker system..."
docker network prune -f
docker volume prune -f
docker builder prune -a -f
docker system prune -a --volumes -f

# Clean Docker logs
echo "📝 Cleaning Docker logs..."
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log 2>/dev/null || true

# Remove ALL project directories (with sudo for permission issues)
echo "📂 Removing project directories..."
sudo rm -rf ~/curavani_backend
sudo rm -rf ~/curavani_frontend_internal
sudo rm -rf ~/curavani_scraping
sudo rm -rf ~/curavani_websites
sudo rm -rf ~/Recovery_Test
sudo rm -rf ~/venv

# Clean apt cache
echo "🔧 Cleaning apt cache..."
sudo apt clean
sudo apt autoremove -y

# Show disk usage after cleanup
echo ""
echo "💾 Disk usage after cleanup:"
df -h /

echo ""
echo "✅ Cleanup complete!"
echo "=================================="