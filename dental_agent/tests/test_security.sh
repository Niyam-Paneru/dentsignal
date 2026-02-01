#!/bin/bash
# =============================================================================
# Dental Agent Security Quick Validation Script
# =============================================================================
# This script provides a quick way to verify security configuration
# without needing Python dependencies.
#
# Usage:
#   chmod +x tests/test_security.sh
#   ./tests/test_security.sh
#
# Exit codes:
#   0 = All critical checks passed
#   1 = One or more critical checks failed
# =============================================================================

set -e  # Exit on error for critical checks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Helper functions
print_header() {
    echo ""
    echo "==================================================================="
    echo "$1"
    echo "==================================================================="
}

print_pass() {
    echo -e "  [${GREEN}PASS${NC}] $1"
    ((PASSED++))
}

print_fail() {
    echo -e "  [${RED}FAIL${NC}] $1"
    if [ -n "$2" ]; then
        echo -e "       $2"
    fi
    ((FAILED++))
}

print_warn() {
    echo -e "  [${YELLOW}WARN${NC}] $1"
    if [ -n "$2" ]; then
        echo -e "       $2"
    fi
    ((WARNINGS++))
}

# =============================================================================
# Main checks
# =============================================================================

echo "==================================================================="
echo "DENTAL AGENT SECURITY QUICK CHECK"
echo "==================================================================="
echo ""
echo "Project directory: $PROJECT_DIR"
echo ""

# ---------------------------------------------------------------------------
# 1. Check environment files exist
# ---------------------------------------------------------------------------
print_header "[1/8] Environment Files"

if [ -f "$PROJECT_DIR/.env" ]; then
    print_pass ".env file exists"
else
    print_fail ".env file missing" "Create from .env.example"
fi

if [ -f "$PROJECT_DIR/.env.example" ]; then
    print_pass ".env.example file exists"
else
    print_warn ".env.example file missing"
fi

if [ -f "$PROJECT_DIR/.env.production.example" ]; then
    print_pass ".env.production.example file exists"
else
    print_warn ".env.production.example file missing"
fi

# Check .env is in .gitignore
if [ -f "$PROJECT_DIR/.gitignore" ]; then
    if grep -q "\.env" "$PROJECT_DIR/.gitignore"; then
        print_pass ".env is in .gitignore"
    else
        print_fail ".env NOT in .gitignore" "Add .env to .gitignore to prevent secrets leak"
    fi
else
    print_warn ".gitignore file missing"
fi

# ---------------------------------------------------------------------------
# 2. Check critical environment variables
# ---------------------------------------------------------------------------
print_header "[2/8] Critical Environment Variables"

# Source the .env file if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    # Use a subshell to avoid polluting current environment
    ENV_CONTENT=$(cat "$PROJECT_DIR/.env")
fi

# Function to check env var
check_env_var() {
    local var_name=$1
    local required=$2
    
    # Try to get from current environment first, then from .env file
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ] && [ -f "$PROJECT_DIR/.env" ]; then
        var_value=$(grep "^${var_name}=" "$PROJECT_DIR/.env" | cut -d '=' -f2- | head -1)
    fi
    
    if [ -n "$var_value" ]; then
        # Check if it's a placeholder
        if [[ "$var_value" == *"changeme"* ]] || [[ "$var_value" == *"your-"* ]] || [[ "$var_value" == "GENERATE_"* ]]; then
            if [ "$required" = "true" ]; then
                print_fail "$var_name" "Still using placeholder value: ${var_value:0:30}..."
            else
                print_warn "$var_name" "Using placeholder value: ${var_value:0:30}..."
            fi
        else
            print_pass "$var_name is set"
        fi
    else
        if [ "$required" = "true" ]; then
            print_fail "$var_name" "Required variable is not set"
        else
            print_warn "$var_name" "Optional variable not set"
        fi
    fi
}

check_env_var "JWT_SECRET" "true"
check_env_var "ENCRYPTION_KEY" "true"
check_env_var "DATABASE_URL" "true"
check_env_var "SESSION_SECRET" "true"
check_env_var "DEEPGRAM_API_KEY" "false"
check_env_var "OPENAI_API_KEY" "false"
check_env_var "REDIS_URL" "false"

# ---------------------------------------------------------------------------
# 3. Check JWT secret strength
# ---------------------------------------------------------------------------
print_header "[3/8] JWT Secret Strength"

