# GPU Terminal Dashboard

A sophisticated real-time terminal-based GPU monitoring dashboard with adaptive UI, high-resolution charts, and live performance visualization. Built with Python curses for cross-platform compatibility and optimized for various terminal sizes.

---

## 🖥️ Features Overview

### Adaptive Interface Design
- **Responsive Layout**: Automatically adjusts to terminal size (from 40x10 to 120x30+)
- **Multiple Display Modes**: Large, Medium, Small, and Minimal configurations
- **Smart Content Scaling**: Shows appropriate detail level based on available space
- **Unicode Graphics**: Beautiful box drawing characters and Braille-based charts

### Real-Time Monitoring
- **Live GPU Metrics**: Temperature, utilization, memory usage, power consumption
- **Utilization History**: Sparkline graphs with configurable history depth
- **Process Information**: Active GPU processes with memory usage
- **Health Status**: Color-coded health indicators

### Advanced Visualization
- **Dual View Modes**: Standard overview and detailed high-resolution charts
- **Sparkline Graphs**: Multiple character sets for different terminal capabilities
- **Braille Charts**: Ultra-high resolution utilization graphs (4x vertical resolution)
- **Color-Coded Metrics**: Intuitive color system for quick status assessment

---

## 🎨 Visual Demo

### Large Terminal (120x30+)
```
═════════════════ GPU MONITOR DASHBOARD - Real-time Performance [STANDARD] ═════════════════
 Terminal: 120x40 │ Mode: LARGE │ Press 'o' for detailed view │ 'q' to quit 

╔═ GPU 0 - SIM-RTX4090 ═══════════════════════════════════════════════════════════════════
║ Temp: 72.0°C │ Mem: 50.0% │ Clock: 2100MHz │ Power: 185.5W │ Health: Healthy
║ Utilization: 85.2% [HIGH]
║ Graph (45 samples):
║ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃
║ Scale: 0% ▁ ... █ 100%
║ Processes:
║  PID:   1234 | GPU Mem:  1.2 GB
║  PID:   5678 | GPU Mem:  800 MB
╚══════════════════════════════════════════════════════════════════════════════════════════
```

### Medium Terminal (80x20)
```
═══════════════════ GPU MONITOR [STANDARD] ═══════════════════
┌─ GPU 0 - SIM-RTX4090 ─────────────────────────────────────
│ Temp: 72.0°C │ Mem: 50.0%
│ Utilization: 85.2% [HIGH]
│ ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█ 85.2%
│ Processes: 2 | Total GPU Mem: 2.0 GB
└───────────────────────────────────────────────────────────
```

### Small Terminal (60x15)
```
GPU Monitor [STANDARD]
GPU 0:
·-=≡█≡=-·-=≡█≡=-·-=≡█≡=-·-=≡█ 85.2%
```

### Detailed View (High-Resolution Charts)
```
┌──────────────────── GPU High-Resolution Monitor - DETAILED VIEW ────┐
│ SIM-RTX4090                                                          │
│ 72.0C | 2100 MHz | 1100 MHz (Mem) | 185.5W                          │
│ Processes: 1234 (1.2 GB), 5678 (800 MB)                             │
│100.0% │                                                             │
│       │    ⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸      │
│ 50.0% │  ⢰⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸    │
│       │⢀⣸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸⡇⢸  │
│  0.0% │⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.7+**
- **GPU Core API** running and accessible
- **Terminal with Unicode support** (recommended)
- **requests** library for HTTP communication

### Installation

#### Option 1: Using pip (Recommended)

```bash
# Navigate to terminal-dashboard directory
cd terminal-dashboard/

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python main_dashboard.py localhost:9555 sim
```

#### Option 2: Using virtual environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python main_dashboard.py localhost:9555 sim
```

#### Option 3: Manual installation

```bash
# Install requests manually
pip install requests

# Run the dashboard
python main_dashboard.py localhost:9555 sim
```

---

### Usage

```bash
# Connect to local Core API using simulation data
python main_dashboard.py localhost:9555 sim

# Connect to local Core API using NVML (real GPUs)
python main_dashboard.py localhost:9555 nvml

# Connect to remote Core API using bash method
python main_dashboard.py 192.168.1.100:9555 bash
```

**Arguments:**
- `ip_port`: Core API server address (format: `IP:PORT`)
- `method`: Query method (`nvml`, `bash`, or `sim`)

