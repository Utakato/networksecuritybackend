#!/bin/bash
# Fetch gossip data from Solana network

# Source environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/setup_env.sh"

# Configuration
OUTPUT_FILE="$PROJECT_ROOT/gossip_service/gossip_data.json"
TEMP_FILE="${OUTPUT_FILE}.tmp"
TIMEOUT_DURATION=300  # 5 minutes

# Function to fetch gossip data
fetch_gossip() {
    log_info "Fetching gossip data from Solana network..."
    
    # Check if solana command is available
    if ! command -v solana &> /dev/null; then
        log_error "Solana CLI not found in PATH"
        return 1
    fi
    
    # Test solana configuration
    if ! timeout_cmd 30 solana config get &> /dev/null; then
        log_error "Solana configuration test failed"
        return 1
    fi
    
    # Note: No backup created - fail fast if fetch operation fails
    
    # Ensure output directory exists
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    
    # Fetch gossip data with timeout
    log_info "Executing: solana gossip --output json"
    if timeout_cmd "$TIMEOUT_DURATION" solana gossip --output json > "$TEMP_FILE" 2>&1; then
        # Validate the JSON output
        if validate_json "$TEMP_FILE"; then
            local content_size=$(wc -c < "$TEMP_FILE")
            if [ "$content_size" -gt 10 ]; then
                mv "$TEMP_FILE" "$OUTPUT_FILE"
                log_info "Successfully fetched gossip data ($content_size bytes)"
                return 0
            else
                log_error "Fetched gossip data is too small ($content_size bytes)"
                return 1
            fi
        else
            log_error "Fetched gossip data is not valid JSON"
            return 1
        fi
    else
        local exit_code=$?
        log_error "Failed to fetch gossip data (exit code: $exit_code)"
        return 1
    fi
}

# Cleanup function
cleanup() {
    rm -f "$TEMP_FILE"
}

# Set up cleanup on exit
trap cleanup EXIT

# Main execution
log_info "Starting gossip data fetch process..."

if fetch_gossip; then
    log_info "Gossip data fetch completed successfully"
    exit 0
else
    log_error "Gossip data fetch failed - no backup restoration, service will use existing data or fail"
    exit 1
fi 