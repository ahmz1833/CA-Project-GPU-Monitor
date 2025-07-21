#!/bin/bash

# GPU Monitor Grafana Startup Script
set -e

echo "🚀 Starting GPU Monitoring Grafana System"
echo "=========================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "💡 You can edit .env to customize Prometheus host/port settings"
else
    echo "✅ .env file exists"
fi

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Set defaults
PROMETHEUS_HOST=${PROMETHEUS_HOST:-localhost}
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}
GRAFANA_PORT=${GRAFANA_PORT:-3000}

echo ""
echo "🔧 Configuration:"
echo "   Prometheus: http://${PROMETHEUS_HOST}:${PROMETHEUS_PORT}"
echo "   Grafana:    http://localhost:${GRAFANA_PORT}"
echo "   Username:   ${GRAFANA_USER:-admin}"
echo "   Password:   ${GRAFANA_PASSWORD:-admin}"
echo ""

# Generate Prometheus datasource configuration
echo "🔧 Generating Prometheus datasource configuration..."
mkdir -p provisioning/datasources
cat > provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://${PROMETHEUS_HOST}:${PROMETHEUS_PORT}
    uid: prometheus
    isDefault: true
    editable: true
    basicAuth: false
    withCredentials: false
    jsonData:
      httpMethod: POST
      prometheusType: Prometheus
      cacheLevel: 'High'
      disableRecordingRules: false
      incrementalQuerying: false
    secureJsonFields: {}
EOF
echo "✅ Datasource configuration updated"
echo ""

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Start Grafana
echo "🐳 Starting Grafana..."
docker compose up -d

# Wait for startup
echo "⏳ Waiting for Grafana to start..."
sleep 10

# Check if Grafana is running
if docker compose ps | grep -q "Up"; then
    echo ""
    echo "🎉 Grafana is now running!"
    echo "================================================"
    echo ""
    echo "📊 Access your dashboards:"
    echo "   URL:      http://localhost:${GRAFANA_PORT}"
    echo "   Username: ${GRAFANA_USER:-admin}"
    echo "   Password: ${GRAFANA_PASSWORD:-admin}"
    echo ""
    echo "📈 Available Dashboards:"
    echo "   • GPU Overview Dashboard    - Essential metrics"
    echo "   • GPU Detailed Performance  - Advanced metrics"
    echo "   • GPU Alerts & Status      - Monitoring alerts"
    echo ""
    echo "🔍 Check status with:"
    echo "   docker compose ps"
    echo "   docker compose logs grafana"
    echo ""
    echo "🛑 Stop with:"
    echo "   docker compose down"
    echo ""
else
    echo "❌ Grafana failed to start. Check the logs:"
    echo "   docker compose logs grafana"
    exit 1
fi
