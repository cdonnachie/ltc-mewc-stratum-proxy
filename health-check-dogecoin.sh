#!/bin/bash
# Health check for Dogecoin daemon

# Try to call getblockchaininfo
if dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getblockchaininfo > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi
