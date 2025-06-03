# 🚗 EV Big Data Project - Real-time Electric Vehicle Telemetry Analytics

## 📋 Project Overview

This project implements a **real-time Big Data analytics pipeline** for Electric Vehicle (EV) telemetry data using Apache Kafka, Elasticsearch, and Kibana (ELK stack). The system simulates and processes live EV data including location, speed, battery status, energy consumption, and driving patterns.

### 🎯 Project Objectives

Following the Big Data module specifications, this project demonstrates:

1. **Real-time data ingestion** using Apache Kafka
2. **Stream processing** with Kafka Streams for data enrichment
3. **Data storage and indexing** with Elasticsearch
4. **Real-time visualization** using Kibana dashboards
5. **Anomaly detection** and alerting for vehicle diagnostics

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EV Simulator  │───▶│  Kafka Producer │───▶│ Kafka (Topics)  │───▶│ Kafka Streams   │
│                 │    │                 │    │                 │    │   Processor     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │                        │
                                                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Kibana Dashboard│◀───│  Elasticsearch  │◀───│ Kafka Connect   │◀───│  Processed Data │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🔧 Technology Stack

- **Apache Kafka**: Message streaming and data ingestion
- **Kafka Streams**: Real-time data processing and enrichment
- **Elasticsearch**: Data storage, indexing, and search
- **Kibana**: Data visualization and dashboards
- **Docker & Docker Compose**: Containerization and orchestration
- **Python**: Data simulation and processing logic

## 📊 Data Schema

The EV telemetry data includes:

### Raw Data Fields
- **Vehicle Information**: ID, specifications
- **Location**: GPS coordinates (latitude, longitude, altitude)
- **Motion**: Speed, acceleration, heading
- **Battery**: Level, voltage, current, temperature, capacity
- **Energy**: Consumption, regeneration, efficiency
- **Vehicle Status**: Driving pattern, odometer, trip distance
- **Diagnostics**: Alerts, error codes, maintenance status
- **Environmental**: Outside temperature, humidity, air quality

### Enriched Data Fields
- **Statistics**: Running averages, trends, variance
- **Anomalies**: Detected issues with severity levels
- **Derived Metrics**: Efficiency calculations, health scores
- **Data Quality**: Completeness, accuracy flags

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.7+ installed
- At least 4GB RAM available for containers

### 1. Setup Infrastructure

```bash
# Clone the repository and navigate to project directory
cd ev-bigdata-project

# Make scripts executable
chmod +x scripts/*.sh

# Run the complete setup
./scripts/setup.sh
```

This script will:
- Start all Docker containers (Kafka, Elasticsearch, Kibana, etc.)
- Create Kafka topics
- Configure Elasticsearch indices
- Set up Kafka Connect
- Install Python dependencies
- Import Kibana dashboards

### 2. Start Data Processing

Open two terminal windows:

**Terminal 1 - Start the Data Processor:**
```bash
./scripts/start_processor.sh
```

**Terminal 2 - Start the Data Producer:**
```bash
./scripts/start_producer.sh
```

### 3. Access Dashboards

- **Kibana Dashboard**: http://localhost:5601
- **Kafka UI**: http://localhost:8081
- **Elasticsearch**: http://localhost:9200

## 📈 Features

### Real-time Data Simulation
- **5 Virtual EVs** with realistic behavior patterns
- **Dynamic driving patterns**: city driving, highway, parking, charging, idle
- **Realistic battery consumption** based on speed and usage
- **GPS movement simulation** around Paris area
- **Environmental factors** affecting vehicle performance

### Stream Processing
- **Data enrichment** with calculated metrics
- **Anomaly detection** for critical conditions:
  - Low battery warnings
  - Overheating alerts
  - Rapid battery drain detection
  - High speed warnings
- **Statistical analysis** with running averages and trends
- **Data quality assessment** with completeness scores

### Visualization Dashboards
- **Fleet Location Map**: Real-time vehicle positions with battery/speed indicators
- **Speed Timeline**: Historical speed data for all vehicles
- **Battery Monitoring**: Current battery levels and health
- **Energy Consumption**: Usage patterns and efficiency metrics
- **Driving Patterns**: Distribution of vehicle behaviors
- **Anomaly Timeline**: Alert history and severity tracking
- **Fleet Metrics**: Key performance indicators

