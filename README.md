# SecKC MHN Dashboard API

## Overview

The SecKC MHN Dashboard API is a modernized Python Flask-based REST API that provides access to honeypot data, statistics, and real-time feeds from the CHN (Community Honeypot Network) stack. This API serves as an interface between the CHN infrastructure and dashboard applications.

## Architecture

The API is built using:
- **Flask 3.0.3** - Modern Python web framework
- **Flask-SocketIO 5.4.1** - Real-time WebSocket communication
- **MongoDB** - Attack data storage via Mnemosyne
- **HPFeeds3** - Honeypot feed protocol
- **GeoIP2** - IP geolocation services

## Configuration

### Environment Variables

```bash
# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=false
SECRET_KEY=your-secret-key

# CHN Stack Endpoints
CHN_AUTH_URL=http://localhost:8000/auth/me/
CHN_SENSOR_URL=http://localhost:8000/api/sensors/
CHN_ATTACKERS_URL=http://localhost:8000/api/top_attackers/
CHN_ATTACKER_STATS_URL=http://localhost:8000/api/attacker_stats/

# MongoDB Configuration
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=mnemosyne

# HPFeeds Configuration
HPFEEDS_HOST=localhost
HPFEEDS_PORT=10000
HPFEEDS_USER=your-username
HPFEEDS_SECRET=your-secret
HPFEEDS_CHANNELS=dionaea.capture,cowrie.sessions,conpot.events

# Socket.IO Configuration
SOCKETIO_HOST=127.0.0.1
SOCKETIO_PORT=5000
```

### Configuration File

The API also supports YAML configuration at `$HOME/data/seckc_mhn_api/shared/config/settings.yaml`:

```yaml
hpfeeds:
  host: "localhost"
  port: 10000
  channels: ["dionaea.capture", "cowrie.sessions", "conpot.events"]
  user: "your-username"
  token: "your-secret"

mnemosyne:
  username: "admin"
  password: "password"

chn:
  apikey: "your-api-key"

# Legacy MHN compatibility
mhn:
  apikey: "legacy-api-key"
```

## API Endpoints

### Authentication

#### GET /auth/me
**Description**: Check authentication status via CHN server  
**Parameters**: None (uses Cookie header)  
**Response**:
```json
{
  "active": true,
  "user": "username",
  "role": "admin"
}
```

**CHN Stack Integration**: Forwards authentication requests to CHN server's auth endpoint.

---

### Sensor Management

#### GET /sensors/locations  
**Description**: Get sensor locations with geocoding data  
**Parameters**: None  
**Response**:
```json
[
  {
    "sensor_data": {
      "id": 1,
      "name": "sensor-01",
      "ip": "192.168.1.100",
      "hostname": "honeypot-01",
      "uuid": "550e8400-e29b-41d4-a716-446655440000"
    },
    "location": {
      "country": {
        "iso_code": "US",
        "name": "United States"
      },
      "city": {
        "name": "Kansas City"  
      },
      "location": {
        "latitude": 39.0997,
        "longitude": -94.5786
      }
    }
  }
]
```

**CHN Stack Integration**: Retrieves sensor data from CHN server and enriches with geolocation.

---

### Statistics & Analytics

#### GET /stats/attacks
**Description**: Get attack statistics from MongoDB  
**Parameters**:
- `date` (string, optional): Filter by date (YYYY-MM-DD format)
- `channel` (string, optional): Filter by HPFeeds channel

**Response**:
```json
[
  {
    "date": "2024-01-15",
    "channel": "dionaea.capture",
    "attack_count": 150,
    "unique_attackers": 45,
    "countries": ["CN", "RU", "US"],
    "top_ports": [22, 80, 443, 23]
  }
]
```

**CHN Stack Integration**: Queries Mnemosyne MongoDB for preprocessed attack statistics.

#### GET /stats/attackers
**Description**: Get top attackers from CHN server  
**Parameters**:
- `hours_ago` (integer, optional): Time window in hours (default: 24)

**Response**:
```json
[
  {
    "source_ip": "1.2.3.4",
    "attack_count": 50,
    "first_seen": "2024-01-15T10:00:00Z",
    "last_seen": "2024-01-15T15:30:00Z",
    "countries": ["CN"],
    "honeypots_targeted": ["sensor-01", "sensor-02"]
  }
]
```

**CHN Stack Integration**: Forwards requests to CHN server's top attackers endpoint.

#### GET /stats/attacker/&lt;ip&gt;
**Description**: Get detailed statistics for a specific attacker IP  
**Parameters**:
- `ip` (string): IP address to analyze

