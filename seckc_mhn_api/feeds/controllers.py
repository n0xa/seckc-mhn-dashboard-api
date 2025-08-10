"""Socket.IO handlers for real-time feed data."""
import json
import time
from collections import deque
from seckc_mhn_api.api_base import SOCKET_IO_APP
from seckc_mhn_api.auth.controllers import socket_user_status, user_status
from flask import request, Blueprint, jsonify
from flask_socketio import join_room, emit

# Create Blueprint for REST endpoints
FEEDS_MODULE = Blueprint('feeds', __name__, url_prefix='/feeds')

# In-memory cache for recent events (last 100 events, 5 minutes retention)
recent_events_cache = deque(maxlen=100)
EVENT_RETENTION_SECONDS = 300

def sanitize_data(d):
    """Recursively sanitize data by removing sensitive fields."""
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [sanitize_data(v) for v in d]
    return {k: sanitize_data(v) for k, v in d.items()
            if k not in {'hostIP', 'local_host', 'victimIP', 'secret'}}

def cache_event(event_data):
    """Cache event data with timestamp for REST API access."""
    cached_event = {
        'data': event_data,
        'timestamp': time.time(),
        'cached_at': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }
    recent_events_cache.append(cached_event)

def get_cached_events(authenticated=False, since=None):
    """Retrieve cached events, optionally filtered by timestamp."""
    current_time = time.time()
    events = []
    
    for cached_event in recent_events_cache:
        # Skip expired events
        if current_time - cached_event['timestamp'] > EVENT_RETENTION_SECONDS:
            continue
            
        # Skip events before 'since' timestamp
        if since and cached_event['timestamp'] <= since:
            continue
            
        event_data = cached_event['data']
        if not authenticated:
            event_data = sanitize_data(event_data)
            
        events.append({
            'event': event_data,
            'timestamp': cached_event['timestamp'],
            'cached_at': cached_event['cached_at']
        })
    
    return events

@SOCKET_IO_APP.on('hpfeedevent')
def handle_hpfeed_event(data):
    """Handle incoming HPFeed events and broadcast to appropriate rooms."""
    try:
        if isinstance(data, str):
            parsed_data = json.loads(data)
        else:
            parsed_data = data
            
        # Cache the event for REST API access
        cache_event(parsed_data)
        
        # Send full data to authenticated users
        emit('hpfeedevent', parsed_data, room='activeUsers')
        
        # Send sanitized data to anonymous users
        sanitized = sanitize_data(parsed_data)
        emit('hpfeedevent', sanitized, room='anonUsers')
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error in hpfeed event: {e}")
    except Exception as e:
        print(f"Error handling hpfeed event: {e}")

@SOCKET_IO_APP.on('connect')
@socket_user_status
def handle_user_connection():
    """Handle user connections and assign to appropriate rooms."""
    try:
        user_agent = request.headers.get("User-Agent", "").encode('utf-8')
        
        if getattr(request, 'user_active', False):
            print("Authenticated user connected")
            join_room("activeUsers")
        else:
            # Don't add bots/automated clients to anonymous room
            if not user_agent.startswith(b"python-requests"):
                print("Anonymous user connected")
                join_room("anonUsers")
                
    except Exception as e:
        print(f"Error handling user connection: {e}")

@SOCKET_IO_APP.on('disconnect')
def handle_disconnect():
    """Handle user disconnections."""
    print("User disconnected")

# REST API Endpoints

@FEEDS_MODULE.route("/events/recent", methods=['GET'])
@user_status
def get_recent_events():
    """Get recent HPFeed events via REST API."""
    try:
        # Get query parameters
        since = request.args.get('since', type=float)
        limit = request.args.get('limit', default=50, type=int)
        
        # Limit the limit to prevent abuse
        limit = min(limit, 100)
        
        # Check if user is authenticated
        authenticated = getattr(request, 'user_active', False)
        
        # Get cached events
        events = get_cached_events(authenticated=authenticated, since=since)
        
        # Apply limit
        events = events[-limit:] if limit else events
        
        return jsonify({
            'events': events,
            'count': len(events),
            'authenticated': authenticated,
            'server_time': time.time()
        })
        
    except Exception as e:
        print(f"Error retrieving recent events: {e}")
        return jsonify({'error': 'Failed to retrieve recent events'}), 500

@FEEDS_MODULE.route("/status", methods=['GET'])
def get_feed_status():
    """Get status of HPFeeds relay and recent events cache."""
    try:
        current_time = time.time()
        valid_events = sum(1 for event in recent_events_cache 
                          if current_time - event['timestamp'] <= EVENT_RETENTION_SECONDS)
        
        return jsonify({
            'status': 'active',
            'cached_events': len(recent_events_cache),
            'valid_events': valid_events,
            'retention_seconds': EVENT_RETENTION_SECONDS,
            'server_time': current_time
        })
        
    except Exception as e:
        print(f"Error getting feed status: {e}")
        return jsonify({'error': 'Failed to get feed status'}), 500

# Uncomment this route if we need to test the events pipeline
# @FEEDS_MODULE.route("/test/inject", methods=['POST'])
# def inject_test_event():
#     """Inject a test event for testing purposes (development only)."""
#     try:
#         import random
#         test_event = {
#             'channel': 'test',
#             'identifier': 'test-sensor',
#             'src_ip': f"192.168.1.{random.randint(1,254)}",
#             'dest_port': random.choice([22, 80, 443, 8080]),
#             'protocol': 'tcp',
#             'attack_type': random.choice(['ssh_bruteforce', 'web_scan', 'port_scan']),
#             'message': 'Test attack event for REST API validation'
#         }
#         
#         # Cache the test event
#         cache_event(test_event)
#         
#         return jsonify({
#             'message': 'Test event injected successfully',
#             'event': test_event,
#             'cached_events': len(recent_events_cache)
#         })
#         
#     except Exception as e:
#         print(f"Error injecting test event: {e}")
#         return jsonify({'error': 'Failed to inject test event'}), 500
