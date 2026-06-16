#!/usr/bin/env python3

import os
import sys
import sqlite3
import subprocess
import json
from datetime import datetime
from pathlib import Path

class BrowserAudit:
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
            
        print("\n[===========================================]")
        print("|  BROWSER AUDIT - RESPONSIBLE USE ONLY  |")
        print("[===========================================]\n")
        print("This tool extracts SENSITIVE data:")
        print("  - Authentication tokens")
        print("  - Session cookies")
        print("  - localStorage data")
        print("  - Stored credentials\n")
        print("AUTHORIZED USE ONLY:")
        print("  - Your own systems")
        print("  - Systems with explicit permission")
        print("  - Test/development environments\n")
        
        response = input("Do you have authorization? (y/n): ").strip().lower()
        if response != 'y':
            print("Audit cancelled.")
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
            print(f"\n[!] Closing browsers: {', '.join(running)}")
            for browser in browsers:
                try:
                    subprocess.run(['pkill', '-9', '-i', browser],
                                 capture_output=True)
                except:
                    pass
            time.sleep(1)
            print("[OK] Browsers closed\n")
            self.log("INFO", "Browsers closed automatically")

    def extract_chrome_cookies(self):
        if self.os_type == 'darwin':
            path = self.home / "Library/Application Support/Google/Chrome/Default/Cookies"
        else:
            path = self.home / ".config/google-chrome/Default/Cookies"
        
        if not path.exists():
            return
        
        print("[*] Extracting Chrome cookies...")
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cookies LIMIT 50")
            
            with open(self.cookies_dir / "chrome_cookies.txt", 'w') as f:
                for row in cursor.fetchall():
                    f.write(str(row) + '\n')
            
            conn.close()
            print("[OK] Chrome cookies extracted\n")
        except Exception as e:
            self.log("ERROR", f"Chrome extraction failed: {e}")

    def extract_firefox_cookies(self):
        if self.os_type == 'darwin':
            profile_dir = self.home / "Library/Application Support/Firefox/Profiles"
        else:
            profile_dir = self.home / ".mozilla/firefox"
        
        if not profile_dir.exists():
            return
        
        print("[*] Extracting Firefox cookies...")
        try:
            for subdir in profile_dir.glob("*default*/"):
                cookies_file = subdir / "cookies.sqlite"
                if cookies_file.exists():
                    conn = sqlite3.connect(cookies_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM moz_cookies LIMIT 50")
                    
                    with open(self.cookies_dir / "firefox_cookies.txt", 'w') as f:
                        for row in cursor.fetchall():
                            f.write(str(row) + '\n')
                    
                    conn.close()
            
            print("[OK] Firefox cookies extracted\n")
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
        
        print("[*] Extracting Zen cookies...")
        try:
            for profile_dir in zen_dir.glob("*/"):
                cookies_file = profile_dir / "cookies.sqlite"
                if cookies_file.exists():
                    conn = sqlite3.connect(cookies_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM moz_cookies LIMIT 50")
                    
                    with open(self.cookies_dir / "zen_cookies.txt", 'w') as f:
                        for row in cursor.fetchall():
                            f.write(str(row) + '\n')
                    
                    conn.close()
            
            print("[OK] Zen cookies extracted\n")
        except Exception as e:
            self.log("ERROR", f"Zen extraction failed: {e}")

    def extract_discord_tokens(self):
        try:
            import plyvel
            import shutil
            import tempfile
        except ImportError:
            return

        print("[*] Extracting Discord Desktop tokens...")

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
            print("[OK] Discord tokens extracted\n")

    def display_results(self):
        print("\n[===========================================]")
        print("    EXTRACTED DATA")
        print("[===========================================]\n")

        files_to_display = [
            ("chrome_cookies.txt", "Chrome Cookies"),
            ("firefox_cookies.txt", "Firefox Cookies"),
            ("zen_cookies.txt", "Zen Cookies"),
            ("discord_tokens.txt", "Discord Desktop Tokens"),
        ]

        for filename, title in files_to_display:
            filepath = self.cookies_dir / filename
            if filepath.exists():
                print(f"\n[{title}]")
                print("-" * 50)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read().strip()
                        if content:
                            print(content)
                        else:
                            print("(no data found)")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
            else:
                print(f"\n[{title}]")
                print("-" * 50)
                print("(no data found)")

    def run(self):
        print("\n[===========================================]")
        print("    Browser Security Audit Tool")
        print("[===========================================]\n")

        self.check_authorization()
        self.close_browsers()

        self.log("INFO", "Audit started")

        self.extract_chrome_cookies()
        self.extract_firefox_cookies()
        self.extract_zen_cookies()
        self.extract_discord_tokens()

        self.display_results()

        print("\n[===========================================]")
        print(f"Output: {self.audit_dir}")
        print("[===========================================]\n")

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

