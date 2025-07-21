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
- **Password**: `admin` (or check `.env` file)

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
PROMETHEUS_HOST=localhost
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
1. Verify Prometheus is running and accessible
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify GPU monitoring API is running
4. Check network connectivity between containers

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
└── old/                      # Backup of previous setup
```

## 🔄 Updating Configuration

### Change Prometheus Server
1. Edit `.env` file:
   ```bash
   PROMETHEUS_HOST=your-prometheus-host
   PROMETHEUS_PORT=9090
   ```

2. Restart Grafana:
   ```bash
   docker compose restart grafana
   ```

### Add Custom Dashboards
1. Create JSON file in `dashboards/` folder
2. Restart Grafana to load new dashboard
3. Or import directly via Grafana UI

## 📝 Notes

- Dashboards support all three collection methods (nvml, bash, sim)
- Configuration is preserved in Docker volumes
- Network `gpu_logging_network` connects to main monitoring system
- Prometheus datasource is auto-configured on startup

## 🆘 Support

For issues:
1. Check logs: `docker compose logs grafana`
2. Verify Prometheus connectivity
3. Ensure GPU monitoring API is running
4. Check port 3000 is not in use

---

**Ready to monitor your GPUs!** 🚀
