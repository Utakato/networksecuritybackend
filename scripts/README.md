# Validators Data Processing Scripts

This directory contains scripts for processing Solana validators data from JSON format into pandas DataFrames and saving to PostgreSQL database.

## Scripts Overview

### 1. `parse_validators_data.py`

Parses validators JSON data into a structured pandas DataFrame with additional computed fields.

**Features:**

- Loads and validates JSON data
- Converts data types appropriately
- Adds derived columns (stake in SOL, performance scores, etc.)
- Provides comprehensive data summary
- Handles missing/null values gracefully

**Usage:**

```python
from scripts.parse_validators_data import load_validators_json, parse_validators_to_dataframe

# Load and parse data
validators_data = load_validators_json('data/validators_data.json')
df = parse_validators_to_dataframe(validators_data)
```

**Run standalone:**

```bash
cd scripts
python parse_validators_data.py
```

### 2. `save_validators_to_db.py`

Saves validators DataFrame to PostgreSQL database with proper schema and indexing.

**Features:**

- Creates database tables automatically
- Handles large datasets with batch processing
- Includes conflict resolution (upsert functionality)
- Saves both validator details and network summary
- Timestamps all data for historical tracking

**Database Tables Created:**

- `validators_data`: Individual validator information
- `network_summary`: Network-wide statistics

**Usage:**

```python
from scripts.save_validators_to_db import main as save_to_db

# Save data to database
save_to_db('data/validators_data.json')
```

**Run standalone:**

```bash
cd scripts
python save_validators_to_db.py [optional_file_path]
```

### 3. `example_usage.py`

Demonstrates complete workflow from JSON parsing to database storage with analysis examples.

**Run:**

```bash
cd scripts
python example_usage.py
```

## Data Schema

### Validators Data Table

```sql
CREATE TABLE validators_data (
    id SERIAL PRIMARY KEY,
    identity_pubkey VARCHAR(100) NOT NULL,
    vote_account_pubkey VARCHAR(100) NOT NULL,
    commission INTEGER NOT NULL,
    last_vote BIGINT,
    root_slot BIGINT,
    credits BIGINT,
    epoch_credits INTEGER,
    activated_stake BIGINT NOT NULL,
    stake_in_sol DECIMAL(20, 9),
    version VARCHAR(20),
    delinquent BOOLEAN NOT NULL DEFAULT FALSE,
    skip_rate DECIMAL(10, 6),
    is_high_commission BOOLEAN DEFAULT FALSE,
    performance_score DECIMAL(10, 6),
    collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(identity_pubkey, collected_at)
);
```

### Network Summary Table

```sql
CREATE TABLE network_summary (
    id SERIAL PRIMARY KEY,
    total_active_stake BIGINT NOT NULL,
    total_current_stake BIGINT NOT NULL,
    total_delinquent_stake BIGINT NOT NULL,
    total_active_stake_sol DECIMAL(20, 9),
    total_validators INTEGER,
    active_validators INTEGER,
    delinquent_validators INTEGER,
    collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## DataFrame Columns

The parsed DataFrame includes these columns:

**Original Fields:**

- `identityPubkey`: Validator identity public key
- `voteAccountPubkey`: Vote account public key
- `commission`: Commission rate (0-100%)
- `lastVote`: Last vote slot number
- `rootSlot`: Root slot number
- `credits`: Total credits earned
- `epochCredits`: Credits earned in current epoch
- `activatedStake`: Stake amount in lamports
- `version`: Validator software version
- `delinquent`: Whether validator is delinquent
- `skipRate`: Skip rate percentage

**Derived Fields:**

- `stake_in_sol`: Stake amount converted to SOL
- `is_high_commission`: Boolean flag for commission >= 10%
- `performance_score`: Normalized performance score (0-1)

## Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

Required packages:

- `pandas>=2.1.1`
- `numpy>=1.26.0`
- `psycopg2-binary>=2.9.9`
- `python-dotenv>=1.0.0`

## Database Configuration

Set up your PostgreSQL connection using environment variables or `.env` file:

```env
POSTGRES_DB=validator_security
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Example Queries

After saving data to the database, you can run analysis queries:

```sql
-- Top 10 validators by stake
SELECT identity_pubkey, stake_in_sol, commission, delinquent
FROM validators_data
WHERE collected_at = (SELECT MAX(collected_at) FROM validators_data)
ORDER BY stake_in_sol DESC
LIMIT 10;

-- Commission distribution
SELECT commission, COUNT(*) as validator_count
FROM validators_data
WHERE collected_at = (SELECT MAX(collected_at) FROM validators_data)
GROUP BY commission
ORDER BY commission;

-- Network health over time
SELECT collected_at, active_validators, delinquent_validators,
       total_active_stake_sol
FROM network_summary
ORDER BY collected_at DESC;
```

## Error Handling

The scripts include comprehensive error handling for:

- Missing or corrupted JSON files
- Database connection issues
- Data validation errors
- Memory management for large datasets

## Performance Notes

- Batch processing is used for database inserts (default: 1000 records per batch)
- Upsert functionality prevents duplicate data
- Proper indexing on key fields for query performance
- Memory-efficient DataFrame operations
