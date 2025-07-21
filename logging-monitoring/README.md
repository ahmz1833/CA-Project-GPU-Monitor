# GPU Monitoring Stack (Prometheus + AlertManager)

A production-ready monitoring and alerting system for GPU infrastructure using Prometheus for metrics collection and AlertManager for intelligent alerting with email notifications.

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GPU Core API  │◄───┤   Prometheus     │◄───┤   AlertManager  │
│   (Port 9555)   │    │   (Port 9090)    │    │   (Port 9093)   │
│                 │    │                  │    │                 │
│ • NVML Method   │    │ • Scrapes Metrics│    │ • Email Alerts  │
│ • Bash Method   │    │ • Stores TSDB    │    │ • Smart Routing │
│ • Sim Method    │    │ • Alert Rules    │    │ • Grouping      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐     ┌─────────────────┐
                       │    Grafana      │     │   Email/Slack   │
                       │  Visualization  │     │  Notifications  │
                       └─────────────────┘     └─────────────────┘
```

---

## 🚀 Features

### Prometheus
- **Multi-Method Support**: Scrapes GPU metrics via NVML, Bash, and Simulation
- **Time-Series Storage**: Efficient storage for historical analysis
- **Alert Rule Engine**: Configurable thresholds and conditions
- **Service Discovery**: Automatic GPU detection and monitoring
- **Health Checks**: Built-in monitoring system health verification

### AlertManager
- **Smart Routing**: Different severity levels (Emergency, Critical, Warning)
- **Email Notifications**: Rich HTML email alerts with GPU details
- **Alert Grouping**: Prevents notification spam
- **Resolve Notifications**: Automatically notifies when issues are resolved
- **Rate Limiting**: Configurable repeat intervals

### Monitoring Capabilities
- **Temperature Monitoring**: Critical (>80°C), Emergency (>85°C)
- **Fan Speed Alerts**: Critical Low (<500 RPM), Warning High (>9000 RPM)
- **Power Consumption**: High power usage alerts (>350W)
- **Memory Usage**: High memory utilization warnings (>90%)
- **GPU Utilization**: Extended high usage alerts (>95% for 15min)
- **Health Status**: GPU health issue detection

---

## 📋 Prerequisites

- Docker and Docker Compose
- GPU Core API running on port 9555
- SMTP server access for email alerts (Gmail, Outlook, etc.)

---

## 🔧 Setup & Configuration

### 1. Environment Configuration

Copy and configure environment variables:

```bash
cp .env.example .env
nano .env
```

Configure the following in `.env`:

```bash
# Prometheus Configuration
PROMETHEUS_PORT=9090

# AlertManager Configuration  
ALERTMANAGER_PORT=9093

# Email Configuration for Alerts
SMTP_HOST=smtp.gmail.com:587           # Your SMTP server
SMTP_FROM=gpu-monitoring@yourdomain.com # Sender email
SMTP_USER=your-email@gmail.com         # SMTP username
SMTP_PASS=your-app-password            # SMTP password/app-password
EMAIL_TO=admin@yourdomain.com          # Alert recipient

# Monitoring Configuration
SCRAPE_INTERVAL=10s
EVALUATION_INTERVAL=15s
LOG_LEVEL=info
```

### 2. Email Setup (Gmail Example)

For Gmail, you need an App Password:

1. Enable 2-Factor Authentication on your Google Account
2. Go to Google Account Settings → Security → App Passwords
3. Generate an App Password for "Mail"
4. Use this App Password in `SMTP_PASS`

### 3. Start the Monitoring Stack

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Verify Services

- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **GPU Metrics**: http://localhost:9090/targets (should show GPU endpoints as UP)

---

## 📊 Alert Rules Configuration

### Current Alert Rules (`prometheus/rules/gpu_alerts.yml`)

| Alert | Condition | Severity | Duration |
|-------|-----------|----------|----------|
| **GPUHighTemperature** | temp > 80°C | Critical | 5m |
| **GPUVeryHighTemperature** | temp > 85°C | Emergency | 1m |
| **GPUCriticalLowFanSpeed** | fan < 500 RPM | Critical | 2m |
| **GPUHighFanSpeed** | fan > 9000 RPM | Warning | 5m |
| **GPUHighPowerConsumption** | power > 350W | Warning | 10m |
| **GPUHighUtilization** | util > 95% | Warning | 15m |
| **GPUHighMemoryUsage** | memory > 90% | Warning | 10m |
| **GPUHealthIssue** | health > 1 | Warning | 2m |

### Adding Custom Rules

Edit `prometheus/rules/gpu_alerts.yml`:

```yaml
- alert: YourCustomAlert
  expr: gpu_temperature_celsius > 75
  for: 3m
  labels:
    severity: warning
    service: gpu-monitoring
  annotations:
    summary: "Custom GPU Alert"
    description: "GPU {{ $labels.gpu_name }} temperature {{ $value }}°C"
