import json
import time
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from ev_data_simulator import EVDataSimulator, simulate_multiple_vehicles
import argparse
import signal
import sys
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EVKafkaProducer:
    """
    Kafka Producer for EV telemetry data
    Sends real-time EV data to Kafka topics for processing
    """
    
    def __init__(self, 
                 bootstrap_servers: str = 'localhost:9092',
                 topic_name: str = 'ev-telemetry',
                 num_vehicles: int = 5):
        
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = topic_name
        self.num_vehicles = num_vehicles
        self.running = True
        
        # Initialize Kafka producer
        self.producer = None
        self._init_producer()
        
        # Initialize EV simulators
        self.simulators = [EVDataSimulator() for _ in range(num_vehicles)]
        
        logger.info(f"Initialized EV Kafka Producer with {num_vehicles} vehicles")
        logger.info(f"Kafka servers: {bootstrap_servers}")
        logger.info(f"Topic: {topic_name}")
    
    def _init_producer(self):
        """Initialize Kafka producer with configuration"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                # Producer configuration for reliability
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,   # Retry failed sends
                batch_size=16384,  # Batch size in bytes
                linger_ms=10,      # Wait up to 10ms to batch records
                buffer_memory=33554432,  # 32MB buffer
                # Compression for better throughput
                compression_type='gzip'
            )
            logger.info("Kafka producer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise
    
    def _delivery_callback(self, record_metadata):
        """Callback for message delivery confirmation"""
        logger.debug(f"Message delivered to topic {record_metadata.topic} "
                    f"partition {record_metadata.partition} "
                    f"offset {record_metadata.offset}")
    
    def _error_callback(self, exception):
        """Callback for message delivery errors"""
        logger.error(f"Message delivery failed: {exception}")
    
    def send_ev_data(self, data: Dict, vehicle_id: str):
        """Send a single EV data point to Kafka"""
        try:
            # Use vehicle_id as the key for partitioning
            future = self.producer.send(
                self.topic_name,
                key=vehicle_id,
                value=data
            )
            
            # Add callback for delivery confirmation
            future.add_callback(self._delivery_callback)
            future.add_errback(self._error_callback)
            
            return future
            
        except Exception as e:
            logger.error(f"Error sending data for vehicle {vehicle_id}: {e}")
            return None
    
    def produce_continuous_data(self, interval: float = 1.0):
        """
        Continuously produce EV data at specified interval
        
        Args:
            interval: Time interval between data points in seconds
        """
        logger.info(f"Starting continuous data production (interval: {interval}s)")
        
        message_count = 0
        
        try:
            while self.running:
                start_time = time.time()
                
                # Generate data for all vehicles
                for simulator in self.simulators:
                    data = simulator.generate_data_point()
                    vehicle_id = data['vehicle_id']
                    
                    # Send to Kafka
                    future = self.send_ev_data(data, vehicle_id)
                    if future:
                        message_count += 1
                
                # Log progress periodically
                if message_count % 50 == 0:
                    logger.info(f"Sent {message_count} messages to Kafka")
                
                # Ensure we maintain the desired interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping producer...")
            self.stop()
        except Exception as e:
            logger.error(f"Error in continuous production: {e}")
            raise
    
    def produce_batch_data(self, batch_size: int = 100):
        """
        Produce a batch of EV data points
        
        Args:
            batch_size: Number of data points to produce
        """
        logger.info(f"Producing batch of {batch_size} data points")
        
        for i in range(batch_size):
            # Rotate through simulators
            simulator = self.simulators[i % len(self.simulators)]
            data = simulator.generate_data_point()
            vehicle_id = data['vehicle_id']
            
            self.send_ev_data(data, vehicle_id)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Produced {i + 1}/{batch_size} messages")
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        logger.info(f"Batch production completed: {batch_size} messages sent")
    
    def stop(self):
        """Stop the producer and clean up resources"""
        logger.info("Stopping EV Kafka Producer...")
        self.running = False
        
        if self.producer:
            # Flush any remaining messages
            self.producer.flush(timeout=10)
            self.producer.close()
            logger.info("Kafka producer closed")
    
    def get_vehicle_info(self) -> List[Dict]:
        """Get information about all simulated vehicles"""
        return [
            {
                'vehicle_id': sim.vehicle_id,
                'current_location': {
                    'lat': sim.current_lat,
                    'lon': sim.current_lon
                },
                'battery_level': sim.battery_level,
                'current_speed': sim.current_speed,
                'driving_pattern': sim.current_pattern
            }
            for sim in self.simulators
        ]

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully"""
    logger.info("Received signal to terminate")
    sys.exit(0)

def main():
    """Main function to run the EV Kafka Producer"""
    parser = argparse.ArgumentParser(description='EV Data Kafka Producer')
    parser.add_argument('--bootstrap-servers', default='localhost:9092',
                       help='Kafka bootstrap servers')
    parser.add_argument('--topic', default='ev-telemetry',
                       help='Kafka topic name')
    parser.add_argument('--vehicles', type=int, default=5,
                       help='Number of vehicles to simulate')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Data production interval in seconds')
    parser.add_argument('--mode', choices=['continuous', 'batch'], default='continuous',
                       help='Production mode')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Batch size for batch mode')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run producer
    producer = None
    try:
        producer = EVKafkaProducer(
            bootstrap_servers=args.bootstrap_servers,
            topic_name=args.topic,
            num_vehicles=args.vehicles
        )
        
        # Display vehicle information
        logger.info("Simulated Vehicles:")
        for i, vehicle_info in enumerate(producer.get_vehicle_info(), 1):
            logger.info(f"  Vehicle {i}: {vehicle_info['vehicle_id'][:8]}... "
                       f"(Battery: {vehicle_info['battery_level']:.1f}%)")
        
        if args.mode == 'continuous':
            producer.produce_continuous_data(args.interval)
        else:
            producer.produce_batch_data(args.batch_size)
            
    except Exception as e:
        logger.error(f"Producer failed: {e}")
        sys.exit(1)
    finally:
        if producer:
            producer.stop()

if __name__ == "__main__":
    main() 