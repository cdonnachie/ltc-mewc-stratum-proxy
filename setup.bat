@echo off
REM Litecoin-Meowcoin AuxPoW Proxy Setup Script for Windows

echo [*] Setting up Litecoin-Meowcoin AuxPoW Proxy...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose is not available. Please install Docker Compose.
        pause
        exit /b 1
    )
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo [*] Creating .env file...
    
    REM Generate random passwords (simplified for Windows)
    set LTC_PASS=ltc_%RANDOM%_%RANDOM%
    set MEWC_PASS=mewc_%RANDOM%_%RANDOM%
    
    (
        echo # Litecoin Configuration
        echo LTC_RPC_USER=litecoin_user
        echo LTC_RPC_PASS=%LTC_PASS%
        echo LTC_RPC_PORT=9332
        echo LTC_P2P_PORT=9333
        echo.
        echo # Meowcoin Configuration
        echo MEWC_RPC_USER=meowcoin_user
        echo MEWC_RPC_PASS=%MEWC_PASS%
        echo MEWC_RPC_PORT=8766
        echo MEWC_P2P_PORT=8767
        echo.
        echo # Wallet Addresses ^(UPDATE THESE WITH YOUR ACTUAL ADDRESSES^)
        echo # Litecoin address ^(optional - first miner connection sets this^)
        echo # LTC_WALLET_ADDRESS=ltc1youraddresshere
        echo MEWC_WALLET_ADDRESS=
        echo.
        echo # Stratum Proxy Configuration
        echo STRATUM_PORT=54321
        echo TESTNET=false
        echo VERBOSE=true
        echo SHOW_JOBS=true
    ) > .env
    
    echo [OK] .env file created with random passwords
    echo [NOTICE] Please update the wallet addresses in .env file
) else (
    echo [OK] .env file already exists
)

REM Create submit_history directory
if not exist submit_history mkdir submit_history

REM Check binaries
echo [*] Checking binaries...
call check-binaries.bat

REM Build and start services
echo [*] Building and starting services...
docker compose build --no-cache
docker compose up -d

echo.
echo [SUCCESS] Setup complete!
echo.
echo [*] Service Status:
docker compose ps

echo.
echo [*] Next Steps:
echo 1. Wait for blockchain sync (check with: docker compose logs -f litecoin meowcoin)
echo 2. Update wallet addresses in .env file
echo 3. Restart proxy: docker compose restart stratum-proxy
echo 4. Connect your miner to localhost:54321
echo.
echo [*] Commands:
echo   View logs:     docker compose logs -f
echo   Stop services: docker compose down
echo   Restart:       docker compose restart
echo.
echo [*] Monitoring:
echo   LTC status:   docker compose exec litecoin litecoin-cli getblockchaininfo
echo   MEWC status:  docker compose exec meowcoin meowcoin-cli getblockchaininfo
echo   Proxy logs:   docker compose logs -f stratum-proxy

pause