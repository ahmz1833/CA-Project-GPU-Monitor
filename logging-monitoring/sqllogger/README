# GPU Metrics SQL Logger

A lightweight, standalone GPU monitoring tool that fetches metrics from the GPU Core API and stores them in a local SQLite database. This system provides simple data persistence and CSV export capabilities for historical analysis.

---

## 🚀 Features

- **Continuous Logging**: Fetches GPU metrics at configurable intervals
- **SQLite Storage**: Lightweight, portable database storage
- **Per-GPU Tables**: Creates separate tables for each GPU UUID
- **CSV Export**: Exports historical data to CSV files for analysis
- **Static Info Management**: Stores GPU hardware information separately
- **Flexible API Integration**: Works with NVML, Bash, or Simulation methods

---

## 📊 Database Structure

### Main Tables

#### 1. `gpu_info` (Static Information)
Stores hardware information for all discovered GPUs:

```sql
CREATE TABLE gpu_info (
    uuid TEXT PRIMARY KEY,        -- GPU UUID identifier
    name TEXT,                    -- GPU model name (e.g., "RTX 4090")
    serial TEXT,                  -- Hardware serial number
    vbios TEXT,                   -- VBIOS version
    driver TEXT,                  -- Driver version
    minor INTEGER,                -- Device minor number
    pciegen INTEGER,              -- PCIe generation (3, 4, 5)
    pciewidth INTEGER,            -- PCIe width (x8, x16)
    plimit INTEGER                -- Power limit in watts
);
```

#### 2. Per-GPU Metrics Tables
For each GPU UUID, a dedicated table stores time-series metrics:

```sql
CREATE TABLE "{GPU_UUID}" (
    timestamp TEXT PRIMARY KEY,                -- ISO format timestamp
    power_watts REAL,                         -- Current power consumption
    temperature_celsius REAL,                 -- GPU core temperature
    gpu_clock_mhz REAL,                      -- GPU core clock frequency
    memory_clock_mhz REAL,                   -- Memory clock frequency
    gpu_utilization_percent REAL,            -- GPU compute utilization
    memory_utilization_percent REAL,         -- GPU memory utilization
    memory_used_mib REAL,                    -- Used GPU memory in MiB
    memory_total_mib REAL,                   -- Total GPU memory in MiB
    memory_usage_percent REAL,               -- Memory usage percentage
    fan_speed REAL,                          -- Fan speed in RPM
    health_status TEXT,                      -- Health status (Healthy, Warning, etc.)
    health_status_numeric INTEGER            -- Numeric health code (0-4)
);
```

### Data Types & Ranges

| Metric | Type | Typical Range | Units |
|--------|------|---------------|-------|
| power_watts | REAL | 50-500 | Watts |
| temperature_celsius | REAL | 30-90 | °C |
| gpu_clock_mhz | REAL | 500-3000 | MHz |
| memory_clock_mhz | REAL | 500-1500 | MHz |
| gpu_utilization_percent | REAL | 0-100 | % |
| memory_utilization_percent | REAL | 0-100 | % |
| memory_used_mib | REAL | 0-24576 | MiB |
| memory_total_mib | REAL | 4096-24576 | MiB |
| fan_speed | REAL | 0-10000 | RPM |
| health_status_numeric | INTEGER | 0-4 | 0=Healthy, 4=Unknown |

---

## 🛠️ Requirements

- Python 3.7+
- Dependencies: `requests`, `pandas`

### 🔧 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 📖 Usage

### 1. Start Continuous Logging

Log GPU metrics continuously to SQLite database:

```bash
# Log simulation data every 30 seconds
python gpu_sql_logger.py localhost:9555 sim 30

# Log real NVML data every 10 seconds
python gpu_sql_logger.py localhost:9555 nvml 10

# Log from remote server every 60 seconds
python gpu_sql_logger.py 192.168.1.100:9555 bash 60
```

**Arguments:**
- `host_port`: IP:PORT of the GPU Core API server
- `method`: Query method (`nvml`, `bash`, or `sim`)
- `interval`: Logging interval in seconds

### 2. Export to CSV

Export all GPU metrics tables to CSV files:

```bash
# Export database to output/ directory
python csv_exporter.py gpu_monitor.db output/
```

This creates separate CSV files for each GPU:
```
output/
├── GPU-0a1b2c3d-4e5f-6172-8192-334455667788.csv
├── GPU-1b2c3d4e-5f6a-7b8c-9d0e-112233445566.csv
└── GPU-2c3d4e5f-6a7b-8c9d-0e1f-223344556677.csv
```

---

## 💡 Example Workflow

```bash
# 1. Start logging (runs continuously)
python gpu_sql_logger.py localhost:9555 sim 15

# 2. In another terminal, export data after some time
python csv_exporter.py gpu_monitor.db exports/

# 3. Analyze CSV files with your preferred tools
# - Excel, LibreOffice Calc
# - Python pandas, R
# - Data visualization tools
```

---

## 🔍 Database Inspection

You can inspect the SQLite database directly:

```bash
# Open database with sqlite3 CLI
sqlite3 gpu_monitor.db

# List all tables
.tables

# View GPU info
SELECT * FROM gpu_info;

# View recent metrics for a specific GPU
SELECT * FROM "GPU-0a1b2c3d-4e5f-6172-8192-334455667788" 
ORDER BY timestamp DESC LIMIT 10;

# Exit
.quit
```

---

## 📝 Output Example

### Console Output (Logger)
```
✅ Logged data for 3 GPUs at 2024-01-15 14:30:15
✅ Logged data for 3 GPUs at 2024-01-15 14:30:45
✅ Logged data for 3 GPUs at 2024-01-15 14:31:15
```

### CSV Export Output
```
✅ Exported GPU-0a1b2c3d-4e5f-6172-8192-334455667788 to output/GPU-0a1b2c3d-4e5f-6172-8192-334455667788.csv
✅ Exported GPU-1b2c3d4e-5f6a-7b8c-9d0e-112233445566 to output/GPU-1b2c3d4e-5f6a-7b8c-9d0e-112233445566.csv
✅ Exported GPU-2c3d4e5f-6a7b-8c9d-0e1f-223344556677 to output/GPU-2c3d4e5f-6a7b-8c9d-0e1f-223344556677.csv
🎉 All exports complete.
```

### Sample CSV Content
```csv
timestamp,power_watts,temperature_celsius,gpu_clock_mhz,memory_clock_mhz,gpu_utilization_percent,memory_utilization_percent,memory_used_mib,memory_total_mib,memory_usage_percent,fan_speed,health_status,health_status_numeric
2024-01-15T14:30:15.123456,185.5,72.0,2100.0,1100.0,85.2,78.9,12000.0,24000.0,50.0,2400.0,Healthy,0
2024-01-15T14:30:30.234567,190.2,73.5,2105.0,1105.0,87.1,80.2,12500.0,24000.0,52.1,2450.0,Healthy,0
```

---

## 🔗 Integration

This SQL logger works alongside:
- **Prometheus + AlertManager**: For real-time monitoring and alerting
- **Grafana**: For live dashboards and visualization
- **Core API**: As the data source for all monitoring systems

Use SQL logger for:
- Historical data analysis
- Long-term data retention
- Offline analysis and reporting
- Data backup and archival