---

## 🎛️ Interactive Controls

| Key | Action | Description |
|-----|--------|-------------|
| `o` / `O` | Toggle View | Switch between Standard and Detailed view modes |
| `q` | Quit | Exit the dashboard |

### View Modes

#### Standard View
- **Overview Mode**: Shows all GPUs with essential metrics
- **Adaptive Layout**: Adjusts content based on terminal size
- **Sparkline Graphs**: Real-time utilization history
- **Process Information**: Active GPU processes and memory usage

#### Detailed View
- **High-Resolution Charts**: Braille-based utilization graphs
- **Enhanced Metrics**: Detailed temperature, clock, and power information
- **Process Details**: Extended process information with memory usage
- **Full-Screen Charts**: Maximizes chart real estate for better visualization

---

## 📊 Display Configurations

The dashboard automatically adapts to your terminal size:

### Large Mode (120x30+)
- **Full Feature Set**: All metrics, detailed graphs, process info
- **Unicode Borders**: Beautiful box drawing characters
- **Extensive History**: Up to 100 data points in sparklines
- **Complete Process List**: Shows individual processes with details

### Medium Mode (80x20)
- **Essential Metrics**: Temperature, memory, utilization
- **Simplified Borders**: Clean ASCII-based borders  
- **Moderate History**: Up to 60 data points
- **Summary Process Info**: Grouped process information

### Small Mode (60x15)
- **Core Metrics Only**: Basic temperature and utilization
- **Compact Layout**: Minimal spacing and borders
- **Limited History**: Up to 40 data points
- **No Process Details**: Focus on performance metrics

### Minimal Mode (<60x15)
- **Critical Info**: Temperature and utilization only
- **Text-Only**: No graphics, plain text display
- **Tiny History**: Up to 20 data points
- **Ultra-Compact**: Maximum information density

---

## 🎨 Color Coding System

### Utilization Levels
| Color | Range | Status | Meaning |
|-------|-------|--------|---------|
| 🟢 Green | 0-30% | IDLE | Low activity, optimal efficiency |
| 🟡 Yellow | 30-70% | ACT | Active usage, normal operation |
| 🟠 Orange | 70-90% | MED | Medium load, monitor closely |
| 🔴 Red | 90-100% | HIGH | High utilization, potential bottleneck |

### Temperature Indicators
| Color | Range | Status |
|-------|-------|--------|
| 🟢 Green | <60°C | Normal |
| 🟡 Yellow | 60-80°C | Warm |
| 🔴 Red | >80°C | Hot |

### Health Status
| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 Green | Healthy | All systems normal |
| 🟡 Yellow | Warning | Minor issues detected |
| 🔴 Red | Critical | Immediate attention required |
| ⚫ Gray | Unknown | Status unavailable |

---

## 🔧 Technical Details

### Data Collection
- **Update Frequency**: ~2 seconds (adjustable)
- **History Depth**: 60-2000 data points (size dependent)
- **Metrics Source**: GPU Core API via HTTP requests
- **Process Information**: Real-time GPU process enumeration

### Visualization Engine
- **Sparkline Rendering**: Multiple character sets for compatibility
- **Braille Charts**: 4x vertical resolution using Unicode Braille patterns
- **Adaptive Scaling**: Dynamic adjustment to terminal capabilities
- **Color Management**: Intelligent color pair management for terminal compatibility

### Character Sets

#### Dense Mode (Large terminals)
```
Braille: ⠀⡀⡄⡆⡇⣇⣧⣷⣿  (9 levels, 4x resolution)
```

#### Normal Mode (Medium terminals)
```
Block: ▁▂▃▄▅▆▇█  (8 levels)
```

#### Simple Mode (Small terminals)
```
ASCII: ·-=≡█  (5 levels)
```

#### Minimal Mode (Tiny terminals)
```
Basic: _-^*  (4 levels)
```

---

## 🛠️ Development & Customization

### Configuration Options

The dashboard automatically configures itself, but you can modify the display logic:

```python
# In main_dashboard.py, modify these constants:
MAX_DATA_POINTS = 2000          # Maximum history length
SPARK_CHARS_DENSE = '⠀⡀⡄⡆⡇⣇⣧⣷⣿'  # High-resolution characters
SPARK_CHARS_NORMAL = '▁▂▃▄▅▆▇█'         # Standard block characters
```