**Response**:
```json
{
  "source_ip": "1.2.3.4",
  "total_attacks": 150,
  "attack_timeline": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "honeypot": "sensor-01",
      "port": 22,
      "protocol": "ssh"
    }
  ],
  "geolocation": {
    "country": "China",
    "city": "Beijing"
  },
  "threat_intel": {
    "malware_families": ["mirai", "gafgyt"],
    "attack_methods": ["brute_force", "exploit"]
  }
}
```

**CHN Stack Integration**: Retrieves detailed attacker data from CHN server.

---

### Geolocation Services

#### GET /geocode/&lt;ip&gt;
**Description**: Get geolocation data for an IP address  
**Parameters**:
- `ip` (string): IP address to geolocate

**Response**:
```json
{
  "country": {
    "iso_code": "US",
    "name": "United States"
  },
  "subdivisions": [
    {
      "iso_code": "MO", 
      "name": "Missouri"
    }
  ],
  "city": {
    "name": "Kansas City"
  },
  "location": {
    "latitude": 39.0997,
    "longitude": -94.5786,
    "accuracy_radius": 50
  },
  "postal": {
    "code": "64111"
  }
}
```

**CHN Stack Integration**: Provides IP geolocation services for enriching honeypot data.

---

## Real-time WebSocket Events

### Connection Handling

The API uses Socket.IO for real-time communication with two room types:

- **activeUsers**: Authenticated users receive full event data
- **anonUsers**: Anonymous users receive sanitized event data (sensitive fields removed)

### Events

#### hpfeedevent
**Description**: Real-time honeypot attack data  
**Data Structure**:
```json
{
  "identifier": "sensor-01",
  "channel": "dionaea.capture", 
  "timestamp": 1642251600.123,
  "src_ip": "1.2.3.4",
  "src_port": 54321,
  "dst_ip": "192.168.1.100",
  "dst_port": 22,
  "protocol": "tcp",
  "data": {
    "username": "admin",
    "password": "password123",
    "session": "ssh-session-data"
  }
}
```

**Note**: Anonymous users receive sanitized data with sensitive fields (hostIP, local_host, victimIP, password, secret) removed.

## CHN Stack Integration

### Authentication Flow

1. Client sends request with cookie/token
2. API forwards auth check to CHN server 
3. CHN server validates and returns user status
4. API decorates request with user permissions

### Data Flow

1. **Honeypots** → HPFeeds broker → **HPFeeds Relay** → Socket.IO → **Dashboard**
2. **CHN Server** → API endpoints → **Dashboard**  
3. **Mnemosyne** → MongoDB → API queries → **Dashboard**

### Deployment Architecture

```
[Honeypots] → [HPFeeds Broker] → [Mnemosyne] → [MongoDB]
                     ↓
[CHN Server] ← → [SecKC API] ← → [Dashboard]
                     ↓
              [Socket.IO Clients]
```

## Security Features

### Data Sanitization
- Removes sensitive fields from anonymous WebSocket feeds
- Validates and sanitizes all user inputs
- Implements proper error handling without information disclosure

### HTTP Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` 
- `X-XSS-Protection: 1; mode=block`
- `Server: ""` (hides server information)

### Authentication
- Cookie-based authentication via CHN server
- User role verification for sensitive operations
- Request timeout protection (30 seconds)

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Descriptive error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (missing/invalid parameters)
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable (database/external service down)

## Installation & Deployment

### Requirements
```bash
pip install -r requirements.txt
```

### Running the API
```bash
# Development
python run.py

# Production with Gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 run:APP
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```

### Compatibility
- Maintains backward compatibility with existing dashboard implementations
- Supports both legacy MHN and new CHN configuration options
- API response formats remain consistent

## Testing

### Manual Testing
```bash
# Test authentication
curl -X GET http://localhost:5000/auth/me

# Test sensor locations  
curl -X GET http://localhost:5000/sensors/locations

# Test attack statistics
curl -X GET "http://localhost:5000/stats/attacks?date=2024-01-15"

# Test geocoding
curl -X GET http://localhost:5000/geocode/8.8.8.8
```

### WebSocket Testing
```javascript
// Connect to Socket.IO
const socket = io('http://localhost:5000');

// Listen for honeypot events
socket.on('hpfeedevent', (data) => {
  console.log('Attack data:', data);
});
```

## Support & Troubleshooting

### Common Issues

1. **MongoDB Connection Errors**: Verify MONGO_HOST and credentials
2. **HPFeeds Not Connecting**: Check HPFEEDS_* environment variables  
3. **GeoIP Database Missing**: Ensure GeoLite2-City.mmdb exists in geodatabase/
4. **Authentication Failures**: Verify CHN_AUTH_URL is accessible

### Logging

Enable debug logging:
```bash
export DEBUG=true
python run.py
```

Log locations:
- Application logs: stdout/stderr
- MongoDB logs: MongoDB server logs  
- HPFeeds logs: Application logs with "HPFeeds" prefix
