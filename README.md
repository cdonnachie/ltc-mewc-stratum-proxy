# Litecoin Multi-Chain Stratum Proxy

A flexible stratum mining proxy for Litecoin with optional merge mining (AuxPoW) support for Dogecoin and/or Meowcoin.

## Merge Mining Modes

This proxy supports **flexible merge mining configurations**. Choose the mode that best suits your needs:

| Mode           | Command                                | Chains              | Disk (Full) | Disk (Pruned) | RAM   | Difficulty  |
| -------------- | -------------------------------------- | ------------------- | ----------- | ------------- | ----- | ----------- |
| **LTC Only**   | `docker compose up -d`                 | Litecoin only       | ~200GB      | ~10GB         | 2GB   | Standard    |
| **LTC + DOGE** | `docker compose --profile doge up -d`  | Litecoin + Dogecoin | ~280GB      | ~20GB         | 3-4GB | Recommended |
| **LTC + MEWC** | `docker cCheck blockchain sync status: |

```bash
# Litecoin
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getblockchaininfo

# Dogecoin
docker compose exec dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getblockchaininfo

# Meowcoin
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getblockchaininfo
```

Check mining info:

````bash
# Litecoin
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getmininginfo

# Dogecoin
docker compose exec dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getmininginfo

# Meowcoin
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getmininginfo
```wc up -d` | Litecoin + Meowcoin | ~205GB      | ~12GB         | 3GB   | Light       |
| **LTC + DOGE + MEWC** | `docker compose --profile full up -d` | All three chains    | ~285GB      | ~22GB         | 4-5GB | Advanced    |

**Most Popular:** LTC + DOGE (Dogecoin has excellent liquidity and value)

### How to Choose

- **LTC Only**: Just want Litecoin rewards, minimal resources
- **LTC + DOGE**: Best value - Dogecoin is popular and liquid
- **LTC + MEWC**: Smaller chain, lower difficulty, good for testing
- **LTC + DOGE + MEWC**: Maximum rewards, but requires most resources

## Quick Start

Choose your setup method:

### Option 1: Docker Compose (Recommended)

**Prerequisites:** Docker and Docker Compose installed

1. **Place Linux binaries**:

   ```bash
   # Required for all modes:
   binaries/litecoin/litecoind
   binaries/litecoin/litecoin-cli

   # Required for LTC+DOGE or LTC+DOGE+MEWC:
   binaries/dogecoin/dogecoind
   binaries/dogecoin/dogecoin-cli

   # Required for LTC+MEWC or LTC+DOGE+MEWC:
   binaries/meowcoin/meowcoind
   binaries/meowcoin/meowcoin-cli

   # Copy Linux x86_64 binaries (NOT Windows/macOS)
````

2. **Configure environment**:

   ```bash
   cp .env.example .env
   # Edit .env - set passwords and wallet addresses for desired chains
   # - Leave addresses blank for LTC only
   # - Set DOGE_WALLET_ADDRESS for LTC+DOGE
   # - Set MEWC_WALLET_ADDRESS for LTC+MEWC
   # - Set both addresses for triple mining
   ```

3. **Start services** (choose your mode):

   ```bash
   # LTC only (no merge mining)
   docker compose up -d

   # LTC + Dogecoin (recommended)
   docker compose --profile doge up -d

   # LTC + Meowcoin
   docker compose --profile mewc up -d

   # LTC + Dogecoin + Meowcoin (all chains)
   docker compose --profile full up -d

   # Watch logs
   docker compose logs -f stratum-proxy
   ```

4. **Connect miner**:
   - Server: `localhost:50000`
   - Username: Your Litecoin address
   - Password: anything

### Option 2: Native Python (Your Own Nodes)

**Prerequisites:** Python 3.8+, running litecoind and optionally dogecoind/meowcoind nodes

1. **Configure blockchain nodes**:

   - Copy `config/litecoin.conf` to your Litecoin data directory
   - Copy `config/dogecoin.conf` to your Dogecoin data directory (optional, for DOGE mining)
   - Copy `config/meowcoin.conf` to your Meowcoin data directory (optional, for MEWC mining)
   - Edit all files with secure passwords
   - Start desired daemons

2. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure proxy**:

   ```bash
   cp .env.example .env
   # Edit .env to match your node RPC settings
   ```

4. **Run proxy**:

   ```bash
   python -m ltc_proxy.run
   ```

5. **Connect miner**: Same as Docker method above

## Configuration

### Essential Environment Variables

| Variable                          | Description                         | Default            |
| --------------------------------- | ----------------------------------- | ------------------ |
| `LTC_RPC_PORT`                    | Litecoin RPC port                   | 9332               |
| `LTC_RPC_USER` / `LTC_RPC_PASS`   | Litecoin RPC credentials            | -                  |
| `DOGE_RPC_PORT`                   | Dogecoin RPC port                   | 22555              |
| `DOGE_RPC_USER` / `DOGE_RPC_PASS` | Dogecoin RPC credentials            | -                  |
| `DOGE_WALLET_ADDRESS`             | Dogecoin address for merge mining   | (blank = disabled) |
| `MEWC_RPC_PORT`                   | Meowcoin RPC port                   | 8766               |
| `MEWC_RPC_USER` / `MEWC_RPC_PASS` | Meowcoin RPC credentials            | -                  |
| `MEWC_WALLET_ADDRESS`             | Meowcoin address for merge mining   | (blank = disabled) |
| `STRATUM_PORT`                    | Port for miners to connect          | 50000              |
| `SHARE_DIFFICULTY_DIVISOR`        | Share difficulty (higher = easier)  | 1000.0             |
| `USE_EASIER_TARGET`               | Use easiest target among all chains | true               |
| `ENABLE_ZMQ`                      | Enable ZMQ block notifications      | true               |

### Share Difficulty

`SHARE_DIFFICULTY_DIVISOR` controls how often miners submit shares:

- **Higher** (e.g., 2000): Easier shares, more frequent, better for home mining
- **Lower** (e.g., 500): Harder shares, less traffic, better for pools
- **Default (1000)**: Good balance

## Merged Mining (AuxPoW)

When auxiliary chain wallet addresses are set, the proxy enables merged mining. You can mine:

- **LTC + DOGE** (set `DOGE_WALLET_ADDRESS`)
- **LTC + MEWC** (set `MEWC_WALLET_ADDRESS`)
- **LTC + DOGE + MEWC** (set both addresses)

Here's how it works:

### How It Works

Litecoin (LTC), Dogecoin (DOGE), and Meowcoin (MEWC) all use the **same Scrypt PoW hash** for difficulty validation:

```
Block Header (80 bytes)
    ↓
Scrypt PoW hash → Compare with LTC, DOGE, and MEWC targets
    ↓
    ├─→ Meets LTC target? → Submit to LTC → Earn LTC
    ├─→ Meets DOGE target? → Submit AuxPoW to DOGE → Earn DOGE
    └─→ Meets MEWC target? → Submit AuxPoW to MEWC → Earn MEWC

Example at typical difficulties:
  Scrypt PoW: 0x00000065...

  Compare: 0x00000065... < 0x0000007e... (LTC target) → ✗ No
  Compare: 0x00000065... < 0x00000078... (DOGE target) → ✓ Yes!
  Compare: 0x00000065... < 0x00000080... (MEWC target) → ✓ Yes!

  Result: Submit to DOGE and MEWC, earn both rewards!
```

### AuxPoW Structure

When submitting to auxiliary chains (DOGE/MEWC), the proxy creates an AuxPoW proof containing:

- Parent (LTC) coinbase transaction
- Parent block hash (double SHA-256) - for block identification
- Merkle proofs
- Parent block header (80 bytes)

**Important**: While double SHA-256 is used for the block hash in the AuxPoW structure (what appears on block explorers), all chains validate difficulty using the **Scrypt PoW hash**.

### Block Finding Scenarios

With typical difficulties, you'll find blocks on different chains:

**Dual Mining (LTC + DOGE):**

1. **DOGE only**: Scrypt PoW meets DOGE target → Submit AuxPoW → Earn DOGE (common)
2. **LTC only**: Scrypt PoW meets LTC target → Submit block → Earn LTC (less common)
3. **Both chains**: Scrypt PoW meets BOTH targets → Submit to both → Double rewards! (rare)

