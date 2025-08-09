# OpenBSD Deployment for SecKC MHN Dashboard API

This directory contains OpenBSD-specific configuration files and scripts for deploying the SecKC MHN Dashboard API as a system service.

## Files

- **`relayd.conf`** - Reverse proxy configuration for relayd with WebSocket support
- **`seckc_mhn_api`** - OpenBSD rc.d init script for system service management
- **`seckc_mhn_api_wrapper.sh`** - Service management wrapper script
- **`uwsgi.ini`** - uWSGI configuration for running the Flask application

## Installation

### 1. Create System User

```bash
# Create dedicated user for the API service
doas useradd -d /opt/chnserver/seckc-mhn-dashboard-api -s /sbin/nologin -c "SecKC MHN API" seckc
doas chown -R seckc:seckc /opt/chnserver/seckc-mhn-dashboard-api
```

### 2. Install Dependencies

```bash
# Install Python and required system packages
doas pkg_add python3 py3-pip py3-virtualenv

# Install optional packages for better performance
doas pkg_add pcre2 # for uWSGI PCRE support
```

### 3. Setup Virtual Environment and Dependencies

```bash
# Run the setup command
doas /opt/chnserver/seckc-mhn-dashboard-api/openbsd/seckc_mhn_api_wrapper.sh setup
```

### 4. Install System Service

```bash
# Copy the init script to the system directory
doas cp /opt/chnserver/seckc-mhn-dashboard-api/openbsd/seckc_mhn_api /etc/rc.d/

# Enable the service
doas rcctl enable seckc_mhn_api
```

### 5. Configure Environment Variables

Create `/etc/rc.conf.local` entries for configuration:

```bash
# Add to /etc/rc.conf.local
seckc_mhn_api_flags=""
export SECRET_KEY="$(openssl rand -hex 32)"
export CHN_AUTH_URL="http://localhost:8000/auth/me/"
export CHN_SENSOR_URL="http://localhost:8000/api/sensors/"
export CHN_ATTACKERS_URL="http://localhost:8000/api/top_attackers/"
export CHN_ATTACKER_STATS_URL="http://localhost:8000/api/attacker_stats/"
export MONGO_HOST="localhost"
export MONGO_PORT="27017"
export MONGO_DB="mnemosyne"
export HPFEEDS_HOST="localhost"
export HPFEEDS_PORT="10000"
```

### 6. Setup Reverse Proxy (Optional)

If you want to use relayd for reverse proxy and load balancing:

```bash
# Backup existing relayd configuration
doas cp /etc/relayd.conf /etc/relayd.conf.backup

# Copy SecKC API relayd configuration
doas cp /opt/chnserver/seckc-mhn-dashboard-api/openbsd/relayd.conf /etc/relayd.conf

# Enable and start relayd
doas rcctl enable relayd
doas rcctl start relayd
```

**Note:** The relayd configuration uses ports 8080 (HTTP) and 8443 (HTTPS) to avoid conflicts with CHN-Server. Modify as needed for your environment.

### 7. GeoIP Database

Download and install the GeoLite2 database:

```bash
# Create geodatabase directory
doas mkdir -p /opt/chnserver/seckc-mhn-dashboard-api/geodatabase

# Download GeoLite2-City database (requires MaxMind account)
# Visit: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
# Extract and place GeoLite2-City.mmdb in the geodatabase directory

doas chown seckc:seckc /opt/chnserver/seckc-mhn-dashboard-api/geodatabase/GeoLite2-City.mmdb
```

## Service Management

### Start/Stop/Restart Service

```bash
# Start the service
doas rcctl start seckc_mhn_api

# Stop the service
doas rcctl stop seckc_mhn_api

# Restart the service
doas rcctl restart seckc_mhn_api

# Check service status
doas rcctl check seckc_mhn_api
```

### Using the Wrapper Script

```bash
# Alternative service management using the wrapper script
doas /opt/chnserver/seckc-mhn-dashboard-api/openbsd/seckc_mhn_api_wrapper.sh start
doas /opt/chnserver/seckc-mhn-dashboard-api/openbsd/seckc_mhn_api_wrapper.sh stop
doas /opt/chnserver/seckc-mhn-dashboard-api/openbsd/seckc_mhn_api_wrapper.sh restart
doas /opt/chnserver/seckc-mhn-dashboard-api/openbsd/seckc_mhn_api_wrapper.sh status
```

