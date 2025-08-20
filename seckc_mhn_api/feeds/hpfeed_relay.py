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

# Environment variables are loaded by uWSGI (env-file) or Docker Compose (env_file)
# No manual file reading required

# HPFeeds configuration with proper fallbacks (environment variables take precedence over SETTINGS values)
HPFEEDS_CONFIG = SETTINGS.get("hpfeeds", {})
HOST = os.environ.get("HPFEEDS_HOST") or HPFEEDS_CONFIG.get("host", "localhost")
PORT = int(os.environ.get("HPFEEDS_PORT") or HPFEEDS_CONFIG.get("port") or "10000")
CHANNELS_STR = os.environ.get("HPFEEDS_CHANNELS") or HPFEEDS_CONFIG.get("channels", "")
CHANNELS = CHANNELS_STR.split(",") if CHANNELS_STR else []
IDENT = os.environ.get("HPFEEDS_USER") or HPFEEDS_CONFIG.get("user", "")
SECRET = os.environ.get("HPFEEDS_SECRET") or HPFEEDS_CONFIG.get("token", "")

# Socket.IO connection settings
SOCKETIO_HOST = os.environ.get("SOCKETIO_HOST", "127.0.0.1")
SOCKETIO_PORT = int(os.environ.get("SOCKETIO_PORT", "5000"))

def main():
    """Main HPFeeds relay function."""
    try:
        import hpfeeds
        hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)

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
