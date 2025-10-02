@echo off
REM Binary setup helper script for Litecoin-Meowcoin AuxPoW Proxy

echo [*] Binary Setup Helper
echo ======================

echo [*] Checking Litecoin binaries...

if exist "binaries\litecoin\litecoind" (
    echo [OK] Litecoin Daemon: Found
) else (
    echo [!!] Litecoin Daemon: Missing
    echo     Expected: binaries\litecoin\litecoind
)

if exist "binaries\litecoin\litecoin-cli" (
    echo [OK] Litecoin CLI: Found
) else (
    echo [!!] Litecoin CLI: Missing
    echo     Expected: binaries\litecoin\litecoin-cli
)

echo.
echo [*] Checking Meowcoin binaries...

if exist "binaries\meowcoin\meowcoind" (
    echo [OK] Meowcoin Daemon: Found
) else (
    echo [!!] Meowcoin Daemon: Missing
    echo     Expected: binaries\meowcoin\meowcoind
)

if exist "binaries\meowcoin\meowcoin-cli" (
    echo [OK] Meowcoin CLI: Found
) else (
    echo [!!] Meowcoin CLI: Missing
    echo     Expected: binaries\meowcoin\meowcoin-cli
)

echo.
echo [*] Directory structure:
echo binaries\
echo +-- litecoin\
if exist "binaries\litecoin" (
    for %%f in (binaries\litecoin\*) do (
        echo ^|   +-- %%~nxf
    )
) else (
    echo ^|   +-- ^(directory missing^)
)

echo +-- meowcoin\
if exist "binaries\meowcoin" (
    for %%f in (binaries\meowcoin\*) do (
        echo     +-- %%~nxf
    )
) else (
    echo     +-- ^(directory missing^)
)

echo.

REM Count missing binaries
set missing=0
if not exist "binaries\litecoin\litecoind" set /a missing+=1
if not exist "binaries\litecoin\litecoin-cli" set /a missing+=1
if not exist "binaries\meowcoin\meowcoind" set /a missing+=1
if not exist "binaries\meowcoin\meowcoin-cli" set /a missing+=1

if %missing%==0 (
    echo [SUCCESS] All required binaries are present!
    echo.
    echo [*] Next steps:
    echo 1. Build Docker images: docker compose build
    echo 2. Start services: docker compose up -d
    echo 3. Check logs: docker compose logs -f
) else (
    echo [WARNING] Missing %missing% required binaries
    echo.
    echo [*] To fix:
    echo 1. Copy binaries to the correct directories ^(see README.md^)
    echo 2. Run this script again to verify
    echo 3. Build Docker images: docker compose build
)

echo.
echo [HELP] Documentation:
echo   Binary requirements: See binaries\README.md
echo   Litecoin setup: See binaries\litecoin\README.md
echo   Meowcoin setup: See binaries\meowcoin\README.md

pause