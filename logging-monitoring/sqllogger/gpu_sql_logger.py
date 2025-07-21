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
    conn.execute('''
        INSERT OR REPLACE INTO gpu_info (uuid, name, serial, vbios, driver, minor, pciegen, pciewidth, plimit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        gpu["uuid"],
        gpu["name"],
        gpu["serial"],
        gpu["vbios"],
        gpu["driver"],
        gpu["minor"],
        gpu["pciegen"],
        gpu["pciewidth"],
        gpu["plimit"]
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

def insert_metrics(conn, uuid: str, metrics: Dict, timestamp: str):
    sanitized_uuid = quote(uuid, safe="")
    conn.execute(f'''
        INSERT OR IGNORE INTO "{sanitized_uuid}" (
            timestamp, power_watts, temperature_celsius, gpu_clock_mhz, memory_clock_mhz,
            gpu_utilization_percent, memory_utilization_percent, memory_used_mib,
            memory_total_mib, memory_usage_percent, fan_speed, health_status, health_status_numeric
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        metrics["power_watts"],
        metrics["temperature_celsius"],
        metrics["gpu_clock_mhz"],
        metrics["memory_clock_mhz"],
        metrics["gpu_utilization_percent"],
        metrics["memory_utilization_percent"],
        metrics["memory_used_mib"],
        metrics["memory_total_mib"],
        metrics["memory_usage_percent"],
        metrics["fan_speed"],
        metrics["health_status"],
        metrics["health_status_numeric"]
    ))
    conn.commit()


def run_logger(base_url, method, interval_sec, db_name="gpu_monitor.db"):
    conn = sqlite3.connect(db_name)
    create_gpu_info_table(conn)

    while True:
        try:
            gpu_list_url = f"{base_url}/gpu/list?method={method}"
            gpu_list = requests.get(gpu_list_url).json()["gpus"]

            for gpu in gpu_list:
                insert_into_gpu_info(conn, gpu)
                uuid = gpu["uuid"]
                metrics_url = f"{base_url}/gpu/metrics/json/{uuid}?method={method}"
                data = requests.get(metrics_url).json()

                create_metrics_table_if_not_exists(conn, uuid)
                insert_metrics(conn, uuid, data["metrics"], data["timestamp"])

            print(f"✅ Logged data for {len(gpu_list)} GPUs at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"⚠️ Error during logging: {e}")

        time.sleep(interval_sec)


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
