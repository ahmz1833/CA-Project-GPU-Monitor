import sys
import json
import random
import subprocess
from enum import Enum
from collections import namedtuple
from typing import Dict, Callable, Any

try:
    import pynvml
except ImportError:
    pynvml = None

GPUInfo = namedtuple('GPUInfo', ['device', 'idx'])
CommandResult = namedtuple('CommandResult', ['output', 'exit_code'])


def make_result(success: bool, value: Any, error: str = "") -> Dict:
    return {
        "value": value,
        "has_error": not success,
        "error": error if not success else ""
    }


def make_error_json(msg: str) -> Dict:
    return make_result(False, None, msg)


class NvmlMethod:
    @staticmethod
    def register_query_functions(query_functions: Dict[str, Callable]) -> None:
        def nvml_str_query(func, key, buf_size):
            def wrapper(info: GPUInfo) -> Dict:
                try:
                    buf = func(info.device)
                    return {key: make_result(True, buf)}
                except pynvml.NVMLError as e:
                    return {key: make_result(False, "", str(e))}

            return wrapper

        def nvml_sys_str_query(func, key, buf_size):
            def wrapper(info: GPUInfo) -> Dict:
                try:
                    buf = func()
                    return {key: make_result(True, buf)}
                except pynvml.NVMLError as e:
                    return {key: make_result(False, "", str(e))}

            return wrapper

        def nvml_uint_query(func, key):
            def wrapper(info: GPUInfo) -> Dict:
                try:
                    val = func(info.device)
                    return {key: make_result(True, val)}
                except pynvml.NVMLError as e:
                    return {key: make_result(False, 0, str(e))}

            return wrapper

        def nvml_pwr_query(func, key):
            def wrapper(info: GPUInfo) -> Dict:
                try:
                    raw = func(info.device)
                    val = raw / 1000.0
                    return {key: make_result(True, val)}
                except pynvml.NVMLError as e:
                    return {key: make_result(False, 0.0, str(e))}

            return wrapper

        query_functions["--name"] = nvml_str_query(pynvml.nvmlDeviceGetName, "name", 64)
        query_functions["--serial"] = nvml_str_query(pynvml.nvmlDeviceGetSerial, "serial", 30)
        query_functions["--uuid"] = nvml_str_query(pynvml.nvmlDeviceGetUUID, "uuid", 80)
        query_functions["--vbios"] = nvml_str_query(pynvml.nvmlDeviceGetVbiosVersion, "vbios", 32)
        query_functions["--driver"] = nvml_sys_str_query(pynvml.nvmlSystemGetDriverVersion, "driver", 80)

        query_functions["--temp"] = lambda info: {
            "temp": make_result(True, pynvml.nvmlDeviceGetTemperature(info.device, pynvml.NVML_TEMPERATURE_GPU))
        } if pynvml else {"temp": make_result(False, 0, "NVML not available")}

        query_functions["--fan"] = nvml_uint_query(pynvml.nvmlDeviceGetFanSpeed, "fan")
        query_functions["--minor"] = nvml_uint_query(pynvml.nvmlDeviceGetMinorNumber, "minor")

        def query_pstate(info: GPUInfo) -> Dict:
            try:
                st = pynvml.nvmlDeviceGetPerformanceState(info.device)
                ps = int(st)
                return {"pstate": make_result(True, ps)}
            except pynvml.NVMLError as e:
                return {"pstate": make_result(False, -1, str(e))}

        query_functions["--pstate"] = query_pstate

        query_functions["--pciegen"] = nvml_uint_query(pynvml.nvmlDeviceGetMaxPcieLinkGeneration, "pciegen")
        query_functions["--pciewidth"] = nvml_uint_query(pynvml.nvmlDeviceGetMaxPcieLinkWidth, "pciewidth")
        query_functions["--power"] = nvml_pwr_query(pynvml.nvmlDeviceGetPowerUsage, "power")
        query_functions["--plimit"] = nvml_pwr_query(pynvml.nvmlDeviceGetPowerManagementLimit, "plimit")

        def query_clocks(info: GPUInfo) -> Dict:
            err_msgs = []
            clocks = {"gpu_clock_mhz": 0, "memory_clock_mhz": 0}
            try:
                sm = pynvml.nvmlDeviceGetClockInfo(info.device, pynvml.NVML_CLOCK_SM)
                clocks["gpu_clock_mhz"] = sm
            except pynvml.NVMLError as e:
                err_msgs.append(f"SM Clock: {str(e)}")
            try:
                mem = pynvml.nvmlDeviceGetClockInfo(info.device, pynvml.NVML_CLOCK_MEM)
                clocks["memory_clock_mhz"] = mem
            except pynvml.NVMLError as e:
                err_msgs.append(f"Memory Clock: {str(e)}")
            return {"clocks": make_result(len(err_msgs) == 0, clocks, "; ".join(err_msgs))}

        query_functions["--clocks"] = query_clocks

        def query_mem(info: GPUInfo) -> Dict:
            try:
                m = pynvml.nvmlDeviceGetMemoryInfo(info.device)
                d = {
                    "memory_used_mib": m.used // (1024 * 1024),
                    "memory_total_mib": m.total // (1024 * 1024),
                    "memory_usage_percent": 100.0 * float(m.used) / float(m.total)
                }
                return {"mem": make_result(True, d)}
            except pynvml.NVMLError as e:
                d = {"memory_used_mib": 0, "memory_total_mib": 0, "memory_usage_percent": 0.0}
                return {"mem": make_result(False, d, str(e))}

        query_functions["--mem"] = query_mem

        def query_util(info: GPUInfo) -> Dict:
            try:
                u = pynvml.nvmlDeviceGetUtilizationRates(info.device)
                d = {
                    "gpu_utilization_percent": u.gpu,
                    "memory_utilization_percent": u.memory
                }
                return {"util": make_result(True, d)}
            except pynvml.NVMLError as e:
                d = {"gpu_utilization_percent": 0, "memory_utilization_percent": 0}
                return {"util": make_result(False, d, str(e))}

        query_functions["--util"] = query_util

        def query_ecc(info: GPUInfo) -> Dict:
            err_msgs = []
            ce, ue = 0, 0
            try:
                ce = pynvml.nvmlDeviceGetTotalEccErrors(
                    info.device, pynvml.NVML_MEMORY_ERROR_TYPE_CORRECTED, pynvml.NVML_VOLATILE_ECC
                )
            except pynvml.NVMLError as e:
                err_msgs.append(f"Corrected Errors: {str(e)}")
            try:
                ue = pynvml.nvmlDeviceGetTotalEccErrors(
                    info.device, pynvml.NVML_MEMORY_ERROR_TYPE_UNCORRECTED, pynvml.NVML_VOLATILE_ECC
                )
            except pynvml.NVMLError as e:
                err_msgs.append(f"Uncorrected Errors: {str(e)}")
            d = {"ecc_corrected_errors": ce, "ecc_uncorrected_errors": ue}
            return {"ecc": make_result(len(err_msgs) == 0, d, "; ".join(err_msgs))}

        query_functions["--ecc"] = query_ecc

        def query_processes(info: GPUInfo) -> Dict:
            try:
                procs = pynvml.nvmlDeviceGetComputeRunningProcesses(info.device)
                processes = []
                for p in procs:
                    processes.append({
                        "pid": p.pid,
                        "gpu_memory": p.usedGpuMemory
                    })
                return {
                    "processes": processes
                }
            except pynvml.NVMLError as _:
                return {
                    "processes": []
                }

        query_functions["--procs"] = query_processes

        def query_health(info: GPUInfo) -> Dict:
            return {
                "health": {
                    "has_error": True,
                    "error": "Value not available",
                    "value": "",
                }
            }

        query_functions["--health"] = query_health


