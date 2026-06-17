# seckc-mhn-dashboard-api -- OpenBSD deployment

See `INSTALL.openbsd.md` at the repo root for full stack installation.
This directory contains the rc.d script and wrapper for this service only.

## Files

- `seckc_mhn_api` -- rc.d init script (copy to `/etc/rc.d/`)
- `seckc_mhn_api_wrapper.sh` -- venv activation wrapper (not used by rc.d directly)

## Quick reference

The rc.d script runs uWSGI directly from the venv:

```
daemon = /opt/chnserver/seckc-mhn-dashboard-api/venv/bin/uwsgi
daemon_flags = --ini /opt/chnserver/seckc-mhn-dashboard-api/uwsgi.ini --daemonize .../logs/uwsgi.log
daemon_user = chn
pexp = .*uwsgi.*seckc-mhn-dashboard-api.*
```

Service binds on `0.0.0.0:5000` (see `uwsgi.ini`). nginx is not configured
to proxy this port by default -- access it directly or add a `/seckcapi/`
location block to `/etc/nginx/conf.d/chn.conf`.

## Required env file

`/opt/chnserver/seckc-mhn-dashboard-api/seckc_mhn_api.env` must exist with:

```
HPFEEDS_HOST=localhost
HPFEEDS_PORT=10000
HPFEEDS_USER=<ident>
HPFEEDS_SECRET=<secret>
HPFEEDS_CHANNELS=cowrie.sessions,cowrie.commands,cowrie.logins,dionaea.connections,conpot.events
SOCKETIO_HOST=127.0.0.1
SOCKETIO_PORT=5000
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGO_DB=mnemosyne
```

Note: the env var is `MONGODB_HOST` (not `MONGO_HOST`). The stats controller
reads `MONGODB_HOST` with `MONGO_HOST` as a fallback.

## Notes

- uWSGI is not in requirements.txt -- install manually: `pip install uwsgi`
- Service user is `chn` (shared with all CHN stack services), not a dedicated `seckc` user
- No relayd config is provided; nginx handles reverse proxy for port 80 (CHN-Server)