**Triple Mining (LTC + DOGE + MEWC):**

1. **MEWC only**: Easiest target → Most common finds
2. **DOGE only**: Medium target → Regular finds
3. **MEWC + DOGE**: Both aux targets met → Double aux rewards!
4. **LTC only**: Hardest target → Rare but valuable
5. **All three**: Jackpot! → Triple rewards! (very rare)

**Why auxiliary blocks are more common:**

- Auxiliary chains typically have easier targets than Litecoin
- All chains check the same Scrypt PoW hash
- The easier target means more shares qualify for auxiliary chains
- **Result**: You'll find more DOGE/MEWC blocks than LTC blocks

**Note:** The proxy automatically uses whichever target is easier when `USE_EASIER_TARGET=true`.

## Monitoring

**Block submissions** are logged to `./submit_history/`:

- `LTC_<height>_<job>_<time>.txt` - Litecoin blocks
- `DOGE_<height>_<job>_<time>.txt` - Dogecoin AuxPoW blocks
- `MEWC_<height>_<job>_<time>.txt` - Meowcoin AuxPoW blocks

**Check logs:**

```bash
# Docker
docker compose logs -f stratum-proxy

# Native
# Watch console output
```

## Troubleshooting

**"Coinbase parts not ready"**: Nodes still syncing, wait for full sync

**"DOGE/MEWC aux job is stale"**: Normal when auxiliary chains find blocks, proxy auto-refreshes

**Miner can't connect**: Check firewall, verify STRATUM_PORT is correct

**Binary format error**: Must use Linux ELF x86_64 binaries for Docker

**Low hashrate**: Increase `SHARE_DIFFICULTY_DIVISOR` for more frequent feedback

**Service won't start with profile**: Ensure binaries exist for that chain (e.g., `binaries/dogecoin/` for `--profile doge`)

## Advanced

### ZMQ Block Notifications

The proxy uses ZMQ for instant block notifications instead of polling:

- **LTC**: Port 28332
- **DOGE**: Port 28444
- **MEWC**: Port 28433

All conf files include ZMQ settings. Disable with `ENABLE_ZMQ=false` if needed.

### Job IDs

Job IDs are Unix timestamps (e.g., `66fb8a10`), updated:

- On new blocks (via ZMQ)
- Every 30 seconds (nTime rolls)
- When auxiliary chains create new templates

### Docker Profiles

Use profiles to control which chains run:

```bash
# LTC only (no profile needed)
docker compose up -d

# Add Dogecoin
docker compose --profile doge up -d

# Add Meowcoin
docker compose --profile mewc up -d

# All chains
docker compose --profile full up -d

# Stop specific profile
docker compose --profile doge down
```

### Project Structure

```
ltc_proxy/
├── consensus/    # Block/transaction building
├── rpc/          # RPC client implementations
├── state/        # Template state management
├── stratum/      # Stratum protocol server
├── utils/        # Hashing and encoding
└── zmq/          # ZMQ block listeners
```

## Additional Documentation

- **[Quick Start Guide](QUICK_START_MULTI_CHAIN.md)** - Fast setup with checklists and examples
- **[Choosing a Mode](CHOOSING_A_MODE.md)** - Detailed comparison to help you decide
- **[Implementation Details](MULTI_CHAIN_IMPLEMENTATION.md)** - Technical architecture and design

## License

MIT License - See LICENSE file

A Docker Compose setup for running a stratum proxy that enables mining Litecoin (parent chain) with optional merge mining of Dogecoin and/or Meowcoin (auxiliary chains) using AuxPoW.

## Quick Start

1. **Place the Linux binaries**:

   - Copy **Linux x86_64** `litecoind` and `litecoin-cli` to `binaries/litecoin/`
   - Copy **Linux x86_64** `dogecoind` and `dogecoin-cli` to `binaries/dogecoin/` (optional, for DOGE mining)
   - Copy **Linux x86_64** `meowcoind` and `meowcoin-cli` to `binaries/meowcoin/` (optional, for MEWC mining)

   ⚠️ **Important**: Use Linux binaries only (not Windows .exe or macOS binaries)

