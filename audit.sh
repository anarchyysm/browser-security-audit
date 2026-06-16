#!/usr/bin/env bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

USE_KEYCHAIN=false
if [ "$1" = "--keychain" ] || [ "$1" = "-k" ]; then
    USE_KEYCHAIN=true
elif [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ "$1" = "help" ]; then
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  (none)         Run WITHOUT keychain access (no password)"
    echo "  --keychain, -k Run WITH keychain access (requires password on macOS)"
    echo "  --help, -h     Show this help message"
    echo ""
    exit 0
elif [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
    FORCE_RUN=true
fi

if [ "$FORCE_RUN" != "true" ]; then
    echo -e "${RED}[========================================]${NC}"
    echo -e "${RED}|  BROWSER AUDIT - RESPONSIBLE USE ONLY  |${NC}"
    echo -e "${RED}[========================================]${NC}"
    echo ""
    echo "This tool extracts SENSITIVE data from browsers:"
    echo "  - Authentication tokens (Discord, GitHub, etc)"
    echo "  - Session cookies"
    echo "  - localStorage data"
    echo "  - Stored credentials"
    echo ""
    echo "AUTHORIZED USE ONLY:"
    echo "  - Your own systems"
    echo "  - Systems with explicit permission (pentesting)"
    echo "  - Test/development environments"
    echo "  - Security research"
    echo ""
    echo "PROHIBITED:"
    echo "  - Unauthorized system access"
    echo "  - Credential theft"
    echo "  - Unauthorized account access"
    echo ""
    read -p "Do you have authorization to audit this system? (y/n): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Audit cancelled.${NC}"
        exit 1
    fi
    echo ""
fi

if [ "$USE_KEYCHAIN" = "true" ]; then
    MODE="WITH KEYCHAIN ACCESS (requires password)"
else
    MODE="WITHOUT KEYCHAIN ACCESS (no password)"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_DIR="$SCRIPT_DIR/audit_output"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$AUDIT_DIR/audit_$TIMESTAMP.log"
COOKIES_DIR="$AUDIT_DIR/cookies_$TIMESTAMP"
REPORT_FILE="$AUDIT_DIR/report_$TIMESTAMP.txt"

mkdir -p "$AUDIT_DIR" "$COOKIES_DIR"

log_message() {
    local level=$1
    local message=$2
    local ts=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$ts] [$level] $message" | tee -a "$LOG_FILE"
}

close_browsers() {
    local running=""
    
    pgrep -x "chrome" > /dev/null 2>&1 && running="$running Chrome,"
    pgrep -x "firefox" > /dev/null 2>&1 && running="$running Firefox,"
    pgrep -x "zen" > /dev/null 2>&1 && running="$running Zen,"

    running=$(echo "$running" | sed 's/,$//')

    if [ -n "$running" ]; then
        echo -e "${YELLOW}[!] Closing browsers: $running${NC}"
        pgrep -f "chrome|firefox|zen" 2>/dev/null | while read pid; do
            kill -9 "$pid" 2>/dev/null
            sleep 0.5
        done
        sleep 1
        echo -e "${GREEN}[OK] Browsers closed${NC}\n"
        log_message "INFO" "Browsers closed automatically"
    fi
}

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}    Browser Security Audit Tool      ${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}    Mode: DATA EXTRACTION + LOGS${NC}"
if [ "$USE_KEYCHAIN" = "true" ]; then
    echo -e "${RED}    [!] $MODE${NC}"
else
    echo -e "${GREEN}    [OK] $MODE${NC}"
fi
echo -e "${BLUE}==================================================${NC}"
echo -e "${YELLOW}[!] Close browsers for complete extraction${NC}\n"

close_browsers

log_message "INFO" "Audit starting"
log_message "INFO" "Keychain mode: $USE_KEYCHAIN"
log_message "INFO" "Output directory: $AUDIT_DIR"

OS="$(uname)"
echo -e "Operating System: ${YELLOW}$OS${NC}\n"

if [ "$OS" = "Darwin" ]; then
    CHROME_DIR="$HOME/Library/Application Support/Google/Chrome"
    FIREFOX_DIR="$HOME/Library/Application Support/Firefox/Profiles"
    ZEN_DIR="$HOME/Library/Application Support/zen/Profiles"
