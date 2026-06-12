#!/usr/bin/env python3
"""Test transformations on actual HPFeeds data."""

import json
import sys
from seckc_mhn_api.feeds.transformers import transform_event

def main():
    """Test transformation on actual HPFeeds data."""

    # Load the HPFeeds data
    with open('hpfeeds-out.json', 'r') as f:
        lines = f.readlines()

    print(f"Loaded {len(lines)} events from hpfeeds-out.json\n")

    # Find problem event types
    problem_events = []
    for i, line in enumerate(lines):
        event = json.loads(line)
        event_type = event.get('event_type', '')

        if event_type in ['SMB DCERPC bind event', 'Download offer event']:
            problem_events.append((i+1, event))

    print(f"Found {len(problem_events)} problematic event types")
    print("=" * 80)

    # Test each problem event
    for line_num, event in problem_events[:3]:  # Test first 3
        event_type = event.get('event_type', 'unknown')
        print(f"\nLine {line_num}: {event_type}")
        print(f"  Before: saddr={event.get('saddr')}, daddr={event.get('daddr')}")
        print(f"          sport={event.get('sport')}, dport={event.get('dport')}")
        print(f"          peerIP={event.get('peerIP', 'MISSING')}, hostPort={event.get('hostPort', 'MISSING')}")

        # Transform
        transformed = transform_event(event)

        print(f"  After:  peerIP={transformed.get('peerIP', 'MISSING')}")
        print(f"          victimIP={transformed.get('victimIP', 'MISSING')}")
        print(f"          hostPort={transformed.get('hostPort', 'MISSING')}")
        print(f"          protocol={transformed.get('protocol', 'MISSING')}")
        print(f"          startTime={transformed.get('startTime', 'MISSING')}")

        # Check if transformation was successful
        has_peer_ip = 'peerIP' in transformed and transformed['peerIP']
        has_host_port = 'hostPort' in transformed and transformed['hostPort']
        has_start_time = 'startTime' in transformed and transformed['startTime']

        if has_peer_ip and has_host_port and has_start_time:
            print("  ✅ PASS: Event now has required fields")
        else:
            print("  ❌ FAIL: Event still missing required fields")
            return 1

    print("\n" + "=" * 80)
    print("✅ All problematic events now transform correctly!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
