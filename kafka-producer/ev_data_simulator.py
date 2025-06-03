import json
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import math

class EVDataSimulator:
    """
    Electric Vehicle Data Simulator
    Generates realistic EV telemetry data including:
    - GPS coordinates (latitude, longitude)
    - Speed and acceleration
    - Battery state (charge level, voltage, temperature)
    - Energy consumption
    - Vehicle status and diagnostics
    """
    
    def __init__(self, vehicle_id: str = None):
        self.vehicle_id = vehicle_id or str(uuid.uuid4())
        
        # Initial vehicle state
        self.current_lat = 48.8566 + random.uniform(-0.1, 0.1)  # Paris area
        self.current_lon = 2.3522 + random.uniform(-0.1, 0.1)
        self.current_speed = 0.0  # km/h
        self.battery_level = random.uniform(20, 100)  # percentage
        self.battery_temp = random.uniform(20, 35)  # Celsius
        self.odometer = random.uniform(1000, 50000)  # km
        self.trip_distance = 0.0
        
        # Vehicle specifications
        self.battery_capacity = 75.0  # kWh
        self.max_speed = 180  # km/h
        self.efficiency = 0.2  # kWh/km average consumption
        
        # Driving patterns
        self.driving_patterns = [
            "city_driving",
            "highway_driving", 
            "parking",
            "charging",
            "idle"
        ]
        self.current_pattern = "idle"
        self.pattern_duration = 0
        
    def _update_driving_pattern(self):
        """Update driving pattern based on probability"""
        if self.pattern_duration <= 0:
            # Choose new pattern
            patterns_prob = {
                "city_driving": 0.3,
                "highway_driving": 0.2,
                "parking": 0.2,
                "charging": 0.1 if self.battery_level < 30 else 0.05,
                "idle": 0.25
            }
            
            rand = random.random()
            cumulative = 0
            for pattern, prob in patterns_prob.items():
                cumulative += prob
                if rand <= cumulative:
                    self.current_pattern = pattern
                    break
            
            # Set pattern duration (in simulation steps)
            self.pattern_duration = random.randint(10, 50)
        else:
            self.pattern_duration -= 1
    
    def _update_speed_and_location(self):
        """Update speed and GPS coordinates based on driving pattern"""
        if self.current_pattern == "city_driving":
            target_speed = random.uniform(20, 60)
            speed_change = random.uniform(-5, 5)
            
        elif self.current_pattern == "highway_driving":
            target_speed = random.uniform(80, 130)
            speed_change = random.uniform(-3, 3)
            
        elif self.current_pattern == "parking":
            target_speed = 0
            speed_change = -min(self.current_speed, 10)
            
        elif self.current_pattern == "charging":
            target_speed = 0
            speed_change = -min(self.current_speed, 15)
            
        else:  # idle
            target_speed = random.uniform(0, 20)
            speed_change = random.uniform(-2, 2)
        
        # Update speed with some inertia
        self.current_speed = max(0, min(self.max_speed, 
                                      self.current_speed + speed_change))
        
        # Update location if moving
        if self.current_speed > 1:
            # Convert speed to coordinate change (rough approximation)
            distance_km = self.current_speed / 3600  # km per second
            
            # Random direction change
            direction = random.uniform(0, 2 * math.pi)
            
            # Update coordinates (very rough conversion)
            lat_change = (distance_km / 111) * math.cos(direction)
            lon_change = (distance_km / (111 * math.cos(math.radians(self.current_lat)))) * math.sin(direction)
            
            self.current_lat += lat_change
            self.current_lon += lon_change
            self.trip_distance += distance_km
            self.odometer += distance_km
    
    def _update_battery(self):
        """Update battery state based on current activity"""
        if self.current_pattern == "charging":
            # Charging: increase battery level
            charge_rate = random.uniform(0.1, 0.3)  # % per second
            self.battery_level = min(100, self.battery_level + charge_rate)
            self.battery_temp = min(45, self.battery_temp + random.uniform(0, 0.2))
            
        elif self.current_speed > 0:
            # Driving: consume battery
            consumption = (self.current_speed / 100) * self.efficiency / 3600  # kWh per second
            battery_consumed = (consumption / self.battery_capacity) * 100  # percentage
            self.battery_level = max(0, self.battery_level - battery_consumed)
            
            # Battery temperature increases with usage
            temp_increase = (self.current_speed / 100) * random.uniform(0, 0.1)
            self.battery_temp = min(50, self.battery_temp + temp_increase)
            
        else:
            # Idle: slight battery drain and cooling
            self.battery_level = max(0, self.battery_level - random.uniform(0, 0.01))
            self.battery_temp = max(20, self.battery_temp - random.uniform(0, 0.05))
    
    def generate_data_point(self) -> Dict:
        """Generate a single data point with all EV telemetry"""
        
        # Update vehicle state
        self._update_driving_pattern()
        self._update_speed_and_location()
        self._update_battery()
        
        # Calculate additional metrics
        acceleration = random.uniform(-2, 2) if self.current_speed > 0 else 0
        energy_consumption = (self.current_speed / 100) * self.efficiency if self.current_speed > 0 else 0
        estimated_range = (self.battery_level / 100) * self.battery_capacity / self.efficiency
        
        # Generate alerts/warnings
        alerts = []
        if self.battery_level < 15:
            alerts.append("LOW_BATTERY")
        if self.battery_temp > 45:
            alerts.append("HIGH_BATTERY_TEMP")
        if self.current_speed > 120:
            alerts.append("HIGH_SPEED")
        
        # Create data point
        data_point = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vehicle_id": self.vehicle_id,
            "location": {
                "latitude": round(self.current_lat, 6),
                "longitude": round(self.current_lon, 6),
                "altitude": random.uniform(50, 200)  # meters
            },
            "motion": {
                "speed": round(self.current_speed, 2),  # km/h
                "acceleration": round(acceleration, 2),  # m/s²
                "heading": random.uniform(0, 360)  # degrees
            },
            "battery": {
                "level": round(self.battery_level, 2),  # percentage
                "voltage": round(random.uniform(350, 400), 2),  # volts
                "current": round(random.uniform(-50, 50), 2),  # amperes
                "temperature": round(self.battery_temp, 1),  # celsius
                "capacity": self.battery_capacity,  # kWh
                "estimated_range": round(estimated_range, 1)  # km
            },
            "energy": {
                "consumption": round(energy_consumption, 3),  # kWh
                "regeneration": round(max(0, -acceleration * 0.1), 3),  # kWh
                "efficiency": round(self.efficiency, 3)  # kWh/km
            },
            "vehicle_status": {
                "driving_pattern": self.current_pattern,
                "odometer": round(self.odometer, 1),  # km
                "trip_distance": round(self.trip_distance, 2),  # km
                "engine_temp": round(random.uniform(80, 95), 1),  # celsius
                "tire_pressure": [round(random.uniform(2.0, 2.5), 2) for _ in range(4)]  # bar
            },
            "diagnostics": {
                "alerts": alerts,
                "error_codes": [],
                "maintenance_due": random.choice([True, False]) if random.random() < 0.05 else False
            },
            "environmental": {
                "outside_temp": round(random.uniform(-10, 35), 1),  # celsius
                "humidity": round(random.uniform(30, 80), 1),  # percentage
                "air_quality_index": random.randint(50, 150)
            }
        }
        
        return data_point

def simulate_multiple_vehicles(num_vehicles: int = 5) -> List[Dict]:
    """Simulate data from multiple vehicles"""
    simulators = [EVDataSimulator() for _ in range(num_vehicles)]
    data_points = []
    
    for simulator in simulators:
        data_points.append(simulator.generate_data_point())
    
    return data_points

if __name__ == "__main__":
    # Test the simulator
    simulator = EVDataSimulator()
    
    print("EV Data Simulator Test")
    print("=" * 50)
    
    for i in range(5):
        data = simulator.generate_data_point()
        print(f"\nData Point {i+1}:")
        print(json.dumps(data, indent=2))
        time.sleep(1) 