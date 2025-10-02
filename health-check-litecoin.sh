#!/bin/bash

# Health check script for litecoin
# This runs as root but switches to litecoin user to run the CLI command
# Explicitly specify connection details to ensure we use the right port

if su litecoin -c "litecoin-cli -rpcconnect=127.0.0.1 -rpcport=${LTC_RPC_PORT:-9332} getblockchaininfo" > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi