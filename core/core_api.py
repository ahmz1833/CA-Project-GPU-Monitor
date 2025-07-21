from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi import Path
from typing import Optional
import subprocess
import json

app = FastAPI()
STATIC_FIELDS = [
	"uuid", "name", "serial", "vbios", "driver",
	"minor", "pciegen", "pciewidth", "plimit"
]

def _run_core_py(method: str, options: list[str]) -> dict:
	"""
	Calls the core.py script with desired query method and options.
	Example: python core.py --nvml --uuid --name ...
	"""
	base_cmd = ["python3", "core.py"]

	if method in ["bash", "nvml", "sim"]:
		base_cmd.append(f"--{method}")
	else:
		raise HTTPException(status_code=400, detail="Invalid method")

	base_cmd += options

	try:
		result = subprocess.run(base_cmd, capture_output=True, check=True, text=True)
		return json.loads(result.stdout)
	except subprocess.CalledProcessError as e:
		raise HTTPException(status_code=500, detail=f"Core.py failed: {e.stderr}")
	except json.JSONDecodeError:
		raise HTTPException(status_code=500, detail="Invalid JSON output from core.py")


def _extract_gpu_by_uuid(core_data: dict, target_uuid: str) -> Optional[dict]:
	"""Extracts GPU data by UUID from the core.py output."""
	for gpu_data in core_data.get("gpus", {}).values():
		uuid_ = gpu_data.get("uuid", {}).get("value")
		# check target_uuid.lower() or "GPU-" + target_uuid.lower()
		if uuid_ and (uuid_.lower() == target_uuid.lower() or f"gpu-{target_uuid.lower()}" == uuid_.lower()):
			return gpu_data
	return None


@app.get("/gpu/list")
def list_gpus(method: str = Query("nvml")):
	"""List all GPUs with uuid and static information"""
	data = _run_core_py(method, ["--" + field for field in STATIC_FIELDS])
	result = {"gpus": []}
	for _,gpu in data.get("gpus", {}).items():
		for field in STATIC_FIELDS:
			if field in gpu:
				gpu[field] = gpu[field].get("value", None)
		result["gpus"].append(gpu)
	return JSONResponse(content=result)


