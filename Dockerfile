FROM python:3.9-alpine
COPY requirements.txt ./

# Declare arguments with default values
ARG MEROSS_EMAIL=default_email@example.com
ARG MEROSS_PASSWORD=default_password
ARG INFLUXDB_URL=http://default-influxdb-url
ARG INFLUXDB_TOKEN=default_token
ARG INFLUXDB_ORG=default_org
ARG INFLUXDB_BUCKET=default_bucket
ARG API_BASE_URL=http://default-api-base-url

# Set environment variables from arguments or default values
ENV EMAIL=$MEROSS_EMAIL \
    PASSWORD=$MEROSS_PASSWORD \
    INFLUXDB_URL=$INFLUXDB_URL \
    INFLUXDB_TOKEN=$INFLUXDB_TOKEN \
    INFLUXDB_ORG=$INFLUXDB_ORG \
    INFLUXDB_BUCKET=$INFLUXDB_BUCKET \
    API_BASE_URL=$API_BASE_URL

# Install necessary system dependencies
RUN apk update && apk add --no-cache \
    gcc \
    libc-dev \
    libffi-dev

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY connector.py .
CMD python -u connector.py

# Health check
COPY healthcheck.py .
HEALTHCHECK --interval=30s --timeout=30s --retries=3 CMD python healthcheck.py
