import json
import logging
import time
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import argparse
import signal
import sys
from typing import Dict, Any
import statistics
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EVDataProcessor:
    """
    Kafka Streams processor for EV telemetry data
    Performs data enrichment, aggregation, and preprocessing
    """
    
    def __init__(self,
                 bootstrap_servers: str = 'localhost:9092',
                 input_topic: str = 'ev-telemetry',
                 output_topic: str = 'ev-processed',
                 consumer_group: str = 'ev-processor-group'):
        
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.consumer_group = consumer_group
        self.running = True
        
        # Initialize consumer and producer
        self.consumer = None
        self.producer = None
        self._init_kafka_clients()
        
        # Data processing state
        self.vehicle_history = defaultdict(lambda: deque(maxlen=10))  # Last 10 data points per vehicle
        self.vehicle_stats = defaultdict(dict)  # Running statistics per vehicle
        
        logger.info(f"Initialized EV Data Processor")
        logger.info(f"Input topic: {input_topic}")
        logger.info(f"Output topic: {output_topic}")
    
    def _init_kafka_clients(self):
        """Initialize Kafka consumer and producer"""
        try:
            # Consumer configuration
            self.consumer = KafkaConsumer(
                self.input_topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',  # Start from latest messages
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            
            # Producer configuration
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                compression_type='gzip'
            )
            
            logger.info("Kafka consumer and producer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka clients: {e}")
            raise
    
    def _calculate_vehicle_statistics(self, vehicle_id: str, data: Dict) -> Dict:
        """Calculate running statistics for a vehicle"""
        history = self.vehicle_history[vehicle_id]
        
        if len(history) == 0:
            return {}
        
        # Extract metrics from history
        speeds = [point['motion']['speed'] for point in history]
        battery_levels = [point['battery']['level'] for point in history]
        consumptions = [point['energy']['consumption'] for point in history if point['energy']['consumption'] > 0]
        
        stats = {}
        
        if speeds:
            stats['speed_stats'] = {
                'avg_speed': round(statistics.mean(speeds), 2),
                'max_speed': round(max(speeds), 2),
                'min_speed': round(min(speeds), 2),
                'speed_variance': round(statistics.variance(speeds) if len(speeds) > 1 else 0, 2)
            }
        
        if battery_levels:
            stats['battery_stats'] = {
                'avg_battery': round(statistics.mean(battery_levels), 2),
                'battery_trend': 'decreasing' if len(battery_levels) > 1 and battery_levels[-1] < battery_levels[0] else 'stable',
                'battery_change_rate': round((battery_levels[-1] - battery_levels[0]) / len(battery_levels), 3) if len(battery_levels) > 1 else 0
            }
        
        if consumptions:
            stats['energy_stats'] = {
                'avg_consumption': round(statistics.mean(consumptions), 3),
                'total_consumption': round(sum(consumptions), 3)
            }
        
        return stats
    
    def _detect_anomalies(self, vehicle_id: str, data: Dict) -> list:
        """Detect anomalies in vehicle data"""
        anomalies = []
        
        # Speed anomalies
        speed = data['motion']['speed']
        if speed > 150:
            anomalies.append({
                'type': 'HIGH_SPEED_ANOMALY',
                'value': speed,
                'threshold': 150,
                'severity': 'HIGH'
            })
        
        # Battery anomalies
        battery_level = data['battery']['level']
        battery_temp = data['battery']['temperature']
        
        if battery_level < 5:
            anomalies.append({
                'type': 'CRITICAL_BATTERY_LOW',
                'value': battery_level,
                'threshold': 5,
                'severity': 'CRITICAL'
            })
        
        if battery_temp > 50:
            anomalies.append({
                'type': 'BATTERY_OVERHEATING',
                'value': battery_temp,
                'threshold': 50,
                'severity': 'HIGH'
            })
        
        # Rapid battery drain detection
        history = self.vehicle_history[vehicle_id]
        if len(history) >= 3:
            recent_levels = [point['battery']['level'] for point in list(history)[-3:]]
            if all(recent_levels[i] > recent_levels[i+1] for i in range(len(recent_levels)-1)):
                drain_rate = recent_levels[0] - recent_levels[-1]
                if drain_rate > 10:  # More than 10% in 3 readings
                    anomalies.append({
                        'type': 'RAPID_BATTERY_DRAIN',
                        'value': drain_rate,
                        'threshold': 10,
                        'severity': 'MEDIUM'
                    })
        
        return anomalies
    
    def _calculate_derived_metrics(self, data: Dict) -> Dict:
        """Calculate additional derived metrics"""
        derived = {}
        
        # Distance calculations
        speed_kmh = data['motion']['speed']
        speed_ms = speed_kmh / 3.6  # Convert to m/s
        
        # Estimated distance traveled in last second (rough approximation)
        derived['estimated_distance_m'] = speed_ms
        
        # Energy efficiency
        consumption = data['energy']['consumption']
        if speed_kmh > 0 and consumption > 0:
            derived['efficiency_kwh_per_100km'] = (consumption / speed_kmh) * 100
        else:
            derived['efficiency_kwh_per_100km'] = 0
        
        # Battery health indicators
        battery_level = data['battery']['level']
        battery_temp = data['battery']['temperature']
        
        # Simple battery health score (0-100)
        temp_score = max(0, 100 - abs(battery_temp - 25) * 2)  # Optimal around 25°C
        level_score = battery_level
        derived['battery_health_score'] = round((temp_score + level_score) / 2, 1)
        
        # Driving behavior classification
        speed = data['motion']['speed']
        acceleration = abs(data['motion']['acceleration'])
        
        if speed == 0:
            derived['driving_behavior'] = 'stationary'
        elif speed < 30 and acceleration < 1:
            derived['driving_behavior'] = 'eco_driving'
        elif speed > 100 or acceleration > 3:
            derived['driving_behavior'] = 'aggressive'
        else:
            derived['driving_behavior'] = 'normal'
        
        return derived
    
    def _enrich_data(self, data: Dict) -> Dict:
        """Enrich the raw EV data with additional information"""
        vehicle_id = data['vehicle_id']
        
        # Add to vehicle history
        self.vehicle_history[vehicle_id].append(data)
        
        # Calculate statistics
        stats = self._calculate_vehicle_statistics(vehicle_id, data)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(vehicle_id, data)
        
        # Calculate derived metrics
        derived_metrics = self._calculate_derived_metrics(data)
        
        # Create enriched data
        enriched_data = data.copy()
        enriched_data.update({
            'processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'statistics': stats,
            'anomalies': anomalies,
            'derived_metrics': derived_metrics,
            'data_quality': {
                'completeness_score': self._calculate_completeness_score(data),
                'freshness_seconds': 0,  # Assuming real-time processing
                'accuracy_flags': self._check_data_accuracy(data)
            }
        })
        
        return enriched_data
    
    def _calculate_completeness_score(self, data: Dict) -> float:
        """Calculate data completeness score (0-100)"""
        required_fields = [
            'timestamp', 'vehicle_id', 'location.latitude', 'location.longitude',
            'motion.speed', 'battery.level', 'battery.temperature'
        ]
        
        present_fields = 0
        for field in required_fields:
            if '.' in field:
                parts = field.split('.')
                if parts[0] in data and parts[1] in data[parts[0]]:
                    present_fields += 1
            else:
                if field in data:
                    present_fields += 1
        
        return round((present_fields / len(required_fields)) * 100, 1)
    
    def _check_data_accuracy(self, data: Dict) -> list:
        """Check for data accuracy issues"""
        flags = []
        
        # Check for impossible values
        if data['motion']['speed'] < 0:
            flags.append('NEGATIVE_SPEED')
        
        if not (0 <= data['battery']['level'] <= 100):
            flags.append('INVALID_BATTERY_LEVEL')
        
        if not (-90 <= data['location']['latitude'] <= 90):
            flags.append('INVALID_LATITUDE')
        
        if not (-180 <= data['location']['longitude'] <= 180):
            flags.append('INVALID_LONGITUDE')
        
        return flags
    
    def process_messages(self):
        """Main processing loop"""
        logger.info("Starting message processing...")
        
        processed_count = 0
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    # Get raw data
                    raw_data = message.value
                    vehicle_id = message.key
                    
                    logger.debug(f"Processing message for vehicle: {vehicle_id}")
                    
                    # Enrich the data
                    enriched_data = self._enrich_data(raw_data)
                    
                    # Send enriched data to output topic
                    future = self.producer.send(
                        self.output_topic,
                        key=vehicle_id,
                        value=enriched_data
                    )
                    
                    processed_count += 1
                    
                    # Log progress
                    if processed_count % 50 == 0:
                        logger.info(f"Processed {processed_count} messages")
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping processor...")
        except Exception as e:
            logger.error(f"Error in message processing: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop the processor and clean up resources"""
        logger.info("Stopping EV Data Processor...")
        self.running = False
        
        if self.producer:
            self.producer.flush(timeout=10)
            self.producer.close()
            logger.info("Kafka producer closed")
        
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    logger.info("Received signal to terminate")
    sys.exit(0)

def main():
    """Main function to run the EV Data Processor"""
    parser = argparse.ArgumentParser(description='EV Data Kafka Streams Processor')
    parser.add_argument('--bootstrap-servers', default='localhost:9092',
                       help='Kafka bootstrap servers')
    parser.add_argument('--input-topic', default='ev-telemetry',
                       help='Input Kafka topic')
    parser.add_argument('--output-topic', default='ev-processed',
                       help='Output Kafka topic')
    parser.add_argument('--consumer-group', default='ev-processor-group',
                       help='Kafka consumer group')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run processor
    processor = None
    try:
        processor = EVDataProcessor(
            bootstrap_servers=args.bootstrap_servers,
            input_topic=args.input_topic,
            output_topic=args.output_topic,
            consumer_group=args.consumer_group
        )
        
        processor.process_messages()
        
    except Exception as e:
        logger.error(f"Processor failed: {e}")
        sys.exit(1)
    finally:
        if processor:
            processor.stop()

if __name__ == "__main__":
    main() 