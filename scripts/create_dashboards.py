#!/usr/bin/env python3
"""
Simple Kibana Dashboard Creator for EV Fleet
Uses correct API endpoints to create visualizations and dashboards
"""

import requests
import json
import time
import sys

KIBANA_URL = "http://localhost:5601"

def get_data_view_id():
    """Get the existing data view ID"""
    headers = {"kbn-xsrf": "true"}
    
    try:
        response = requests.get(f"{KIBANA_URL}/api/data_views", headers=headers)
        if response.status_code == 200:
            data_views = response.json().get("data_view", [])
            for dv in data_views:
                if "ev-processed" in dv.get("title", ""):
                    print(f"✅ Found data view: {dv['title']} (ID: {dv['id']})")
                    return dv["id"]
    except Exception as e:
        print(f"Error getting data view: {e}")
    
    print("❌ No EV data view found")
    return None

def create_simple_dashboard():
    """Create a simple dashboard with basic panels"""
    print("🎯 Creating EV Fleet Dashboard...")
    
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true"
    }
    
    # Simple dashboard configuration
    dashboard_config = {
        "attributes": {
            "title": "🚗 EV Fleet Real-time Dashboard",
            "description": "Real-time monitoring of electric vehicle fleet",
            "panelsJSON": "[]",
            "timeRestore": False,
            "timeTo": "now",
            "timeFrom": "now-30m",
            "refreshInterval": {
                "pause": False,
                "value": 5000
            },
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": "{\"query\":{\"match_all\":{}},\"filter\":[]}"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/dashboard",
            headers=headers,
            json=dashboard_config
        )
        
        if response.status_code in [200, 201]:
            dashboard_id = response.json()["id"]
            dashboard_url = f"{KIBANA_URL}/app/dashboards#/view/{dashboard_id}"
            
            print(f"✅ Dashboard created successfully!")
            print(f"🌐 Dashboard URL: {dashboard_url}")
            print(f"📋 Dashboard ID: {dashboard_id}")
            
            return dashboard_id, dashboard_url
        else:
            print(f"❌ Failed to create dashboard: {response.status_code}")
            print(response.text)
            return None, None
            
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        return None, None

def create_lens_visualizations(data_view_id):
    """Create Lens visualizations using the new API"""
    print("🎨 Creating visualizations...")
    
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true"
    }
    
    # Battery Level Chart
    battery_chart = {
        "attributes": {
            "title": "🔋 Battery Levels",
            "type": "lens",
            "state": {
                "visualization": {
                    "title": "Empty XY chart",
                    "type": "lnsXY",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "accessors": ["y-axis-column"],
                            "position": "top",
                            "seriesType": "line",
                            "showGridlines": False,
                            "xAccessor": "x-axis-column",
                            "splitAccessor": "breakdown-column"
                        }
                    ]
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "indexpattern": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x-axis-column": {
                                        "label": "@timestamp",
                                        "dataType": "date",
                                        "operationType": "date_histogram",
                                        "sourceField": "timestamp",
                                        "isBucketed": True,
                                        "scale": "interval",
                                        "params": {"interval": "auto"}
                                    },
                                    "y-axis-column": {
                                        "label": "Average of battery.level",
                                        "dataType": "number",
                                        "operationType": "average",
                                        "sourceField": "battery.level",
                                        "isBucketed": False,
                                        "scale": "ratio"
                                    },
                                    "breakdown-column": {
                                        "label": "Top values of vehicle_id",
                                        "dataType": "string",
                                        "operationType": "terms",
                                        "sourceField": "vehicle_id",
                                        "isBucketed": True,
                                        "scale": "ordinal",
                                        "params": {"size": 5, "orderBy": {"type": "alphabetical"}}
                                    }
                                },
                                "columnOrder": ["breakdown-column", "x-axis-column", "y-axis-column"],
                                "indexPatternId": data_view_id
                            }
                        }
                    }
                }
            },
            "references": [
                {
                    "type": "index-pattern",
                    "id": data_view_id,
                    "name": "indexpattern-datasource-current-indexpattern"
                }
            ]
        }
    }
    
    # Speed Chart
    speed_chart = {
        "attributes": {
            "title": "🚗 Vehicle Speed",
            "type": "lens",
            "state": {
                "visualization": {
                    "title": "Empty XY chart",
                    "type": "lnsXY",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "accessors": ["y-axis-column"],
                            "position": "top",
                            "seriesType": "area",
                            "showGridlines": False,
                            "xAccessor": "x-axis-column",
                            "splitAccessor": "breakdown-column"
                        }
                    ]
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "indexpattern": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x-axis-column": {
                                        "label": "@timestamp",
                                        "dataType": "date",
                                        "operationType": "date_histogram",
                                        "sourceField": "timestamp",
                                        "isBucketed": True,
                                        "scale": "interval",
                                        "params": {"interval": "auto"}
                                    },
                                    "y-axis-column": {
                                        "label": "Average of motion.speed",
                                        "dataType": "number",
                                        "operationType": "average",
                                        "sourceField": "motion.speed",
                                        "isBucketed": False,
                                        "scale": "ratio"
                                    },
                                    "breakdown-column": {
                                        "label": "Top values of vehicle_id",
                                        "dataType": "string",
                                        "operationType": "terms",
                                        "sourceField": "vehicle_id",
                                        "isBucketed": True,
                                        "scale": "ordinal",
                                        "params": {"size": 5, "orderBy": {"type": "alphabetical"}}
                                    }
                                },
                                "columnOrder": ["breakdown-column", "x-axis-column", "y-axis-column"],
                                "indexPatternId": data_view_id
                            }
                        }
                    }
                }
            },
            "references": [
                {
                    "type": "index-pattern",
                    "id": data_view_id,
                    "name": "indexpattern-datasource-current-indexpattern"
                }
            ]
        }
    }
    
    # Vehicle Count Metric
    vehicle_count = {
        "attributes": {
            "title": "📊 Active Vehicles",
            "type": "lens",
            "state": {
                "visualization": {
                    "title": "Empty Metric chart",
                    "type": "lnsMetric",
                    "layerId": "layer1",
                    "accessor": "metric-column"
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "indexpattern": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "metric-column": {
                                        "label": "Unique count of vehicle_id",
                                        "dataType": "number",
                                        "operationType": "unique_count",
                                        "sourceField": "vehicle_id",
                                        "isBucketed": False,
                                        "scale": "ratio"
                                    }
                                },
                                "columnOrder": ["metric-column"],
                                "indexPatternId": data_view_id
                            }
                        }
                    }
                }
            },
            "references": [
                {
                    "type": "index-pattern",
                    "id": data_view_id,
                    "name": "indexpattern-datasource-current-indexpattern"
                }
            ]
        }
    }
    
    visualizations = [
        ("battery", battery_chart),
        ("speed", speed_chart),
        ("count", vehicle_count)
    ]
    
    created_viz = []
    
    for viz_name, viz_config in visualizations:
        try:
            response = requests.post(
                f"{KIBANA_URL}/api/saved_objects/lens",
                headers=headers,
                json=viz_config
            )
            
            if response.status_code in [200, 201]:
                viz_id = response.json()["id"]
                created_viz.append((viz_name, viz_id))
                print(f"✅ Created {viz_config['attributes']['title']} (ID: {viz_id})")
            else:
                print(f"❌ Failed to create {viz_name}: {response.status_code}")
                print(response.text[:200])
                
        except Exception as e:
            print(f"❌ Error creating {viz_name}: {e}")
    
    return created_viz

def main():
    """Main function"""
    print("🚗 EV Fleet Dashboard Creator")
    print("=" * 35)
    
    # Get data view
    data_view_id = get_data_view_id()
    if not data_view_id:
        print("❌ Please ensure your data view exists first")
        sys.exit(1)
    
    # Create visualizations
    visualizations = create_lens_visualizations(data_view_id)
    
    if visualizations:
        print(f"\n✅ Created {len(visualizations)} visualizations")
        for viz_name, viz_id in visualizations:
            print(f"   • {viz_name}: {viz_id}")
    
    # Create dashboard
    dashboard_id, dashboard_url = create_simple_dashboard()
    
    if dashboard_id:
        print(f"\n🎉 Success! Your EV Fleet Dashboard is ready!")
        print(f"🌐 URL: {dashboard_url}")
        print(f"\n📝 Next steps:")
        print(f"   1. Open the dashboard URL above")
        print(f"   2. Click 'Edit' to add visualizations")
        print(f"   3. Click 'Add from library' to add your charts")
        print(f"   4. Arrange and save your dashboard")
        print(f"\n🔄 The dashboard will auto-refresh every 5 seconds")
    else:
        print("❌ Failed to create dashboard")

if __name__ == "__main__":
    main() 