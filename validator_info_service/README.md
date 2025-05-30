# Validator Info Service

This service saves Solana validator information from JSON files into a TimescaleDB hypertable for time-series analysis and querying.

## Overview

The validator info service processes Solana validator metadata including:

- Identity and info public keys
- Validator names and descriptions
- Website URLs and icon URLs
- Keybase usernames
- Detailed validator descriptions

## Database Schema

The service creates a `validator_info` hypertable with the following structure:

```sql
CREATE TABLE validator_info (
    identity_pubkey TEXT NOT NULL,
    info_pubkey TEXT,
    name TEXT,
    details TEXT,
    website TEXT,
    icon_url TEXT,
    keybase_username TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (identity_pubkey, timestamp)
);
```

## Files

- `save_validator_info_to_db.py` - Main service for saving validator info to database
- `query_validator_info.py` - Utility for querying validator information
- `main.py` - Entry point for the service
- `README.md` - This documentation

## Usage

### Running the Service

From the project root directory:

```bash
# Using the provided script
./run_validator_info_service.sh

# Or directly with Python
python3 validator_info_service/main.py

# Or with a specific file
python3 validator_info_service/save_validator_info_to_db.py --file path/to/validator_info.json
```

### Querying Validator Information

```bash
# Get latest 20 validators
python3 validator_info_service/query_validator_info.py

# Search by name
python3 validator_info_service/query_validator_info.py --search "Bitcoin"

# Get specific validator by pubkey
python3 validator_info_service/query_validator_info.py --pubkey "2swwdmPFEPFUJ38nJbJJBA9kKooJzaeUZBJ9o1mYHepc"

# Get all validators with websites
python3 validator_info_service/query_validator_info.py --websites

# Get latest 50 validators
python3 validator_info_service/query_validator_info.py --latest 50
```

## Data Format

The service expects JSON data in the following format:

```json
[
  {
    "identityPubkey": "2swwdmPFEPFUJ38nJbJJBA9kKooJzaeUZBJ9o1mYHepc",
    "infoPubkey": "2vmo2jgyBR2QVvvWVyZ1xeFfknZkfWAc2CeB6yoZsyNU",
    "info": {
      "details": "Cheerful crypto mutant from Tartaria =)",
      "name": "sobolk_n",
      "website": "https://t.me/sobolk_n",
      "iconUrl": "https://example.com/icon.png",
      "keybaseUsername": "sobolk"
    }
  }
]
```

## Features

- **Batch Processing**: Efficiently processes large datasets using batch inserts
- **Time-Series Storage**: Uses TimescaleDB hypertables for optimal time-series performance
- **Conflict Resolution**: Handles duplicate entries with ON CONFLICT updates
- **Statistics**: Provides detailed statistics about the imported data
- **Flexible Querying**: Multiple query options for different use cases
- **Error Handling**: Robust error handling and validation

## Dependencies

- `psycopg2` - PostgreSQL adapter for Python
- `python-dotenv` - Environment variable management
- TimescaleDB extension for PostgreSQL

## Environment Variables

The service uses the following environment variables (with defaults):

- `DB_NAME` - Database name (default: validator_timescale)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password (default: postgres)
- `DB_HOST` - Database host (default: 127.0.0.1)
- `DB_PORT` - Database port (default: 5433)

## Performance Notes

- Uses batch inserts for optimal performance
- Hypertable partitioning provides excellent query performance
- Indexes on `identity_pubkey` and `timestamp` for fast lookups
- DISTINCT ON queries for getting latest validator information

## Integration

This service integrates with the existing network security backend infrastructure and shares the same database connection patterns as other services in the project.
