import time
from typing import Dict, List, Tuple, Optional

import requests


class GPUMonitor:
    URL = None

    def __init__(self, url: str = ""):
        if url == "":
            url = self.URL
        self.url = url
        self.metrics_history: Dict[int, Dict[str, List[Tuple[float, float]]]] = {}
        self.gpu_info: Dict[int, Dict[str, str]] = {}
        self.last_fetch_time = 0
        self.cache_duration = 2  # seconds

    def fetch_metrics(self) -> bool:
        current_time = time.time()
        if current_time - self.last_fetch_time > self.cache_duration:
            try:
                response = requests.get(self.url)
                response.raise_for_status()
                self._parse_metrics(response.text)
                self.last_fetch_time = current_time
                return True
            except requests.RequestException as e:
                raise Exception(f"Error fetching metrics: {e}")
        return True

    def _parse_metrics(self, raw_data: str):
        lines = raw_data.split('\n')

        for line in lines:
            if line.startswith('#') or not line.strip():
                continue

            try:
                metric_name, rest = line.split('{', 1)
                labels_part, value_part = rest.split('}', 1)
                value = float(value_part.strip())

                labels = {}
                for label in labels_part.split(','):
                    key, val = label.split('=')
                    labels[key.strip()] = val.strip('"')

                gpu_index = int(labels['gpu_index'])

                if gpu_index not in self.gpu_info:
                    self.gpu_info[gpu_index] = {
                        'uuid': labels['gpu_uuid'],
                        'name': labels['gpu_name'],
                        'health': labels['gpu_health']
                    }

                if gpu_index not in self.metrics_history:
                    self.metrics_history[gpu_index] = {}

                # Add the current value with timestamp
                if metric_name not in self.metrics_history[gpu_index]:
                    self.metrics_history[gpu_index][metric_name] = []

                self.metrics_history[gpu_index][metric_name].append(
                    (time.time(), value)
                )

            except (ValueError, KeyError) as e:
                print(f"Error parsing line: {line}\nError: {e}")
                continue

    def get_gpu_list(self) -> Dict[int, Dict[str, str]]:
        if not self.fetch_metrics():
            return {}
        return {idx: info for idx, info in self.gpu_info.items()}

    def get_gpu_metric(self, gpu_index: int, metric_name: str) -> Optional[List[Tuple[float, float]]]:
        if not self.fetch_metrics():
            return None

        if gpu_index not in self.metrics_history:
            print(f"GPU index {gpu_index} not found")
            return None

        if metric_name not in self.metrics_history[gpu_index]:
            available_metrics = list(self.metrics_history[gpu_index].keys())
            print(f"Metric {metric_name} not found. Available metrics: {available_metrics}")
            return None

        return self.metrics_history[gpu_index][metric_name]

    def get_available_metrics(self, gpu_index: int) -> List[str]:
        if not self.fetch_metrics():
            return []

        if gpu_index in self.metrics_history:
            return list(self.metrics_history[gpu_index].keys())
        return []


def print_gpu_list(gpus: Dict[int, Dict[str, str]]):
    print("\nAvailable GPUs:")
    print("-" * 50)
    print(f"{'Index':<10}{'Name':<20}{'UUID':<40}{'Health'}")
    print("-" * 50)
    for idx, info in gpus.items():
        print(f"{idx:<10}{info['name']:<20}{info['uuid']:<40}{info['health']}")
    print("-" * 50)
    print(f"Total GPUs: {len(gpus)}\n")


def monitor_gpu_metric(monitor: GPUMonitor, gpu_index: int, metric_name: str):
    print(f"\nMonitoring GPU {gpu_index} - {metric_name} (Ctrl+C to stop)...\n")
    print(f"{'Timestamp':<25}{'Value'}")
    print("-" * 40)

    try:
        while True:
            history = monitor.get_gpu_metric(gpu_index, metric_name)
            print(history)
            if history:
                # Print only the latest value
                timestamp, value = history[-1]
                # print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)):<25}{value}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def main():
    url = input("Enter the metrics URL: ").strip()
    monitor = GPUMonitor(url)
    gpus = monitor.get_gpu_list()
    print(gpus)
    if not gpus:
        print("No GPU information available. Please check the URL.")
        return

    print_gpu_list(gpus)
    while True:
        try:
            gpu_index = int(input("Enter GPU index to monitor (-1 to show list again, -2 to exit): ").strip())

            if gpu_index == -1:
                gpus = monitor.get_gpu_list()
                print_gpu_list(gpus)
                continue

            if gpu_index == -2:
                print("Exiting...")
                break

            if gpu_index not in gpus:
                print(f"Invalid GPU index. Available indices: {list(gpus.keys())}")
                continue

            metrics = monitor.get_available_metrics(gpu_index)
            print(metrics)
            print(f"\nAvailable metrics for GPU {gpu_index}:")
            for i, metric in enumerate(metrics, 1):
                print(f"{i}. {metric}")

            try:
                metric_choice = int(input("Select metric number to monitor: ").strip())
                if 1 <= metric_choice <= len(metrics):
                    selected_metric = metrics[metric_choice - 1]
                    monitor_gpu_metric(monitor, gpu_index, selected_metric)
                else:
                    print("Invalid metric number")
            except ValueError:
                print("Please enter a valid number")

        except ValueError:
            print("Please enter a valid number")


if __name__ == "__main__":
    main()