JWT_SECRET="${JWT_SECRET:-}"
if [ -z "$JWT_SECRET" ] && [ -f "$PROJECT_DIR/.env" ]; then
    JWT_SECRET=$(grep "^JWT_SECRET=" "$PROJECT_DIR/.env" | cut -d '=' -f2- | head -1)
fi

if [ -n "$JWT_SECRET" ] && [[ ! "$JWT_SECRET" == *"changeme"* ]]; then
    JWT_LENGTH=${#JWT_SECRET}
    
    if [ $JWT_LENGTH -ge 32 ]; then
        print_pass "JWT_SECRET length >= 32 chars ($JWT_LENGTH)"
    else
        print_fail "JWT_SECRET length" "Only $JWT_LENGTH chars, need >= 32"
    fi
    
    # Check for complexity
    if [[ "$JWT_SECRET" =~ [A-Z] ]]; then
        print_pass "JWT_SECRET has uppercase"
    else
        print_fail "JWT_SECRET missing uppercase"
    fi
    
    if [[ "$JWT_SECRET" =~ [a-z] ]]; then
        print_pass "JWT_SECRET has lowercase"
    else
        print_fail "JWT_SECRET missing lowercase"
    fi
    
    if [[ "$JWT_SECRET" =~ [0-9] ]]; then
        print_pass "JWT_SECRET has digits"
    else
        print_fail "JWT_SECRET missing digits"
    fi
    
    if [[ "$JWT_SECRET" =~ [!@#$%^&*()\-_=+{}\[\]:;|\'",.<>/?\`~\\] ]]; then
        print_pass "JWT_SECRET has special characters"
    else
        print_fail "JWT_SECRET missing special characters"
    fi
else
    print_fail "JWT_SECRET" "Not set or using placeholder"
fi

# ---------------------------------------------------------------------------
# 4. Check encryption key
# ---------------------------------------------------------------------------
print_header "[4/8] Encryption Key"

ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
if [ -z "$ENCRYPTION_KEY" ] && [ -f "$PROJECT_DIR/.env" ]; then
    ENCRYPTION_KEY=$(grep "^ENCRYPTION_KEY=" "$PROJECT_DIR/.env" | cut -d '=' -f2- | head -1)
fi

if [ -n "$ENCRYPTION_KEY" ] && [[ ! "$ENCRYPTION_KEY" == *"changeme"* ]]; then
    ENC_LENGTH=${#ENCRYPTION_KEY}
    
    if [ $ENC_LENGTH -ge 32 ]; then
        print_pass "ENCRYPTION_KEY length >= 32 chars ($ENC_LENGTH)"
    else
        print_fail "ENCRYPTION_KEY length" "Only $ENC_LENGTH chars, recommended >= 32"
    fi
else
    print_fail "ENCRYPTION_KEY" "Not set or using placeholder"
fi

# ---------------------------------------------------------------------------
# 5. Check log directories exist
# ---------------------------------------------------------------------------
print_header "[5/8] Log Directories"

if [ -d "$PROJECT_DIR/logs" ]; then
    print_pass "logs/ directory exists"
else
    print_warn "logs/ directory missing" "Creating..."
    mkdir -p "$PROJECT_DIR/logs"
    if [ -d "$PROJECT_DIR/logs" ]; then
        print_pass "logs/ directory created"
    fi
fi

# Check log file permissions (should not be world-writable)
if [ -d "$PROJECT_DIR/logs" ]; then
    LOG_PERMS=$(stat -c "%a" "$PROJECT_DIR/logs" 2>/dev/null || stat -f "%A" "$PROJECT_DIR/logs" 2>/dev/null)
    if [ -n "$LOG_PERMS" ]; then
        # Remove any '0' prefix for octal comparison
        LOG_PERMS=$(echo "$LOG_PERMS" | sed 's/^0*//')
        if [ "$LOG_PERMS" -le 755 ] 2>/dev/null; then
            print_pass "logs/ permissions are secure ($LOG_PERMS)"
        else
            print_warn "logs/ permissions may be too permissive ($LOG_PERMS)"
        fi
    fi
fi

# ---------------------------------------------------------------------------
# 6. Check Python security modules exist
# ---------------------------------------------------------------------------
print_header "[6/8] Security Modules"

SECURITY_MODULES=(
    "auth.py:JWT Authentication"
    "encryption.py:Database Encryption"
    "validators.py:Input Validation"
    "audit_logger.py:Audit Logging"
    "session_security.py:Session Security"
    "rate_limiter.py:Rate Limiting"
)

for module_info in "${SECURITY_MODULES[@]}"; do
    IFS=':' read -r module_name description <<< "$module_info"
    if [ -f "$PROJECT_DIR/$module_name" ]; then
        print_pass "$description ($module_name)"
    else
        print_fail "$description" "$module_name missing"
    fi
done

# ---------------------------------------------------------------------------
# 7. Check for critical security imports in main app
# ---------------------------------------------------------------------------
print_header "[7/8] Security Middleware Integration"

if [ -f "$PROJECT_DIR/api_main.py" ]; then
    if grep -q "SecurityHeadersMiddleware" "$PROJECT_DIR/api_main.py"; then
        print_pass "SecurityHeadersMiddleware found in api_main.py"
    else
        print_fail "SecurityHeadersMiddleware" "Not found in api_main.py"
    fi
    
    if grep -q "CORSMiddleware" "$PROJECT_DIR/api_main.py"; then
        print_pass "CORSMiddleware found in api_main.py"
    else
        print_warn "CORSMiddleware" "Not found in api_main.py"
    fi
    
    if grep -q "RateLimitMiddleware" "$PROJECT_DIR/api_main.py"; then
        print_pass "RateLimitMiddleware found in api_main.py"
    else
        print_warn "RateLimitMiddleware" "Not found in api_main.py"
    fi
else
    print_fail "api_main.py" "Main application file not found"
fi

# ---------------------------------------------------------------------------
# 8. Check for secrets in code
# ---------------------------------------------------------------------------
print_header "[8/8] Code Security Scan"

# Check for hardcoded secrets (basic checks)
if [ -d "$PROJECT_DIR" ]; then
    # Look for potential secrets (this is a basic check)
    SUSPICIOUS_PATTERNS=(
        "password\s*=\s*[\"'][^\"']{3,}[\"']"
        "secret\s*=\s*[\"'][^\"']{8,}[\"']"
        "api_key\s*=\s*[\"'][^\"']{10,}[\"']"
        "token\s*=\s*[\"'][^\"']{10,}[\"']"
    )
    
    FOUND_SECRETS=0
    for pattern in "${SUSPICIOUS_PATTERNS[@]}"; do
        # Exclude .pyc files and check Python files
        if grep -rE "$pattern" "$PROJECT_DIR" --include="*.py" 2>/dev/null | grep -v "^Binary" | grep -v "test_" | grep -v "example" | grep -v "placeholder" | grep -v "changeme" | head -5; then
            FOUND_SECRETS=1
        fi
    done
    
    if [ $FOUND_SECRETS -eq 0 ]; then
        print_pass "No obvious hardcoded secrets found"
    else
        print_warn "Potential hardcoded secrets found" "Review the matches above"
    fi
    
    # Check for SQL injection vulnerabilities (basic)
    if grep -rn "execute.*%" "$PROJECT_DIR" --include="*.py" 2>/dev/null | head -1; then
        print_warn "Possible SQL formatting detected" "Review for SQL injection risks"
    else
        print_pass "No obvious SQL injection patterns"
    fi
    
    # Check for eval() usage
    if grep -rn "\beval(" "$PROJECT_DIR" --include="*.py" 2>/dev/null | grep -v "#" | head -1; then
        print_warn "eval() usage detected" "Review for security implications"
    else
        print_pass "No eval() usage detected"
    fi
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "==================================================================="
echo "SECURITY CHECK SUMMARY"
echo "==================================================================="
echo ""
echo "Total checks:"
echo -e "  ${GREEN}PASSED:   $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "  ${RED}FAILED:   $FAILED${NC}"
fi
if [ $WARNINGS -gt 0 ]; then
    echo -e "  ${YELLOW}WARNINGS: $WARNINGS${NC}"
fi

echo ""
echo "==================================================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}[OK] All critical security checks passed!${NC}"
    echo ""
    echo "For more comprehensive testing, run:"
    echo "  python tests/security_validation.py"
    echo ""
    exit 0
else
    echo -e "${RED}[FAIL] $FAILED critical check(s) failed. Please review and fix.${NC}"
    echo ""
    exit 1
fi
