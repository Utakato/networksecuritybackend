#!/bin/bash
# Metadata service entry point

# Source environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/setup_env.sh"

# Configuration
SERVICE_NAME="metadata"
LOCK_FILE="/tmp/locks/${SERVICE_NAME}_service.lock"
SERVICE_TIMEOUT=600  # 10 minutes

# Set up signal handlers for cleanup
setup_signal_handlers "$LOCK_FILE"

# Function to run metadata service
run_metadata_service() {
    log_info "Starting Metadata Service..."
    log_info "============================="
    
    # Create lock to prevent concurrent runs
    if ! create_lock "$LOCK_FILE" "$SERVICE_NAME"; then
        return 1
    fi
    
    # Fetch metadata first
    log_info "Step 1: Fetching metadata..."
    if ! timeout 300 "$SCRIPT_DIR/../data/fetch_metadata.sh"; then
        log_error "Failed to fetch metadata"
        return 1
    fi
    
    # Run the Python service
    log_info "Step 2: Running metadata service..."
    if [ ! -f "$PROJECT_ROOT/metadata_service/main.py" ]; then
        log_error "Metadata service main.py not found at: $PROJECT_ROOT/metadata_service/main.py"
        return 1
    fi
    
    log_info "Executing: python3 $PROJECT_ROOT/metadata_service/main.py"
    if timeout "$SERVICE_TIMEOUT" python3 "$PROJECT_ROOT/metadata_service/main.py"; then
        log_info "Metadata service completed successfully"
        return 0
    else
        local exit_code=$?
        log_error "Metadata service failed (exit code: $exit_code)"
        
        if [ $exit_code -eq 124 ]; then
            log_error "Service timed out after $SERVICE_TIMEOUT seconds"
        fi
        
        return 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up metadata service..."
    remove_lock "$LOCK_FILE"
}

# Set up cleanup on exit
trap cleanup EXIT

# Main execution
log_info "Metadata service starting at $(date)"
log_info "Lock file: $LOCK_FILE"
log_info "Service timeout: ${SERVICE_TIMEOUT}s"

if run_metadata_service; then
    log_info "Metadata service completed successfully at $(date)"
    exit 0
else
    log_error "Metadata service failed at $(date)"
    exit 1
fi 