class BashMethod:
    @staticmethod
    def trim(s: str) -> str:
        return s.strip()

    @staticmethod
    def execute(cmd: str) -> CommandResult:
        try:
            output = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True
            ).strip()
            return CommandResult(output, 0)
        except subprocess.CalledProcessError as e:
            return CommandResult(BashMethod.trim(e.output), e.returncode)

    @staticmethod
    def create_json(attr_name: str, value: str, return_code: int) -> Dict:
        success = return_code == 0 and value != "[N/A]"
        return {
            attr_name: make_result(
                success,
                value if success else "",
                "Value not available" if value == "[N/A]" else value
            )
        }

    @staticmethod
    def create_json_from_json(attr_name: str, value_json: Dict) -> Dict:
        return {attr_name: make_result(True, value_json)}

    @staticmethod
    def simple_query(query: str, attr_name: str) -> Callable[[int], Dict]:
        def func(index: int) -> Dict:
            cmd = f"nvidia-smi -i {index} --query-gpu={query} --format=csv,noheader,nounits"
            res = BashMethod.execute(cmd)
            return BashMethod.create_json(attr_name, res.output, res.exit_code)

        return func

    @staticmethod
    def complex_query(parser: Callable, query: str, attr_name: str) -> Callable[[int], Dict]:
        def func(index: int) -> Dict:
            cmd = f"nvidia-smi -i {index} --query-gpu={query} --format=csv,noheader,nounits"
            res = BashMethod.execute(cmd)
            if res.exit_code != 0:
                return BashMethod.create_json(attr_name, res.output, res.exit_code)
            # noinspection PyBroadException
            try:
                parts = res.output.split(', ')
                val1, val2 = parts[0].strip(), parts[1].strip()
                return BashMethod.create_json_from_json(attr_name, parser(val1, val2))
            except Exception:
                return BashMethod.create_json(attr_name, f"Parse error: {res.output}", -1)

        return func

    @staticmethod
    def register_query_functions(query_functions: Dict[str, Callable]) -> None:
        def adapter(func: Callable) -> Callable:
            return lambda info: func(info.idx)

        query_functions["--name"] = adapter(BashMethod.simple_query("gpu_name", "name"))
        query_functions["--uuid"] = adapter(BashMethod.simple_query("uuid", "uuid"))
        query_functions["--vbios"] = adapter(BashMethod.simple_query("vbios_version", "vbios"))
        query_functions["--temp"] = adapter(BashMethod.simple_query("temperature.gpu", "temp"))
        query_functions["--serial"] = adapter(BashMethod.simple_query("serial", "serial"))
        query_functions["--pstate"] = adapter(BashMethod.simple_query("pstate", "pstate"))
        query_functions["--power"] = adapter(BashMethod.simple_query("power.draw", "power"))
        query_functions["--plimit"] = adapter(BashMethod.simple_query("power.limit", "plimit"))
        query_functions["--driver"] = adapter(BashMethod.simple_query("driver_version", "driver"))
        query_functions["--ecc"] = adapter(BashMethod.simple_query("ecc.mode.current", "ecc"))
        query_functions["--fan"] = adapter(BashMethod.simple_query("fan.speed", "fan"))

        def not_supported(_: int) -> Dict:
            return BashMethod.create_json("pciewidth", "Not Supported", 1)

        query_functions["--pciewidth"] = adapter(not_supported)

        def not_supported2(_: int) -> Dict:
            return BashMethod.create_json("pciegen", "Not Supported", 1)

        query_functions["--pciegen"] = adapter(not_supported2)

        def not_supported3(_: int) -> Dict:
            return BashMethod.create_json("minor", "Not Supported", 1)

        query_functions["--minor"] = adapter(not_supported3)

        def mem_parser(total: str, used: str) -> Dict:
            total_val = float(total)
            used_val = float(used)
            usage_percent = (used_val / total_val) * 100.0 if total_val > 0 else 0.0
            return {
                "memory_total_mib": int(total_val),
                "memory_used_mib": int(used_val),
                "memory_usage_percent": usage_percent
            }

        query_functions["--mem"] = adapter(
            BashMethod.complex_query(mem_parser, "memory.total,memory.used", "mem")
        )

        def clocks_parser(gpu: str, mem: str) -> Dict:
            return {"gpu_clock_mhz": int(gpu), "memory_clock_mhz": int(mem)}

        query_functions["--clocks"] = adapter(
            BashMethod.complex_query(clocks_parser, "clocks.gr,clocks.mem", "clocks")
        )

        def util_parser(gpu: str, mem: str) -> Dict:
            return {"gpu_utilization_percent": int(gpu), "memory_utilization_percent": int(mem)}

        query_functions["--util"] = adapter(
            BashMethod.complex_query(util_parser, "utilization.gpu,utilization.memory", "util")
        )

        def query_processes(info: GPUInfo) -> Dict:
            return {
                "processes": []
            }

        query_functions["--procs"] = query_processes

        def query_health(info: GPUInfo) -> Dict:
            cmd_check = f"dcgmi health --host localhost -g {info.idx} -c -j"
            out = BashMethod.execute(cmd_check)
            data = None
            if out.exit_code == 0:
                try:
                    data = json.loads(out.output)
                except json.JSONDecodeError:
                    out.exit_code = 1
            return {
                "health": {
                    "has_error": out.exit_code != 0,
                    "error": "" if out.exit_code == 0 else out.output,
                    "value": data if out.exit_code == 0 else "",
                }
            }

        query_functions["--health"] = query_health


