#!/bin/bash

# GitHub Upload Readiness Verification Script
# Run this before uploading to GitHub

echo "🔍 Enterprise AI Agent - GitHub Upload Readiness Check"
echo "=============================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to print error
error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((ERRORS++))
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo "1. Checking for sensitive data..."
echo "-----------------------------------"

# Check if .env exists and is gitignored
if [ -f ".env" ]; then
    if grep -q "^\.env$" .gitignore 2>/dev/null; then
        success ".env is gitignored"
    else
        error ".env exists but is NOT in .gitignore!"
    fi
else
    warning ".env file not found (OK if not created yet)"
fi

# Check for API keys in code
if grep -r "sk-proj-" . --exclude-dir=venv --exclude-dir=node_modules --exclude=".env" --exclude="*.md" 2>/dev/null | grep -v ".env.example" | grep -q .; then
    error "Found API key in code! Remove it immediately!"
    grep -r "sk-proj-" . --exclude-dir=venv --exclude-dir=node_modules --exclude=".env" --exclude="*.md" 2>/dev/null | grep -v ".env.example"
else
    success "No API keys found in code"
fi

# Check .env.example has placeholder
if [ -f ".env.example" ]; then
    if grep -q "your-api-key-here" .env.example; then
        success ".env.example has placeholder (not real key)"
    else
        warning ".env.example might contain real API key - verify manually"
    fi
else
    warning ".env.example not found"
fi

echo ""
echo "2. Checking for large files..."
echo "-----------------------------------"

# Check for large directories
if [ -d "web-frontend" ]; then
    SIZE=$(du -sh web-frontend 2>/dev/null | cut -f1)
    warning "web-frontend/ directory exists (Size: $SIZE) - consider removing"
fi

if [ -d "antigravity" ]; then
    warning "antigravity/ directory exists - consider removing (IDE artifacts)"
fi

if [ -d "venv" ]; then
    if grep -q "^venv/" .gitignore 2>/dev/null; then
        success "venv/ is gitignored"
    else
        error "venv/ exists but is NOT gitignored!"
    fi
fi

echo ""
echo "3. Checking professional files..."
echo "-----------------------------------"

# Check for required files
[ -f "README.md" ] && success "README.md exists" || error "README.md missing"
[ -f "LICENSE" ] && success "LICENSE exists" || warning "LICENSE missing (recommended)"
[ -f ".gitignore" ] && success ".gitignore exists" || error ".gitignore missing"
[ -f "requirements.txt" ] && success "requirements.txt exists" || error "requirements.txt missing"
[ -f "SECURITY.md" ] && success "SECURITY.md exists" || warning "SECURITY.md missing (recommended)"
[ -f "CONTRIBUTING.md" ] && success "CONTRIBUTING.md exists" || warning "CONTRIBUTING.md missing (recommended)"

echo ""
echo "4. Checking .gitignore coverage..."
echo "-----------------------------------"

# Check important gitignore entries
if [ -f ".gitignore" ]; then
    grep -q "^\.env$" .gitignore && success ".env is gitignored" || error ".env not in .gitignore"
    grep -q "^data/" .gitignore && success "data/ is gitignored" || error "data/ not in .gitignore"
    grep -q "^venv/" .gitignore && success "venv/ is gitignored" || error "venv/ not in .gitignore"
    grep -q "^__pycache__/" .gitignore && success "__pycache__/ is gitignored" || warning "__pycache__/ not in .gitignore"
    grep -q "^backups/" .gitignore && success "backups/ is gitignored" || warning "backups/ not in .gitignore"
fi

echo ""
echo "5. Checking for personal information..."
echo "-----------------------------------"

# Check if README has placeholder text
if grep -q "\[Your Name\]" README.md 2>/dev/null; then
    warning "README.md contains '[Your Name]' - update with your actual name"
fi

if grep -q "yourusername" README.md 2>/dev/null; then
    warning "README.md contains 'yourusername' - update with your GitHub username"
fi

if grep -q "your.email@example.com" README.md 2>/dev/null; then
    warning "README.md contains placeholder email - update with your email"
fi

echo ""
echo "=============================================="
echo "📊 SUMMARY"
echo "=============================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 Perfect! Your project is ready for GitHub!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review GITHUB_UPLOAD_GUIDE.md"
    echo "2. Update personal information in README.md and LICENSE"
    echo "3. Run: git init"
    echo "4. Run: git add ."
    echo "5. Run: git commit -m 'feat: initial commit'"
    echo "6. Create GitHub repository and push"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Almost ready! You have $WARNINGS warning(s).${NC}"
    echo ""
    echo "Review the warnings above and fix if needed."
    echo "Most warnings are optional but recommended for professional projects."
else
    echo -e "${RED}❌ NOT READY! You have $ERRORS error(s) and $WARNINGS warning(s).${NC}"
    echo ""
    echo "⚠️  DO NOT UPLOAD YET!"
    echo "Fix all errors above before uploading to GitHub."
    echo ""
    echo "Critical issues:"
    echo "- Remove any API keys from code"
    echo "- Ensure .env is gitignored"
    echo "- Add missing required files"
fi

echo ""
echo "For detailed instructions, see: GITHUB_UPLOAD_GUIDE.md"
echo ""

exit $ERRORS