2. **Update the environment file**:

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Configure wallet addresses** (optional):
   Edit the `.env` file and set:

   - `DOGE_WALLET_ADDRESS`: Your Dogecoin address for LTC+DOGE mining (leave blank to disable)
   - `MEWC_WALLET_ADDRESS`: Your Meowcoin address for LTC+MEWC mining (leave blank to disable)
   - Update RPC credentials for security

4. **Start the services**:

   ```bash
   docker compose up -d
   ```

5. **Check logs**:

   ```bash
   docker compose logs -f stratum-proxy
   ```

6. **Connect your miner**:
   - Point your miner to `localhost:50000`
   - Use your Litecoin address as username
   - Any password

## Configuration

### Environment Variables

| Variable                   | Description                                            | Default                 |
| -------------------------- | ------------------------------------------------------ | ----------------------- |
| `LTC_RPC_USER`             | Litecoin RPC username                                  | litecoin_user           |
| `LTC_RPC_PASS`             | Litecoin RPC password                                  | -                       |
| `LTC_RPC_PORT`             | Litecoin RPC port                                      | 9332                    |
| `LTC_P2P_PORT`             | Litecoin P2P port                                      | 9333                    |
| `DOGE_RPC_USER`            | Dogecoin RPC username                                  | dogecoin_user           |
| `DOGE_RPC_PASS`            | Dogecoin RPC password                                  | -                       |
| `DOGE_RPC_PORT`            | Dogecoin RPC port                                      | 22555                   |
| `DOGE_P2P_PORT`            | Dogecoin P2P port                                      | 22556                   |
| `DOGE_WALLET_ADDRESS`      | Dogecoin wallet address (blank = disabled)             | (blank - disables DOGE) |
| `MEWC_RPC_USER`            | Meowcoin RPC username                                  | meowcoin_user           |
| `MEWC_RPC_PASS`            | Meowcoin RPC password                                  | -                       |
| `MEWC_RPC_PORT`            | Meowcoin RPC port                                      | 8766                    |
| `MEWC_P2P_PORT`            | Meowcoin P2P port                                      | 8767                    |
| `MEWC_WALLET_ADDRESS`      | Meowcoin wallet address (blank = disabled)             | (blank - disables MEWC) |
| `STRATUM_PORT`             | Stratum proxy port                                     | 50000                   |
| `PROXY_SIGNATURE`          | Custom coinbase signature                              | /ltc-stratum-proxy/     |
| `USE_EASIER_TARGET`        | Enable easier target selection                         | true                    |
| `SHARE_DIFFICULTY_DIVISOR` | Share difficulty divisor (higher = easier/more shares) | 1000.0                  |
| `TESTNET`                  | Use testnet                                            | false                   |
| `VERBOSE`                  | Enable verbose logging                                 | true                    |
| `SHOW_JOBS`                | Show job updates in logs                               | true                    |

## Binary Setup

This setup uses local binaries instead of pre-built Docker images, giving you complete control over the cryptocurrency node versions.

### Required Binaries

Place the following files in their respective directories:

**Litecoin** (`binaries/litecoin/`) - Required:

- `litecoind` - The main daemon
- `litecoin-cli` - CLI client

**Dogecoin** (`binaries/dogecoin/`) - Optional (for DOGE mining):

- `dogecoind` - The main daemon
- `dogecoin-cli` - CLI client

**Meowcoin** (`binaries/meowcoin/`) - Optional (for MEWC mining):

- `meowcoind` - The main daemon
- `meowcoin-cli` - CLI client

### Binary Requirements

⚠️ **Critical**: Only Linux binaries work with Docker containers!

- **Platform**: Linux x86_64 ELF binaries (NOT Windows .exe or macOS binaries)
- **Base System**: Ubuntu 24.04 compatible
- **glibc Version**: 2.36+ support (Ubuntu 24.04 provides glibc 2.39)
- **Executable permissions**: Set automatically by Docker
- **Dependencies**: Must be included or statically linked

### Getting Binaries

1. **Download releases** from official repositories
2. **Build from source** for your specific needs
3. **Extract from existing installations**

### Verification

Check if binaries are correct format:

```bash
file binaries/litecoin/litecoind
file binaries/dogecoin/dogecoind
file binaries/meowcoin/meowcoind
```

**Expected Output:**