class SimMethod:
    @staticmethod
    def register_query_functions(funcs: dict) -> None:
        names = ["SIM-RTX4090", "SIM-RTX3080", "SIM-GTX1060"]
        uuids = [
            "GPU-0a1b2c3d-4e5f-6172-8192-334455667788",
            "GPU-1b2c3d4e-5f6a-7b8c-9d0e-112233445566",
            "GPU-2c3d4e5f-6a7b-8c9d-0e1f-223344556677"
        ]
        serials = ["SIM123456", "SIM654321", "SIM000001"]
        vbios_versions = ["90.00.01.00.AB", "90.00.02.00.CD", "90.00.03.00.EF"]
        driver_version = "525.00"

        base_temps = [45, 55, 65]
        base_fans = [40, 60, 80]
        base_power = [100, 200, 300]
        base_gpu_clocks = [2100, 1800, 1500]
        base_mem_clocks = [1100, 900, 700]
        base_utils = [30, 60, 90]
        base_mem_used = [3000, 6000, 2000]
        base_mem_total = [24000, 16000, 8000]

        def add_noise(base_value, variation=0.1):
            noise = base_value * variation * random.uniform(-1, 1)
            return max(base_value + noise, base_value * 0.5)

        def mk_result(success, value, error_msg=""):
            return {'value': value, 'has_error': not success, 'error': error_msg}

        def fixed_attr_query(attr_name, values):
            def wrapper(info):
                return {attr_name: mk_result(True, values[info.idx])}

            return wrapper

        def temp_query(info):
            base = base_temps[info.idx]
            return {"temp": mk_result(True, add_noise(base, 0.05))}

        def fan_query(info):
            base = base_fans[info.idx]
            return {"fan": mk_result(True, add_noise(base, 0.1))}

        def power_query(info):
            base = base_power[info.idx]
            return {"power": mk_result(True, add_noise(base, 0.15))}

        def clocks_query(info):
            return {"clocks": mk_result(True, {
                "gpu_clock_mhz": add_noise(base_gpu_clocks[info.idx], 0.05),
                "memory_clock_mhz": add_noise(base_mem_clocks[info.idx], 0.05)
            })}

        def util_query(info):
            return {"util": mk_result(True, {
                "gpu_utilization_percent": add_noise(base_utils[info.idx], 0.2),
                "memory_utilization_percent": add_noise(base_utils[info.idx] * 0.8, 0.2)
            })}

        def mem_query(info):
            idx = info.idx
            used = add_noise(base_mem_used[idx], 0.15)
            total = base_mem_total[idx]
            return {"mem": mk_result(True, {
                "memory_used_mib": used,
                "memory_total_mib": total,
                "memory_usage_percent": 100 * used / total
            })}

        def query_processes(info) -> Dict:
            num_processes = random.randint(0, 5)
            processes = []
            for _ in range(num_processes):
                processes.append({
                    "pid": random.randint(1000, 9999),
                    "gpu_memory": random.randint(100, 2000) * 1024 * 1024 if random.random() < 0.8 else None})
            return {
                "processes": processes
            }

        funcs.update({
            "--name": fixed_attr_query("name", names),
            "--uuid": fixed_attr_query("uuid", uuids),
            "--serial": fixed_attr_query("serial", serials),
            "--vbios": fixed_attr_query("vbios", vbios_versions),
            "--driver": lambda _: {"driver": mk_result(True, driver_version)},
            "--temp": temp_query,
            "--fan": fan_query,
            "--power": power_query,
            "--clocks": clocks_query,
            "--util": util_query,
            "--mem": mem_query,
            "--minor": fixed_attr_query("minor", [0, 1, 2]),
            "--pstate": fixed_attr_query("pstate", [0, 1, 2]),
            "--pciegen": fixed_attr_query("pciegen", [4, 3, 2]),
            "--pciewidth": fixed_attr_query("pciewidth", [16, 8, 4]),
            "--plimit": fixed_attr_query("plimit", [350, 250, 150]),
            "--procs": query_processes,

            "--ecc": lambda _: {"ecc": mk_result(True, {
                "ecc_corrected_errors": 0,
                "ecc_uncorrected_errors": 0
            })}
        })


