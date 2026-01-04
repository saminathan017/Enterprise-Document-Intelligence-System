#!/bin/bash

# ============================================
# 🔒 GitHub Security Pre-Upload Checker
# Enterprise AI Agent Project
# ============================================
# Run this script before EVERY git push to GitHub
# It will scan for sensitive data and prevent leaks

echo ""
echo "======================================================================"
echo "🔒 SECURITY SCAN - Enterprise AI Agent"
echo "======================================================================"
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}❌ CRITICAL: $1${NC}"
    ((ERRORS++))
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. CHECKING FOR EXPOSED API KEYS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for OpenAI API keys in code
if grep -r "sk-proj-" . --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=backups --exclude=".env" --exclude=".env.*" --exclude="*.md" --exclude="security_check.sh" 2>/dev/null | grep -v ".env.example" | grep -v "your-api-key" | grep -q .; then
    error "OpenAI API key found in code!"
    echo "   Found in:"
    grep -rn "sk-proj-" . --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=backups --exclude=".env" --exclude=".env.*" --exclude="*.md" --exclude="security_check.sh" 2>/dev/null | grep -v ".env.example" | grep -v "your-api-key"
else
    success "No OpenAI API keys found in code"
fi

# Check for other API key patterns
if grep -rI "api[_-]key.*=.*['\"][a-zA-Z0-9]{20,}" . --exclude-dir=venv --exclude-dir=node_modules --exclude-dir=backups --exclude=".env" 2>/dev/null | grep -v ".env.example" | grep -v "getenv" | grep -q .; then
    warning "Potential API key pattern found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. CHECKING .ENV FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if .env exists and is gitignored
if [ -f ".env" ]; then
    if grep -q "^\.env$" .gitignore 2>/dev/null; then
        success ".env is properly gitignored"
    else
        error ".env exists but is NOT in .gitignore!"
    fi
    
    # Check if .env has actual API key
    if grep -q "sk-proj-" .env 2>/dev/null; then
        info ".env contains OpenAI API key (this is OK as long as it's gitignored)"
    fi
else
    warning ".env file not found (you'll need to create it)"
fi

# Check .env.example
if [ -f ".env.example" ]; then
    if grep -q "sk-proj-" .env.example 2>/dev/null; then
        error ".env.example contains REAL API key! Must use placeholder only!"
    else
        success ".env.example has placeholder values (safe)"
    fi
else
    warning ".env.example not found (recommended to have template)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. CHECKING SENSITIVE FILES & DIRECTORIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check critical directories are gitignored
CRITICAL_DIRS=("data" "venv" "backups" "logs" "sessions")
for dir in "${CRITICAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        if grep -q "^${dir}/" .gitignore 2>/dev/null; then
            success "$dir/ is gitignored"
        else
            error "$dir/ exists but is NOT gitignored!"
        fi
    fi
done

# Check for credentials files
if find . -name "*credential*" -o -name "*secret*" -o -name "*.key" -o -name "*.pem" 2>/dev/null | grep -v "venv" | grep -v "node_modules" | grep -q .; then
    warning "Found potential credential files:"
    find . -name "*credential*" -o -name "*secret*" -o -name "*.key" -o -name "*.pem" 2>/dev/null | grep -v "venv" | grep -v "node_modules"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. CHECKING DATABASE & SESSION FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for database files
if find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null | grep -v "venv" | grep -q .; then
    if grep -q "\.db$\|\.sqlite" .gitignore 2>/dev/null; then
        success "Database files are gitignored"
    else
        error "Database files found but NOT gitignored!"
    fi
fi

# Check session files
if [ -d "data/sessions" ] && [ "$(ls -A data/sessions 2>/dev/null)" ]; then
    SESSION_COUNT=$(find data/sessions -type f 2>/dev/null | wc -l)
    info "Found $SESSION_COUNT session files (contains user queries)"
    if grep -q "sessions/" .gitignore 2>/dev/null; then
        success "Sessions directory is gitignored"
    else
        error "Sessions directory NOT gitignored!"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. CHECKING PERSONAL INFORMATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for email patterns (excluding example emails)
if grep -rI "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,}" . --exclude-dir=venv --exclude-dir=node_modules --exclude="*.md" 2>/dev/null | grep -v "example.com" | grep -v "your-email" | grep -q .; then
    warning "Found email addresses in code (review if they should be there)"
fi

# Check for common placeholder text
if grep -q "\[Your Name\]" README.md 2>/dev/null; then
    info "README contains placeholder - update with your name if desired"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. CHECKING GIT STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if git rev-parse --git-dir > /dev/null 2>&1; then
    info "Git repository detected"
    
    # Check if .env is tracked
    if git ls-files --error-unmatch .env > /dev/null 2>&1; then
        error ".env is TRACKED by git! Remove it immediately with: git rm --cached .env"
    else
        success ".env is not tracked by git"
    fi
    
    # Show what would be committed
    STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l)
    if [ $STAGED -gt 0 ]; then
        info "Files staged for commit: $STAGED"
        echo "   Review these files:"
        git diff --cached --name-only 2>/dev/null | head -20
    fi
else
    info "Git not initialized yet - will check when you run 'git init'"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. FINAL SECURITY ASSESSMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║  🎉 SECURITY CHECK PASSED - SAFE TO PUSH TO GITHUB! 🎉        ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "1. git add ."
    echo "2. git commit -m 'Initial commit'"
    echo "3. git push origin main"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                                                                ║${NC}"
    echo -e "${YELLOW}║  ⚠️  REVIEW WARNINGS - Likely safe but please review          ║${NC}"
    echo -e "${YELLOW}║                                                                ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "You have $WARNINGS warning(s). Review them above."
    echo "Most warnings are optional but worth checking."
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}║  🚨 CRITICAL ERRORS - DO NOT PUSH TO GITHUB! 🚨               ║${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "You have $ERRORS CRITICAL error(s) and $WARNINGS warning(s)."
    echo ""
    echo "🔒 IMMEDIATE ACTIONS REQUIRED:"
    echo "1. Fix all CRITICAL errors above"
    echo "2. Remove any API keys from code"
    echo "3. Ensure all sensitive files are gitignored"
    echo "4. Run this script again before pushing"
fi

echo ""
echo "======================================================================"
echo "Scan complete - Errors: $ERRORS | Warnings: $WARNINGS"
echo "======================================================================"
echo ""

exit $ERRORS
