#!/bin/ksh
# SecKC MHN Dashboard API wrapper for OpenBSD
# Simple launcher - let rc.d handle process management

cd /opt/chnserver/seckc-mhn-dashboard-api

# Activate virtual environment
. /opt/chnserver/seckc-mhn-dashboard-api/venv/bin/activate

# Launch uWSGI with configuration
exec ./venv/bin/uwsgi --ini uwsgi.ini
