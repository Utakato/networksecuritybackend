#!/bin/bash
# Interactive start script for development and manual execution

# Source environment setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils/setup_env.sh"

# Function to show usage
show_usage() {
    echo "Network Security Backend - Interactive Launcher"
    echo "==============================================="
    echo ""
    echo "Usage: $0 [SERVICE] [OPTIONS]"
    echo ""
    echo "Services:"
    echo "  metadata      - Run metadata service"
    echo "  gossip        - Run gossip service" 
    echo "  validators    - Run validators service"
    echo "  ports         - Run ports scanning service"
    echo "  vulnerability - Run vulnerability scanning service"
    echo "  all           - Run all services (parallel execution)"
    echo ""
    echo "Options:"
    echo "  --sequential - Run 'all' services sequentially instead of parallel"
    echo "  --help, -h   - Show this help message"
    echo "  --status     - Show status of running services"
    echo "  --stop       - Stop running services"
    echo ""
    echo "Examples:"
    echo "  $0                           # Interactive menu"
    echo "  $0 metadata                  # Run metadata service"
    echo "  $0 vulnerability             # Run vulnerability scanning service"
    echo "  $0 all                       # Run all services in parallel"
    echo "  $0 all --sequential          # Run all services sequentially"
    echo "  $0 --status                  # Show service status"
}

# Function to check service status
check_service_status() {
    local services=("metadata" "gossip" "validators" "ports" "vulnerability")
    
    echo "Service Status:"
    echo "==============="
    
    for service in "${services[@]}"; do
        local lock_file="/tmp/locks/${service}_service.lock"
        if is_process_running "$lock_file"; then
            local pid=$(cat "$lock_file")
            echo "  $service: RUNNING (PID: $pid)"
        else
            echo "  $service: STOPPED"
        fi
    done
}

# Function to stop services
stop_services() {
    local services=("metadata" "gossip" "validators" "ports" "vulnerability")
    local stopped_count=0
    
    echo "Stopping services..."
    
    for service in "${services[@]}"; do
        local lock_file="/tmp/locks/${service}_service.lock"
        if is_process_running "$lock_file"; then
            local pid=$(cat "$lock_file")
            log_info "Stopping $service service (PID: $pid)"
            if kill "$pid" 2>/dev/null; then
                sleep 2
                if ! kill -0 "$pid" 2>/dev/null; then
                    log_info "$service service stopped successfully"
                    rm -f "$lock_file"
                    ((stopped_count++))
                else
                    log_warn "Forcefully killing $service service"
                    kill -9 "$pid" 2>/dev/null || true
                    rm -f "$lock_file"
                    ((stopped_count++))
                fi
            else
                log_warn "Could not stop $service service"
                rm -f "$lock_file"  # Clean up stale lock
            fi
        else
            log_info "$service service is not running"
        fi
    done
    
    log_info "Stopped $stopped_count services"
}

# Interactive menu
show_interactive_menu() {
    echo ""
    echo "Network Security Backend - Service Launcher"
    echo "==========================================="
    echo ""
    echo "Please select a service to run:"
    echo ""
    echo "1) Metadata Service"
    echo "2) Gossip Service"
    echo "3) Validators Service"
    echo "4) Ports Scanning Service"
    echo "5) Vulnerability Scanning Service"
    echo "6) All Services (Parallel)"
    echo "7) All Services (Sequential)"
    echo "8) Show Service Status"
    echo "9) Stop All Services"
    echo "10) Exit"
    echo ""
    read -p "Enter your choice (1-10): " choice
    
    case $choice in
        1) run_service_interactive "metadata" ;;
        2) run_service_interactive "gossip" ;;
        3) run_service_interactive "validators" ;;
        4) run_service_interactive "ports" ;;
        5) run_service_interactive "vulnerability" ;;
        6) run_all_services_parallel ;;
        7) run_all_services_sequential ;;
        8) check_service_status ;;
        9) stop_services ;;
        10) echo "Goodbye!"; exit 0 ;;
        *) echo "Invalid choice. Please try again."; show_interactive_menu ;;
    esac
}

# Function to run service interactively
run_service_interactive() {
    local service_name="$1"
    
    echo ""
    log_info "Starting $service_name service..."
    
    if bash "$SCRIPT_DIR/services/${service_name}.sh"; then
        echo ""
        log_info "$service_name service completed successfully!"
    else
        echo ""
        log_error "$service_name service failed!"
    fi
    
    echo ""
    read -p "Press Enter to continue..."
    show_interactive_menu
}

# Function to run all services in parallel
run_all_services_parallel() {
    local services=("metadata" "gossip" "validators" "ports" "vulnerability")
    local pids=()
    
    echo ""
    log_info "Starting all services in parallel..."
    
    for service in "${services[@]}"; do
        bash "$SCRIPT_DIR/services/${service}.sh" &
        pids+=($!)
        log_info "Started $service service (PID: ${pids[-1]})"
    done
    
    echo ""
    log_info "Waiting for all services to complete..."
    
    # Wait for all services to complete
    local failed=0
    for i in "${!services[@]}"; do
        local service="${services[$i]}"
        local pid="${pids[$i]}"
        
        if wait "$pid"; then
            log_info "$service service completed successfully"
        else
            log_error "$service service failed"
            ((failed++))
        fi
    done
    
    echo ""
    if [ $failed -eq 0 ]; then
        log_info "All services completed successfully!"
    else
        log_error "$failed services failed"
    fi
    
    read -p "Press Enter to continue..."
    show_interactive_menu
}

# Function to run all services sequentially
run_all_services_sequential() {
    echo ""
    bash "$SCRIPT_DIR/cron_runner.sh" all
    echo ""
    read -p "Press Enter to continue..."
    show_interactive_menu
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_usage
        exit 0
        ;;
    --status)
        check_service_status
        exit 0
        ;;
    --stop)
        stop_services
        exit 0
        ;;
    metadata|gossip|validators|ports|vulnerability)
        bash "$SCRIPT_DIR/services/$1.sh"
        exit $?
        ;;
    all)
        if [ "${2:-}" = "--sequential" ]; then
            bash "$SCRIPT_DIR/cron_runner.sh" all
            exit $?
        else
            # Run in parallel
            services=("metadata" "gossip" "validators" "ports" "vulnerability")
            pids=()
            
            for service in "${services[@]}"; do
                bash "$SCRIPT_DIR/services/${service}.sh" &
                pids+=($!)
            done
            
            # Wait for all and collect exit codes
            failed=0
            for pid in "${pids[@]}"; do
                if ! wait "$pid"; then
                    ((failed++))
                fi
            done
            
            exit $failed
        fi
        ;;
    "")
        # No arguments - show interactive menu
        show_interactive_menu
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac 