"""Run SecKC MHN Dashboard API."""
import os
from seckc_mhn_api.api_base import APP, SOCKET_IO_APP

if __name__ == "__main__":
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting SecKC MHN API server on {host}:{port}")
    SOCKET_IO_APP.run(APP, host=host, port=port, debug=debug)