### Adding Custom Metrics

To display additional metrics, modify the `parse_prometheus_metrics` function:

```python
def parse_prometheus_metrics(text):
    # Add custom metric parsing logic here
    # Extend the gpu_metrics dictionary with new fields
    pass
```

### Customizing Colors

Modify the color initialization in `draw_screen`:

```python
curses.init_pair(1, curses.COLOR_GREEN, -1)    # Low/Good
curses.init_pair(2, curses.COLOR_YELLOW, -1)   # Medium/Warning  
curses.init_pair(3, curses.COLOR_RED, -1)      # High/Critical
# Add more color pairs as needed
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Dashboard Won't Start
```bash
# Check Core API connectivity
curl "http://localhost:9555/gpu/metric?method=sim"

# Verify Python curses support
python -c "import curses; print('Curses OK')"
```

#### 2. Garbled Display
```bash
# Check terminal Unicode support
echo "Unicode test: ▁▂▃▄▅▆▇█ ⠀⡀⡄⡆"

# Set proper locale
export LC_ALL=en_US.UTF-8
```

#### 3. Colors Not Working
```bash
# Check terminal color support
echo $TERM
tput colors

# Try running with color test
python -c "import curses; curses.wrapper(lambda x: print('Colors OK'))"
```

#### 4. Process Information Missing
```bash
# Check Core API process endpoint
curl "http://localhost:9555/gpu/GPU-uuid/processes?method=sim"

# Verify method supports process data
# Note: Process info may not be available for all methods
```

### Performance Optimization

#### For Slow Terminals
- Use smaller terminal size to trigger minimal mode
- Reduce update frequency by modifying sleep time
- Use `sim` method for testing without hardware load

#### For Remote Connections
- Consider terminal multiplexers (tmux, screen) for stability
- Use compression (ssh -C) for better performance
- Monitor network latency impact on updates

---

## 📈 Integration Examples

### Running with Systemd (Background Service)
```ini
# /etc/systemd/system/gpu-dashboard.service
[Unit]
Description=GPU Terminal Dashboard
After=network.target

[Service]
Type=simple
User=monitor
Environment=DISPLAY=:0
ExecStart=/usr/bin/python3 /path/to/main_dashboard.py localhost:9555 nvml
Restart=always

[Install]
WantedBy=multi-user.target
```

### Script Wrapper
```bash
#!/bin/bash
# gpu-monitor.sh - Dashboard launcher with error handling

API_HOST=${1:-localhost:9555}
METHOD=${2:-sim}

while true; do
    echo "Starting GPU Dashboard..."
    python3 main_dashboard.py "$API_HOST" "$METHOD"
    
    if [ $? -eq 0 ]; then
        echo "Dashboard exited normally"
        break
    else
        echo "Dashboard crashed, restarting in 5 seconds..."
        sleep 5
    fi
done
```

### Docker Container
```dockerfile
FROM python:3.9-alpine
WORKDIR /app
COPY main_dashboard.py .
RUN pip install requests
CMD ["python", "main_dashboard.py", "core-api:9555", "nvml"]
```

---

## 🤝 Related Components

- **GPU Core API**: Provides the metrics data endpoint
- **Prometheus + AlertManager**: Complementary monitoring for alerts
- **SQL Logger**: Historical data persistence
- **Grafana Dashboards**: Web-based visualization alternative

---

## 📝 Terminal Compatibility

### Tested Terminals
| Terminal | Unicode | Colors | Braille | Status |
|----------|---------|--------|---------|--------|
| **iTerm2** | ✅ | ✅ | ✅ | Excellent |
| **Terminal.app** | ✅ | ✅ | ✅ | Excellent |
| **GNOME Terminal** | ✅ | ✅ | ✅ | Excellent |
| **Konsole** | ✅ | ✅ | ✅ | Excellent |
| **Windows Terminal** | ✅ | ✅ | ✅ | Excellent |
| **PuTTY** | ⚠️ | ✅ | ❌ | Good |
| **xterm** | ✅ | ✅ | ✅ | Good |
| **tmux/screen** | ✅ | ✅ | ✅ | Good |

### Fallback Behavior
- **No Unicode**: Automatically uses ASCII characters
- **No Colors**: Falls back to monochrome display
- **Small Screen**: Switches to minimal display mode
- **SSH/Remote**: Detects and adapts to connection limitations
