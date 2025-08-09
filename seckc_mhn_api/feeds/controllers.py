"""Socket.IO handlers for real-time feed data."""
import json
from seckc_mhn_api.api_base import SOCKET_IO_APP
from seckc_mhn_api.auth.controllers import socket_user_status
from flask import request
from flask_socketio import join_room, emit

def sanitize_data(d):
    """Recursively sanitize data by removing sensitive fields."""
    if not isinstance(d, (dict, list)):
        return d
    if isinstance(d, list):
        return [sanitize_data(v) for v in d]
    return {k: sanitize_data(v) for k, v in d.items()
            if k not in {'hostIP', 'local_host', 'victimIP', 'password', 'secret'}}

@SOCKET_IO_APP.on('hpfeedevent')
def handle_hpfeed_event(data):
    """Handle incoming HPFeed events and broadcast to appropriate rooms."""
    try:
        if isinstance(data, str):
            parsed_data = json.loads(data)
        else:
            parsed_data = data
            
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
