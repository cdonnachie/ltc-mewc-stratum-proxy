#!/bin/bash

# Health check script for meowcoin
# This runs as root but switches to meowcoin user to run the CLI command
# Explicitly specify connection details to ensure we use the right port

if su meowcoin -c "meowcoin-cli -rpcconnect=127.0.0.1 -rpcport=${MEWC_RPC_PORT:-8766} getblockchaininfo" > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi