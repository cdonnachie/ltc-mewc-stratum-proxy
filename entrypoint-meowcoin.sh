#!/bin/bash
set -e

# Ensure the data directory exists and has correct permissions
mkdir -p /home/meowcoin/.meowcoin
chown -R meowcoin:meowcoin /home/meowcoin/.meowcoin

# Create meowcoin.conf from environment variables
cat > /home/meowcoin/.meowcoin/meowcoin.conf << EOF
# Generated from environment variables
rpcuser=${MEWC_RPC_USER}
rpcpassword=${MEWC_RPC_PASS}
rpcport=${MEWC_RPC_PORT:-8766}
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0:${MEWC_RPC_PORT:-8766}
server=1
listen=1
daemon=0
printtoconsole=1

# P2P port
port=${MEWC_P2P_PORT:-8767}

# ZMQ Configuration for block notifications
zmqpubhashblock=tcp://0.0.0.0:${MEWC_ZMQ_PORT:-28433}
zmqpubrawblock=tcp://0.0.0.0:${MEWC_ZMQ_RAW_PORT:-28434}

# Additional settings for better operation
maxconnections=50
timeout=30000

# Pruning configuration (0 = disabled/full node, >550 = prune to specified MB)
prune=${MEWC_PRUNE:-0}
EOF

# Fix ownership of the config file
chown meowcoin:meowcoin /home/meowcoin/.meowcoin/meowcoin.conf

echo "Generated meowcoin.conf with RPC settings"

# Switch to meowcoin user and start meowcoind with the configuration file
exec su meowcoin -c "meowcoind $*"