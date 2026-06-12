#!/usr/bin/env python3
"""
Test script for dionaea event transformers.

This script loads sample events from unsupported.json and tests the
transformation logic to ensure all dionaea events will be properly
formatted for the seckc-encom-boardroom visualization.
"""

import json
import sys
from pathlib import Path

# Add the seckc_mhn_api directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from seckc_mhn_api.feeds.transformers import transform_event


def test_transformations():
    """Test transformation of all events in unsupported.json"""

    # Load unsupported events
    unsupported_file = Path(__file__).parent / "unsupported.json"

    if not unsupported_file.exists():
        print(f"Error: {unsupported_file} not found")
        return False

    print(f"Loading events from {unsupported_file}")

    # Read events line by line (JSONL format)
    events = []
    with open(unsupported_file, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    print(f"Loaded {len(events)} events")

    # Count event types
    event_types = {}
    for event in events:
        event_type = event.get('event_type', 'no_event_type')
        event_types[event_type] = event_types.get(event_type, 0) + 1

    print("\nEvent type distribution:")
    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {event_type}: {count}")

    # Test transformations
    print("\n" + "="*80)
    print("TESTING TRANSFORMATIONS")
    print("="*80)

    success_count = 0
    failure_count = 0

    # Test one of each type
    tested_types = set()

    for i, event in enumerate(events):
        event_type = event.get('event_type', 'no_event_type')

        # Test one sample of each type
        if event_type in tested_types:
            continue

        tested_types.add(event_type)

        print(f"\n--- Testing {event_type} (event #{i+1}) ---")
        print(f"Input: {json.dumps(event, indent=2)[:200]}...")

        try:
            transformed = transform_event(event.copy())

            # Check if visualization-required fields are present
            has_ip = 'peerIP' in transformed or 'attackerIP' in transformed or 'remote_host' in transformed
            has_port = 'hostPort' in transformed or 'victimPort' in transformed
            has_activity = 'loggedin' in transformed or 'connectionType' in transformed

            print(f"\nTransformed successfully:")
            print(f"  ✓ Has IP field: {has_ip}")
            print(f"    - peerIP: {transformed.get('peerIP', 'N/A')}")
            print(f"    - victimIP: {transformed.get('victimIP', 'N/A')}")
            print(f"  ✓ Has port field: {has_port}")
            print(f"    - hostPort: {transformed.get('hostPort', 'N/A')}")
            print(f"  ✓ Has activity field: {has_activity}")
            print(f"    - connectionType: {transformed.get('connectionType', 'N/A')}")
            print(f"    - loggedin: {transformed.get('loggedin', 'N/A')}")

            if has_ip and (has_port or has_activity):
                success_count += 1
                print("  ✅ PASS: Event has minimum required fields for visualization")
            else:
                failure_count += 1
                print("  ⚠️  WARNING: Event may not display properly in visualization")

        except Exception as e:
            failure_count += 1
            print(f"  ❌ FAIL: Transformation error: {e}")
            import traceback
            traceback.print_exc()

    # Test all events for basic transformation (no errors)
    print("\n" + "="*80)
    print("BATCH TRANSFORMATION TEST (all events)")
    print("="*80)

    error_count = 0
    for i, event in enumerate(events):
        try:
            transformed = transform_event(event.copy())
        except Exception as e:
            error_count += 1
            print(f"Error transforming event #{i+1}: {e}")

    print(f"\nBatch test results:")
    print(f"  Total events: {len(events)}")
    print(f"  Successful transformations: {len(events) - error_count}")
    print(f"  Errors: {error_count}")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Event types tested: {len(tested_types)}")
    print(f"Successful tests: {success_count}")
    print(f"Failed tests: {failure_count}")
    print(f"Batch transformation errors: {error_count}")

    if failure_count == 0 and error_count == 0:
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = test_transformations()
    sys.exit(0 if success else 1)