## Configuration

### Environment Variables

The service supports configuration through environment variables:

- **`SECRET_KEY`** - Flask secret key for sessions (auto-generated if not set)
- **`CHN_AUTH_URL`** - CHN server authentication endpoint
- **`CHN_SENSOR_URL`** - CHN server sensor data endpoint  
- **`CHN_ATTACKERS_URL`** - CHN server attackers endpoint
- **`CHN_ATTACKER_STATS_URL`** - CHN server attacker statistics endpoint
- **`MONGO_HOST`** - MongoDB host (default: localhost)
- **`MONGO_PORT`** - MongoDB port (default: 27017)
- **`MONGO_DB`** - MongoDB database name (default: mnemosyne)
- **`HPFEEDS_HOST`** - HPFeeds broker host
- **`HPFEEDS_PORT`** - HPFeeds broker port
- **`HPFEEDS_USER`** - HPFeeds username
- **`HPFEEDS_SECRET`** - HPFeeds secret/token
- **`HPFEEDS_CHANNELS`** - Comma-separated list of HPFeeds channels

### YAML Configuration

Alternatively, configuration can be provided via YAML file at:
`$HOME/data/seckc_mhn_api/shared/config/settings.yaml`

### uWSGI Configuration

The uWSGI configuration can be customized by editing:
`/opt/chnserver/seckc-mhn-dashboard-api/uwsgi.ini`

## Networking

### Default Ports

- **API Service:** 5000 (localhost only)
- **Relayd HTTP:** 8080 
- **Relayd HTTPS:** 8443

### Firewall Configuration

If using pf firewall, add rules to allow access:

```bash
# Add to /etc/pf.conf
pass in quick on egress proto tcp to port { 8080 8443 }
pass out quick on lo0 proto tcp to port 5000
```

## Logs

Service logs are located at:
- **Application logs:** `/var/log/seckc-mhn-api/uwsgi.log`
- **System logs:** `/var/log/daemon` (via syslog)

## Troubleshooting

### Common Issues

1. **Service won't start:**
   - Check if CHN-Server is running: `nc -z localhost 8000`
   - Verify user permissions: `doas -u seckc ls /opt/chnserver/seckc-mhn-dashboard-api`
   - Check log files: `tail -f /var/log/seckc-mhn-api/uwsgi.log`

2. **WebSocket connections failing:**
   - Ensure relayd is configured correctly for WebSocket upgrades
   - Check that uWSGI is compiled with gevent support

3. **Database connection errors:**
   - Verify MongoDB is running: `doas rcctl check mongod`
   - Check MongoDB connection: `mongo --eval "db.stats()"`

4. **Missing GeoIP data:**
   - Download GeoLite2-City.mmdb from MaxMind
   - Verify file permissions: `ls -la /opt/chnserver/seckc-mhn-dashboard-api/geodatabase/`

### Debug Mode

To run in debug mode for troubleshooting:

```bash
# Stop the service
doas rcctl stop seckc_mhn_api

# Run manually with debug enabled
doas -u seckc sh -c 'cd /opt/chnserver/seckc-mhn-dashboard-api && DEBUG=true ./venv/bin/python run.py'
```

## Security Considerations

1. **Service User:** Runs as unprivileged `seckc` user
2. **Network Binding:** API binds only to localhost (127.0.0.1:5000)
3. **Reverse Proxy:** Use relayd for SSL termination and security headers
4. **Logs:** Ensure log directory has proper permissions (755)
5. **Secrets:** Use strong SECRET_KEY and secure HPFeeds credentials

## Integration with CHN Stack

The API integrates with the CHN stack as follows:

```
[Honeypots] → [HPFeeds Broker] → [Mnemosyne] → [MongoDB]
                     ↓               ↓
[CHN-Server:8000] ←→ [SecKC API:5000] ←→ [Dashboard]
                     ↓
              [WebSocket Clients]
```

Ensure all components are running and properly configured for full functionality.