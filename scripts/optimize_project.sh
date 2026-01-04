#!/bin/bash

# Enterprise AI Agent Project Optimization & Cleanup Script
# This script organizes the project structure professionally
# Removes duplicates, secures sensitive data, and creates clean structure

echo "🚀 Enterprise AI Agent Project Optimization Starting..."
echo ""

# Create backup directory with timestamp
BACKUP_DIR="backups/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Step 1: Creating backup..."
# Backup important files before cleanup
cp -r app "$BACKUP_DIR/" 2>/dev/null
cp -r data "$BACKUP_DIR/" 2>/dev/null
cp index.html "$BACKUP_DIR/" 2>/dev/null
cp .env "$BACKUP_DIR/" 2>/dev/null
echo "✅ Backup created in: $BACKUP_DIR"
echo ""

echo "🗑️  Step 2: Removing duplicate and test files..."
# Remove duplicate HTML files (keep only index.html)
rm -f index-backup.html
rm -f enterprise-ai-agent-app.html
rm -f enterprise-ai-agent.html
rm -f test-background.html
rm -f test-canvas.html
echo "✅ Removed duplicate HTML files"

# Remove .env.backup (sensitive data)
rm -f .env.backup
echo "✅ Removed .env.backup (sensitive)"

# Remove server logs (can be regenerated)
rm -f server.log
echo "✅ Removed server.log"

# Remove test data directory if empty or not needed
if [ -d "test_data" ]; then
    echo "⚠️  test_data directory exists - review manually"
fi
echo ""

echo "📁 Step 3: Organizing directory structure..."
# Create organized directory structure
mkdir -p frontend
mkdir -p scripts
mkdir -p logs
mkdir -p backups

# Move frontend file to frontend directory
if [ -f "index.html" ]; then
    cp index.html frontend/index.html
    echo "✅ Copied index.html to frontend/"
fi

# Move start script to scripts directory
if [ -f "start.sh" ]; then
    mv start.sh scripts/start.sh
    chmod +x scripts/start.sh
    echo "✅ Moved start.sh to scripts/"
fi

# Create logs directory for future logs
touch logs/.gitkeep
echo "✅ Created logs directory"
echo ""

echo "🔒 Step 4: Securing sensitive data..."
# Ensure .env is in .gitignore
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "✅ Added .env to .gitignore"
fi

# Ensure backup directory is in .gitignore
if ! grep -q "^backups/" .gitignore 2>/dev/null; then
    echo "backups/" >> .gitignore
    echo "✅ Added backups/ to .gitignore"
fi

# Ensure logs are in .gitignore
if ! grep -q "^logs/\*.log" .gitignore 2>/dev/null; then
    echo "logs/*.log" >> .gitignore
    echo "✅ Added logs/*.log to .gitignore"
fi

# Ensure data directory is in .gitignore
if ! grep -q "^data/" .gitignore 2>/dev/null; then
    echo "data/" >> .gitignore
    echo "✅ Added data/ to .gitignore"
fi
echo ""

echo "🧹 Step 5: Cleaning Python cache..."
# Remove Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
echo "✅ Removed Python cache files"
echo ""

echo "📊 Step 6: Analyzing web-frontend directory..."
# Check if web-frontend is needed (old Next.js project)
if [ -d "web-frontend" ]; then
    WEB_SIZE=$(du -sh web-frontend | cut -f1)
    echo "⚠️  web-frontend directory found (Size: $WEB_SIZE)"
    echo "   This appears to be the old Next.js frontend (no longer used)"
    echo "   Consider removing it to save space:"
    echo "   rm -rf web-frontend"
    echo ""
fi

echo "📊 Step 7: Analyzing antigravity directory..."
# Check antigravity directory
if [ -d "antigravity" ]; then
    echo "⚠️  antigravity directory found"
    echo "   This appears to be IDE artifacts"
    echo "   Consider reviewing and removing if not needed"
    echo ""
fi

echo "✅ Step 8: Optimization complete!"
echo ""
echo "📋 Summary of changes:"
echo "  ✓ Removed duplicate HTML files (5 files)"
echo "  ✓ Removed sensitive .env.backup"
echo "  ✓ Removed server.log"
echo "  ✓ Cleaned Python cache"
echo "  ✓ Organized directory structure"
echo "  ✓ Secured .gitignore"
echo "  ✓ Created backup in: $BACKUP_DIR"
echo ""
echo "⚠️  Manual review recommended for:"
echo "  - web-frontend/ (old Next.js project - can be removed)"
echo "  - antigravity/ (IDE artifacts - can be removed)"
echo "  - test_data/ (review contents)"
echo ""
echo "🎯 Next steps:"
echo "  1. Review the backup in: $BACKUP_DIR"
echo "  2. Test the application: python -m uvicorn app.main:app --reload"
echo "  3. Open frontend: open frontend/index.html"
echo "  4. If everything works, you can remove web-frontend/"
echo ""
echo "🚀 Project is now optimized and organized!"
