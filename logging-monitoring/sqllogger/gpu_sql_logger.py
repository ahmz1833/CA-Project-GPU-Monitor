#!/usr/bin/env python3
import requests
import sqlite3
import argparse
import time
from typing import Dict
from urllib.parse import quote


def create_gpu_info_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS gpu_info (
            uuid TEXT PRIMARY KEY,
            name TEXT,
            serial TEXT,
            vbios TEXT,
            driver TEXT,
            minor INTEGER,
            pciegen INTEGER,
            pciewidth INTEGER,
            plimit INTEGER
        );
    ''')
    conn.commit()

def insert_into_gpu_info(conn, gpu: Dict):
    """Insert static GPU information, handling missing fields gracefully"""
    conn.execute('''
        INSERT OR REPLACE INTO gpu_info (uuid, name, serial, vbios, driver, minor, pciegen, pciewidth, plimit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        gpu.get("uuid"),
        gpu.get("name"),
        gpu.get("serial"),
        gpu.get("vbios"),
        gpu.get("driver"),
        gpu.get("minor"),
        gpu.get("pciegen"),
        gpu.get("pciewidth"),
        gpu.get("plimit")
    ))
    conn.commit()

def create_metrics_table_if_not_exists(conn, uuid: str):
    sanitized_uuid = quote(uuid, safe="")
    conn.execute(f'''
        CREATE TABLE IF NOT EXISTS "{sanitized_uuid}" (
            timestamp TEXT PRIMARY KEY,
            power_watts REAL,
            temperature_celsius REAL,
            gpu_clock_mhz REAL,
            memory_clock_mhz REAL,
            gpu_utilization_percent REAL,
            memory_utilization_percent REAL,
            memory_used_mib REAL,
            memory_total_mib REAL,
            memory_usage_percent REAL,
            fan_speed REAL,
            health_status TEXT,
            health_status_numeric INTEGER
        );
    ''')
    conn.commit()

def safe_get_metric(metrics: Dict, key: str, default_value=None):
    """Safely get a metric value, return default if missing or None"""
    return metrics.get(key, default_value)

