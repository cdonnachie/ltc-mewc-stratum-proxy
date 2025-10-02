@echo off
echo Testing CLI connectivity to blockchain nodes...
echo.

echo Testing Litecoin CLI connection...
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getblockchaininfo
echo.

echo Testing Dogecoin CLI connection...
docker compose exec dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getblockchaininfo
echo.

echo Testing Meowcoin CLI connection...
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getblockchaininfo  
echo.

echo Testing wallet generation...
echo Litecoin new address:
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getnewaddress
echo.

echo Dogecoin new address:
docker compose exec dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getnewaddress
echo.

echo Meowcoin new address:
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getnewaddress
echo.

echo CLI tests complete!
pause