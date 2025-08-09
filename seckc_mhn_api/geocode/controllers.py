"""Geocode module for IP geolocation services."""
import os
import json
from pathlib import Path
from flask import Blueprint, request, jsonify
import requests
from seckc_mhn_api.config import SETTINGS
import geoip2.database
import geoip2.errors

GEOCODE_MODULE = Blueprint('geocode', __name__, url_prefix='/geocode')

# Path to GeoLite2 database
script_dir = Path(__file__).parent
geodatabase_path = script_dir / ".." / ".." / "geodatabase" / "GeoLite2-City.mmdb"

# Initialize GeoIP reader with error handling
reader = None
try:
    if geodatabase_path.exists():
        reader = geoip2.database.Reader(str(geodatabase_path))
        print(f"GeoIP database loaded: {geodatabase_path}")
    else:
        print(f"GeoIP database not found: {geodatabase_path}")
except Exception as e:
    print(f"Failed to load GeoIP database: {e}")

@GEOCODE_MODULE.route("/<ip>", methods=['GET'])
def geocode(ip):
    """Get geolocation data for an IP address."""
    if not reader:
        return jsonify({"error": "GeoIP database unavailable"}), 500
    
    try:
        response = reader.city(ip)
        return jsonify(response.raw)
    except geoip2.errors.AddressNotFoundError:
        return jsonify({"error": f"No geolocation data found for IP: {ip}"}), 404
    except Exception as e:
        print(f"Geocoding error for IP {ip}: {e}")
        return jsonify({"error": "Geocoding failed"}), 500

def geocodeinternal(ip):
    """Internal function for geocoding IPs."""
    if not reader:
        return {"error": "GeoIP database unavailable"}
    
    try:
        response = reader.city(ip)
        return response.raw
    except geoip2.errors.AddressNotFoundError:
        return {"error": f"No geolocation data found for IP: {ip}"}
    except Exception as e:
        print(f"Internal geocoding error for IP {ip}: {e}")
        return {"error": "Geocoding failed"}
