"""Auth module for handling authentication with CHN stack."""
import json
import os
from functools import wraps
from flask import Blueprint, request, jsonify
import requests
import certifi
from seckc_mhn_api.config import SETTINGS

AUTH_MODULE = Blueprint('auth', __name__, url_prefix='/auth')

# Updated to use CHN server instead of old MHN server
CHN_AUTH_URL = os.environ.get('CHN_AUTH_URL', 'http://localhost:8000/auth/me/')

@AUTH_MODULE.route("/me", methods=['GET'])
def auth_me():
    """Check authentication status via CHN server."""
    request_headers = dict(request.headers.items())
    
    if 'Cookie' in request_headers:
        headers = {
            "Cookie": request_headers["Cookie"],
            "Connection": "close", 
            "Accept": "application/json"
        }
        
        try:
            auth_request = requests.get(
                CHN_AUTH_URL, 
                headers=headers, 
                verify=certifi.where(),
                timeout=10
            )
            auth_request.raise_for_status()
            return auth_request.json()
            
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Auth request failed: {e}")
            return jsonify({"active": False})
    
    return jsonify({"active": False})

def user_status(f):
    """Decorator to check user authentication status."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_headers = dict(request.headers.items())
        
        if 'Cookie' in request_headers:
            headers = {
                "Cookie": request_headers["Cookie"],
                "Connection": "close", 
                "Accept": "application/json"
            }
            
            try:
                auth_request = requests.get(
                    CHN_AUTH_URL, 
                    headers=headers, 
                    verify=certifi.where(),
                    timeout=10
                )
                auth_request.raise_for_status()
                auth_response = auth_request.json()
                request.user_active = auth_response.get("active", False)
                
            except (requests.RequestException, json.JSONDecodeError) as e:
                print(f"Auth check failed: {e}")
                request.user_active = False
        else:
            request.user_active = False
            
        return f(*args, **kwargs)
    return decorated_function

def socket_user_status(f):
    """Decorator for socket authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_headers = dict(request.headers.items())
        
        if 'Accept-Language' in request_headers:
            headers = {
                "Cookie": request_headers["Accept-Language"].encode('utf-8'),
                "Connection": "close", 
                "Accept": "application/json"
            }
            
            try:
                auth_request = requests.get(
                    CHN_AUTH_URL,
                    headers=headers, 
                    verify=certifi.where(),
                    timeout=10
                )
                auth_request.raise_for_status()
                auth_response = auth_request.json()
                request.user_active = auth_response.get("active", False)
                
            except Exception as e:
                print(f"Socket auth check failed: {e}")
                request.user_active = False
        else:
            request.user_active = False
            
        return f(*args, **kwargs)
    return decorated_function
