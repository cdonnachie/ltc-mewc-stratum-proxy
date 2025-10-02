#!/bin/bash

echo "Testing CLI connectivity to blockchain nodes..."
echo

echo "Testing Litecoin CLI connection..."
docker compose exec litecoin litecoin-cli getblockchaininfo | head -5
echo

echo "Testing Meowcoin CLI connection..."  
docker compose exec meowcoin meowcoin-cli getblockchaininfo | head -5
echo

echo "Testing wallet generation..."
echo "Litecoin new address:"
docker compose exec litecoin litecoin-cli getnewaddress
echo

echo "Meowcoin new address:"
docker compose exec meowcoin meowcoin-cli getnewaddress
echo

echo "CLI tests complete!"