"""HPFeeds relay for connecting to CHN honeypot feeds."""
import sys
import os
import logging
import traceback
import json
import threading
import time
from seckc_mhn_api.config import SETTINGS

# Try to import socketio (modern python-socketio), disable HPFeeds relay if not available
try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("python-socketio not available, HPFeeds relay will be disabled")
    SOCKETIO_AVAILABLE = False
    socketio = None

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Load environment variables manually from .env file since uWSGI env-file isn't working
def load_env_file(env_file_path):
    """Load environment variables from file."""
    env_vars = {}
    try:
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
        return env_vars
    except Exception as e:
        logger.error(f"Failed to load environment file {env_file_path}: {e}")
        return {}

# Load environment variables
env_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'seckc_mhn_api.env')
env_vars = load_env_file(env_file_path)

# HPFeeds configuration with proper fallbacks (environment variables take precedence over empty SETTINGS values)
HPFEEDS_CONFIG = SETTINGS.get("hpfeeds", {})
HOST = HPFEEDS_CONFIG.get("host") or os.environ.get("HPFEEDS_HOST", "localhost")
PORT = HPFEEDS_CONFIG.get("port") or int(os.environ.get("HPFEEDS_PORT", "10000"))
CHANNELS_STR = HPFEEDS_CONFIG.get("channels") or os.environ.get("HPFEEDS_CHANNELS", "")
CHANNELS = CHANNELS_STR.split(",") if CHANNELS_STR else []
IDENT = HPFEEDS_CONFIG.get("user") or os.environ.get("HPFEEDS_USER", "")
SECRET = HPFEEDS_CONFIG.get("token") or os.environ.get("HPFEEDS_SECRET", "")

# Socket.IO connection settings
SOCKETIO_HOST = os.environ.get("SOCKETIO_HOST", "127.0.0.1")
SOCKETIO_PORT = int(os.environ.get("SOCKETIO_PORT", "5000"))

def main():
    """Main HPFeeds relay function."""
    try:
        # Try to import hpfeeds3 first, fall back to hpfeeds
        try:
            import hpfeeds3
            hpc = hpfeeds3.new(HOST, PORT, IDENT, SECRET)
        except ImportError:
            try:
                import hpfeeds
                hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
            except ImportError:
                logger.error("Neither hpfeeds3 nor hpfeeds available")
                return 1

        # Import cache_event and emit functions to directly communicate with controllers
        from seckc_mhn_api.feeds.controllers import cache_event, sanitize_data
        from seckc_mhn_api.api_base import SOCKET_IO_APP
        
        def on_message(identifier, channel, payload):
            """Handle incoming HPFeeds messages."""
            try:
                # Parse payload
                if isinstance(payload, bytes):
                    payload = payload.decode('utf-8', errors='ignore')
                
                message_data = json.loads(str(payload))
                message_data['identifier'] = identifier
                message_data['channel'] = channel
                message_data['timestamp'] = time.time()
                
                # Cache the event directly and emit via Socket.IO app
                cache_event(message_data)
                SOCKET_IO_APP.emit('hpfeedevent', message_data, room='activeUsers')
                SOCKET_IO_APP.emit('hpfeedevent', sanitize_data(message_data), room='anonUsers')
                
            except json.JSONDecodeError as e:
                logger.error(f'JSON decode error for message from {identifier}: {e}')
            except Exception as e:
                logger.error(f'Error forwarding message from {identifier}: {e}')
                traceback.print_exc()

        def on_error(payload):
            """Handle HPFeeds errors."""
            logger.error(f'HPFeeds error: {payload}')
            hpc.stop()

        # Subscribe to channels and start processing
        if CHANNELS and CHANNELS[0]:  # Check if channels are configured
            hpc.subscribe(CHANNELS)
            hpc.run(on_message, on_error)
        else:
            logger.warning("No HPFeeds channels configured")
            
        hpc.close()
        return 0
        
    except ImportError:
        logger.error("hpfeeds3 not available, falling back to basic operation")
        return 1
    except Exception as e:
        logger.error(f"HPFeeds relay error: {e}")
        traceback.print_exc()
        return 1

def start():
    """Start HPFeeds relay in daemon thread."""
    if not SOCKETIO_AVAILABLE:
        logger.warning("python-socketio not available, HPFeeds relay not started")
        return
        
    if not all([HOST, PORT, IDENT, SECRET]):
        logger.warning("HPFeeds configuration incomplete, relay not started")
        return
        
    relay_thread = threading.Thread(target=main, name="HPFeedsRelay")
    relay_thread.daemon = True
    relay_thread.start()
    logger.info("HPFeeds relay started")

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("HPFeeds relay stopped by user")
        sys.exit(0)
