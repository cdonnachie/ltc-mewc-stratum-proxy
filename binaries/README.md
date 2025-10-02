# Cryptocurrency Binaries Directory

This directory contains the local binaries for both Litecoin and Meowcoin that will be used in the Docker containers.

⚠️ **CRITICAL**: Only **Linux x86_64 ELF binaries** work with Docker containers! Do NOT use Windows .exe or macOS binaries.

## Directory Structure:

```
binaries/
├── litecoin/
│   ├── litecoind      # Litecoin daemon
│   ├── litecoin-cli   # Litecoin CLI
│   └── README.md
├── meowcoin/
│   ├── meowcoind      # Meowcoin daemon
│   ├── meowcoin-cli   # Meowcoin CLI
│   └── README.md
└── README.md          # This file
```

## Setup Instructions:

1. **Copy Litecoin binaries** (Linux x86_64 ELF format) into `litecoin/` directory:

   - `litecoind`
   - `litecoin-cli`

2. **Copy Meowcoin binaries** (Linux x86_64 ELF format) into `meowcoin/` directory:

   - `meowcoind`
   - `meowcoin-cli`

3. **Build the Docker images**:

   ```bash
   docker compose build litecoin meowcoin
   ```

4. **Start the services**:
   ```bash
   docker compose up -d
   ```

## Binary Requirements:

**Platform**: Linux x86_64 ELF executables ONLY

### Litecoin:

- **Format**: Linux x86_64 ELF executable
- **Compatibility**: Ubuntu 24.04 Linux (glibc 2.39+)
- **Dependencies**: Statically linked or with required dependencies included
- **Permissions**: Executable permissions (set automatically by Docker)

### Meowcoin:

- **Format**: Linux x86_64 ELF executable
- **Compatibility**: Ubuntu 24.04 Linux (glibc 2.39+)
- **Features**: AuxPoW support enabled
- **Permissions**: Executable permissions (set automatically by Docker)

## Troubleshooting:

### Missing binaries:

```bash
# Check if files exist
ls -la binaries/litecoin/
ls -la binaries/meowcoin/

# Build specific service
docker compose build litecoin
docker compose build meowcoin
```

### Permission issues:

The Dockerfile automatically sets execute permissions, but if you're having issues:

```bash
chmod +x binaries/litecoin/*
chmod +x binaries/meowcoin/*
```

### Architecture mismatch:

Ensure your binaries are compiled for Linux x86_64:

```bash
file binaries/litecoin/litecoind
file binaries/meowcoin/meowcoind
```

**Expected output:**

```
binaries/litecoin/litecoind: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0
binaries/meowcoin/meowcoind: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 3.2.0
```

❌ **Wrong formats (will cause container failures):**

- Windows: `PE32+ executable (console) x86-64, for MS Windows`
- macOS: `Mach-O 64-bit executable x86_64`
