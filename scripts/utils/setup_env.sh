#!/bin/bash
# Cron-compatible environment setup

# Set strict error handling
set -euo pipefail

# Determine project root from script location (works regardless of cwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common utilities
source "$SCRIPT_DIR/common.sh"

# Set up comprehensive PATH for cron compatibility
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin"

# Add Solana CLI to PATH
if [ -d "/root/.local/share/solana/install/active_release/bin" ]; then
    export PATH="/root/.local/share/solana/install/active_release/bin:$PATH"
fi

# Add local Python paths
export PATH="/usr/bin/python3:$PATH"
export PATH="/usr/local/bin/python3:$PATH"

# Python environment
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1  # Important for cron logging

# Set working directory to project root
cd "$PROJECT_ROOT"

# Create necessary directories
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "/tmp/locks"

# Set up logging for the current script
CALLER_SCRIPT="${BASH_SOURCE[1]}"
if [ -n "$CALLER_SCRIPT" ]; then
    SCRIPT_NAME="$(basename "$CALLER_SCRIPT" .sh)"
else
    SCRIPT_NAME="unknown"
fi

export LOG_FILE="$PROJECT_ROOT/logs/${SCRIPT_NAME}_$(date +%Y%m%d_%H%M%S).log"

# Initialize logging only if not already set up
if [ -z "${LOGGING_INITIALIZED:-}" ]; then
    # Redirect all output to log file and console
    exec > >(tee -a "$LOG_FILE")
    exec 2>&1
    export LOGGING_INITIALIZED=1
fi

# Environment validation
validate_environment() {
    log_info "Validating environment..."
    
    # Check critical dependencies
    local required_deps=("python3")
    if ! check_dependencies "${required_deps[@]}"; then
        log_error "Critical dependencies missing"
        return 1
    fi
    
    # Check optional dependencies and warn if missing
    local optional_deps=("solana")
    for dep in "${optional_deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_warn "Optional dependency '$dep' not found"
        fi
    done
    
    # Validate project structure
    local required_dirs=("metadata_service" "gossip_service" "validators_service" "ports_service")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$PROJECT_ROOT/$dir" ]; then
            log_warn "Service directory not found: $dir"
        fi
    done
    
    log_info "Environment validation completed"
    return 0
}

# Set up signal handlers for cleanup
setup_signal_handlers() {
    local lock_file="${1:-}"
    
    cleanup() {
        log_info "Received signal, cleaning up..."
        if [ -n "$lock_file" ] && [ -f "$lock_file" ]; then
            remove_lock "$lock_file"
        fi
        exit 130
    }
    
    trap cleanup SIGINT SIGTERM
}

# Export functions for use in other scripts
export -f log_info log_warn log_error log_debug
export -f check_dependencies validate_json safe_write
export -f create_lock remove_lock is_process_running

# Run environment validation
validate_environment

log_info "Environment setup completed successfully"
log_info "Project root: $PROJECT_ROOT"
log_info "Log file: $LOG_FILE"
log_info "Working directory: $(pwd)" 