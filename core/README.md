# GPU Core API

A high-performance FastAPI-based REST service that provides comprehensive GPU monitoring capabilities. The Core API serves as the central data hub for the entire GPU monitoring ecosystem, offering multiple query methods and flexible data access patterns.

---

## 🏗️ Architecture Overview

```
┌─────────────────────┐    ┌────────────────────┐    ┌──────────────────┐
│     GPU Hardware    │    │   Query Methods    │    │    Core API      │
│                     │    │                    │    │   (Port 9555)    │
│ • NVIDIA GPUs       │◄───┤ • NVML (PyNVML)    │◄───┤                  │
│ • Multiple cards    │    │ • Bash (nvidia-smi)│    │ • REST Endpoints │
│ • Real-time data    │    │ • Simulation Mode  │    │ • JSON/Prometheus│
└─────────────────────┘    └────────────────────┘    │ • Auto-discovery │
                                                     └──────────────────┘
                                                              │
                             ┌────────────────────────────────┼─────────────────────────────────┐
                             │                                │                                 │
                             ▼                                ▼                                 ▼
                    ┌─────────────────┐              ┌─────────────────┐            ┌─────────────────┐
                    │   Prometheus    │              │   SQL Logger    │            │    Grafana      │
                    │   Monitoring    │              │   Historical    │            │  Visualization  │
                    └─────────────────┘              └─────────────────┘            └─────────────────┘
```

---

## 🚀 Features

### Multi-Method GPU Querying
- **NVML Method**: Direct NVIDIA library access for maximum performance and accuracy
- **Bash Method**: nvidia-smi command wrapper for compatibility and fallback
- **Simulation Mode**: Mock data generation for testing and development

### Flexible Data Access
- **REST API**: RESTful endpoints with JSON responses
- **Prometheus Integration**: Native metrics export in Prometheus format
- **Static Information**: Hardware details (model, serial, VBIOS, etc.)
- **Dynamic Metrics**: Real-time performance data (temperature, power, utilization)

### Advanced Features
- **UUID-based Access**: Query specific GPUs by UUID
- **Deep Field Access**: Nested field navigation with path-based queries
- **Error Handling**: Robust error reporting and graceful degradation
- **Auto-discovery**: Automatic GPU detection and enumeration

---

## 📋 Prerequisites

- **Python 3.7+**
- **NVIDIA GPU(s)** (for NVML/Bash methods)
- **NVIDIA Drivers** installed
- **nvidia-ml-py** (PyNVML) for direct GPU access

### Optional Dependencies
- **nvidia-smi** CLI tool (usually included with drivers)
- **DCGM** for advanced health monitoring

---

## 🔧 Installation & Setup

### 1. Automatic Setup (Recommended)

Use the provided setup script for automatic environment creation:

```bash
# Make script executable
chmod +x run_core.sh

# Start the API server (auto-creates venv and installs dependencies)
./run_core.sh
```

The script will:
- Create a Python virtual environment (`.venv/`)
- Install all dependencies from `requirements.txt`
- Start the FastAPI server on port 9555

### 2. Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn core_api:app --host 0.0.0.0 --port 9555 --reload
```

### 3. Configuration

The API runs on **port 9555** by default and listens on all interfaces (`0.0.0.0`).

To change the configuration, modify the `run_core.sh` script or use uvicorn parameters:

```bash
# Custom host and port
uvicorn core_api:app --host 127.0.0.1 --port 8000
```

---

## 📚 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/gpu/list` | GET | List all GPUs with static information |
| `/gpu/metric` | GET | Prometheus-format metrics for all GPUs |
| `/gpu/metrics/json` | GET | JSON metrics for all GPUs with timestamp |
| `/gpu/metrics/json/{uuid}` | GET | JSON metrics for specific GPU |
| `/gpu/{uuid}` | GET | Complete information for specific GPU |
| `/gpu/{uuid}/static` | GET | Static information for specific GPU |
| `/gpu/{uuid}/{path}` | GET | Deep field access with nested paths |

### Query Parameters

All endpoints support the `method` query parameter:

| Method | Description | Use Case |
|--------|-------------|----------|
| `nvml` | Direct NVIDIA library access | **Default**, best performance |
| `bash` | nvidia-smi command wrapper | Compatibility, remote access |
| `sim` | Simulated GPU data | Testing, development, demos |

---

## 🔍 Detailed Endpoint Documentation

### 1. List GPUs (`/gpu/list`)

Get all GPUs with static hardware information.

```bash
curl "http://localhost:9555/gpu/list?method=nvml"
```

**Response:**
```json
{
  "gpus": [
    {
      "uuid": "GPU-0a1b2c3d-4e5f-6172-8192-334455667788",
      "name": "NVIDIA GeForce RTX 4090",
      "serial": "1234567890",
      "vbios": "90.00.01.00.AB",
      "driver": "525.85.05",
      "minor": 0,
      "pciegen": 4,
      "pciewidth": 16,
      "plimit": 450
    }
  ]
}
```

### 2. Prometheus Metrics (`/gpu/metric`)

Get all GPU metrics in Prometheus exposition format.

```bash
curl "http://localhost:9555/gpu/metric?method=sim"
```

**Response:**
```
# HELP gpu_power_watts GPU power consumption in watts
# TYPE gpu_power_watts gauge
# HELP gpu_temperature_celsius GPU temperature in celsius
# TYPE gpu_temperature_celsius gauge
gpu_power_watts{gpu_uuid="GPU-0a1b2c3d-4e5f-6172-8192-334455667788",gpu_index="0",gpu_name="SIM-RTX4090",gpu_health="healthy"} 185.5
gpu_temperature_celsius{gpu_uuid="GPU-0a1b2c3d-4e5f-6172-8192-334455667788",gpu_index="0",gpu_name="SIM-RTX4090",gpu_health="healthy"} 72.0
gpu_fan_speed{gpu_uuid="GPU-0a1b2c3d-4e5f-6172-8192-334455667788",gpu_index="0",gpu_name="SIM-RTX4090",gpu_health="healthy"} 2400.0
```

### 3. JSON Metrics - All GPUs (`/gpu/metrics/json`)

Get real-time metrics for all GPUs in JSON format with timestamp.

```bash
curl "http://localhost:9555/gpu/metrics/json?method=sim"
```

**Response:**
```json
{
  "timestamp": "2024-01-15T14:30:45.123456",
  "gpus": [
    {
      "gpu_index": "0",
      "uuid": "GPU-0a1b2c3d-4e5f-6172-8192-334455667788",
      "name": "SIM-RTX4090",
      "metrics": {
        "power_watts": 185.5,
        "temperature_celsius": 72.0,
        "gpu_clock_mhz": 2100.0,
        "memory_clock_mhz": 1100.0,
        "gpu_utilization_percent": 85.2,
        "memory_utilization_percent": 78.9,
        "memory_used_mib": 12000.0,
        "memory_total_mib": 24000.0,
        "memory_usage_percent": 50.0,
        "fan_speed": 2400.0,
        "health_status": "healthy",
        "health_status_numeric": 0
      }
    }
  ]
}
```

### 4. JSON Metrics - Specific GPU (`/gpu/metrics/json/{uuid}`)

Get metrics for a specific GPU by UUID.

```bash
curl "http://localhost:9555/gpu/metrics/json/0a1b2c3d-4e5f-6172-8192-334455667788?method=sim"
```

**Response:**
```json
{
  "gpu_index": "0",
  "uuid": "GPU-0a1b2c3d-4e5f-6172-8192-334455667788",
  "name": "SIM-RTX4090",
  "timestamp": "2024-01-15T14:30:45.123456",
  "metrics": {
    "power_watts": 185.5,
    "temperature_celsius": 72.0,
    "fan_speed": 2400.0,
    "health_status": "healthy",
    "health_status_numeric": 0
  }
}
```

### 5. Complete GPU Information (`/gpu/{uuid}`)

Get all available information for a specific GPU.

```bash
curl "http://localhost:9555/gpu/GPU-0a1b2c3d-4e5f-6172-8192-334455667788?method=nvml"
```

