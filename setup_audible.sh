#!/bin/bash
# Audiobook Manager - Audible Authentication Setup

echo "=== Audible Authentication Setup ==="
echo ""
echo "This script helps you authenticate with Audible to enable automatic metadata lookup."
echo ""

# Check if config directory exists
mkdir -p config

# Check if auth file already exists
if [ -f config/auth.json ]; then
    echo "Auth file already exists at config/auth.json"
    read -p "Do you want to regenerate it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing auth file."
        exit 0
    fi
fi

echo "You'll need your Amazon credentials to authenticate."
echo ""

# Check if python3 and pip are available
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Please install Python 3.8+ first."
    exit 1
fi

# Install audible library if not present
pip install audible --quiet 2>/dev/null || pip3 install audible --quiet 2>/dev/null

echo "Starting authentication flow..."
echo "You may need to use the web browser that opens."
echo ""

python3 << 'EOF'
import os
import sys

try:
    from audible import Authenticator
    from audible.client import AudibleClient
    
    print("Starting authentication with Audible...")
    print("A browser window may open for login.")
    print("")
    
    # Create auth using CLI auth flow
    auth = Authenticator.from_cli(store=True)
    
    # Save to our config directory
    auth_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'auth.json')
    os.makedirs(os.path.dirname(auth_file), exist_ok=True)
    auth.to_file(auth_file)
    
    print(f"Authentication successful! Saved to {auth_file}")
    print("")
    print("You can now restart the audiobook manager and it will use Audible for metadata lookups.")
    
except ImportError:
    print("Error: audible library not installed")
    print("Run: pip install audible")
    sys.exit(1)
except Exception as e:
    print(f"Authentication failed: {e}")
    sys.exit(1)
EOF

echo ""
echo "Note: You may need to re-run this if authentication expires."