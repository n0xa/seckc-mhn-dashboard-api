"""Stats module for retrieving attack statistics and analytics."""
import os
import json
import datetime
from pymongo import MongoClient
from flask import Blueprint, request, abort, jsonify
import requests
from seckc_mhn_api.config import SETTINGS
from seckc_mhn_api.auth.controllers import user_status
import certifi

STATS_MODULE = Blueprint('stats', __name__, url_prefix='/stats')

# MongoDB connection with error handling
try:
    mongo_host = os.environ.get('MONGO_HOST', 'localhost')
    mongo_port = int(os.environ.get('MONGO_PORT', 27017))
    database = os.environ.get('MONGO_DB', 'mnemosyne')
    
    dbconn = MongoClient(host=mongo_host, port=mongo_port, serverSelectionTimeoutMS=5000)
    db = dbconn[database]
    
    # Test connection
    dbconn.admin.command('ismaster')
    print(f"Connected to MongoDB at {mongo_host}:{mongo_port}")
    
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    db = None

# Updated URLs for CHN stack
CHN_ATTACKERS_URL = os.environ.get('CHN_ATTACKERS_URL', 'http://localhost:8000/api/top_attackers/')
CHN_ATTACKER_STATS_URL = os.environ.get('CHN_ATTACKER_STATS_URL', 'http://localhost:8000/api/attacker_stats/')

@STATS_MODULE.route("/attacks", methods=['GET'])
def getstats():
    """Get attack statistics from MongoDB."""
    if not db:
        return jsonify({"error": "Database connection unavailable"}), 500
    
    try:
        date_param = request.args.get('date', default=None, type=str)
        channel_param = request.args.get('channel', default=None, type=str)
        
        # Build MongoDB query
        query = {}
        if date_param:
            query['date'] = date_param
        if channel_param:
            query['channel'] = channel_param
            
        if not query:
            abort(400, 'Date or channel parameter required')
        
        results = list(db['daily_stats'].find(query))
        
        # Remove MongoDB ObjectId from results
        for result in results:
            if '_id' in result:
                del result['_id']
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error retrieving attack stats: {e}")
        return jsonify({"error": "Failed to retrieve attack statistics"}), 500

@STATS_MODULE.route("/attackers", methods=['GET'])
def getattackers():
    """Get top attackers from CHN server."""
    try:
        hours_ago = request.args.get('hours_ago', default=24, type=int)
        api_key = SETTINGS.get("chn", {}).get("apikey", SETTINGS.get("mhn", {}).get("apikey", ""))
        
        attacker_url = f"{CHN_ATTACKERS_URL}?hours_ago={hours_ago}&api_key={api_key}"
        
        top_attacker_request = requests.get(
            attacker_url, 
            verify=certifi.where(),
            timeout=30
        )
        top_attacker_request.raise_for_status()
        
        if top_attacker_request.status_code == 200:
            return jsonify(top_attacker_request.json())
        
        return jsonify({"error": "Failed to retrieve attackers"}), top_attacker_request.status_code
        
    except requests.RequestException as e:
        print(f"Attacker request failed: {e}")
        return jsonify({"error": "Failed to connect to CHN server"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@STATS_MODULE.route("/attacker/<ip>", methods=['GET'])
def getattackerstats(ip):
    """Get statistics for a specific attacker IP."""
    try:
        api_key = SETTINGS.get("chn", {}).get("apikey", SETTINGS.get("mhn", {}).get("apikey", ""))
        attacker_stat_url = f"{CHN_ATTACKER_STATS_URL}{ip}/?api_key={api_key}"
        
        attacker_request = requests.get(
            attacker_stat_url, 
            verify=certifi.where(),
            timeout=30
        )
        attacker_request.raise_for_status()
        
        if attacker_request.status_code == 200:
            return jsonify(attacker_request.json())
        
        return jsonify({"error": f"Failed to retrieve stats for {ip}"}), attacker_request.status_code
        
    except requests.RequestException as e:
        print(f"Attacker stats request failed: {e}")
        return jsonify({"error": "Failed to connect to CHN server"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500