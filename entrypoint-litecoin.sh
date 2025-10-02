#!/bin/bash
set -e

# Ensure the data directory exists and has correct permissions
mkdir -p /home/litecoin/.litecoin
chown -R litecoin:litecoin /home/litecoin/.litecoin

# Create litecoin.conf from environment variables
cat > /home/litecoin/.litecoin/litecoin.conf << EOF
# Generated from environment variables
rpcuser=${LTC_RPC_USER}
rpcpassword=${LTC_RPC_PASS}
rpcport=${LTC_RPC_PORT:-9332}
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0:${LTC_RPC_PORT:-9332}
server=1
listen=1
daemon=0
printtoconsole=1
bind=0.0.0.0:${LTC_P2P_PORT:-9333}

# P2P port
port=${LTC_P2P_PORT:-9333}

# ZMQ Configuration for block notifications
zmqpubhashblock=tcp://0.0.0.0:${LTC_ZMQ_PORT:-28332}
zmqpubrawblock=tcp://0.0.0.0:${LTC_ZMQ_RAW_PORT:-28333}

# Additional settings for better operation
maxconnections=50
timeout=30000

# Pruning configuration (0 = disabled/full node, >550 = prune to specified MB)
prune=${LTC_PRUNE:-0}
EOF

# Fix ownership of the config file
chown litecoin:litecoin /home/litecoin/.litecoin/litecoin.conf

echo "Generated litecoin.conf with RPC settings"

# Switch to litecoin user and start litecoind with the configuration file
exec su litecoin -c "litecoind $*"