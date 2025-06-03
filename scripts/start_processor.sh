#!/bin/bash

# EV Data Processor Startup Script

set -e

echo "⚙️ Starting EV Data Processor"
echo "============================="

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
    echo -e "${BLUE}[PROCESSOR]${NC} $1"
}

# Default configuration
BOOTSTRAP_SERVERS="localhost:9092"
INPUT_TOPIC="ev-telemetry"
OUTPUT_TOPIC="ev-processed"
CONSUMER_GROUP="ev-processor-group"
VERBOSE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --input-topic)
            INPUT_TOPIC="$2"
            shift 2
            ;;
        --output-topic)
            OUTPUT_TOPIC="$2"
            shift 2
            ;;
        --consumer-group)
            CONSUMER_GROUP="$2"
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
            echo "  --input-topic TOPIC    Input Kafka topic (default: ev-telemetry)"
            echo "  --output-topic TOPIC   Output Kafka topic (default: ev-processed)"
            echo "  --consumer-group GROUP Consumer group ID (default: ev-processor-group)"
            echo "  --verbose              Enable verbose logging"
            echo "  --help                 Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Start with default settings"
            echo "  $0 --verbose                          # Enable verbose logging"
            echo "  $0 --input-topic custom-topic         # Use custom input topic"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Kafka is running and topics exist
check_kafka() {
    print_header "Checking Kafka connection and topics..."
    
    if ! docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
        print_warning "Kafka is not running or not accessible"
        print_status "Please run './scripts/setup.sh' first to start the infrastructure"
        exit 1
    fi
    
    # Check if input topic exists
    if ! docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list | grep -q "^${INPUT_TOPIC}$"; then
        print_warning "Input topic '${INPUT_TOPIC}' does not exist"
        print_status "Creating topic '${INPUT_TOPIC}'..."
        docker exec kafka kafka-topics --create \
            --bootstrap-server localhost:9092 \
            --topic "${INPUT_TOPIC}" \
            --partitions 3 \
            --replication-factor 1 \
            --if-not-exists
    fi
    
    # Check if output topic exists
    if ! docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list | grep -q "^${OUTPUT_TOPIC}$"; then
        print_warning "Output topic '${OUTPUT_TOPIC}' does not exist"
        print_status "Creating topic '${OUTPUT_TOPIC}'..."
        docker exec kafka kafka-topics --create \
            --bootstrap-server localhost:9092 \
            --topic "${OUTPUT_TOPIC}" \
            --partitions 3 \
            --replication-factor 1 \
            --if-not-exists
    fi
    
    print_status "Kafka is accessible and topics are ready ✓"
}

# Start the processor
start_processor() {
    print_header "Starting EV Data Processor..."
    print_status "Configuration:"
    echo "  - Input Topic: $INPUT_TOPIC"
    echo "  - Output Topic: $OUTPUT_TOPIC"
    echo "  - Consumer Group: $CONSUMER_GROUP"
    echo ""
    
    cd kafka-streams
    
    # Build the command
    CMD="python3 ev_data_processor.py"
    CMD="$CMD --bootstrap-servers $BOOTSTRAP_SERVERS"
    CMD="$CMD --input-topic $INPUT_TOPIC"
    CMD="$CMD --output-topic $OUTPUT_TOPIC"
    CMD="$CMD --consumer-group $CONSUMER_GROUP"
    
    if [ -n "$VERBOSE" ]; then
        CMD="$CMD $VERBOSE"
    fi
    
    print_status "Starting processor with command: $CMD"
    echo ""
    print_status "Processor is now listening for messages on topic '$INPUT_TOPIC'..."
    print_status "Processed data will be sent to topic '$OUTPUT_TOPIC'"
    echo ""
    
    # Execute the command
    exec $CMD
}

# Signal handler for graceful shutdown
cleanup() {
    print_header "Shutting down processor..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_kafka
    start_processor
}

# Run main function
main "$@" 