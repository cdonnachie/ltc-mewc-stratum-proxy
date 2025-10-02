#!/bin/bash
set -e

# Ensure the data directory exists and has correct permissions
mkdir -p /home/dogecoin/.dogecoin
chown -R dogecoin:dogecoin /home/dogecoin/.dogecoin

# Create dogecoin.conf from environment variables
cat > /home/dogecoin/.dogecoin/dogecoin.conf << EOF
# Generated from environment variables
rpcuser=${DOGE_RPC_USER}
rpcpassword=${DOGE_RPC_PASS}
rpcport=${DOGE_RPC_PORT:-22555}
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0:${DOGE_RPC_PORT:-22555}
server=1
listen=1
daemon=0
printtoconsole=1

# P2P port
port=${DOGE_P2P_PORT:-22556}

# ZMQ Configuration for block notifications
zmqpubhashblock=tcp://0.0.0.0:${DOGE_ZMQ_PORT:-28444}
zmqpubrawblock=tcp://0.0.0.0:${DOGE_ZMQ_RAW_PORT:-28445}

# Additional settings for better operation
maxconnections=50
timeout=30000

# Pruning configuration (0 = disabled/full node, >550 = prune to specified MB)
prune=${DOGE_PRUNE:-0}
EOF

# Fix ownership of the config file
chown dogecoin:dogecoin /home/dogecoin/.dogecoin/dogecoin.conf

echo "Generated dogecoin.conf with RPC settings"

# Switch to dogecoin user and start dogecoind with the configuration file
exec su dogecoin -c "dogecoind $*"
