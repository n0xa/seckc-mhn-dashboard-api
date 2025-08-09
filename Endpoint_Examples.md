# SecKC MHN Dashboard API - Endpoint Examples

This document provides example curl commands to test the various API endpoints.

## Authentication & Status

Check API status:
```bash
curl http://localhost:5000/
```

Get authentication info (if no auth required):
```bash
curl http://localhost:5000/auth/status
```

## Sensor Data

List all sensors:
```bash
curl http://localhost:5000/sensors/
```

Get sensor statistics:
```bash
curl http://localhost:5000/sensors/stats
```

## Attack Statistics

Get general attack stats:
```bash
curl http://localhost:5000/stats/
```

Get top attackers:
```bash
curl http://localhost:5000/stats/attackers
```

Get stats for specific attacker IP:
```bash
curl http://localhost:5000/stats/attacker/1.2.3.4
```

Get attack timeline/hourly stats:
```bash
curl http://localhost:5000/stats/attacks
```

## Geolocation Data

Geocode an IP address:
```bash
curl http://localhost:5000/geocode/8.8.8.8
```

## Feeds

Get feed status (if HPFeeds is working):
```bash
curl http://localhost:5000/feeds/status
```

List available channels:
```bash
curl http://localhost:5000/feeds/channels
```

## Getting Started

Start by testing the basic API status:
```bash
curl http://localhost:5000/
```

Then explore the sensor and stats endpoints to see what data is available in your honeypot deployment.