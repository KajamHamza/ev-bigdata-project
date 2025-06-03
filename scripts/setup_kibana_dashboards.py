#!/usr/bin/env python3
"""
Automated Kibana Dashboard Setup for EV Fleet
Creates data views, visualizations, and dashboards automatically
"""

import requests
import json
import time
import sys

KIBANA_URL = "http://localhost:5601"
ELASTICSEARCH_URL = "http://localhost:9200"

def wait_for_kibana():
    """Wait for Kibana to be ready"""
    print("🔄 Waiting for Kibana to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{KIBANA_URL}/api/status")
            if response.status_code == 200:
                print("✅ Kibana is ready!")
                return True
        except:
            pass
        time.sleep(2)
        print(f"   Attempt {i+1}/30...")
    return False

def create_data_view():
    """Create the EV Fleet data view or get existing one"""
    print("📊 Creating EV Fleet data view...")
    
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true"
    }
    
    # First, try to get existing data views
    try:
        response = requests.get(f"{KIBANA_URL}/api/data_views", headers=headers)
        if response.status_code == 200:
            data_views = response.json().get("data_view", [])
            for dv in data_views:
                if dv.get("title") == "ev-processed*":
                    print(f"✅ Found existing data view with ID: {dv['id']}")
                    return dv["id"]
    except Exception as e:
        print(f"⚠️ Could not check existing data views: {e}")
    
    # If not found, create new one
    data_view = {
        "data_view": {
            "title": "ev-processed*",
            "name": "EV Fleet Data",
            "timeFieldName": "timestamp"
        }
    }
    
    try:
        response = requests.post(
            f"{KIBANA_URL}/api/data_views/data_view",
            headers=headers,
            json=data_view
        )
        
        if response.status_code in [200, 201]:
            data_view_id = response.json()["data_view"]["id"]
            print(f"✅ Data view created with ID: {data_view_id}")
            return data_view_id
        elif response.status_code == 400 and "Duplicate" in response.text:
            # Try to find the existing one by listing all data views
            try:
                list_response = requests.get(f"{KIBANA_URL}/api/data_views", headers=headers)
                if list_response.status_code == 200:
                    data_views = list_response.json().get("data_view", [])
                    for dv in data_views:
                        if "ev-processed" in dv.get("title", ""):
                            print(f"✅ Using existing data view with ID: {dv['id']}")
                            return dv["id"]
            except:
                pass
            print(f"❌ Data view exists but couldn't retrieve ID")
            return None
        else:
            print(f"❌ Failed to create data view: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error creating data view: {e}")
        return None

def create_visualizations(data_view_id):
    """Create all visualizations"""
    print("🎨 Creating visualizations...")
    
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true"
    }
    
    visualizations = []
    
    # 1. Battery Levels Chart
    battery_viz = {
        "attributes": {
            "title": "🔋 Battery Levels by Vehicle",
            "type": "lens",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["x_axis", "y_axis", "breakdown"],
                                "columns": {
                                    "x_axis": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "@timestamp",
                                        "operationType": "date_histogram",
                                        "sourceField": "timestamp",
                                        "params": {"interval": "auto"}
                                    },
                                    "y_axis": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Average battery.level",
                                        "operationType": "average",
                                        "sourceField": "battery.level"
                                    },
                                    "breakdown": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Top values of vehicle_id",
                                        "operationType": "terms",
                                        "sourceField": "vehicle_id",
                                        "params": {"size": 10}
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["y_axis"],
                        "position": "top",
                        "seriesType": "line",
                        "showGridlines": False,
                        "xAccessor": "x_axis",
                        "splitAccessor": "breakdown"
                    }]
                }
            },
            "references": [{"type": "index-pattern", "id": data_view_id, "name": "indexpattern-datasource-current-indexpattern"}]
        }
    }
    
    # 2. Speed Timeline
    speed_viz = {
        "attributes": {
            "title": "🚗 Speed Timeline",
            "type": "lens",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["x_axis", "y_axis", "breakdown"],
                                "columns": {
                                    "x_axis": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "@timestamp",
                                        "operationType": "date_histogram",
                                        "sourceField": "timestamp",
                                        "params": {"interval": "auto"}
                                    },
                                    "y_axis": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Average motion.speed",
                                        "operationType": "average",
                                        "sourceField": "motion.speed"
                                    },
                                    "breakdown": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Top values of vehicle_id",
                                        "operationType": "terms",
                                        "sourceField": "vehicle_id",
                                        "params": {"size": 10}
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["y_axis"],
                        "position": "top",
                        "seriesType": "area",
                        "showGridlines": False,
                        "xAccessor": "x_axis",
                        "splitAccessor": "breakdown"
                    }]
                }
            },
            "references": [{"type": "index-pattern", "id": data_view_id, "name": "indexpattern-datasource-current-indexpattern"}]
        }
    }
    
    # 3. Vehicle Count Metric
    count_viz = {
        "attributes": {
            "title": "📊 Active Vehicles",
            "type": "lens",
            "visualizationType": "lnsMetric",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["metric"],
                                "columns": {
                                    "metric": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Unique count of vehicle_id",
                                        "operationType": "unique_count",
                                        "sourceField": "vehicle_id"
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layerId": "layer1",
                    "accessor": "metric"
                }
            },
            "references": [{"type": "index-pattern", "id": data_view_id, "name": "indexpattern-datasource-current-indexpattern"}]
        }
    }
    
    # 4. Energy Consumption Chart
    energy_viz = {
        "attributes": {
            "title": "⚡ Energy Consumption",
            "type": "lens",
            "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columnOrder": ["x_axis", "y_axis", "breakdown"],
                                "columns": {
                                    "x_axis": {
                                        "dataType": "date",
                                        "isBucketed": True,
                                        "label": "@timestamp",
                                        "operationType": "date_histogram",
                                        "sourceField": "timestamp",
                                        "params": {"interval": "auto"}
                                    },
                                    "y_axis": {
                                        "dataType": "number",
                                        "isBucketed": False,
                                        "label": "Average energy.consumption",
                                        "operationType": "average",
                                        "sourceField": "energy.consumption"
                                    },
                                    "breakdown": {
                                        "dataType": "string",
                                        "isBucketed": True,
                                        "label": "Top values of vehicle_id",
                                        "operationType": "terms",
                                        "sourceField": "vehicle_id",
                                        "params": {"size": 10}
                                    }
                                }
                            }
                        }
                    }
                },
                "visualization": {
                    "layers": [{
                        "layerId": "layer1",
                        "accessors": ["y_axis"],
                        "position": "top",
                        "seriesType": "bar",
                        "showGridlines": False,
                        "xAccessor": "x_axis",
                        "splitAccessor": "breakdown"
                    }]
                }
            },
            "references": [{"type": "index-pattern", "id": data_view_id, "name": "indexpattern-datasource-current-indexpattern"}]
        }
    }
    
    viz_configs = [
        ("battery", battery_viz),
        ("speed", speed_viz),
        ("count", count_viz),
        ("energy", energy_viz)
    ]
    
    for viz_name, viz_config in viz_configs:
        try:
            response = requests.post(
                f"{KIBANA_URL}/api/saved_objects/visualization",
                headers=headers,
                json=viz_config
            )
            
            if response.status_code in [200, 201]:
                viz_id = response.json()["id"]
                visualizations.append((viz_name, viz_id))
                print(f"✅ Created {viz_config['attributes']['title']} (ID: {viz_id})")
            else:
                print(f"❌ Failed to create {viz_name} visualization: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error creating {viz_name} visualization: {e}")
    
    return visualizations