## 🛠️ Advanced Usage

### Custom Configuration

**Producer Options:**
```bash
./scripts/start_producer.sh --vehicles 10 --interval 0.5 --verbose
```

**Processor Options:**
```bash
./scripts/start_processor.sh --verbose --consumer-group custom-group
```

### Manual Operations

**View Kafka Topics:**
```bash
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

**Monitor Messages:**
```bash
docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic ev-telemetry --from-beginning
```

**Check Elasticsearch Indices:**
```bash
curl http://localhost:9200/_cat/indices
```

## 📁 Project Structure

```
ev-bigdata-project/
├── docker-compose/
│   └── docker-compose.yml          # Infrastructure definition
├── kafka-producer/
│   ├── ev_data_simulator.py        # EV telemetry simulator
│   ├── kafka_producer.py           # Kafka producer implementation
│   └── requirements.txt            # Python dependencies
├── kafka-streams/
│   └── ev_data_processor.py        # Stream processing logic
├── elasticsearch-config/
│   ├── ev_index_mapping.json       # Elasticsearch index mapping
│   └── kafka-connect-elasticsearch.json  # Kafka Connect config
├── kibana-dashboards/
│   └── ev-dashboard-config.json    # Dashboard definitions
├── scripts/
│   ├── setup.sh                    # Complete setup script
│   ├── start_producer.sh           # Producer startup script
│   └── start_processor.sh          # Processor startup script
└── README.md                       # This file
```

## 🔍 Monitoring and Troubleshooting

### Service Health Checks

```bash
# Check all containers
docker-compose -f docker-compose/docker-compose.yml ps

# View logs
docker-compose -f docker-compose/docker-compose.yml logs kafka
docker-compose -f docker-compose/docker-compose.yml logs elasticsearch
docker-compose -f docker-compose/docker-compose.yml logs kibana
```

### Common Issues

1. **Services not starting**: Ensure sufficient memory (4GB+)
2. **Kafka connection errors**: Wait for all services to be fully ready
3. **No data in Kibana**: Check that both producer and processor are running
4. **Dashboard not loading**: Manually import dashboard configuration

## 📚 Educational Value

This project demonstrates key Big Data concepts:

### 1. Data Ingestion (Apache Kafka)
- **Producer patterns** for real-time data streaming
- **Topic partitioning** for scalability
- **Message serialization** and key-based routing

### 2. Stream Processing (Kafka Streams)
- **Real-time data transformation** and enrichment
- **Stateful processing** with windowing
- **Anomaly detection** algorithms

### 3. Data Storage (Elasticsearch)
- **Document-based storage** for semi-structured data
- **Index mapping** optimization for time-series data
- **Search and aggregation** capabilities

### 4. Visualization (Kibana)
- **Real-time dashboards** with auto-refresh
- **Geospatial visualization** for location data
- **Time-series analysis** and trending

## 🎓 Project Deliverables

### Demo Components
1. **Live Data Streaming**: Real-time EV telemetry generation
2. **Processing Pipeline**: Data enrichment and anomaly detection
3. **Interactive Dashboards**: Multiple visualization types
4. **Architecture Presentation**: System design and data flow

### Technical Report
- **Architecture documentation** with component descriptions
- **Data flow diagrams** showing processing stages
- **Performance metrics** and scalability considerations
- **Lessons learned** and potential improvements

## 🔧 Cleanup

To stop all services and clean up:

```bash
# Stop all containers
docker-compose -f docker-compose/docker-compose.yml down

# Remove volumes (optional - deletes all data)
docker-compose -f docker-compose/docker-compose.yml down -v

# Remove images (optional)
docker system prune -a
```

## 🤝 Contributing

This project is designed for educational purposes. Feel free to:
- Add new vehicle types or sensors
- Implement additional anomaly detection algorithms
- Create new dashboard visualizations
- Optimize performance for larger datasets

## 📄 License

This project is created for educational purposes as part of a Big Data technologies module.

---

**Happy Big Data Processing! 🚗⚡📊** 