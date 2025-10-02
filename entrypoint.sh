#!/bin/bash

# Docker entrypoint script for stratum proxy
# Handles conditional argument passing based on environment variables

ARGS=(
    "python" "-m" "ltc_proxy.main"
    "--ip=0.0.0.0"
    "--port=${STRATUM_PORT:-50000}"
    "--rpcip=litecoin"
    "--rpcport=${LTC_RPC_PORT:-9332}"
    "--rpcuser=${LTC_RPC_USER}"
    "--rpcpass=${LTC_RPC_PASS}"
    "--aux-rpcip=meowcoin"
    "--aux-rpcport=${MEWC_RPC_PORT:-8766}"
    "--aux-rpcuser=${MEWC_RPC_USER}"
    "--aux-rpcpass=${MEWC_RPC_PASS}"
    "--aux-address=${MEWC_WALLET_ADDRESS}"
)

# Add conditional arguments
if [ -n "${PROXY_SIGNATURE}" ]; then
    ARGS+=("--proxy-signature=${PROXY_SIGNATURE}")
fi

# Add conditional flags only if they are explicitly set to "true"
if [ "${TESTNET,,}" = "true" ]; then
    ARGS+=("--testnet")
fi

if [ "${VERBOSE,,}" = "true" ]; then
    ARGS+=("--verbose")
fi

if [ "${SHOW_JOBS,,}" = "true" ]; then
    ARGS+=("--jobs")
fi

if [ "${USE_EASIER_TARGET,,}" = "true" ]; then
    ARGS+=("--use-easier-target")
fi

if [ "${DEBUG_SHARES,,}" = "true" ]; then
    ARGS+=("--debug-shares")
fi

# ZMQ arguments
if [ "${ENABLE_ZMQ,,}" = "true" ]; then
    ARGS+=("--enable-zmq")
    if [ -n "${LTC_ZMQ_ENDPOINT}" ]; then
        ARGS+=("--ltc-zmq-endpoint=${LTC_ZMQ_ENDPOINT}")
    fi
    if [ -n "${MEWC_ZMQ_ENDPOINT}" ]; then
        ARGS+=("--mewc-zmq-endpoint=${MEWC_ZMQ_ENDPOINT}")
    fi
elif [ "${ENABLE_ZMQ,,}" = "false" ]; then
    ARGS+=("--disable-zmq")
fi

echo "Starting with arguments: ${ARGS[@]}"
exec "${ARGS[@]}"