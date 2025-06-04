#!/bin/bash
# Main entry point designed for cron usage

# Strict error handling
set -euo pipefail

# Absolute path resolution (critical for cron)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source environment setup
source "$SCRIPT_DIR/utils/setup_env.sh"

# Show usage information
show_usage() {
    echo "Usage: $0 [SERVICE] [OPTIONS]"
    echo ""
    echo "Services:"
    echo "  metadata    - Run metadata collection and processing service"
    echo "  gossip      - Run gossip data collection and processing service"
    echo "  validators  - Run validators data collection and processing service"
    echo "  ports       - Run port scanning service"
    echo "  all         - Run all services sequentially"
    echo ""
    echo "Options:"
    echo "  --help, -h  - Show this help message"
    echo "  --version   - Show version information"
    echo ""
    echo "Environment Variables:"
    echo "  THREADS     - Number of threads for port scanning (default: 100)"
    echo "  DEBUG       - Enable debug logging (set to 1)"
    echo ""
    echo "Examples:"
    echo "  $0 metadata                    # Run metadata service"
    echo "  THREADS=50 $0 ports           # Run port scanning with 50 threads"
    echo "  DEBUG=1 $0 gossip             # Run gossip service with debug logging"
}

# Function to run service with proper error handling
run_service() {
    local service_name="$1"
    local service_script="$SCRIPT_DIR/services/${service_name}.sh"
    
    log_info "Attempting to run $service_name service"
    
    if [ ! -f "$service_script" ]; then
        log_error "Service script not found: $service_script"
        return 1
    fi
    
    if [ ! -x "$service_script" ]; then
        log_warn "Service script is not executable, making it executable: $service_script"
        chmod +x "$service_script"
    fi
    
    log_info "Starting $service_name service"
    local start_time=$(date +%s)
    
    if bash "$service_script"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_info "$service_name service completed successfully in ${duration}s"
        return 0
    else
        local exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_error "$service_name service failed after ${duration}s (exit code: $exit_code)"
        return $exit_code
    fi
}

# Function to run all services
run_all_services() {
    local services=("metadata" "gossip" "validators" "ports")
    local failed_services=()
    local successful_services=()
    
    log_info "Running all services..."
    
    for service in "${services[@]}"; do
        if run_service "$service"; then
            successful_services+=("$service")
        else
            failed_services+=("$service")
        fi
    done
    
    # Report results
    log_info "=== SERVICE EXECUTION SUMMARY ==="
    if [ ${#successful_services[@]} -gt 0 ]; then
        log_info "Successful services: ${successful_services[*]}"
    fi
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "Failed services: ${failed_services[*]}"
        return 1
    else
        log_info "All services completed successfully"
        return 0
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --version)
            echo "Network Security Backend Cron Runner v1.0"
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            break
            ;;
    esac
    shift
done

# Get the service name (default to metadata if none provided)
SERVICE_NAME="${1:-metadata}"

# Main execution
log_info "Network Security Backend Cron Runner starting at $(date)"
log_info "Service: $SERVICE_NAME"
log_info "Project Root: $PROJECT_ROOT"
log_info "Log File: $LOG_FILE"

case "$SERVICE_NAME" in
    metadata)
        run_service "metadata"
        exit_code=$?
        ;;
    gossip)
        run_service "gossip"
        exit_code=$?
        ;;
    validators)
        run_service "validators"
        exit_code=$?
        ;;
    ports)
        run_service "ports"
        exit_code=$?
        ;;
    all)
        run_all_services
        exit_code=$?
        ;;
    *)
        log_error "Unknown service: $SERVICE_NAME"
        show_usage
        exit 1
        ;;
esac

if [ $exit_code -eq 0 ]; then
    log_info "Cron runner completed successfully at $(date)"
else
    log_error "Cron runner failed at $(date) with exit code: $exit_code"
fi

exit $exit_code 