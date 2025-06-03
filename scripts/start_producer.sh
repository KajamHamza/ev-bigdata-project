#!/bin/bash

# EV Data Producer Startup Script

set -e

echo "🚗 Starting EV Data Producer"
echo "============================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[PRODUCER]${NC} $1"
}

# Default configuration
BOOTSTRAP_SERVERS="localhost:9092"
TOPIC="ev-telemetry"
VEHICLES=5
INTERVAL=1.0
MODE="continuous"
VERBOSE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --vehicles)
            VEHICLES="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --vehicles NUM     Number of vehicles to simulate (default: 5)"
            echo "  --interval FLOAT   Data production interval in seconds (default: 1.0)"
            echo "  --mode MODE        Production mode: continuous|batch (default: continuous)"
            echo "  --verbose          Enable verbose logging"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Start with default settings"
            echo "  $0 --vehicles 10 --interval 0.5      # 10 vehicles, 0.5s interval"
            echo "  $0 --mode batch --verbose             # Batch mode with verbose output"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Kafka is running
check_kafka() {
    print_header "Checking Kafka connection..."
    
    if ! docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
        print_warning "Kafka is not running or not accessible"
        print_status "Please run './scripts/setup.sh' first to start the infrastructure"
        exit 1
    fi
    
    print_status "Kafka is accessible ✓"
}

# Start the producer
start_producer() {
    print_header "Starting EV Data Producer..."
    print_status "Configuration:"
    echo "  - Vehicles: $VEHICLES"
    echo "  - Interval: ${INTERVAL}s"
    echo "  - Mode: $MODE"
    echo "  - Topic: $TOPIC"
    echo ""
    
    cd kafka-producer
    
    # Build the command
    CMD="python3 kafka_producer.py"
    CMD="$CMD --bootstrap-servers $BOOTSTRAP_SERVERS"
    CMD="$CMD --topic $TOPIC"
    CMD="$CMD --vehicles $VEHICLES"
    CMD="$CMD --interval $INTERVAL"
    CMD="$CMD --mode $MODE"
    
    if [ -n "$VERBOSE" ]; then
        CMD="$CMD $VERBOSE"
    fi
    
    print_status "Starting producer with command: $CMD"
    echo ""
    
    # Execute the command
    exec $CMD
}

# Signal handler for graceful shutdown
cleanup() {
    print_header "Shutting down producer..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_kafka
    start_producer
}

# Run main function
main "$@" 