### 6. Static Information (`/gpu/{uuid}/static`)

Get only hardware information for a specific GPU.

```bash
curl "http://localhost:9555/gpu/0a1b2c3d-4e5f-6172-8192-334455667788/static?method=nvml"
```

### 7. Deep Field Access (`/gpu/{uuid}/{path}`)

Access nested fields using path-based navigation.

```bash
# Get GPU clock frequency
curl "http://localhost:9555/gpu/0a1b2c3d-4e5f-6172-8192-334455667788/clocks/gpu_clock_mhz?method=nvml"

# Get memory usage percentage  
curl "http://localhost:9555/gpu/0a1b2c3d-4e5f-6172-8192-334455667788/mem/memory_usage_percent?method=sim"

# Get health status
curl "http://localhost:9555/gpu/0a1b2c3d-4e5f-6172-8192-334455667788/health/value?method=sim"
```

---

## 📊 Available Metrics

### Static Information
| Field | Description | Example |
|-------|-------------|---------|
| `uuid` | Unique GPU identifier | "GPU-0a1b2c3d..." |
| `name` | GPU model name | "RTX 4090" |
| `serial` | Hardware serial number | "1234567890" |
| `vbios` | VBIOS version | "90.00.01.00.AB" |
| `driver` | Driver version | "525.85.05" |
| `minor` | Device minor number | 0 |
| `pciegen` | PCIe generation | 4 |
| `pciewidth` | PCIe width | 16 |
| `plimit` | Power limit (watts) | 450 |

### Dynamic Metrics
| Metric | Description | Unit | Range |
|--------|-------------|------|-------|
| `power_watts` | Current power consumption | Watts | 50-500 |
| `temperature_celsius` | GPU core temperature | °C | 30-90 |
| `gpu_clock_mhz` | GPU core clock frequency | MHz | 500-3000 |
| `memory_clock_mhz` | Memory clock frequency | MHz | 500-1500 |
| `gpu_utilization_percent` | GPU compute utilization | % | 0-100 |
| `memory_utilization_percent` | GPU memory utilization | % | 0-100 |
| `memory_used_mib` | Used GPU memory | MiB | 0-24576 |
| `memory_total_mib` | Total GPU memory | MiB | 4096-24576 |
| `memory_usage_percent` | Memory usage percentage | % | 0-100 |
| `fan_speed` | Fan speed | RPM | 0-10000 |
| `health_status` | Health status text | String | healthy/warning/critical |
| `health_status_numeric` | Health status number | Integer | 0-4 |

---

## 🔧 Query Methods Deep Dive

### NVML Method (`method=nvml`)
**Best for**: Production environments, maximum accuracy, lowest latency

- Direct access to NVIDIA Management Library
- Real-time hardware data
- Comprehensive metrics support
- **Requires**: NVIDIA drivers, PyNVML library

```bash
curl "http://localhost:9555/gpu/metric?method=nvml"
```

### Bash Method (`method=bash`)
**Best for**: Compatibility, remote monitoring, scripting integration

- Uses `nvidia-smi` command-line tool
- Good compatibility across systems
- Slightly higher latency than NVML
- **Requires**: NVIDIA drivers, nvidia-smi tool

```bash
curl "http://localhost:9555/gpu/metric?method=bash"
```

### Simulation Method (`method=sim`)
**Best for**: Development, testing, demonstrations

- Generates realistic GPU data
- No hardware requirements
- Configurable scenarios
- Includes edge cases (critical temps, low fan speeds)

```bash
curl "http://localhost:9555/gpu/metric?method=sim"
```

**Simulation Features:**
- 3 virtual GPUs with different characteristics
- Temperature variation: 45-65°C base with noise
- Fan speeds: 450 RPM (critical), 2400 RPM (normal), 9500 RPM (warning)  
- Power consumption: 100-300W with realistic fluctuations
- Memory usage: Varied patterns across different GPU types

---

## 🛠️ Development & Testing

### Testing Different Methods