```

Reload configuration:
```bash
docker-compose restart prometheus
```

---

## 📧 Email Alert Examples

### Critical Temperature Alert
```
🚨 CRITICAL GPU Monitor Alert

GPU Temperature Critical
Description: GPU RTX 4090 (0) temperature is 82.5°C, which is above the critical threshold of 80°C
Severity: critical
GPU: RTX 4090 (Index: 0)
Started: 2024-01-15T14:30:45Z
Status: firing
```

### Fan Speed Warning
```
⚠️ GPU Monitor Warning

GPU High Fan Speed Warning
Description: GPU RTX 3080 (1) fan speed is 9200 RPM, indicating high thermal load or cooling system stress
GPU: RTX 3080 (Index: 1)
Started: 2024-01-15T14:25:12Z
```

---

## 🛠️ Maintenance & Operations

### View Active Alerts
```bash
# Check AlertManager web interface
open http://localhost:9093

# Check Prometheus alerts
open http://localhost:9090/alerts
```

### Service Management
```bash
# Stop services
docker-compose down

# Update and restart
docker-compose down
docker-compose pull
docker-compose up -d

# View specific service logs
docker-compose logs prometheus
docker-compose logs alertmanager
```

### Backup Configuration
```bash
# Backup Prometheus data
docker run --rm -v logging-monitoring_prometheus_data:/data \
  -v $(pwd)/backup:/backup alpine \
  tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /data

# Backup AlertManager data  
docker run --rm -v logging-monitoring_alertmanager_data:/data \
  -v $(pwd)/backup:/backup alpine \
  tar czf /backup/alertmanager-$(date +%Y%m%d).tar.gz /data
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. GPU Metrics Not Appearing
```bash
# Check if Core API is running
curl http://localhost:9555/gpu/metric?method=sim

# Check Prometheus targets
open http://localhost:9090/targets

# View Prometheus logs
docker-compose logs prometheus
```

#### 2. Email Alerts Not Sending
```bash
# Check AlertManager logs
docker-compose logs alertmanager

# Test email configuration
docker-compose exec alertmanager \
  amtool config show --config.file=/etc/alertmanager/alertmanager.yml
```

#### 3. Alert Rules Not Loading
```bash
# Validate alert rules syntax
docker-compose exec prometheus \
  promtool check rules /etc/prometheus/rules/gpu_alerts.yml

# Check rule evaluation
open http://localhost:9090/rules
```

### Health Checks
```bash
# Check all container health
docker-compose ps

# Manual health check
curl http://localhost:9090/-/healthy
curl http://localhost:9093/-/healthy
```

---

## 📈 Integration with Grafana

This monitoring stack integrates seamlessly with Grafana:

1. **Add Prometheus Data Source**: http://prometheus:9090
2. **Import GPU Dashboards**: Use dashboards from `../grafana/dashboards/`
3. **Alert Annotations**: View alert firings directly on graphs
4. **Custom Panels**: Create panels using the collected metrics

---

## 🔒 Security Considerations

- **Network Security**: Use Docker networks for service isolation
- **SMTP Credentials**: Store email credentials securely in `.env`
- **Access Control**: Consider adding authentication to Prometheus/AlertManager
- **TLS/SSL**: Configure TLS for production email sending
- **Firewall**: Restrict access to monitoring ports if needed

---

## 📚 Metrics Reference

### Available Metrics

| Metric | Description | Type | Labels |
|--------|-------------|------|--------|
| `gpu_power_watts` | GPU power consumption | Gauge | gpu_uuid, gpu_index, gpu_name |
| `gpu_temperature_celsius` | GPU core temperature | Gauge | gpu_uuid, gpu_index, gpu_name |
| `gpu_fan_speed` | Fan speed in RPM | Gauge | gpu_uuid, gpu_index, gpu_name |
| `gpu_utilization_percent` | GPU compute utilization | Gauge | gpu_uuid, gpu_index, gpu_name |
| `gpu_memory_usage_percent` | GPU memory usage | Gauge | gpu_uuid, gpu_index, gpu_name |
| `gpu_clock_mhz` | GPU core clock frequency | Gauge | gpu_uuid, gpu_index, gpu_name |
| `gpu_memory_clock_mhz` | Memory clock frequency | Gauge | gpu_uuid, gpu_index, gpu_name |
| `gpu_health_status` | Health status (0-4) | Gauge | gpu_uuid, gpu_index, gpu_name |

### Query Examples

```promql
# Average temperature across all GPUs
avg(gpu_temperature_celsius)

# GPUs running hot (>75°C)
gpu_temperature_celsius > 75

# Total power consumption
sum(gpu_power_watts)

# High utilization GPUs
gpu_utilization_percent > 80

# Memory usage by GPU
gpu_memory_usage_percent by (gpu_name)
```

---

## 🤝 Related Components

- **GPU Core API**: Provides the metrics endpoint
- **SQL Logger**: Complementary system for historical data storage  
- **Grafana Dashboards**: Visualization layer for the monitoring stack
- **Terminal Dashboard**: Real-time console monitoring interface
