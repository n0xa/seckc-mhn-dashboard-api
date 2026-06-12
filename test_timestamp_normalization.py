#!/usr/bin/env python3
"""Test timestamp normalization across all event types."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from seckc_mhn_api.feeds.transformers import transform_event

# Test data with different timestamp formats
test_events = [
    {
        "name": "Dionaea FTP login",
        "event": {
            "event_type": "FTP login event",
            "time": "2025-10-19 06:31:07.300342 GMT +0000",
            "saddr": "192.168.1.121",
            "sport": "36476",
            "daddr": "172.18.0.2",
            "dport": "21",
            "username": "anonymous",
            "password": "test"
        }
    },
    {
        "name": "Dionaea MSSQL login",
        "event": {
            "event_type": "MSSQL login event",
            "time": "2025-10-19 06:31:12.009047 GMT +0000",
            "saddr": "192.168.1.121",
            "sport": "38388",
            "daddr": "172.18.0.2",
            "dport": "1433",
            "username": "sa",
            "password": "password"
        }
    },
    {
        "name": "Dionaea download",
        "event": {
            "event_type": "Download with file hash",
            "time": "2025-10-19 10:18:50.796478 GMT +0000",
            "saddr": "5.125.221.53",
            "sport": "64478",
            "daddr": "172.18.0.2",
            "dport": "445",
            "md5": "996c2b2ca30180129c69352a3a3515e4"
        }
    },
    {
        "name": "Cowrie session (already ISO 8601)",
        "event": {
            "event_type": "Cowrie session",
            "startTime": "2025-10-19T17:27:14.653401Z",
            "peerIP": "14.63.196.175",
            "hostPort": 22
        }
    }
]

print("="*80)
print("TIMESTAMP NORMALIZATION TEST")
print("="*80)

all_passed = True

for test in test_events:
    print(f"\n--- {test['name']} ---")
    original_time = test['event'].get('time') or test['event'].get('startTime', 'N/A')
    print(f"Input timestamp:  {original_time}")

    transformed = transform_event(test['event'].copy())

    # Check all possible timestamp fields
    output_times = {}
    for field in ['time', 'startTime', 'timestamp']:
        if field in transformed:
            output_times[field] = transformed[field]

    if output_times:
        for field, value in output_times.items():
            print(f"Output {field}:    {value}")

            # Check if it's ISO 8601 format (has 'T' and ends with 'Z')
            if 'T' in value and value.endswith('Z'):
                print(f"  ✅ PASS: ISO 8601 format")
            else:
                print(f"  ❌ FAIL: Not ISO 8601 format")
                all_passed = False
    else:
        print("  ℹ️  No timestamp fields in output")

print("\n" + "="*80)
if all_passed:
    print("✅ ALL TIMESTAMP TESTS PASSED")
    print("\nAll timestamps are now in ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffffZ)")
    print("This ensures consistency across Cowrie, Dionaea, and all future honeypots!")
else:
    print("❌ SOME TESTS FAILED")

sys.exit(0 if all_passed else 1)
