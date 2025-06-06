#!/bin/bash
# Fetch validator metadata from Solana network

# Source environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/setup_env.sh"

# Configuration
OUTPUT_FILE="$PROJECT_ROOT/metadata_service/validator_info.json"
TEMP_FILE="${OUTPUT_FILE}.tmp"
TIMEOUT_DURATION=300  # 5 minutes

# Function to fetch metadata
fetch_metadata() {
    log_info "Fetching validator metadata from Solana network..."
    
    # Check if solana command is available
    if ! command -v solana &> /dev/null; then
        log_error "Solana CLI not found in PATH"
        log_error "Current PATH: $PATH"
        return 1
    fi
    
    # Test solana configuration
    log_info "Testing Solana configuration..."
    if ! timeout_cmd 30 solana config get &> /dev/null; then
        log_error "Solana configuration test failed"
        log_info "Attempting to show solana version..."
        solana --version || log_warn "Could not get Solana version"
        return 1
    fi
    
    # Note: No backup created - fail fast if fetch operation fails
    
    # Fetch validator info with timeout
    log_info "Executing: solana validator-info get --output json"
    if timeout_cmd "$TIMEOUT_DURATION" solana validator-info get --output json > "$TEMP_FILE" 2>&1; then
        # Validate the JSON output
        if validate_json "$TEMP_FILE"; then
            # Check if file has reasonable content (not empty or just null)
            local content_size=$(wc -c < "$TEMP_FILE")
            if [ "$content_size" -gt 10 ]; then
                mv "$TEMP_FILE" "$OUTPUT_FILE"
                log_info "Successfully fetched validator metadata ($content_size bytes)"
                log_info "Output saved to: $OUTPUT_FILE"
                return 0
            else
                log_error "Fetched metadata is too small ($content_size bytes), likely empty or invalid"
                cat "$TEMP_FILE" | head -5
                return 1
            fi
        else
            log_error "Fetched data is not valid JSON"
            log_info "First few lines of output:"
            head -5 "$TEMP_FILE" 2>/dev/null || true
            return 1
        fi
    else
        local exit_code=$?
        log_error "Failed to fetch validator metadata (exit code: $exit_code)"
        
        if [ $exit_code -eq 124 ]; then
            log_error "Command timed out after $TIMEOUT_DURATION seconds"
        fi
        
        # Show error output if available
        if [ -f "$TEMP_FILE" ] && [ -s "$TEMP_FILE" ]; then
            log_info "Error output:"
            head -10 "$TEMP_FILE" 2>/dev/null || true
        fi
        
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
log_info "Starting metadata fetch process..."
log_info "Output file: $OUTPUT_FILE"
log_info "Timeout: ${TIMEOUT_DURATION}s"

if fetch_metadata; then
    log_info "Metadata fetch completed successfully"
    
    # Show file info
    if [ -f "$OUTPUT_FILE" ]; then
        file_size=$(wc -c < "$OUTPUT_FILE")
        line_count=$(wc -l < "$OUTPUT_FILE")
        log_info "Final output: $file_size bytes, $line_count lines"
    fi
    
    exit 0
else
    log_error "Metadata fetch failed - no backup restoration, service will use existing data or fail"
    exit 1
fi 