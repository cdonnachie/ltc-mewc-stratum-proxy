# Dogecoin Binaries

Place your Dogecoin daemon binaries in this directory.

## Required Files

- `dogecoind` - Dogecoin daemon (main node software)
- `dogecoin-cli` - Dogecoin command-line interface

## Binary Requirements

⚠️ **CRITICAL**: For Docker deployment, you **MUST** use Linux binaries!

### Platform Requirements

- **Architecture**: Linux x86_64 ELF binaries
- **NOT compatible**: Windows `.exe` or macOS binaries
- **Base System**: Ubuntu 24.04 compatible
- **glibc Version**: 2.36+ support recommended

### Verification

Check your binaries are the correct format:

```bash
file dogecoind
# Expected: ELF 64-bit LSB executable, x86-64, ...

file dogecoin-cli
# Expected: ELF 64-bit LSB executable, x86-64, ...
```

❌ **Wrong formats** (will NOT work in Docker):

- Windows: `PE32+ executable (console) x86-64, for MS Windows`
- macOS: `Mach-O 64-bit executable x86_64`

## Where to Get Binaries

### Option 1: Official Releases

Download from the official Dogecoin repository:

- https://github.com/dogecoin/dogecoin/releases

Look for the Linux x86_64 release (usually `dogecoin-*-x86_64-linux-gnu.tar.gz`)

### Option 2: Build from Source

```bash
git clone https://github.com/dogecoin/dogecoin.git
cd dogecoin
./autogen.sh
./configure --without-gui
make
# Binaries will be in src/ directory
```

### Option 3: Extract from Existing Installation

If you have Dogecoin Core installed on a Linux system:

```bash
# Usually located in:
/usr/local/bin/dogecoind
/usr/local/bin/dogecoin-cli

# Or
/usr/bin/dogecoind
/usr/bin/dogecoin-cli
```

## Blockchain Size

Dogecoin blockchain is approximately:

- **Full node**: ~80GB+
- **Pruned node** (recommended): ~10GB with `prune=10000`

## Security Note

Always verify checksums of downloaded binaries against official releases.

## Need Help?

Check the main project README.md for more information about:

- Docker setup
- Binary verification
- Troubleshooting
