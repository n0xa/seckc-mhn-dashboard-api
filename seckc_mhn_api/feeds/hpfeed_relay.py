"""HPFeeds relay for connecting to CHN honeypot feeds."""
import sys
import os
import logging
import traceback
import json
import threading
import time
from seckc_mhn_api.config import SETTINGS

# Try to import socketIO_client, disable HPFeeds relay if not available
try:
    from socketIO_client import SocketIO, LoggingNamespace
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("socketIO_client not available, HPFeeds relay will be disabled")
    SOCKETIO_AVAILABLE = False
    SocketIO = None
    LoggingNamespace = None

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# HPFeeds configuration with fallbacks
HPFEEDS_CONFIG = SETTINGS.get("hpfeeds", {})
HOST = HPFEEDS_CONFIG.get("host", os.environ.get("HPFEEDS_HOST", "localhost"))
PORT = HPFEEDS_CONFIG.get("port", int(os.environ.get("HPFEEDS_PORT", "10000")))
CHANNELS = HPFEEDS_CONFIG.get("channels", os.environ.get("HPFEEDS_CHANNELS", "").split(","))
IDENT = HPFEEDS_CONFIG.get("user", os.environ.get("HPFEEDS_USER", ""))
SECRET = HPFEEDS_CONFIG.get("token", os.environ.get("HPFEEDS_SECRET", ""))

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
        logger.info(f'Connected to HPFeeds broker: {hpc.brokername}')

        # Create Socket.IO connection  
        socket_connection = SocketIO(SOCKETIO_HOST, SOCKETIO_PORT, LoggingNamespace)
        
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
                
                # Emit to Socket.IO
                socket_connection.emit('hpfeedevent', json.dumps(message_data))
                
                logger.debug(f"Forwarded message from {identifier} on channel {channel}")
                
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
            logger.info(f"Subscribing to channels: {CHANNELS}")
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
        logger.warning("socketIO_client not available, HPFeeds relay not started")
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