```
binaries/litecoin/litecoind: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, stripped
binaries/dogecoin/dogecoind: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, stripped
binaries/meowcoin/meowcoind: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0, stripped
```

❌ **Wrong formats** (will NOT work):

- Windows: `PE32+ executable (console) x86-64, for MS Windows`
- macOS: `Mach-O 64-bit executable x86_64`

### Services

- **litecoin**: Litecoin daemon (parent chain)
  - RPC: `localhost:9332`
  - P2P: `localhost:9333`
- **dogecoin**: Dogecoin daemon (auxiliary chain, optional)
  - RPC: `localhost:22555`
  - P2P: `localhost:22556`
- **meowcoin**: Meowcoin daemon (auxiliary chain, optional)
  - RPC: `localhost:8766`
  - P2P: `localhost:8767`
- **stratum-proxy**: Mining proxy
  - Stratum: `localhost:50000`

## Customization

### Proxy Signature

The proxy includes a customizable signature in coinbase transactions to identify your mining setup. This appears in the blockchain and helps identify blocks found by your proxy.

**Configuration Options:**

1. **Environment Variable** (recommended for Docker):

   ```bash
   # In .env file
   PROXY_SIGNATURE=/your-pool-name/
   ```

2. **Command Line Argument**:
   ```bash
   python -m ltc_proxy.run --proxy-signature="/my-custom-signature/"
   ```

**Guidelines:**

- Keep it short (max 32 bytes recommended)
- Use forward slashes or other characters to make it recognizable
- Examples: `/MyPool/`, `/Solo-Miner-2025/`, `/LTC-MEWC-Proxy/`

**Default:** `/ltc-stratum-proxy/`

## Usage

### Native Python Execution (Without Docker)

If you prefer to run the proxy directly with Python instead of using Docker:

#### Prerequisites

1. **Python 3.8+** installed on your system
2. **Litecoin node** running (required), and optionally **Dogecoin and/or Meowcoin nodes** (for merge mining)
3. **Python dependencies** installed

#### Setup Steps

1. **Install Python dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your blockchain nodes** (optional):

   For convenience, you can use the provided configuration templates:

   - **Litecoin**: Copy `litecoin.conf` to your Litecoin data directory
   - **Dogecoin**: Copy `dogecoin.conf` to your Dogecoin data directory (optional)
   - **Meowcoin**: Copy `meowcoin.conf` to your Meowcoin data directory (optional)

   **Data directory locations:**

   - Windows: `%APPDATA%\Litecoin\`, `%APPDATA%\Dogecoin\`, and `%APPDATA%\Meowcoin\`
   - Linux: `~/.litecoin/`, `~/.dogecoin/`, and `~/.meowcoin/`
   - macOS: `~/Library/Application Support/Litecoin/`, `~/Library/Application Support/Dogecoin/`, and `~/Library/Application Support/Meowcoin/`

3. **Ensure your nodes are running**:

   - Litecoin node accessible via RPC (default: `localhost:9332`)
   - Dogecoin node accessible via RPC (default: `localhost:22555`) - optional
   - Meowcoin node accessible via RPC (default: `localhost:8766`) - optional

4. **Run the proxy**:

   **For localhost testing only:**

   ```bash
   python -m ltc_proxy.run \
     --ip=127.0.0.1 \
     --port=50000 \
     --rpcuser=your_ltc_rpc_user \
     --rpcpass=your_ltc_rpc_password \
     --rpcip=127.0.0.1 \
     --rpcport=9332 \
     --aux-rpcuser=your_mewc_rpc_user \
     --aux-rpcpass=your_mewc_rpc_password \
     --aux-rpcip=127.0.0.1 \
     --aux-rpcport=8766 \
     --aux-address=your_meowcoin_address \
     --use-easier-target \
     --verbose
   ```

   **For HiveOS rigs or remote miners:**

   ```bash
   python -m ltc_proxy.run \
     --ip=0.0.0.0 \
     --port=50000 \
     --rpcuser=your_ltc_rpc_user \
     --rpcpass=your_ltc_rpc_password \
     --aux-address=your_meowcoin_address \
     --use-easier-target \
     --verbose
   ```

#### Example with Environment Variables

You can also use environment variables (create a `.env` file or export them):

```bash
# Set environment variables
export LTC_RPC_USER=your_ltc_user
export LTC_RPC_PASS=your_ltc_password
export MEWC_RPC_USER=your_mewc_user
export MEWC_RPC_PASS=your_mewc_password
export MEWC_WALLET_ADDRESS=your_meowcoin_address
export PROXY_SIGNATURE=/my-custom-proxy/

