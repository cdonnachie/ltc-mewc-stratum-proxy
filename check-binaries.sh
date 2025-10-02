#!/bin/bash

# Binary setup helper script for Litecoin-Meowcoin AuxPoW Proxy

set -e

echo "🔧 Binary Setup Helper"
echo "======================"

# Function to check if a file exists and is executable
check_binary() {
    local file=$1
    local name=$2
    
    if [ -f "$file" ]; then
        if [ -x "$file" ]; then
            echo "✅ $name: Found and executable"
            
            # Check architecture
            if file "$file" | grep -q "ELF 64-bit"; then
                echo "   📋 Architecture: Linux x86_64 ✓"
            else
                echo "   ⚠️  Architecture: $(file "$file" | cut -d: -f2)"
            fi
            
            # Check glibc requirements
            if command -v objdump >/dev/null 2>&1; then
                local glibc_vers=$(objdump -p "$file" 2>/dev/null | grep GLIBC_ | sed 's/.*GLIBC_/GLIBC_/' | sort -V | tail -1)
                if [ ! -z "$glibc_vers" ]; then
                    echo "   🔗 Required: $glibc_vers"
                    case "$glibc_vers" in
                        "GLIBC_2.3"[4-5]*) echo "   💡 Suggestion: Use Ubuntu 22.04+ dockerfile" ;;
                        "GLIBC_2.36"*) echo "   💡 Suggestion: Use Ubuntu 24.04 or Debian dockerfile" ;;
                        "GLIBC_2.3"[7-9]*) echo "   💡 Suggestion: May need newer base or custom glibc" ;;
                    esac
                fi
            else
                echo "   ℹ️  Install objdump to check glibc requirements"
            fi
        else
            echo "⚠️  $name: Found but not executable"
            echo "   💡 Fix: chmod +x $file"
        fi
    else
        echo "❌ $name: Missing"
        echo "   📁 Expected location: $file"
    fi
}

echo "📦 Checking Litecoin binaries..."
check_binary "binaries/litecoin/litecoind" "Litecoin Daemon"
check_binary "binaries/litecoin/litecoin-cli" "Litecoin CLI"

echo ""
echo "📦 Checking Meowcoin binaries..."
check_binary "binaries/meowcoin/meowcoind" "Meowcoin Daemon"
check_binary "binaries/meowcoin/meowcoin-cli" "Meowcoin CLI"

echo ""
echo "📋 Directory structure:"
echo "binaries/"
echo "├── litecoin/"
if [ -d "binaries/litecoin" ]; then
    for file in binaries/litecoin/*; do
        if [ -f "$file" ]; then
            echo "│   ├── $(basename "$file")"
        fi
    done
else
    echo "│   └── (directory missing)"
fi

echo "└── meowcoin/"
if [ -d "binaries/meowcoin" ]; then
    for file in binaries/meowcoin/*; do
        if [ -f "$file" ]; then
            echo "    ├── $(basename "$file")"
        fi
    done
else
    echo "    └── (directory missing)"
fi

echo ""

# Check if all required binaries are present
missing_binaries=0
required_files=(
    "binaries/litecoin/litecoind"
    "binaries/litecoin/litecoin-cli" 
    "binaries/meowcoin/meowcoind"
    "binaries/meowcoin/meowcoin-cli"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_binaries=$((missing_binaries + 1))
    fi
done

if [ $missing_binaries -eq 0 ]; then
    echo "🎉 All required binaries are present!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Build Docker images: docker compose build"
    echo "2. Start services: docker compose up -d"
    echo "3. Check logs: docker compose logs -f"
else
    echo "⚠️  Missing $missing_binaries required binaries"
    echo ""
    echo "📝 To fix:"
    echo "1. Copy binaries to the correct directories (see README.md)"
    echo "2. Run this script again to verify"
    echo "3. Build Docker images: docker compose build"
fi

echo ""
echo "💡 Help:"
echo "  Binary requirements: See binaries/README.md"
echo "  Litecoin setup: See binaries/litecoin/README.md" 
echo "  Meowcoin setup: See binaries/meowcoin/README.md"