#!/usr/bin/env python3
"""
Quick EV Fleet Visualizations Creator
Creates basic visualizations that can be added to the dashboard
"""

import requests
import json

KIBANA_URL = "http://localhost:5601"

def create_basic_visualizations():
    """Create basic visualizations using simpler API calls"""
    
    headers = {
        "Content-Type": "application/json",
        "kbn-xsrf": "true"
    }
    
    # Get data view ID
    response = requests.get(f"{KIBANA_URL}/api/data_views", headers=headers)
    data_view_id = None
    
    if response.status_code == 200:
        data_views = response.json().get("data_view", [])
        for dv in data_views:
            if "ev-processed" in dv.get("title", ""):
                data_view_id = dv["id"]
                break
    
    if not data_view_id:
        print("❌ No data view found")
        return
    
    print(f"✅ Using data view: {data_view_id}")
    
    # Create a simple line chart for battery levels
    battery_viz = {
        "attributes": {
            "title": "🔋 EV Battery Levels",
            "type": "line",
            "params": {
                "grid": {"categoryLines": False, "style": {"color": "#eee"}},
                "categoryAxes": [{"id": "CategoryAxis-1", "type": "category", "position": "bottom", "show": True, "style": {}, "scale": {"type": "linear"}, "labels": {"show": True, "truncate": 100}, "title": {}}],
                "valueAxes": [{"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value", "position": "left", "show": True, "style": {}, "scale": {"type": "linear", "mode": "normal"}, "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100}, "title": {"text": "Battery Level"}}],
                "seriesParams": [{"show": True, "type": "line", "mode": "normal", "data": {"label": "Average battery.level", "id": "1"}, "valueAxis": "ValueAxis-1", "drawLinesBetweenPoints": True, "showCircles": True}],
                "addTooltip": True,
                "addLegend": True,
                "legendPosition": "right",
                "times": [],
                "addTimeMarker": False
            },
            "aggs": [
                {"id": "1", "enabled": True, "type": "avg", "schema": "metric", "params": {"field": "battery.level"}},
                {"id": "2", "enabled": True, "type": "date_histogram", "schema": "segment", "params": {"field": "timestamp", "interval": "auto", "customInterval": "2h", "min_doc_count": 1, "extended_bounds": {}}}
            ]
        },
        "references": [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index", "type": "index-pattern", "id": data_view_id}]
    }
    
    try:
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/visualization",
            headers=headers,
            json=battery_viz
        )
        
        if response.status_code in [200, 201]:
            viz_id = response.json()["id"]
            print(f"✅ Created Battery Chart (ID: {viz_id})")
        else:
            print(f"❌ Failed to create battery chart: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🎨 Creating Quick EV Visualizations...")
    create_basic_visualizations()
    print("\n🎯 Dashboard is ready at:")
    print("http://localhost:5601/app/dashboards#/view/edc72180-3fe0-11f0-8570-79c7981bd79a")

if __name__ == "__main__":
    main() 