#!/bin/bash
# Ports scanning service entry point

# Source environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/setup_env.sh"

# Configuration
SERVICE_NAME="ports"
LOCK_FILE="/tmp/locks/${SERVICE_NAME}_service.lock"
SERVICE_TIMEOUT=1800  # 30 minutes (port scanning can take longer)
THREADS="${THREADS:-100}"

# Set up signal handlers for cleanup
setup_signal_handlers "$LOCK_FILE"

# Function to run ports service
run_ports_service() {
    log_info "Starting Ports Scanning Service..."
    log_info "=================================="
    
    # Create lock to prevent concurrent runs
    if ! create_lock "$LOCK_FILE" "$SERVICE_NAME"; then
        return 1
    fi
    
    # Run the Python port scanning service
    log_info "Running port scanning service with $THREADS threads..."
    if [ ! -f "$PROJECT_ROOT/ports_service/main.py" ]; then
        log_error "Ports service main.py not found at: $PROJECT_ROOT/ports_service/main.py"
        return 1
    fi
    
    log_info "Executing: python3 $PROJECT_ROOT/ports_service/main.py --threads=$THREADS"
    if timeout "$SERVICE_TIMEOUT" python3 "$PROJECT_ROOT/ports_service/main.py" --threads="$THREADS"; then
        log_info "Ports service completed successfully"
        return 0
    else
        local exit_code=$?
        log_error "Ports service failed (exit code: $exit_code)"
        
        if [ $exit_code -eq 124 ]; then
            log_error "Service timed out after $SERVICE_TIMEOUT seconds"
        fi
        
        return 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up ports service..."
    remove_lock "$LOCK_FILE"
}

# Set up cleanup on exit
trap cleanup EXIT

# Main execution
log_info "Ports service starting at $(date)"
log_info "Lock file: $LOCK_FILE"
log_info "Service timeout: ${SERVICE_TIMEOUT}s"
log_info "Threads: $THREADS"

if run_ports_service; then
    log_info "Ports service completed successfully at $(date)"
    exit 0
else
    log_error "Ports service failed at $(date)"
    exit 1
fi 