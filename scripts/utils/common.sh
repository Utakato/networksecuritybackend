#!/bin/bash
# Common utility functions

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions with timestamps
log_info() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1" >&2
}

log_debug() {
    if [ "${DEBUG:-0}" = "1" ]; then
        echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [DEBUG]${NC} $1"
    fi
}

# Check if required commands exist
check_dependencies() {
    local deps=("$@")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing[*]}"
        return 1
    fi
    
    log_info "All required dependencies found: ${deps[*]}"
    return 0
}

# Wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local check_command="$2"
    local max_attempts="${3:-30}"
    local attempt=1
    
    log_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" &> /dev/null; then
            log_info "$service_name is ready"
            return 0
        fi
        log_debug "Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "$service_name failed to start within $(($max_attempts * 2)) seconds"
    return 1
}

# Check if a process is running by PID file
is_process_running() {
    local pid_file="$1"
    
    if [ ! -f "$pid_file" ]; then
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        # Clean up stale PID file
        rm -f "$pid_file"
        return 1
    fi
}

# Create lock file with process ID
create_lock() {
    local lock_file="$1"
    local service_name="$2"
    
    if [ -f "$lock_file" ]; then
        local existing_pid=$(cat "$lock_file" 2>/dev/null)
        if kill -0 "$existing_pid" 2>/dev/null; then
            log_error "$service_name is already running (PID: $existing_pid)"
            return 1
        else
            log_warn "Removing stale lock file for $service_name"
            rm -f "$lock_file"
        fi
    fi
    
    echo $$ > "$lock_file"
    log_info "Created lock file for $service_name (PID: $$)"
    return 0
}

# Remove lock file
remove_lock() {
    local lock_file="$1"
    rm -f "$lock_file"
}

# Safe file operations
safe_write() {
    local content="$1"
    local target_file="$2"
    local temp_file="${target_file}.tmp"
    
    echo "$content" > "$temp_file" && mv "$temp_file" "$target_file"
}

# Cross-platform timeout function
timeout_cmd() {
    local duration="$1"
    shift
    
    # Detect which timeout command to use
    if command -v timeout &> /dev/null; then
        timeout "$duration" "$@"
    elif command -v gtimeout &> /dev/null; then
        gtimeout "$duration" "$@"
    else
        log_warn "No timeout command available, running without timeout"
        "$@"
    fi
}

# JSON validation
validate_json() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        log_error "JSON file not found: $file"
        return 1
    fi
    
    if python3 -m json.tool "$file" &> /dev/null; then
        log_info "JSON file is valid: $file"
        return 0
    else
        log_error "Invalid JSON file: $file"
        return 1
    fi
} 