class QueryMethod(Enum):
    NVML = 1
    BASH = 2
    SIM = 3


class GPUQuery:
    def __init__(self, method: QueryMethod) -> None:
        self.method = method
        self.initialized = False
        self.query_functions = {}
        if method == QueryMethod.NVML:
            if pynvml:
                NvmlMethod.register_query_functions(self.query_functions)
            else:
                raise RuntimeError("pynvml not installed for NVML method")
        elif method == QueryMethod.BASH:
            BashMethod.register_query_functions(self.query_functions)
        elif method == QueryMethod.SIM:
            SimMethod.register_query_functions(self.query_functions)
        else:
            raise RuntimeError(f"Unknown query method: {method}")

    def __del__(self) -> None:
        if self.initialized and self.method == QueryMethod.NVML and pynvml:
            # noinspection PyBroadException
            try:
                pynvml.nvmlShutdown()
            except:
                pass

    def initialize(self) -> bool:
        if self.method == QueryMethod.NVML:
            try:
                pynvml.nvmlInit()
                self.initialized = True
                return True
            except pynvml.NVMLError:
                return False
        return True

    def get_gpu_count(self) -> int:
        if self.method == QueryMethod.NVML:
            try:
                return pynvml.nvmlDeviceGetCount()
            except pynvml.NVMLError:
                return 0
        elif self.method == QueryMethod.SIM:
            return 3
        else:
            # noinspection PyBroadException
            try:
                cmd = "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l"
                res = subprocess.check_output(cmd, shell=True, text=True)
                return int(res.strip())
            except:
                return 0

    def execute_query(self, index: int, flags: list) -> dict:
        info = GPUInfo(None, index)
        if self.method == QueryMethod.NVML:
            try:
                device = pynvml.nvmlDeviceGetHandleByIndex(index)
                info = info._replace(device=device)
            except pynvml.NVMLError as e:
                return {"error": make_error_json(str(e))}

        gpu_json = {}
        if "--all" in flags:
            for flag, func in self.query_functions.items():
                if flag != "--count":
                    res = func(info)
                    gpu_json.update(res)
        else:
            for flag in flags:
                if flag in self.query_functions and flag != "--count":
                    res = self.query_functions[flag](info)
                    gpu_json.update(res)
        return gpu_json

    def query_gpu(self, target_gpu: int, flags: list) -> dict:
        result = {}
        count = self.get_gpu_count()

        if "--count" in flags:
            result["count"] = count

        need_per_gpu = any(flag != "--count" for flag in flags)
        if count == 0:
            if need_per_gpu:
                result["error"] = "No NVIDIA GPUs found"
            return result

        if not need_per_gpu:
            return result

        if target_gpu >= count:
            return {"error": f"Invalid GPU index: {target_gpu}"}

        if target_gpu >= 0:
            result["gpus"] = {str(target_gpu): self.execute_query(target_gpu, flags)}
        else:
            result["gpus"] = {}
            for i in range(count):
                result["gpus"][str(i)] = self.execute_query(i, flags)

        return result


