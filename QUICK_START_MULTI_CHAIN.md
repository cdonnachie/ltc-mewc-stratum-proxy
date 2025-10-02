# Multi-Chain Merge Mining Quick Reference

## Quick Start Commands

### Choose Your Mining Mode

```bash
# LTC Only (2GB RAM, ~10-200GB disk)
docker compose up -d

# LTC + Dogecoin (3-4GB RAM, ~20-280GB disk) - RECOMMENDED
docker compose --profile doge up -d

# LTC + Meowcoin (3GB RAM, ~12-205GB disk)
docker compose --profile mewc up -d

# LTC + Dogecoin + Meowcoin (4-5GB RAM, ~22-285GB disk)
docker compose --profile full up -d
```

## Setup Checklist

### For LTC Only

- [x] Copy `litecoind` and `litecoin-cli` to `binaries/litecoin/`
- [ ] Edit `.env` with LTC_RPC_USER and LTC_RPC_PASS
- [ ] Run: `docker compose up -d`

### For LTC + DOGE (Recommended)

- [x] Copy Litecoin binaries (above)
- [x] Copy `dogecoind` and `dogecoin-cli` to `binaries/dogecoin/`
- [ ] Edit `.env`:
  - Set LTC_RPC_USER and LTC_RPC_PASS
  - Set DOGE_RPC_USER and DOGE_RPC_PASS
  - Set DOGE_WALLET_ADDRESS=DYourDogeAddress
- [ ] Run: `docker compose --profile doge up -d`

### For LTC + MEWC

- [x] Copy Litecoin binaries (above)
- [x] Copy `meowcoind` and `meowcoin-cli` to `binaries/meowcoin/`
- [ ] Edit `.env`:
  - Set LTC_RPC_USER and LTC_RPC_PASS
  - Set MEWC_RPC_USER and MEWC_RPC_PASS
  - Set MEWC_WALLET_ADDRESS=MYourMewcAddress
- [ ] Run: `docker compose --profile mewc up -d`

### For Triple Mining (LTC + DOGE + MEWC)

- [x] Copy all binaries (Litecoin, Dogecoin, Meowcoin)
- [ ] Edit `.env` with all RPC credentials and wallet addresses
- [ ] Run: `docker compose --profile full up -d`

## Binary Downloads

### Litecoin

- Official: https://litecoin.org/
- GitHub: https://github.com/litecoin-project/litecoin/releases
- Need: Linux x86_64 binaries

### Dogecoin

- Official: https://dogecoin.com/
- GitHub: https://github.com/dogecoin/dogecoin/releases
- Need: Linux x86_64 binaries (`dogecoin-*-x86_64-linux-gnu.tar.gz`)

### Meowcoin

- Official: https://www.mewccrypto.com/
- GitHub: https://github.com/Meowcoin-Foundation/Meowcoin/releases
- Need: Linux x86_64 binaries

## .env Configuration Examples

### LTC Only

```bash
LTC_RPC_USER=litecoin_user
LTC_RPC_PASS=your_secure_password
DOGE_WALLET_ADDRESS=
MEWC_WALLET_ADDRESS=
```

### LTC + DOGE (Popular!)

```bash
LTC_RPC_USER=litecoin_user
LTC_RPC_PASS=your_ltc_password
DOGE_RPC_USER=dogecoin_user
DOGE_RPC_PASS=your_doge_password
DOGE_WALLET_ADDRESS=DYourDogeAddress123
MEWC_WALLET_ADDRESS=
```

### LTC + MEWC

```bash
LTC_RPC_USER=litecoin_user
LTC_RPC_PASS=your_ltc_password
MEWC_RPC_USER=meowcoin_user
MEWC_RPC_PASS=your_mewc_password
DOGE_WALLET_ADDRESS=
MEWC_WALLET_ADDRESS=MYourMewcAddress123
```

### Triple Mining

```bash
LTC_RPC_USER=litecoin_user
LTC_RPC_PASS=your_ltc_password
DOGE_RPC_USER=dogecoin_user
DOGE_RPC_PASS=your_doge_password
MEWC_RPC_USER=meowcoin_user
MEWC_RPC_PASS=your_mewc_password
DOGE_WALLET_ADDRESS=DYourDogeAddress123
MEWC_WALLET_ADDRESS=MYourMewcAddress123
```

## Pruning Configuration (Save Disk Space)

Add these to `.env` to enable pruning:

```bash
# Prune to ~10GB each (instead of full ~200GB+)
LTC_PRUNE=10000
DOGE_PRUNE=10000
MEWC_PRUNE=2000

# Total disk usage with pruning: ~22GB
# Total disk usage without pruning: ~285GB
```

## Useful Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f stratum-proxy
docker compose logs -f litecoin
docker compose logs -f dogecoin
docker compose logs -f meowcoin
```

### Check Status

```bash
# List running containers
docker compose ps

# Check blockchain sync status
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getblockchaininfo
docker compose exec dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getblockchaininfo
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getblockchaininfo
```

### Generate Wallet Addresses

```bash
# Litecoin (create wallet first)
docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" createwallet "default"
docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getnewaddress

# Dogecoin (create wallet first)
docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" createwallet "default"
docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getnewaddress

# Meowcoin (wallet.dat auto-created)
docker compose exec -it meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getnewaddress
```

### Stop Services

```bash
# Stop all
docker compose down

# Stop specific profile
docker compose --profile doge down
docker compose --profile mewc down
```

### Change Mining Mode

```bash
# Stop current mode
docker compose down

# Update .env with new wallet addresses

# Start new mode
docker compose --profile doge up -d    # or mewc, or full
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose logs [service-name]

# Verify binaries exist
ls -la binaries/litecoin/
ls -la binaries/dogecoin/
ls -la binaries/meowcoin/

# Verify binary format (must be Linux ELF)
file binaries/litecoin/litecoind
```

### Sync Taking Too Long

- **Expected**: Initial sync can take hours or days
- **Check progress**: Use `getblockchaininfo` commands above
- **Speed up**: Ensure good internet connection, consider using bootstrap

### Out of Disk Space

- Enable pruning in `.env` (see Pruning Configuration above)
- Restart services: `docker compose down && docker compose up -d`

### Miner Can't Connect

```bash
# Check proxy is running
docker compose ps

# Test connection
telnet localhost 50000

# Check firewall
# Ensure port 50000 is open if mining from remote machines
```

## Miner Configuration

Point your Scrypt miner to:

- **Server**: `your_server_ip:50000`
- **Algorithm**: `scrypt`
- **Username**: Your Litecoin address (e.g., `ltc1qyouraddress`)
- **Password**: `x` (or anything)

Example:

```bash
minerd -a scrypt -o stratum+tcp://192.168.1.100:50000 -u ltc1qyouraddress -p x
```

## Expected Results

### Block Finding Rates (Approximate)

With typical network difficulties:

**LTC + DOGE Mode:**

- Dogecoin blocks: More frequent (easier difficulty)
- Litecoin blocks: Less frequent (harder difficulty)
- Both simultaneously: Rare but awesome!

**LTC + DOGE + MEWC Mode:**

- Meowcoin blocks: Most frequent (easiest)
- Dogecoin blocks: Regular
- Litecoin blocks: Least frequent (hardest)
- Multiple chains: Occasional
- All three chains: Very rare jackpot!

## Support

- Main README: `README.md`
- Implementation Details: `MULTI_CHAIN_IMPLEMENTATION.md`
- Binary Setup: `binaries/*/README.md`
- Configuration Templates: `config/*.conf`
