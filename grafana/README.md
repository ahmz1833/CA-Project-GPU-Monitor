# GPU Monitor Grafana Dashboard

This is a clean, simplified Grafana setup for monitoring GPUs with support for three data collection methods: NVML, Bash, and Simulation.

## 🚀 Quick Start

### 1. Start Grafana
```bash
./start-grafana.sh
```

### 2. Access Grafana
- **URL**: http://localhost:3000
- **Username**: `admin` 
- **Password**: `gpu_monitor_2025` (default, or check `.env` file)

## 📊 Available Dashboards

### 1. GPU Overview Dashboard
- **Essential metrics**: Temperature, Utilization, Power, Memory
- **Multi-GPU support**: Shows all GPUs with meaningful labels
- **Real-time monitoring**: Updates every few seconds
- **Perfect for**: Day-to-day monitoring

### 2. GPU Detailed Performance
- **Advanced metrics**: Clock frequencies, fan speed, memory utilization
- **Health monitoring**: GPU health status tracking
- **Memory details**: Both usage percentage and absolute values (MiB)
- **Perfect for**: Performance analysis and troubleshooting

### 3. GPU Alerts & Status
- **Status overview**: Table with current GPU status and color-coded alerts
- **Threshold gauges**: Maximum temperature, utilization, and power
- **Alert tracking**: Count of GPUs exceeding thresholds over time
- **Perfect for**: Operations monitoring and incident response

## ⚙️ Configuration

### Environment Variables (.env file)

```bash
# Grafana Configuration
GRAFANA_HOST=localhost
GRAFANA_PORT=3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Prometheus Connection (adjust to your setup)
# Use 'gpu-logging-prometheus' for container name or 'host.docker.internal' for host network
PROMETHEUS_HOST=host.docker.internal
PROMETHEUS_PORT=9090
```

### Connecting to Different Data Sources

The dashboards automatically work with all three collection methods:

1. **NVML Method**: Real NVIDIA GPU data via NVIDIA Management Library
2. **Bash Method**: GPU data via nvidia-smi commands  
3. **Simulation Method**: Simulated GPU data for testing/demo

The Prometheus scraping configuration handles all three methods automatically.

## 🔧 Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Ensure .env file exists
cp .env.example .env
# Edit .env with your settings

# 2. Start containers
docker compose up -d

# 3. Check status
docker compose ps
docker compose logs grafana
```

## 📈 Dashboard Features

### Multi-GPU Support
- Each panel shows all GPUs with clear labels
- GPU name and index displayed in legends
- Variable filters to focus on specific GPUs or collection methods

### Meaningful Labels
- `{{gpu_name}} (Index {{gpu_index}})` format
- Color-coded thresholds for easy identification
- Health status mapping (Healthy/Caution/Warning/Critical)

### Alert Thresholds
- **Temperature**: Yellow >70°C, Red >80°C
- **Power**: Yellow >300W, Red >350W  
- **Utilization**: Yellow >70%, Red >90%
- **Memory**: Yellow >80%, Red >90%

## 🛠️ Troubleshooting

### Grafana Won't Start
```bash
# Check logs
docker compose logs grafana

# Reset containers
docker compose down
docker compose up -d
```

### No Data in Dashboards
1. **Check Prometheus connection**:
   ```bash
   # Test from host
   curl http://localhost:9090/api/v1/targets
   
   # Test from Grafana container
   docker compose exec grafana curl http://gpu-logging-prometheus:9090/api/v1/targets
   ```

2. **Verify GPU monitoring API is running**:
   ```bash
   curl http://localhost:9555/gpu/metric?method=sim
   ```

3. **Check Grafana datasource**:
   - Go to Configuration → Data sources → Prometheus
   - Click "Save & test" to verify connection
   - Ensure URL is set correctly (auto-configured by start script)

### Dashboard Issues
- All dashboards are provisioned automatically
- Changes made in UI are preserved
- To reset: delete `grafana_data` volume and restart

## 🏗️ Project Structure

```
grafana/
├── dashboards/                 # Dashboard JSON files
│   ├── 01-gpu-overview.json   # Essential metrics
│   ├── 02-gpu-detailed.json   # Detailed performance
│   └── 03-gpu-alerts.json     # Alerts & status
├── provisioning/               # Grafana configuration
│   ├── dashboards/
│   │   └── dashboard.yml      # Dashboard provisioning
│   └── datasources/
│       └── prometheus.yml     # Prometheus connection
├── docker-compose.yml         # Container definition
├── start-grafana.sh          # Quick start script
├── .env.example              # Configuration template
```

## 🔄 Updating Configuration

### Change Prometheus Server
1. Edit `.env` file:
   ```bash
   # For container-to-container communication
   PROMETHEUS_HOST=gpu-logging-prometheus
   
   # For host network access
   PROMETHEUS_HOST=host.docker.internal
   
   # For remote Prometheus server
   PROMETHEUS_HOST=your-prometheus-ip
   PROMETHEUS_PORT=9090
   ```

2. **Restart with new configuration**:
   ```bash
   ./start-grafana.sh
   ```
   (This will regenerate the datasource configuration automatically)

### Add Custom Dashboards
1. Create JSON file in `dashboards/` folder
2. Restart Grafana to load new dashboard
3. Or import directly via Grafana UI

## 📝 Important Notes

### Data Collection Methods
- **NVML**: Requires NVIDIA drivers and GPUs (may show errors without proper hardware)
- **Bash**: Uses nvidia-smi command (requires NVIDIA drivers) 
- **Simulation**: Always works, generates realistic test data

### Network Configuration
- Grafana connects to `gpu_logging_network` to reach Prometheus
- Datasource URL is auto-generated based on `.env` configuration
- Container-to-container communication uses service names

### Data Persistence
- Dashboard changes are saved in `grafana_data` Docker volume
- Datasource configuration is regenerated on each startup
- `.env` file controls all configuration parameters

## 🆘 Support

For issues:
1. Check logs: `docker compose logs grafana`
2. Verify Prometheus connectivity
3. Ensure GPU monitoring API is running
4. Check port 3000 is not in use

---

**Ready to monitor your GPUs!** 🚀