# Run with minimal arguments (reads from environment)
python -m ltc_proxy.run \
  --rpcuser=$LTC_RPC_USER \
  --rpcpass=$LTC_RPC_PASS \
  --aux-rpcuser=$MEWC_RPC_USER \
  --aux-rpcpass=$MEWC_RPC_PASS \
  --aux-address=$MEWC_WALLET_ADDRESS \
  --use-easier-target \
  --verbose
```

#### Network Binding Options

The `--ip` parameter controls which network interface the proxy binds to:

| IP Address      | Use Case                | Security | Description                                             |
| --------------- | ----------------------- | -------- | ------------------------------------------------------- |
| `127.0.0.1`     | **Testing/Development** | High     | Localhost only - miners must run on same machine        |
| `0.0.0.0`       | **Production Mining**   | Medium   | All interfaces - HiveOS rigs, remote miners can connect |
| `192.168.1.100` | **Specific Network**    | Medium   | Bind to specific IP - only that network interface       |

**Security Considerations:**

- `127.0.0.1`: Safest, only local access
- `0.0.0.0`: Requires firewall rules to restrict access
- Specific IP: Good compromise between accessibility and security

#### Available Options

Run `python -m ltc_proxy.run --help` to see all available options:

- `--ip`: IP address to bind proxy server on (default: 127.0.0.1)
- `--port`: Stratum port (default: 50000)
- `--rpcip/--rpcport`: Litecoin RPC connection
- `--aux-rpcip/--aux-rpcport`: Auxiliary chain RPC connection (DOGE or MEWC)
- `--proxy-signature`: Custom coinbase signature
- `--use-easier-target`: Enable easier target selection
- `--testnet`: Use testnet mode
- `--verbose`: Enable debug logging
- `--jobs`: Show job updates

### Docker Compose Usage

For a complete containerized setup:

#### Start All Services

```bash
docker compose up -d
```

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

### Stop Services

```bash
docker compose down
```

### Update Configuration

```bash
# Edit environment
nano .env

# Restart services
docker compose down && docker compose up -d
```

### Choosing Between Native Python vs Docker

| Aspect               | Native Python                        | Docker Compose                    |
| -------------------- | ------------------------------------ | --------------------------------- |
| **Setup Complexity** | Medium - requires manual node setup  | Easy - everything automated       |
| **Resource Usage**   | Lower - no container overhead        | Higher - container isolation      |
| **Development**      | Easier debugging and development     | More isolated but harder to debug |
| **Dependencies**     | Manual Python dependency management  | Fully contained environment       |
| **Node Management**  | Manual - you manage nodes separately | Automatic - nodes included        |
| **Platform**         | Any OS with Python support           | Any OS with Docker support        |
| **Customization**    | Full control over all components     | Limited to configuration files    |
| **Production**       | Requires more system administration  | Better for deployment and scaling |

**Choose Native Python if:**

- You're developing or debugging the proxy
- You already have Litecoin/Dogecoin/Meowcoin nodes running
- You want minimal resource usage
- You need fine-grained control

**Choose Docker Compose if:**

- You want a complete, easy setup
- You're deploying to production
- You prefer isolated environments
- You don't want to manage nodes manually

### Mining

Connect your miner to the stratum proxy:

- **Host**: Your server IP
- **Port**: 50000 (or your configured STRATUM_PORT)
- **Username**: Your Litecoin address (e.g., `ltc1qyour_litecoin_address.worker1`)
- **Password**: Any value

The first address that connects becomes the payout address for Litecoin rewards. If `DOGE_WALLET_ADDRESS` is configured, Dogecoin rewards go to that address. If `MEWC_WALLET_ADDRESS` is configured, Meowcoin rewards go to that address. If both auxiliary addresses are blank, only Litecoin will be mined.

#### Sample Miner Commands

**cpuminer-multi or similar (Scrypt algorithm):**

```bash
# For localhost testing
minerd -a scrypt -o stratum+tcp://localhost:50000 -u ltc1qyour_litecoin_address -p x

