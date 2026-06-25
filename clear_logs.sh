#!/bin/bash

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    DISCORD_LOGS=~/Library/Application\ Support/discord/logs
else
    DISCORD_LOGS=~/.config/discord/logs
fi

echo "[*] Clearing Discord logs..."

if [ -d "$DISCORD_LOGS" ]; then
    rm -rf "$DISCORD_LOGS"
    mkdir -p "$DISCORD_LOGS"
    echo "[OK] Discord logs cleared"
else
    echo "[!] Discord logs directory not found"
    exit 1
fi
