# Browser Security Audit

Security audit tool for extracting cookies, tokens, and sensitive data from browsers and Electron apps.

## Features

- Extract cookies from Chrome, Firefox, Zen Browser
- Extract tokens from Discord Desktop, Canary, and Equicord
- Extract localStorage and local storage data
- Identify authentication tokens and sensitive credentials
- Cross-platform support (Linux, macOS)

## Quick Start

```bash
chmod +x audit.sh

# Close browsers first (important!)
./audit.sh

# Results in audit_output/
```

## Requirements

- Linux or macOS
- bash 4+
- sqlite3
- Python 3 + plyvel (for Discord Desktop tokens)

## Usage

```bash
# Basic mode (no password prompt)
./audit.sh

# With Keychain access (macOS, requires password)
./audit.sh --keychain

# Skip confirmation
./audit.sh --force

# Help
./audit.sh --help
```

## Output

Results saved in `audit_output/`:
- `chrome_cookies.txt` - Chrome cookies
- `firefox_cookies.txt` - Firefox cookies
- `zen_cookies.txt` - Zen Browser cookies
- `audit_*.log` - Detailed logs

## Security Warning

**Authorized Use Only:**
- Your own systems
- Systems with explicit permission
- Test/development environments
- Security research

**Prohibited:**
- Unauthorized system access
- Credential theft
- Unauthorized account access

## License

GNU General Public License v3.0 - See LICENSE file