# For remote server
minerd -a scrypt -o stratum+tcp://192.168.1.100:50000 -u ltc1qyour_litecoin_address.worker1 -p x
```

**HiveOS Configuration:**

```bash
# Miner: Select your preferred Scrypt miner
# Algorithm: scrypt
# Pool: stratum+tcp://YOUR_SERVER_IP:50000
# Wallet: ltc1qyour_litecoin_address.%WORKER_NAME%
# Password: x
```

**Note**: Replace `ltc1qyour_litecoin_address` with your actual Litecoin address.

### Configuration Files

The Docker containers automatically generate configuration files (`litecoin.conf`, `dogecoin.conf`, and `meowcoin.conf`) from your `.env` file settings. This ensures that CLI tools work properly and all settings are consistent.

**Generated configuration includes:**

- RPC credentials and port settings
- Network and connection parameters
- Optimized settings for proxy operation

### RPC Command Line Access

You can interact with the blockchain nodes using RPC commands for monitoring, debugging, and management. Here are examples for both Docker and native setups:

#### Docker Container RPC Commands

**Litecoin Commands:**

```bash
# Get mining information
docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getmininginfo

# Get blockchain info
docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getblockchaininfo

# Get wallet info
docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getwalletinfo

# Generate new address
docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getnewaddress

# Get network connections
docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getconnectioncount

# Alternative: Switch to litecoin user first
docker compose exec -it litecoin /bin/bash
su - litecoin
litecoin-cli getmininginfo
```

**Dogecoin Commands:**

```bash
# Get mining information
docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getmininginfo

# Get blockchain info
docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getblockchaininfo

# Get wallet info
docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getwalletinfo

# Generate new address
docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getnewaddress

# Get AuxPoW information
docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getauxblock

# Alternative: Switch to dogecoin user first
docker compose exec -it dogecoin /bin/bash
su - dogecoin
dogecoin-cli getmininginfo
```

**Meowcoin Commands:**

```bash
# Get mining information
docker compose exec -it meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getmininginfo

# Get blockchain info
docker compose exec -it meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getblockchaininfo

# Get wallet info
docker compose exec -it meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getwalletinfo

# Generate new address
docker compose exec -it meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getnewaddress

# Get AuxPoW information
docker compose exec -it meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getauxblock

# Alternative: Switch to meowcoin user first
docker compose exec -it meowcoin /bin/bash
su - meowcoin
meowcoin-cli getmininginfo
```

#### Native Installation RPC Commands

**Litecoin Commands:**

```bash
# Using configuration file (recommended)
litecoin-cli getmininginfo

# Using explicit RPC parameters
litecoin-cli -rpcuser=litecoin_user -rpcpassword=litecoin_password -rpcport=9332 getmininginfo
```

**Dogecoin Commands:**

```bash
# Using configuration file (recommended)
dogecoin-cli getmininginfo

# Using explicit RPC parameters
dogecoin-cli -rpcuser=dogecoin_user -rpcpassword=dogecoin_password -rpcport=22555 getmininginfo
```

**Meowcoin Commands:**

```bash
# Using configuration file (recommended)
meowcoin-cli getmininginfo

# Using explicit RPC parameters
meowcoin-cli -rpcuser=meowcoin_user -rpcpassword=meowcoin_password -rpcport=8766 getmininginfo
```

#### Useful RPC Commands for Mining

**Monitor Mining Status:**

```bash
# Check if mining is active
getmininginfo

# Get current block height
getblockcount

# Get network hash rate
getnetworkhashps

# Check wallet balance
getbalance

# List recent transactions
listtransactions
```

**Debug Network Issues:**

```bash
# Check peer connections
getconnectioncount
getpeerinfo

# Check sync status
getblockchaininfo

# Verify daemon is responsive
uptime
```

**AuxPoW Specific (Dogecoin/Meowcoin):**

```bash
# Get auxiliary block for mining
getauxblock