elif [ "$OS" = "Linux" ]; then
    CHROME_DIR="$HOME/.config/google-chrome"
    FIREFOX_DIR="$HOME/.mozilla/firefox"
    if [ -d "$HOME/.var/app/io.github.zen_browser.zen/.zen" ]; then
        ZEN_DIR="$HOME/.var/app/io.github.zen_browser.zen/.zen"
    elif [ -d "$HOME/.zen" ]; then
        ZEN_DIR="$HOME/.zen"
    else
        ZEN_DIR="$HOME/.config/zen/Profiles"
    fi
fi

# Extract Chrome cookies
if [ -d "$CHROME_DIR/Default" ]; then
    echo -e "${BLUE}[*] Extracting Chrome cookies...${NC}"
    sqlite3 "$CHROME_DIR/Default/Cookies" "SELECT * FROM cookies LIMIT 50;" > "$COOKIES_DIR/chrome_cookies.txt" 2>/dev/null
    echo -e "${GREEN}[OK] Chrome cookies extracted${NC}\n"
fi

# Extract Firefox cookies  
if [ -d "$FIREFOX_DIR" ]; then
    echo -e "${BLUE}[*] Extracting Firefox cookies...${NC}"
    for profile_dir in "$FIREFOX_DIR"/*default*/; do
        if [ -f "$profile_dir/cookies.sqlite" ]; then
            sqlite3 "$profile_dir/cookies.sqlite" "SELECT * FROM moz_cookies LIMIT 50;" > "$COOKIES_DIR/firefox_cookies.txt" 2>/dev/null
        fi
    done
    echo -e "${GREEN}[OK] Firefox cookies extracted${NC}\n"
fi

# Extract Zen cookies
if [ -d "$ZEN_DIR" ]; then
    echo -e "${BLUE}[*] Extracting Zen cookies...${NC}"
    for profile_dir in "$ZEN_DIR"/*/ ; do
        if [ -f "$profile_dir/cookies.sqlite" ]; then
            sqlite3 "$profile_dir/cookies.sqlite" "SELECT * FROM moz_cookies LIMIT 50;" > "$COOKIES_DIR/zen_cookies.txt" 2>/dev/null
        fi
    done
    echo -e "${GREEN}[OK] Zen cookies extracted${NC}\n"
fi

# Extract Discord Desktop tokens
PYTHON_CMD="python3"
if [ -f "env/bin/python" ]; then
    PYTHON_CMD="env/bin/python"
fi

if $PYTHON_CMD -c "import plyvel" 2>/dev/null; then
    echo -e "${BLUE}[*] Extracting Discord Desktop tokens...${NC}"
    
    $PYTHON_CMD << 'PYTHON_EXTRACT' 2>/dev/null
import plyvel
import os

discord_dirs = {
    "Discord": os.path.expanduser("~/.config/discord"),
    "Discord Canary": os.path.expanduser("~/.config/discordcanary"),
    "Equicord": os.path.expanduser("~/.config/Equicord")
}

for app_name, discord_dir in discord_dirs.items():
    leveldb_path = os.path.join(discord_dir, "Local Storage/leveldb")
    
    if not os.path.exists(leveldb_path):
        continue
    
    try:
        db = plyvel.DB(leveldb_path, create_if_missing=False)
        
        for key, value in db.iterator():
            key_str = key.decode('utf-8', errors='ignore')
            
            if 'token' in key_str.lower() and 'discord' in key_str.lower():
                try:
                    value_str = value.decode('utf-8', errors='ignore').strip('"')
                    
                    if len(value_str) > 50 and any(x in value_str for x in ['MjcyMjE', 'MzA', 'NzA', 'mfa.', 'dbl_']):
                        print(f"FOUND_TOKEN:{app_name}:{value_str}")
                except:
                    pass
        
        db.close()
    except:
        pass

PYTHON_EXTRACT
    
    echo -e "${GREEN}[OK] Discord tokens extracted${NC}\n"
fi

echo -e "${BLUE}==================================================${NC}"
echo "Audit completed."
echo "Output: $AUDIT_DIR"
echo -e "${BLUE}==================================================${NC}\n"

log_message "INFO" "Audit completed successfully"

