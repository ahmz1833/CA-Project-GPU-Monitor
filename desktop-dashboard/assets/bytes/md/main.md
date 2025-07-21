# 🖥️ GPU Monitor

**GPU Monitor** is a simple Python-based app that lets you monitor the current state of your GPU. It supports various backends like **NVML**, **DCGM**, **nvidia-smi**, and **simulation mode**, giving you flexible options to read real-time GPU metrics.

## 🔧 Features

- Monitor real-time GPU health and stats
- View:
  - Temperature
  - Power usage
  - GPU and memory clock speeds
  - Health state and performance indicators
- Supports multiple data sources:
  - `NVML` (NVIDIA Management Library)
  - `DCGM` (Data Center GPU Manager)
  - `nvidia-smi` (NVIDIA System Management Interface)
  - `sim` (Simulation mode for testing)
- Simple and clean Python codebase

## 🚀 Usage

### Run the app:

```bash
python ./main.py <URL>
```