def create_dashboard(visualizations):
    """Create the main dashboard"""
    print("🎯 Creating EV Fleet Dashboard...")
    
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true"
    }
    
    # Create panel references
    panels = []
    panel_id = 1
    
    # Layout configuration
    layouts = [
        {"x": 0, "y": 0, "w": 24, "h": 15},   # Battery chart
        {"x": 24, "y": 0, "w": 24, "h": 15},  # Speed chart
        {"x": 0, "y": 15, "w": 12, "h": 10},  # Vehicle count
        {"x": 12, "y": 15, "w": 36, "h": 10}  # Energy consumption
    ]
    
    for i, (viz_name, viz_id) in enumerate(visualizations):
        if i < len(layouts):
            layout = layouts[i]
            panels.append({
                "version": "8.11.0",
                "gridData": {
                    "x": layout["x"],
                    "y": layout["y"],
                    "w": layout["w"],
                    "h": layout["h"],
                    "i": str(panel_id)
                },
                "panelIndex": str(panel_id),
                "embeddableConfig": {},
                "panelRefName": f"panel_{panel_id}"
            })
            panel_id += 1
    
    # Create references
    references = []
    for i, (viz_name, viz_id) in enumerate(visualizations):
        if i < len(panels):
            references.append({
                "name": f"panel_{i+1}",
                "type": "visualization",
                "id": viz_id
            })
    
    dashboard = {
        "attributes": {
            "title": "🚗 EV Fleet Real-time Dashboard",
            "description": "Real-time monitoring of electric vehicle fleet with battery levels, speed, and energy consumption",
            "panelsJSON": json.dumps(panels),
            "timeRestore": False,
            "timeTo": "now",
            "timeFrom": "now-15m",
            "refreshInterval": {
                "pause": False,
                "value": 5000
            },
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"match_all": {}},
                    "filter": []
                })
            }
        },
        "references": references
    }
    
    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/dashboard",
            headers=headers,
            json=dashboard
        )
        
        if response.status_code in [200, 201]:
            dashboard_id = response.json()["id"]
            print(f"✅ Dashboard created successfully!")
            print(f"🌐 Access it at: {KIBANA_URL}/app/dashboards#/view/{dashboard_id}")
            return dashboard_id
        else:
            print(f"❌ Failed to create dashboard: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        return None

def main():
    """Main function"""
    print("🚗 EV Fleet Kibana Dashboard Setup")
    print("=" * 40)
    
    # Wait for Kibana
    if not wait_for_kibana():
        print("❌ Kibana is not ready. Please check if it's running.")
        sys.exit(1)
    
    # Create data view
    data_view_id = create_data_view()
    if not data_view_id:
        print("❌ Failed to create data view. Exiting.")
        sys.exit(1)
    
    # Wait a bit for data view to be ready
    time.sleep(2)
    
    # Create visualizations
    visualizations = create_visualizations(data_view_id)
    if not visualizations:
        print("❌ No visualizations created. Exiting.")
        sys.exit(1)
    
    # Wait a bit for visualizations to be ready
    time.sleep(2)
    
    # Create dashboard
    dashboard_id = create_dashboard(visualizations)
    if dashboard_id:
        print("\n🎉 Setup completed successfully!")
        print(f"🌐 Dashboard URL: {KIBANA_URL}/app/dashboards#/view/{dashboard_id}")
        print("\n📊 Your dashboard includes:")
        print("   • 🔋 Battery Levels by Vehicle")
        print("   • 🚗 Speed Timeline")
        print("   • 📊 Active Vehicles Count")
        print("   • ⚡ Energy Consumption")
        print("\n🔄 Dashboard auto-refreshes every 5 seconds")
    else:
        print("❌ Failed to create dashboard.")
        sys.exit(1)

if __name__ == "__main__":
    main() 