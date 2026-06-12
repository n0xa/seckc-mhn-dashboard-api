#!/usr/bin/env python3
"""Test timestamp fallback for events without explicit timestamps."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from seckc_mhn_api.feeds.transformers import transform_event

# Test event similar to MySQL connection (no time field)
mysql_event = {
    "event_type": "Dionaea connection event",
    "connection_type": "accept",
    "connection_transport": "tcp",
    "connection_protocol": "mysqld",
    "remote_host": "206.168.34.222",
    "remote_port": 56789,
    "remote_hostname": "",
    "local_host": "172.18.0.2",
    "local_port": 3306,
    "timestamp": time.time(),  # Unix timestamp added by hpfeed_relay.py
    "identifier": "test-sensor",
    "channel": "dionaea.connections"
}

print("="*80)
print("TIMESTAMP FALLBACK TEST")
print("="*80)
print("\nTest: MySQL connection event (no 'time' field)")
print(f"Input event has 'time' field: {'time' in mysql_event}")
print(f"Input event has 'startTime' field: {'startTime' in mysql_event}")
print(f"Input event has 'timestamp' field (Unix): {'timestamp' in mysql_event}")

if 'timestamp' in mysql_event:
    print(f"  timestamp value: {mysql_event['timestamp']}")

transformed = transform_event(mysql_event.copy())

print(f"\nAfter transformation:")
print(f"Output has 'startTime' field: {'startTime' in transformed}")

if 'startTime' in transformed:
    print(f"  startTime value: {transformed['startTime']}")

    # Verify it's ISO 8601 format
    if 'T' in transformed['startTime'] and transformed['startTime'].endswith('Z'):
        print(f"  ✅ PASS: startTime is in ISO 8601 format")
        print(f"\nVisualization will display:")
        print(f"  {transformed.get('connectionType', 'N/A')}    {transformed.get('peerIP', 'N/A')}    {transformed.get('hostPort', 'N/A')}    {transformed['startTime']}")
        sys.exit(0)
    else:
        print(f"  ❌ FAIL: startTime is NOT in ISO 8601 format")
        sys.exit(1)
else:
    print(f"  ❌ FAIL: No startTime field created")
    sys.exit(1)