# Submit auxiliary proof of work
getauxblock <hash> <auxpow>
```

#### Troubleshooting RPC Access

If you encounter RPC authentication errors:

1. **Verify credentials match your `.env` file**
2. **For Docker**: Use the `-datadir` parameter or switch to the correct user
3. **For native**: Ensure the configuration file exists in the expected location
4. **Check the daemon is running**: Look for the process in `docker compose ps` or system processes

### Wallet Setup

**Important**: Litecoin requires creating and loading a wallet. Dogecoin and Meowcoin use the traditional single wallet.dat file that is automatically created.

1. **Create Litecoin Wallet**:

   ```bash
   # Create a new wallet named "default"
   docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" createwallet "default"

   # Load the wallet and set it to load on startup
   docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" loadwallet "default" true
   ```

2. **Generate Litecoin Address**:

   ```bash
   docker compose exec -it litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getnewaddress
   ```

3. **Generate Dogecoin Address** (optional, for DOGE mining):

   ```bash
   # Dogecoin uses traditional wallet.dat (auto-created on first run)
   docker compose exec -it dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getnewaddress
   ```

4. **Generate Meowcoin Address** (optional, for MEWC mining):

   ```bash
   # Meowcoin uses traditional wallet.dat (auto-created on first run)
   docker compose exec -it meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getnewaddress
   ```

5. **Update .env file** with your addresses (optional - leave auxiliary addresses blank to disable those chains)

### CLI Testing

Test that CLI tools are working correctly:

```bash
# Linux/macOS
./test-cli.sh

# Windows
test-cli.bat

# Or manually test individual commands
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getblockchaininfo
docker compose exec dogecoin dogecoin-cli -datadir="/home/dogecoin/.dogecoin" getblockchaininfo
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getblockchaininfo
```

### Monitoring

````

Check blockchain sync status:

```bash
# Litecoin
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getblockchaininfo

# Meowcoin
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getblockchaininfo
````

Check mining info:

```bash
# Litecoin
docker compose exec litecoin litecoin-cli -datadir="/home/litecoin/.litecoin" getmininginfo

# Meowcoin
docker compose exec meowcoin meowcoin-cli -datadir="/home/meowcoin/.meowcoin" getmininginfo
```

## Troubleshooting

### Services Won't Start

- Check Docker logs: `docker compose logs [service-name]`
- Verify `.env` file configuration
- Ensure ports aren't already in use

### Proxy Connection Issues

- Verify all enabled daemons are synced
- Check RPC connectivity for each chain
- Review proxy logs for errors

### Mining Issues

- Ensure miner is pointing to correct host:port
- Verify wallet address format
- Check proxy logs for submission details

## Security Notes

- Change default RPC passwords in `.env`
- Consider using firewall rules for RPC ports
- Keep wallet backups secure
- Monitor for unauthorized access

## File Structure

```
ltc-auxpow-stratum-proxy/
├── docker-compose.yml       # Main compose file
├── .env.example             # Example environment configuration
├── .gitignore               # Git ignore rules
├── Dockerfile               # Proxy container build
├── Dockerfile.litecoin      # Litecoin daemon container
├── Dockerfile.dogecoin      # Dogecoin daemon container
├── Dockerfile.meowcoin      # Meowcoin daemon container
├── entrypoint.sh            # Docker entrypoint script
├── requirements.txt         # Python dependencies
├── setup.sh / setup.bat     # Setup scripts for different platforms
├── health-check.sh          # Health check scripts
├── binaries/                # Cryptocurrency binaries directory
│   ├── litecoin/            # Litecoin binaries
│   ├── dogecoin/            # Dogecoin binaries
│   └── meowcoin/            # Meowcoin binaries
├── config/                  # Configuration templates directory
│   ├── litecoin.conf        # Litecoin daemon config template
│   ├── dogecoin.conf        # Dogecoin daemon config template
│   └── meowcoin.conf        # Meowcoin daemon config template
├── ltc_proxy/               # Proxy application package
│   ├── consensus/          # Block/transaction building
│   ├── rpc/                # RPC client implementations
│   ├── state/              # Template state management
│   ├── stratum/            # Stratum protocol server
│   ├── utils/              # Hashing and encoding
│   └── zmq/                # ZMQ block listeners
└── submit_history/          # Block submission logs
```
