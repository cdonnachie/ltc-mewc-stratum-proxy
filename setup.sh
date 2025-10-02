#!/bin/bash

# Litecoin-Meowcoin AuxPoW Proxy Setup Script

set -e

echo "🚀 Setting up Litecoin-Meowcoin AuxPoW Proxy..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    
    # Generate secure passwords
    LTC_PASS=$(generate_password)
    MEWC_PASS=$(generate_password)
    
    cat > .env << EOF
# Litecoin Configuration
LTC_RPC_USER=litecoin_user
LTC_RPC_PASS=${LTC_PASS}
LTC_RPC_PORT=9332
LTC_P2P_PORT=9333

# Meowcoin Configuration
MEWC_RPC_USER=meowcoin_user
MEWC_RPC_PASS=${MEWC_PASS}
MEWC_RPC_PORT=8766
MEWC_P2P_PORT=8767

# Wallet Addresses (UPDATE THESE WITH YOUR ACTUAL ADDRESSES)
# Litecoin address (optional - first miner connection sets this)
# LTC_WALLET_ADDRESS=ltc1youraddresshere
MEWC_WALLET_ADDRESS=

# Stratum Proxy Configuration
STRATUM_PORT=54321
TESTNET=false
VERBOSE=true
SHOW_JOBS=true
EOF

    echo "✅ .env file created with random passwords"
    echo "⚠️  Please update the wallet addresses in .env file"
else
    echo "✅ .env file already exists"
fi

# Update config files with passwords from .env
source .env

# Update litecoin.conf
sed -i "s/rpcuser=.*/rpcuser=${LTC_RPC_USER}/" config/litecoin.conf
sed -i "s/rpcpassword=.*/rpcpassword=${LTC_RPC_PASS}/" config/litecoin.conf

# Update meowcoin.conf
sed -i "s/rpcuser=.*/rpcuser=${MEWC_RPC_USER}/" config/meowcoin.conf
sed -i "s/rpcpassword=.*/rpcpassword=${MEWC_RPC_PASS}/" config/meowcoin.conf

echo "✅ Configuration files updated"

# Create submit_history directory
mkdir -p submit_history

# Check binaries
echo "🔍 Checking binaries..."
./check-binaries.sh

# Build and start services
echo "🔨 Building and starting services..."
docker compose build --no-cache
docker compose up -d

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "📝 Next Steps:"
echo "1. Wait for blockchain sync (check with: docker compose logs -f litecoin meowcoin)"
echo "2. Update wallet addresses in .env file"
echo "3. Restart proxy: docker compose restart stratum-proxy"
echo "4. Connect your miner to localhost:${STRATUM_PORT}"
echo ""
echo "📖 Commands:"
echo "  View logs:     docker compose logs -f"
echo "  Stop services: docker compose down"
echo "  Restart:       docker compose restart"
echo ""
echo "🔧 Monitoring:"
echo "  LTC status:   docker compose exec litecoin litecoin-cli getblockchaininfo"
echo "  MEWC status:  docker compose exec meowcoin meowcoin-cli getblockchaininfo"
echo "  Proxy logs:   docker compose logs -f stratum-proxy"