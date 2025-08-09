"""Base API. Import all modules Here. Attach middleware."""
import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from seckc_mhn_api.config import SETTINGS

APP = Flask(__name__)
APP.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

CORS(APP, origins="*", allow_headers=["Content-Type", "Authorization", "Cookie"])
SOCKET_IO_APP = SocketIO(APP, cors_allowed_origins="*", logger=True, engineio_logger=True)

from seckc_mhn_api.auth.controllers import AUTH_MODULE
from seckc_mhn_api.geocode.controllers import GEOCODE_MODULE  
from seckc_mhn_api.stats.controllers import STATS_MODULE
from seckc_mhn_api.sensors.controllers import SENSORS_MODULE

import seckc_mhn_api.feeds.hpfeed_relay
seckc_mhn_api.feeds.hpfeed_relay.start()
import seckc_mhn_api.feeds.controllers

APP.register_blueprint(AUTH_MODULE)
APP.register_blueprint(GEOCODE_MODULE)
APP.register_blueprint(STATS_MODULE)  
APP.register_blueprint(SENSORS_MODULE)

@APP.after_request
def manage_security_headers(response):
    response.headers["Server"] = ""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

if __name__ == "__main__":
    SOCKET_IO_APP.run(APP, host='0.0.0.0', port=5000, debug=False)