@app.get("/gpu/metric")
def get_gpu_metrics(method: str = Query("nvml")):
	"""Return only dynamic (time-varying) numeric data, for Prometheus use"""
	metric_fields = ["--uuid", "--name", "--power", "--temp", "--clocks", "--util", "--mem", "--fan", "--health"]
	
	data = _run_core_py(method, metric_fields)
	prometheus_lines = []
	
	# Add HELP and TYPE comments for each metric
	prometheus_lines.extend([
		"# HELP gpu_power_watts GPU power consumption in watts",
		"# TYPE gpu_power_watts gauge",
		"# HELP gpu_temperature_celsius GPU temperature in celsius",
		"# TYPE gpu_temperature_celsius gauge",
		"# HELP gpu_clock_mhz GPU clock frequency in MHz",
		"# TYPE gpu_clock_mhz gauge",
		"# HELP gpu_memory_clock_mhz GPU memory clock frequency in MHz", 
		"# TYPE gpu_memory_clock_mhz gauge",
		"# HELP gpu_utilization_percent GPU utilization percentage",
		"# TYPE gpu_utilization_percent gauge",
		"# HELP gpu_memory_utilization_percent GPU memory utilization percentage",
		"# TYPE gpu_memory_utilization_percent gauge",
		"# HELP gpu_memory_used_mib GPU memory used in MiB",
		"# TYPE gpu_memory_used_mib gauge",
		"# HELP gpu_memory_total_mib GPU memory total in MiB",
		"# TYPE gpu_memory_total_mib gauge",
		"# HELP gpu_memory_usage_percent GPU memory usage percentage",
		"# TYPE gpu_memory_usage_percent gauge",
		"# HELP gpu_fan_speed GPU fan speed",
		"# TYPE gpu_fan_speed gauge",
		"# HELP gpu_health_status GPU health status (0=Healthy, 1=Caution, 2=Warning, 3=Critical, 4=Unknown)",
		"# TYPE gpu_health_status gauge",
	])
	
	# Process each GPU
	for gpu_idx, gpu_data in data.get("gpus", {}).items():
		uuid = gpu_data.get("uuid", {}).get("value", "unknown")
		name = gpu_data.get("name", {}).get("value", "unknown")
		
		# Get health status for labels
		health = gpu_data.get("health", {})
		overall_health = "unknown"
		if not health.get("has_error", True) and health.get("value") is not None:
			health_data = health.get("value", {})
			overall_health = health_data.get("body", {}).get("Overall Health", {}).get("value", "unknown")
		
		gpu_labels = f'gpu_uuid="{uuid}",gpu_index="{gpu_idx}",gpu_name="{name}",gpu_health="{overall_health.lower()}"'
		
		# Power
		power = gpu_data.get("power", {})
		if not power.get("has_error", True) and power.get("value") is not None:
			prometheus_lines.append(f"gpu_power_watts{{{gpu_labels}}} {power['value']}")
		
		# Temperature
		temp = gpu_data.get("temp", {})
		if not temp.get("has_error", True) and temp.get("value") is not None:
			prometheus_lines.append(f"gpu_temperature_celsius{{{gpu_labels}}} {temp['value']}")
		
		# Clocks
		clocks = gpu_data.get("clocks", {})
		if not clocks.get("has_error", True) and clocks.get("value") is not None:
			clock_data = clocks["value"]
			if "gpu_clock_mhz" in clock_data:
				prometheus_lines.append(f"gpu_clock_mhz{{{gpu_labels}}} {clock_data['gpu_clock_mhz']}")
			if "memory_clock_mhz" in clock_data:
				prometheus_lines.append(f"gpu_memory_clock_mhz{{{gpu_labels}}} {clock_data['memory_clock_mhz']}")
		
		# Utilization
		util = gpu_data.get("util", {})
		if not util.get("has_error", True) and util.get("value") is not None:
			util_data = util["value"]
			if "gpu_utilization_percent" in util_data:
				prometheus_lines.append(f"gpu_utilization_percent{{{gpu_labels}}} {util_data['gpu_utilization_percent']}")
			if "memory_utilization_percent" in util_data:
				prometheus_lines.append(f"gpu_memory_utilization_percent{{{gpu_labels}}} {util_data['memory_utilization_percent']}")
		
		# Memory
		mem = gpu_data.get("mem", {})
		if not mem.get("has_error", True) and mem.get("value") is not None:
			mem_data = mem["value"]
			if "memory_used_mib" in mem_data:
				prometheus_lines.append(f"gpu_memory_used_mib{{{gpu_labels}}} {mem_data['memory_used_mib']}")
			if "memory_total_mib" in mem_data:
				prometheus_lines.append(f"gpu_memory_total_mib{{{gpu_labels}}} {mem_data['memory_total_mib']}")
			if "memory_usage_percent" in mem_data:
				prometheus_lines.append(f"gpu_memory_usage_percent{{{gpu_labels}}} {mem_data['memory_usage_percent']}")
		
		# Fan
		fan = gpu_data.get("fan", {})
		if not fan.get("has_error", True) and fan.get("value") is not None:
			prometheus_lines.append(f"gpu_fan_speed{{{gpu_labels}}} {fan['value']}")
		
		# Health status as a metric
		if not health.get("has_error", True) and health.get("value") is not None:
			# Map health status to numeric values
			health_map = {"healthy": 0, "caution": 1, "warning": 2, "critical": 3}
			health_value = health_map.get(overall_health.lower(), 4)  # 4 for Unknown
			prometheus_lines.append(f"gpu_health_status{{{gpu_labels}}} {health_value}")

	return Response(content="\n".join(prometheus_lines) + "\n", media_type="text/plain")


@app.get("/gpu/{gpu_uuid}")
def get_gpu_full(gpu_uuid: str, method: str = Query("nvml")):
	"""Return all info about a specific GPU"""
	data = _run_core_py(method, ["--all"])
	gpu_data = _extract_gpu_by_uuid(data, gpu_uuid)
	if not gpu_data:
		raise HTTPException(status_code=404, detail="GPU not found")
	return JSONResponse(content=gpu_data)


@app.get("/gpu/{gpu_uuid}/static")
def get_gpu_static(gpu_uuid: str, method: str = Query("nvml")):
	"""Return static information about a specific GPU"""
	data = _run_core_py(method, ["--" + field for field in STATIC_FIELDS])
	gpu_data = _extract_gpu_by_uuid(data, gpu_uuid)
	if not gpu_data:
		raise HTTPException(status_code=404, detail="GPU not found")
	for field in STATIC_FIELDS:
		if field in gpu_data:
			gpu_data[field] = gpu_data[field].get("value", None)
		else:
			gpu_data[field] = None
	return JSONResponse(content=gpu_data)


@app.get("/gpu/{gpu_uuid}/{key_path:path}")
def get_gpu_field_deep(gpu_uuid: str, key_path: str = Path(...), method: str = Query("nvml")):
    """
    Allows nested field access using slash-separated path.
    Example: /gpu/{uuid}/clocks/memory_clock_mhz
    """
    data = _run_core_py(method, ["--all"])
    gpu_data = _extract_gpu_by_uuid(data, gpu_uuid)
    if not gpu_data:
        raise HTTPException(status_code=404, detail="GPU not found")

    keys = key_path.strip("/").split("/")
    current = gpu_data
    try:
        for k in keys:
            current = current[k] if isinstance(current, dict) else current[int(k)]
        return JSONResponse(content={key_path: current})
    except (KeyError, IndexError, ValueError, TypeError):
        raise HTTPException(status_code=404, detail=f"Field path '{key_path}' not found")

