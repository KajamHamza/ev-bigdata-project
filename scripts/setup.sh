#!/bin/bash

# EV Big Data Project Setup Script
# This script sets up the complete infrastructure for the EV telemetry project

set -e

echo "🚗 EV Big Data Project Setup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker and Docker Compose are installed
check_prerequisites() {
    print_header "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed ✓"
}

# Start the infrastructure
start_infrastructure() {
    print_header "Starting infrastructure with Docker Compose..."
    
    cd docker-compose
    
    # Pull images first
    print_status "Pulling Docker images..."
    docker-compose pull
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    cd ..
    
    print_status "Infrastructure started ✓"
}

# Wait for services to be ready
wait_for_services() {
    print_header "Waiting for services to be ready..."
    
    # Wait for Kafka
    print_status "Waiting for Kafka..."
    timeout=60
    while ! docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            print_error "Kafka failed to start within 60 seconds"
            exit 1
        fi
    done
    print_status "Kafka is ready ✓"
    
    # Wait for Elasticsearch
    print_status "Waiting for Elasticsearch..."
    timeout=60
    while ! curl -s http://localhost:9200/_cluster/health &> /dev/null; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            print_error "Elasticsearch failed to start within 60 seconds"
            exit 1
        fi
    done
    print_status "Elasticsearch is ready ✓"
    
    # Wait for Kibana
    print_status "Waiting for Kibana..."
    timeout=120
    while ! curl -s http://localhost:5601/api/status &> /dev/null; do
        sleep 3
        timeout=$((timeout - 3))
        if [ $timeout -le 0 ]; then
            print_error "Kibana failed to start within 120 seconds"
            exit 1
        fi
    done
    print_status "Kibana is ready ✓"
    
    # Wait for Kafka Connect
    print_status "Waiting for Kafka Connect..."
    timeout=90
    while ! curl -s http://localhost:8083/connectors &> /dev/null; do
        sleep 3
        timeout=$((timeout - 3))
        if [ $timeout -le 0 ]; then
            print_error "Kafka Connect failed to start within 90 seconds"
            exit 1
        fi
    done
    print_status "Kafka Connect is ready ✓"
}

# Create Kafka topics
create_kafka_topics() {
    print_header "Creating Kafka topics..."
    
    # Create ev-telemetry topic
    docker exec kafka kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic ev-telemetry \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists
    
    # Create ev-processed topic
    docker exec kafka kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic ev-processed \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists
    
    print_status "Kafka topics created ✓"
}

# Setup Elasticsearch index
setup_elasticsearch() {
    print_header "Setting up Elasticsearch index..."
    
    # Create index with mapping
    curl -X PUT "localhost:9200/ev-processed" \
        -H "Content-Type: application/json" \
        -d @elasticsearch-config/ev_index_mapping.json
    
    print_status "Elasticsearch index created ✓"
}

# Setup Kafka Connect
setup_kafka_connect() {
    print_header "Setting up Kafka Connect..."
    
    # Wait a bit more for Kafka Connect to be fully ready
    sleep 10
    
    # Create Elasticsearch sink connector
    curl -X POST "localhost:8083/connectors" \
        -H "Content-Type: application/json" \
        -d @elasticsearch-config/kafka-connect-elasticsearch.json
    
    print_status "Kafka Connect configured ✓"
}

# Install Python dependencies
install_python_deps() {
    print_header "Installing Python dependencies..."
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    # Install dependencies for producer
    cd kafka-producer
    pip3 install -r requirements.txt
    cd ..
    
    # Install dependencies for streams processor
    cd kafka-streams
    pip3 install -r requirements.txt 2>/dev/null || pip3 install kafka-python statistics
    cd ..
    
    print_status "Python dependencies installed ✓"
}

# Import Kibana dashboards
import_kibana_dashboards() {
    print_header "Importing Kibana dashboards..."
    
    # Wait for Kibana to be fully ready
    sleep 15
    
    # Import dashboard configuration
    curl -X POST "localhost:5601/api/saved_objects/_import" \
        -H "kbn-xsrf: true" \
        -H "Content-Type: application/json" \
        -d @kibana-dashboards/ev-dashboard-config.json \
        2>/dev/null || print_warning "Dashboard import may need manual setup"
    
    print_status "Kibana dashboards imported ✓"
}

# Display service URLs
display_urls() {
    print_header "Service URLs:"
    echo ""
    echo "🌐 Kibana Dashboard:     http://localhost:5601"
    echo "🔍 Elasticsearch:        http://localhost:9200"
    echo "📊 Kafka UI:             http://localhost:8080"
    echo "🔗 Kafka Connect:        http://localhost:8083"
    echo ""
    print_status "All services are ready!"
}

# Main setup function
main() {
    echo "Starting EV Big Data Project setup..."
    echo ""
    
    check_prerequisites
    start_infrastructure
    wait_for_services
    create_kafka_topics
    setup_elasticsearch
    setup_kafka_connect
    install_python_deps
    import_kibana_dashboards
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    display_urls
    
    echo ""
    print_status "Next steps:"
    echo "1. Start the data producer: ./scripts/start_producer.sh"
    echo "2. Start the data processor: ./scripts/start_processor.sh"
    echo "3. Open Kibana dashboard: http://localhost:5601"
    echo ""
    print_warning "Note: It may take a few minutes for data to appear in Kibana"
}

# Run main function
main "$@" 