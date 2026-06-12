FROM alpine:3.22

LABEL maintainer="n0xa"
LABEL name="seckc-mhn-dashboard-api"
LABEL version="2.2.0"
LABEL release="1"
LABEL summary="SecKC MHN Dashboard API server"
LABEL description="Dashboard API for SecKC MHN (Modern Honey Network) providing real-time honeypot data visualization"
LABEL authoritative-source-url="https://github.com/SecKC/chnserver"

# Install Python and build dependencies
RUN apk --no-cache add python3 python3-dev py3-pip gcc musl-dev git linux-headers

# Create virtual environment
RUN python3 -m venv /app
ENV PATH="/app/bin:$PATH"

# Set working directory
WORKDIR /opt/seckc-mhn-dashboard-api

# Copy requirements and install dependencies
COPY requirements.txt /opt/seckc-mhn-dashboard-api/
RUN pip install --upgrade pip setuptools wheel \
  && pip install -r requirements.txt

# Copy application code
COPY . /opt/seckc-mhn-dashboard-api/

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "run.py"]