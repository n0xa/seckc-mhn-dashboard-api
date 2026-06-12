"""HPFeeds event transformers for normalizing dionaea honeypot events.

This module transforms dionaea honeypot events into a standardized format
expected by the seckc-encom-boardroom WebGL visualization.

Dionaea events use field names like 'remote_host', 'saddr', 'daddr', but the
visualization expects 'peerIP', 'victimIP', 'hostPort', 'loggedin', etc.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def transform_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform dionaea honeypot events to visualization-expected format.

    This is the main entry point for event transformation. It detects the event type
    and applies the appropriate transformation function, then normalizes all timestamps
    to ISO 8601 format for consistency across all honeypot types.

    Args:
        event_data: Raw event dictionary from HPFeeds

    Returns:
        Transformed event dictionary with visualization-expected field names and normalized timestamps
    """
    # Make a copy to avoid modifying the original
    transformed = event_data.copy()

    # Detect event type and apply appropriate transformation
    event_type = event_data.get('event_type', '')

    if event_type == 'Dionaea connection event':
        transformed = transform_dionaea_connection(transformed)
    elif event_type == 'FTP login event':
        transformed = transform_ftp_login(transformed)
    elif event_type == 'MSSQL login event':
        transformed = transform_mssql_login(transformed)
    elif event_type == 'Download with file hash':
        transformed = transform_download(transformed)
    elif event_type == 'Download offer event':
        # Transform download offer events (saddr/daddr format)
        transformed = transform_generic_dionaea_event(transformed)
    elif event_type == 'SMB DCERPC bind event':
        # Transform SMB DCERPC bind events (saddr/daddr format)
        transformed = transform_generic_dionaea_event(transformed)
    elif 'remote_host' in event_data and 'connection_type' in event_data:
        # Raw dionaea.connections event (no event_type field)
        transformed = transform_raw_dionaea_connection(transformed)
    elif 'saddr' in event_data and 'md5' in event_data:
        # Raw dionaea.capture event (no event_type field)
        transformed = transform_raw_dionaea_capture(transformed)
    elif 'saddr' in event_data and 'daddr' in event_data:
        # Generic dionaea event with saddr/daddr fields (catch-all)
        transformed = transform_generic_dionaea_event(transformed)
    else:
        # Unknown/unsupported event - pass through unchanged
        logger.debug(f"Unknown event type, passing through: {event_type or 'no event_type'}")

    # Normalize ALL timestamp fields to ISO 8601 format (works for all honeypot types)
    # This ensures consistency across cowrie, dionaea, conpot, and future honeypots
    timestamp_fields = ['time', 'startTime', 'timestamp', 'created_at', 'updated_at', 'endTime']
    for field in timestamp_fields:
        if field in transformed and isinstance(transformed[field], str):
            transformed[field] = _normalize_timestamp(transformed[field])

    # Ensure startTime exists - use timestamp field (Unix) or current time as fallback
    if 'startTime' not in transformed or not transformed['startTime']:
        if 'timestamp' in transformed and isinstance(transformed['timestamp'], (int, float)):
            # Convert Unix timestamp to ISO 8601
            transformed['startTime'] = datetime.utcfromtimestamp(transformed['timestamp']).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        elif 'time' in transformed and transformed['time']:
            # Use the time field if available
            transformed['startTime'] = transformed['time']
        else:
            # Last resort: use current time
            transformed['startTime'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return transformed


def transform_dionaea_connection(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform CHN-enriched 'Dionaea connection event' to visualization format.

    Input example:
    {
        "event_type": "Dionaea connection event",
        "connection_type": "accept",
        "connection_transport": "tcp",
        "connection_protocol": "smbd",
        "remote_host": "192.168.1.121",
        "remote_port": 32882,
        "remote_hostname": "",
        "local_host": "172.18.0.2",
        "local_port": 445
    }

    Output format:
    {
        "peerIP": "192.168.1.121",
        "victimIP": "172.18.0.2",
        "peerPort": 32882,
        "hostPort": 445,
        "victimPort": 445,
        "connectionType": "accept",
        "protocol": "smbd (tcp)",
        ... (original fields preserved)
    }
    """
    # Map dionaea fields to visualization-expected fields
    if 'remote_host' in event_data:
        event_data['peerIP'] = event_data['remote_host']
        event_data['attackerIP'] = event_data['remote_host']  # Alternative field name

    if 'local_host' in event_data:
        event_data['victimIP'] = event_data['local_host']

    if 'remote_port' in event_data:
        event_data['peerPort'] = _ensure_int(event_data['remote_port'])

    if 'local_port' in event_data:
        port = _ensure_int(event_data['local_port'])
        event_data['hostPort'] = port
        event_data['victimPort'] = port

    # Build descriptive activity string
    if 'connection_type' in event_data:
        event_data['connectionType'] = event_data['connection_type']

    # Build protocol string with transport info
    protocol_parts = []
    if 'connection_protocol' in event_data:
        protocol_parts.append(event_data['connection_protocol'])
    if 'connection_transport' in event_data:
        protocol_parts.append(f"({event_data['connection_transport']})")
    if protocol_parts:
        event_data['protocol'] = ' '.join(protocol_parts)

    logger.debug(f"Transformed dionaea connection event: {event_data.get('peerIP')} -> {event_data.get('victimIP')}:{event_data.get('hostPort')}")

    return event_data


def transform_raw_dionaea_connection(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw dionaea.connections channel event (without CHN enrichment).

    This handles events directly from dionaea hpfeeds.py that don't have
    the 'event_type' field added by CHN middleware.

    Input matches transform_dionaea_connection() but without event_type field.
    """
    # Add event_type for consistency
    event_data['event_type'] = 'Dionaea connection event'

    # Use the same transformation logic
    return transform_dionaea_connection(event_data)


def transform_ftp_login(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform CHN-enriched 'FTP login event' to visualization format.

    Input example:
    {
        "event_type": "FTP login event",
        "time": "2025-10-19 06:31:07.300342 GMT +0000",
        "saddr": "192.168.1.121",
        "sport": "36476",
        "daddr": "172.18.0.2",
        "dport": "21",
        "username": "anonymous",
        "password": "IEUser@"
    }

    Output format adds:
    {
        "peerIP": "192.168.1.121",
        "victimIP": "172.18.0.2",
        "peerPort": 36476,
        "hostPort": 21,
        "victimPort": 21,
        "loggedin": ["anonymous", "IEUser@"],
        "connectionType": "FTP login",
        "startTime": "2025-10-19 06:31:07.300342 GMT +0000",
        "protocol": "ftp",
        ... (original fields preserved)
    }
    """
    # Map saddr/daddr fields to visualization-expected fields
    if 'saddr' in event_data:
        event_data['peerIP'] = event_data['saddr']
        event_data['attackerIP'] = event_data['saddr']

    if 'daddr' in event_data:
        event_data['victimIP'] = event_data['daddr']

    if 'sport' in event_data:
        event_data['peerPort'] = _ensure_int(event_data['sport'])

    if 'dport' in event_data:
        port = _ensure_int(event_data['dport'])
        event_data['hostPort'] = port
        event_data['victimPort'] = port

    # Map credentials to loggedin array format
    username = event_data.get('username', '')
    password = event_data.get('password', '')
    event_data['loggedin'] = [username, password]

    # Set connection type
    event_data['connectionType'] = 'FTP login'
    event_data['protocol'] = 'ftp'

    # Map time field to startTime (will be normalized to ISO 8601 by transform_event)
    if 'time' in event_data:
        event_data['startTime'] = event_data['time']

    logger.debug(f"Transformed FTP login event: {username}@{event_data.get('peerIP')}")

    return event_data


def transform_mssql_login(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform CHN-enriched 'MSSQL login event' to visualization format.

    Input example:
    {
        "event_type": "MSSQL login event",
        "time": "2025-10-19 06:31:12.009047 GMT +0000",
        "saddr": "192.168.1.121",
        "sport": "38388",
        "daddr": "172.18.0.2",
        "dport": "1433",
        "username": "",
        "password": ""
    }

    Output format adds:
    {
        "peerIP": "192.168.1.121",
        "victimIP": "172.18.0.2",
        "peerPort": 38388,
        "hostPort": 1433,
        "victimPort": 1433,
        "loggedin": ["", ""],
        "connectionType": "MSSQL login",
        "startTime": "2025-10-19 06:31:12.009047 GMT +0000",
        "protocol": "mssql",
        ... (original fields preserved)
    }
    """
    # Map saddr/daddr fields
    if 'saddr' in event_data:
        event_data['peerIP'] = event_data['saddr']
        event_data['attackerIP'] = event_data['saddr']

    if 'daddr' in event_data:
        event_data['victimIP'] = event_data['daddr']

    if 'sport' in event_data:
        event_data['peerPort'] = _ensure_int(event_data['sport'])

    if 'dport' in event_data:
        port = _ensure_int(event_data['dport'])
        event_data['hostPort'] = port
        event_data['victimPort'] = port

    # Map credentials to loggedin array format
    username = event_data.get('username', '')
    password = event_data.get('password', '')
    event_data['loggedin'] = [username, password]

    # Set connection type
    event_data['connectionType'] = 'MSSQL login'
    event_data['protocol'] = 'mssql'

    # Map time field to startTime (will be normalized to ISO 8601 by transform_event)
    if 'time' in event_data:
        event_data['startTime'] = event_data['time']

    logger.debug(f"Transformed MSSQL login event: {username}@{event_data.get('peerIP')}")

    return event_data


def transform_download(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform CHN-enriched 'Download with file hash' event to visualization format.

    Input example:
    {
        "event_type": "Download with file hash",
        "time": "2025-10-19 10:18:50.796478 GMT +0000",
        "saddr": "5.125.221.53",
        "sport": "64478",
        "daddr": "172.18.0.2",
        "dport": "445",
        "md5": "996c2b2ca30180129c69352a3a3515e4",
        "url": "",
        "action": "download",
        "status": "successful"
    }

    Output format adds:
    {
        "peerIP": "5.125.221.53",
        "victimIP": "172.18.0.2",
        "peerPort": 64478,
        "hostPort": 445,
        "victimPort": 445,
        "loggedin": ["malware", "996c2b2ca30180129c69352a3a3515e4"],
        "connectionType": "Malware download",
        "startTime": "2025-10-19 10:18:50.796478 GMT +0000",
        "protocol": "smb",
        ... (original fields preserved including md5, url, sha512)
    }
    """
    # Map saddr/daddr fields
    if 'saddr' in event_data:
        event_data['peerIP'] = event_data['saddr']
        event_data['attackerIP'] = event_data['saddr']

    if 'daddr' in event_data:
        event_data['victimIP'] = event_data['daddr']

    if 'sport' in event_data:
        event_data['peerPort'] = _ensure_int(event_data['sport'])

    if 'dport' in event_data:
        port = _ensure_int(event_data['dport'])
        event_data['hostPort'] = port
        event_data['victimPort'] = port

        # Infer protocol from port
        if port == 445 or port == 139:
            event_data['protocol'] = 'smb'
        elif port == 21:
            event_data['protocol'] = 'ftp'
        elif port == 80 or port == 8080:
            event_data['protocol'] = 'http'
        elif port == 443:
            event_data['protocol'] = 'https'

    # Create loggedin array with download indicator and MD5
    md5_hash = event_data.get('md5', 'unknown')
    event_data['loggedin'] = ['malware', md5_hash]

    # Set connection type
    event_data['connectionType'] = 'Malware download'

    # Map time field to startTime (will be normalized to ISO 8601 by transform_event)
    if 'time' in event_data:
        event_data['startTime'] = event_data['time']

    logger.debug(f"Transformed download event: {event_data.get('peerIP')} -> MD5: {md5_hash[:8]}...")

    return event_data


def transform_raw_dionaea_capture(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw dionaea.capture channel event (without CHN enrichment).

    This handles events directly from dionaea hpfeeds.py that publish to
    the 'dionaea.capture' channel without an 'event_type' field.

    Input matches transform_download() but without event_type field.
    """
    # Add event_type for consistency
    event_data['event_type'] = 'Download with file hash'

    # Use the same transformation logic
    return transform_download(event_data)


def transform_generic_dionaea_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform generic dionaea events with saddr/daddr fields to visualization format.

    This is a catch-all transformer for dionaea events that don't fit specific
    categories (like SMB DCERPC bind, Download offer, etc.) but still need to be
    displayed on the dashboard.

    Input example:
    {
        "event_type": "SMB DCERPC bind event",
        "time": "2025-10-20 17:54:49.620784 GMT +0000",
        "saddr": "179.189.193.130",
        "sport": "56728",
        "daddr": "172.18.0.2",
        "dport": "445",
        "smb_uuid": "4b324fc8-1670-01d3-1278-5a47bf6ee188",
        ...
    }

    Output format adds:
    {
        "peerIP": "179.189.193.130",
        "victimIP": "172.18.0.2",
        "peerPort": 56728,
        "hostPort": 445,
        "victimPort": 445,
        "startTime": "2025-10-20T17:54:49.620784Z",
        "protocol": "smb",
        ... (original fields preserved)
    }
    """
    # Map saddr/daddr fields to visualization-expected fields
    if 'saddr' in event_data:
        event_data['peerIP'] = event_data['saddr']
        event_data['attackerIP'] = event_data['saddr']

    if 'daddr' in event_data:
        event_data['victimIP'] = event_data['daddr']

    if 'sport' in event_data:
        event_data['peerPort'] = _ensure_int(event_data['sport'])

    if 'dport' in event_data:
        port = _ensure_int(event_data['dport'])
        event_data['hostPort'] = port
        event_data['victimPort'] = port

        # Infer protocol from port if not already set
        if 'protocol' not in event_data:
            if port == 445 or port == 139:
                event_data['protocol'] = 'smb'
            elif port == 21:
                event_data['protocol'] = 'ftp'
            elif port == 3306:
                event_data['protocol'] = 'mysql'
            elif port == 1433:
                event_data['protocol'] = 'mssql'
            elif port == 22:
                event_data['protocol'] = 'ssh'
            elif port == 23:
                event_data['protocol'] = 'telnet'
            elif port == 80 or port == 8080:
                event_data['protocol'] = 'http'
            elif port == 443:
                event_data['protocol'] = 'https'

    # Map time field to startTime (will be normalized to ISO 8601 by transform_event)
    if 'time' in event_data:
        event_data['startTime'] = event_data['time']

    # Set a generic connection type if not already set
    if 'connectionType' not in event_data:
        event_type = event_data.get('event_type', 'Unknown')
        if 'bind' in event_type.lower():
            event_data['connectionType'] = 'Protocol negotiation'
        elif 'offer' in event_type.lower():
            event_data['connectionType'] = 'Download offer'
        else:
            event_data['connectionType'] = event_type

    logger.debug(f"Transformed generic dionaea event: {event_data.get('event_type', 'unknown')} from {event_data.get('peerIP')}")

    return event_data


def _ensure_int(value: Any) -> int:
    """
    Ensure a value is an integer, converting strings if necessary.

    Dionaea sometimes publishes ports as strings, sometimes as integers.
    This helper function normalizes them to integers.

    Args:
        value: Port number as int or string

    Returns:
        Integer port number, or 0 if conversion fails
    """
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert port value to int: {value}")
        return 0


def _normalize_timestamp(timestamp_str: str) -> str:
    """
    Convert dionaea timestamp format to ISO 8601 format (matching Cowrie).

    Dionaea format: "2025-10-19 17:27:45.272665 GMT +0000"
    Cowrie format:  "2025-10-19T17:27:14.653401Z"

    Args:
        timestamp_str: Dionaea timestamp string

    Returns:
        ISO 8601 formatted timestamp string
    """
    if not timestamp_str:
        return timestamp_str

    # If already in ISO format, return as-is
    if 'T' in timestamp_str and timestamp_str.endswith('Z'):
        return timestamp_str

    try:
        # Remove " GMT +0000" suffix if present
        cleaned = timestamp_str.replace(' GMT +0000', '').replace(' GMT', '')

        # Replace space with 'T' and add 'Z' suffix
        iso_timestamp = cleaned.replace(' ', 'T') + 'Z'

        return iso_timestamp
    except Exception as e:
        logger.warning(f"Failed to normalize timestamp '{timestamp_str}': {e}")
        return timestamp_str


def get_transformation_stats() -> Dict[str, int]:
    """
    Get statistics about event transformations (placeholder for future metrics).

    Returns:
        Dictionary with transformation statistics
    """
    return {
        'total_transformed': 0,
        'dionaea_connection': 0,
        'ftp_login': 0,
        'mssql_login': 0,
        'download': 0,
        'passthrough': 0
    }
