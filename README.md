# Network Security Backend

A comprehensive network security monitoring and analysis backend system for Solana validators.

## Overview

This system provides automated collection and analysis of:

- Validator metadata
- Gossip network data
- Validator performance data
- Port scanning and security analysis

## Project Structure

```
.
├── scripts/                    # Organized entry scripts
│   ├── start.sh               # Interactive launcher for development
│   ├── cron_runner.sh         # Main entry point for cron jobs
│   ├── services/              # Individual service entry points
│   │   ├── metadata.sh        # Metadata collection service
│   │   ├── gossip.sh          # Gossip data collection service
│   │   ├── validators.sh      # Validator data collection service
│   │   └── ports.sh           # Port scanning service
│   ├── data/                  # Data fetching scripts
│   │   ├── fetch_metadata.sh  # Fetch validator metadata
│   │   ├── fetch_gossip.sh    # Fetch gossip data
│   │   └── fetch_validators.sh # Fetch validator data
│   └── utils/                 # Shared utilities
│       ├── common.sh          # Common functions and utilities
│       └── setup_env.sh       # Environment setup and configuration
├── metadata_service/          # Metadata processing service
├── gossip_service/           # Gossip data processing service
├── validators_service/       # Validator data processing service
├── ports_service/           # Port scanning service
├── logs/                    # Log files (auto-created)
└── data/                    # Data files
```

## Quick Start

### Interactive Mode (Development)

For development and manual testing:

```bash
# Run interactive menu
./scripts/start.sh

# Or run specific services
./scripts/start.sh metadata
./scripts/start.sh gossip
./scripts/start.sh validators
./scripts/start.sh ports

# Run all services in parallel
./scripts/start.sh all

# Run all services sequentially
./scripts/start.sh all --sequential

# Check service status
./scripts/start.sh --status

# Stop running services
./scripts/start.sh --stop
```

### Production Mode (Cron)

For production deployment with cron:

```bash
# Run individual services
./scripts/cron_runner.sh metadata
./scripts/cron_runner.sh gossip
./scripts/cron_runner.sh validators
./scripts/cron_runner.sh ports

# Run all services
./scripts/cron_runner.sh all
```

## Cron Setup

### Example Crontab Configuration

```bash
# Edit crontab
crontab -e

# Add these entries (adjust paths to your installation):

# Run metadata service every 30 minutes
*/30 * * * * /path/to/networksecuritybackend/scripts/cron_runner.sh metadata

# Run gossip service every hour
0 * * * * /path/to/networksecuritybackend/scripts/cron_runner.sh gossip

# Run validators service every 2 hours
0 */2 * * * /path/to/networksecuritybackend/scripts/cron_runner.sh validators

# Run ports scan daily at 2 AM
0 2 * * * /path/to/networksecuritybackend/scripts/cron_runner.sh ports
```

### Environment Variables for Cron

You can customize behavior using environment variables:

```bash
# Number of threads for port scanning
THREADS=50 /path/to/networksecuritybackend/scripts/cron_runner.sh ports

# Enable debug logging
DEBUG=1 /path/to/networksecuritybackend/scripts/cron_runner.sh metadata
```

## Features

### Robust Error Handling

- Timeout protection for all operations
- Lock files prevent concurrent execution
- Comprehensive logging with timestamps
- Automatic backup and recovery of data files

### Cron-Compatible Design

- Works in minimal cron environments
- Absolute path resolution
- Comprehensive PATH setup
- No dependency on interactive shell features

### Monitoring and Logging

- All output logged to timestamped files in `logs/`
- Service status checking
- Process management and cleanup
- Detailed error reporting

### Data Validation

- JSON validation for all fetched data
- File size validation
- Backup creation before data updates
- Graceful fallback to previous data on failures

## Configuration

### Prerequisites

1. **Solana CLI**: Must be installed and configured

   ```bash
   # Check installation
   solana --version
   solana config get
   ```

2. **Python 3**: Required for processing services

   ```bash
   # Check installation
   python3 --version
   ```

3. **Dependencies**: Install Python requirements
   ```bash
   pip install -r requirements.txt
   ```

### Directory Permissions

Ensure the script directories have proper permissions:

```bash
chmod +x scripts/start.sh scripts/cron_runner.sh
chmod +x scripts/services/*.sh
chmod +x scripts/data/*.sh
chmod +x scripts/utils/*.sh
```

### Lock Directory

The system uses lock files in `/tmp/locks/`. This directory is created automatically.

## Service Details

### Metadata Service

- Fetches validator metadata using `solana validator-info get`
- Processes and stores metadata in the database
- Timeout: 10 minutes

### Gossip Service

- Fetches gossip network data using `solana gossip`
- Processes network topology information
- Timeout: 10 minutes

### Validators Service

- Fetches validator performance data using `solana validators`
- Analyzes validator performance metrics
- Timeout: 10 minutes

### Ports Service

- Performs port scanning on discovered validators
- Configurable thread count (default: 100)
- Timeout: 30 minutes

## Logging

All services log to `logs/` directory with timestamped filenames:

```
logs/
├── metadata_20240315_143022.log
├── gossip_20240315_143045.log
├── validators_20240315_143110.log
└── ports_20240315_143200.log
```

Log files include:

- Timestamps for all operations
- Detailed error messages
- Performance metrics
- Service status information

## Troubleshooting

### Common Issues

1. **Solana CLI not found**

   - Ensure Solana CLI is installed and in PATH
   - Check the PATH configuration in `scripts/utils/setup_env.sh`

2. **Python module not found**

   - Ensure you're in the correct virtual environment
   - Install requirements: `pip install -r requirements.txt`

3. **Permission denied**

   - Make scripts executable: `chmod +x scripts/**/*.sh`
   - Check file ownership and permissions

4. **Service already running**
   - Check status: `./scripts/start.sh --status`
   - Stop services: `./scripts/start.sh --stop`
   - Clear stale locks: `rm -f /tmp/locks/*_service.lock`

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
DEBUG=1 ./scripts/start.sh metadata
```

### Testing Cron Environment

Test scripts in cron-like environment:

```bash
env -i HOME=/root PATH=/usr/bin:/bin bash -c './scripts/cron_runner.sh metadata'
```

## Migration from Old Scripts

The new organization replaces these old scripts:

- `run_validator_info_service.sh` → `scripts/services/metadata.sh`
- `fetch_metadata.sh` → `scripts/data/fetch_metadata.sh`
- `fetch_data.sh` → Split into individual data fetching scripts
- `exec_metadata.sh` → `scripts/cron_runner.sh metadata`

Old scripts can be safely removed after testing the new system.

## Support

For issues or questions:

1. Check the logs in `logs/` directory
2. Run with `DEBUG=1` for detailed output
3. Verify all prerequisites are installed
4. Check cron logs: `grep CRON /var/log/syslog`
