"""Sensors module for retrieving sensor location data."""
import os
import json
from flask import Blueprint, request, jsonify
import requests
from seckc_mhn_api.config import SETTINGS
import certifi
from seckc_mhn_api.geocode.controllers import geocodeinternal

SENSORS_MODULE = Blueprint('sensors', __name__, url_prefix='/sensors')

# Updated to use CHN server instead of old MHN server
CHN_SENSOR_URL = os.environ.get('CHN_SENSOR_URL', 'http://localhost:8000/api/sensor/')

@SENSORS_MODULE.route("/locations", methods=['GET'])
def sensors():
    """Get sensor locations with geocoding."""
    try:
        # Use CHN API endpoint instead of old MHN
        api_key = os.environ.get("CHN_APIKEY", SETTINGS.get("chn", {}).get("apikey", SETTINGS.get("mhn", {}).get("apikey", "")))
        
        headers = {
            'apikey': api_key
        }
        
        sensor_request = requests.get(
            CHN_SENSOR_URL, 
            headers=headers,
            verify=certifi.where(),
            timeout=30
        )
        sensor_request.raise_for_status()
        
        print(f"Sensor request status: {sensor_request.status_code}")
        
        if sensor_request.status_code == 200:
            response_json = sensor_request.json()
            sensor_json = []
            
            for sensor in response_json:
                try:
                    sensor_lookup = geocodeinternal(sensor.get("ip", ""))
                    if sensor_lookup and "traits" in sensor_lookup:
                        del sensor_lookup["traits"]
                    
                    # Flatten location structure for frontend compatibility
                    location_data = sensor_lookup
                    if sensor_lookup and "location" in sensor_lookup and isinstance(sensor_lookup["location"], dict):
                        # Extract latitude/longitude from nested structure
                        nested_location = sensor_lookup["location"]
                        if "latitude" in nested_location and "longitude" in nested_location:
                            location_data = dict(sensor_lookup)  # Copy the response
                            location_data["latitude"] = nested_location["latitude"]
                            location_data["longitude"] = nested_location["longitude"]
                    
                    sensor_json.append({
                        "sensor_data": sensor,
                        "location": location_data
                    })
                except Exception as e:
                    print(f"Error geocoding sensor {sensor.get('ip', 'unknown')}: {e}")
                    sensor_json.append({
                        "sensor_data": sensor,
                        "location": None
                    })
                    
            return jsonify(sensor_json)
        
        return jsonify({"error": "Failed to retrieve sensors"}), sensor_request.status_code
        
    except requests.RequestException as e:
        print(f"Sensor request failed: {e}")
        return jsonify({"error": "Failed to connect to CHN server"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500