```bash
# Test NVML method (requires real GPUs)
curl "http://localhost:9555/gpu/list?method=nvml"

# Test simulation (no hardware needed)
curl "http://localhost:9555/gpu/list?method=sim" | jq

# Test Prometheus format
curl "http://localhost:9555/gpu/metric?method=sim"
```

### Health Check

```bash
# Basic API health
curl -f http://localhost:9555/gpu/list?method=sim

# Check specific GPU exists
curl -f "http://localhost:9555/gpu/0a1b2c3d-4e5f-6172-8192-334455667788?method=sim"
```

### Performance Testing

```bash
# Benchmark endpoint response times
time curl -s "http://localhost:9555/gpu/metric?method=nvml" > /dev/null

# Monitor continuous requests
watch -n 1 'curl -s "http://localhost:9555/gpu/metrics/json?method=sim" | jq ".gpus[0].metrics.temperature_celsius"'
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. API Not Starting
```bash
# Check if port is already in use
lsof -i :9555

# Check Python virtual environment
source .venv/bin/activate
python -c "import fastapi; print('FastAPI installed')"
```

#### 2. NVML Method Failing
```bash
# Check NVIDIA drivers
nvidia-smi

# Test PyNVML
python -c "import pynvml; pynvml.nvmlInit(); print('NVML OK')"
```

#### 3. No GPUs Detected
```bash
# Test direct core.py calls
python core.py --nvml --count
python core.py --sim --count

# Check nvidia-smi
nvidia-smi -L
```

#### 4. Permissions Issues
```bash
# Check GPU device permissions
ls -la /dev/nvidia*

# Add user to video group (if needed)
sudo usermod -a -G video $USER
```

### API Error Responses

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 400 | Bad Request | Invalid method parameter |
| 404 | Not Found | GPU UUID doesn't exist |
| 500 | Internal Server Error | Hardware access failure, driver issues |

---

## 📈 Performance & Scaling

### Performance Characteristics

| Method | Latency | CPU Usage | Memory |
|--------|---------|-----------|--------|
| NVML | ~1-5ms | Very Low | ~10MB |
| Bash | ~10-50ms | Low | ~15MB |
| Simulation | ~1ms | Very Low | ~5MB |

### Scaling Considerations

- **Concurrent Requests**: FastAPI handles multiple requests efficiently
- **Update Frequency**: Recommended polling interval: 1-15 seconds
- **Memory Usage**: Minimal memory footprint, scales with GPU count
- **CPU Impact**: Very low CPU usage for all methods

### Production Deployment

```bash
# Production server with more workers
uvicorn core_api:app --host 0.0.0.0 --port 9555 --workers 4

# With process manager (systemd, supervisor, etc.)
# See deployment documentation for production setup
```

---

## 🔗 Integration Examples

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'gpu-monitor'
    static_configs:
      - targets: ['localhost:9555']
    metrics_path: '/gpu/metric'
    params:
      method: ['nvml']
    scrape_interval: 10s
```

### Python Client Example
```python
import requests
import json

# Get all GPU metrics
response = requests.get('http://localhost:9555/gpu/metrics/json?method=nvml')
data = response.json()

for gpu in data['gpus']:
    print(f"GPU {gpu['name']}: {gpu['metrics']['temperature_celsius']}°C")
```

### Shell Monitoring Script
```bash
#!/bin/bash
# Simple GPU temperature monitor
while true; do
    temp=$(curl -s "http://localhost:9555/gpu/metrics/json?method=nvml" | \
           jq -r '.gpus[0].metrics.temperature_celsius')
    echo "$(date): GPU Temp: ${temp}°C"
    sleep 5
done
```

---

## 🤝 Related Components

- **Prometheus + AlertManager**: Real-time monitoring and alerting
- **SQL Logger**: Historical data persistence and CSV export
- **Grafana Dashboards**: Data visualization and analysis  
- **Terminal Dashboard**: Real-time console monitoring interface

---

## 📝 API Versioning & Updates

This API follows semantic versioning. Current version: **v1.0**

### Future Enhancements
- Authentication and authorization
- WebSocket support for real-time streaming
- Additional GPU vendors (AMD, Intel)
- Kubernetes health check endpoints
- GraphQL query interface
