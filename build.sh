#!/bin/bash
set -e

echo "=== Browser Security Audit - Build Script ==="
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    BINARY_NAME="audit-macos"
else
    OS="linux"
    BINARY_NAME="audit-linux"
fi

echo "[*] OS detected: $OS"

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[*] Using: $PYTHON_VERSION"

echo "[*] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[*] Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install system dependencies
if [ "$OS" = "macos" ]; then
    echo "[*] Installing macOS dependencies via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "[ERROR] Homebrew not found. Install from https://brew.sh"
        exit 1
    fi
    brew install leveldb
    export LDFLAGS="-L/opt/homebrew/opt/leveldb/lib"
    export CPPFLAGS="-I/opt/homebrew/opt/leveldb/include"
else
    echo "[*] Installing Linux dependencies via apt..."
    sudo apt-get update
    sudo apt-get install -y libleveldb-dev libleveldb1d
fi

echo "[*] Installing Python dependencies..."
pip install pyinstaller plyvel

echo "[*] Building executable: $BINARY_NAME"
pyinstaller --onefile --hidden-import=plyvel --name "$BINARY_NAME" audit.py

echo ""
echo "=== Build Complete ==="
echo "[✓] Executable: ./dist/$BINARY_NAME"
echo "[✓] Run it: ./dist/$BINARY_NAME"
echo ""