def insert_metrics(conn, uuid: str, metrics: Dict, timestamp: str):
    """Insert metrics into database, handling missing values gracefully"""
    sanitized_uuid = quote(uuid, safe="")
    
    # Extract metrics safely, using None for missing values
    values = (
        timestamp,
        safe_get_metric(metrics, "power_watts"),
        safe_get_metric(metrics, "temperature_celsius"),
        safe_get_metric(metrics, "gpu_clock_mhz"),
        safe_get_metric(metrics, "memory_clock_mhz"),
        safe_get_metric(metrics, "gpu_utilization_percent"),
        safe_get_metric(metrics, "memory_utilization_percent"),
        safe_get_metric(metrics, "memory_used_mib"),
        safe_get_metric(metrics, "memory_total_mib"),
        safe_get_metric(metrics, "memory_usage_percent"),
        safe_get_metric(metrics, "fan_speed"),
        safe_get_metric(metrics, "health_status"),
        safe_get_metric(metrics, "health_status_numeric")
    )
    
    conn.execute(f'''
        INSERT OR IGNORE INTO "{sanitized_uuid}" (
            timestamp, power_watts, temperature_celsius, gpu_clock_mhz, memory_clock_mhz,
            gpu_utilization_percent, memory_utilization_percent, memory_used_mib,
            memory_total_mib, memory_usage_percent, fan_speed, health_status, health_status_numeric
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', values)
    conn.commit()


def run_logger(base_url, method, interval_sec, db_name="gpu_monitor.db"):
    conn = sqlite3.connect(db_name)
    create_gpu_info_table(conn)
    
    print(f"🚀 Starting GPU monitoring logger")
    print(f"📍 Target: {base_url}")
    print(f"🔧 Method: {method}")
    print(f"⏱️  Interval: {interval_sec} seconds")
    print(f"🗄️  Database: {db_name}")
    print(f"🎯 Scheduling: Precise time-based intervals")
    print()
    
    # Initialize timing
    next_run_time = time.time()
    iteration = 0

    while True:
        iteration += 1
        start_time = time.time()
        
        # Calculate if we're running on time
        time_drift = start_time - next_run_time
        if abs(time_drift) > 1.0:  # More than 1 second drift
            drift_status = f" (drift: {time_drift:+.1f}s)" if time_drift != 0 else ""
        else:
            drift_status = ""
        
        try:
            # Fetch GPU list
            gpu_list_url = f"{base_url}/gpu/list?method={method}"
            response = requests.get(gpu_list_url, timeout=10)
            response.raise_for_status()
            gpu_list = response.json()["gpus"]
            
            successful_logs = 0
            warnings = []

            for gpu in gpu_list:
                try:
                    # Insert/update GPU static information
                    insert_into_gpu_info(conn, gpu)
                    
                    # Check if GPU has UUID (critical for identification)
                    uuid = gpu.get("uuid")
                    if not uuid:
                        warnings.append(f"GPU missing UUID field, skipping: {gpu}")
                        continue
                        
                    gpu_name = gpu.get("name", "Unknown GPU")
                    
                    # Fetch GPU metrics
                    metrics_url = f"{base_url}/gpu/metrics/json/{uuid}?method={method}"
                    metrics_response = requests.get(metrics_url, timeout=10)
                    metrics_response.raise_for_status()
                    data = metrics_response.json()

                    # Create table if needed
                    create_metrics_table_if_not_exists(conn, uuid)
                    
                    # Check for missing critical metrics and warn
                    metrics = data["metrics"]
                    missing_metrics = []
                    for key in ["power_watts", "temperature_celsius", "gpu_utilization_percent", "fan_speed"]:
                        if key not in metrics or metrics[key] is None:
                            missing_metrics.append(key)
                    
                    if missing_metrics:
                        warnings.append(f"{gpu_name}: Missing {', '.join(missing_metrics)}")
                    
                    # Insert metrics (with safe handling of missing values)
                    insert_metrics(conn, uuid, metrics, data["timestamp"])
                    successful_logs += 1
                    
                except requests.exceptions.RequestException as e:
                    warnings.append(f"{gpu.get('name', uuid)}: Network error - {e}")
                except KeyError as e:
                    warnings.append(f"{gpu.get('name', uuid)}: Missing data field - {e}")
                except Exception as e:
                    warnings.append(f"{gpu.get('name', uuid)}: {e}")

            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Print status with timing information
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            if successful_logs > 0:
                print(f"✅ #{iteration:04d} Logged {successful_logs}/{len(gpu_list)} GPUs at {timestamp} (exec: {execution_time:.2f}s){drift_status}")
            else:
                print(f"❌ #{iteration:04d} Failed to log any GPU at {timestamp} (exec: {execution_time:.2f}s){drift_status}")
            
            # Print warnings if any
            for warning in warnings:
                print(f"⚠️  {warning}")
                
            # Warn if execution is taking too long
            if execution_time > interval_sec * 0.8:  # More than 80% of interval
                print(f"⚠️  Execution time ({execution_time:.2f}s) is close to interval ({interval_sec}s)")
                
        except requests.exceptions.RequestException as e:
            execution_time = time.time() - start_time
            print(f"🌐 #{iteration:04d} Network error at {time.strftime('%Y-%m-%d %H:%M:%S')} (exec: {execution_time:.2f}s): {e}")
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"💥 #{iteration:04d} Unexpected error at {time.strftime('%Y-%m-%d %H:%M:%S')} (exec: {execution_time:.2f}s): {e}")

        # Calculate next run time (precise scheduling)
        next_run_time += interval_sec
        current_time = time.time()
        
        # Calculate sleep time needed to hit the next scheduled time
        sleep_time = next_run_time - current_time
        
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # We're running behind schedule
            if abs(sleep_time) > interval_sec:
                # If we're more than one full interval behind, reset the schedule
                next_run_time = current_time + interval_sec
                print(f"⚠️  Schedule reset due to {abs(sleep_time):.1f}s delay")
            # If we're just slightly behind, let it catch up naturally


def main():
    parser = argparse.ArgumentParser(description="Continuous GPU Metrics Logger")
    parser.add_argument("host_port", type=str, help="IP:PORT of server (e.g., 185.176.35.77:9555)")
    parser.add_argument("method", type=str, help="Metric method (e.g., sim)")
    parser.add_argument("interval", type=int, help="Logging interval in seconds")
    args = parser.parse_args()

    base_url = f"http://{args.host_port}"
    run_logger(base_url, args.method, args.interval)


if __name__ == "__main__":
    main()