def print_usage(prog: str) -> None:
    print(f"Usage: {prog} [--bash|--nvml|--sim] [--gpu <idx>] [OPTION]...")
    print("Query Methods:")
    print("  --bash        Use nvidia-smi commands for querying")
    print("  --nvml        Use NVML library for querying (default)")
    print("  --sim         Use simulated GPU data for querying")
    print()
    print("Options:")
    print("  --count       Show GPU count\n  --name        Show GPU name")
    print("  --temp        Show GPU temperature\n  --clocks      Show GPU and memory clocks")
    print("  --power       Show power usage\n  --plimit      Show power limit")
    print("  --mem         Show memory usage\n  --util        Show GPU and memory utilization")
    print("  --uuid        Show GPU UUID\n  --fan         Show fan speed")
    print("  --minor       Show minor number")
    print("  --serial      Show serial number\n  --vbios       Show VBIOS version")
    print("  --driver      Show driver version\n  --ecc         Show ECC error counts")
    print("  --pstate      Show performance state\n  --pciegen     Show PCIe generation")
    print("  --pciewidth   Show PCIe width\n  --health      Show GPU health status")
    print("  --procs       Show processes using GPU\n  --all         Show all information")


def main() -> None:
    valid_flags = [
        "--count", "--name", "--temp", "--clocks", "--power", "--plimit", "--mem", "--util",
        "--uuid", "--fan", "--minor", "--serial", "--vbios", "--driver", "--ecc",
        "--pstate", "--pciegen", "--pciewidth", "--procs", "--health", "--all"
    ]

    method = QueryMethod.NVML
    filtered_args = [sys.argv[0]]
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--bash":
            method = QueryMethod.BASH
        elif arg == "--nvml":
            method = QueryMethod.NVML
        elif arg == "--sim":
            method = QueryMethod.SIM
        else:
            filtered_args.append(arg)
        i += 1

    # Parse arguments
    target_gpu = -1
    flags = []
    i = 1
    while i < len(filtered_args):
        arg = filtered_args[i]
        if arg == "--gpu":
            if i + 1 >= len(filtered_args):
                print_usage(sys.argv[0])
                sys.exit(1)
            try:
                target_gpu = int(filtered_args[i + 1])
                i += 1
            except ValueError:
                print_usage(sys.argv[0])
                sys.exit(1)
        elif arg in valid_flags:
            flags.append(arg)
        else:
            print_usage(sys.argv[0])
            sys.exit(1)
        i += 1

    if not flags:
        print_usage(sys.argv[0])
        return

    try:
        tool = GPUQuery(method)
        if not tool.initialize():
            print("Failed to initialize NVIDIA query tool", file=sys.stderr)
            sys.exit(1)
        result = tool.query_gpu(target_gpu, flags)
        print(json.dumps(result, indent=4))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
