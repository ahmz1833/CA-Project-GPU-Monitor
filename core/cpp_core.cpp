#include <map>
#include <vector>
#include <string>
#include <iostream>
#include <algorithm>

#include <nvml.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

struct GPUInfo {
    nvmlDevice_t device;
    int idx;
};


class NvmlMethod {
public:
    static void registerQueryFunctions(
            std::map<std::string, std::function<json(const GPUInfo &)>> &query_functions_) {

        auto makeResult = [](bool success, auto value, const char *error = "") {
            return json{
                    {"value",     value},
                    {"has_error", !success},
                    {"error",     success ? "" : error}
            };
        };

#define NVML_STR_Q(cmd, json_key, buf_size)                                                             \
            query_functions_["--" json_key] = [&](const GPUInfo &info) {                                \
                char buf[buf_size];                                                                     \
                nvmlReturn_t ret = cmd(info.device, buf, sizeof(buf));                                  \
                return json{{json_key, makeResult(ret == NVML_SUCCESS,                                  \
                                                ret == NVML_SUCCESS ? std::string(buf) : std::string(), \
                                                nvmlErrorString(ret))}};                                \
            };

#define NVML_SYS_STR_Q(cmd, json_key, buf_size)                                                          \
            query_functions_["--" json_key] = [&](const GPUInfo &) {                                     \
                char buf[buf_size];                                                                      \
                nvmlReturn_t ret = cmd(buf, sizeof(buf));                                                \
                return json{{json_key, makeResult(ret == NVML_SUCCESS,                                   \
                                                ret == NVML_SUCCESS ? std::string(buf) : std::string(),  \
                                                nvmlErrorString(ret))}};                                 \
            };

#define NVML_UINT_Q(cmd, json_key)                                             \
            query_functions_["--" json_key] = [&](const GPUInfo &info) {       \
                unsigned val = 0;                                              \
                nvmlReturn_t ret = cmd(info.device, &val);                     \
                return json{{json_key, makeResult(ret == NVML_SUCCESS,         \
                                                ret == NVML_SUCCESS ? val : 0u,\
                                                nvmlErrorString(ret))}};       \
            };

#define NVML_PWR_Q(cmd, json_key)                                                                     \
            query_functions_["--" json_key] = [&](const GPUInfo &info) {                              \
                unsigned raw = 0;                                                                     \
                nvmlReturn_t ret = cmd(info.device, &raw);                                            \
                double val = (ret == NVML_SUCCESS) ? raw / 1000.0 : 0.0;                              \
                return json{{json_key, makeResult(ret == NVML_SUCCESS, val, nvmlErrorString(ret))}};  \
            };

        NVML_STR_Q(nvmlDeviceGetName, "name", NVML_DEVICE_NAME_BUFFER_SIZE)
        NVML_STR_Q(nvmlDeviceGetSerial, "serial", NVML_DEVICE_SERIAL_BUFFER_SIZE)
        NVML_STR_Q(nvmlDeviceGetUUID, "uuid", NVML_DEVICE_UUID_BUFFER_SIZE)
        NVML_STR_Q(nvmlDeviceGetVbiosVersion, "vbios", NVML_DEVICE_VBIOS_VERSION_BUFFER_SIZE)

        NVML_SYS_STR_Q(nvmlSystemGetDriverVersion, "driver", NVML_SYSTEM_DRIVER_VERSION_BUFFER_SIZE)

        query_functions_["--temp"] = [&](const GPUInfo &info) {
            unsigned temp = 0;
            nvmlReturn_t ret = nvmlDeviceGetTemperature(info.device, NVML_TEMPERATURE_GPU, &temp);
            return json{
                    {"temp", makeResult(ret == NVML_SUCCESS, ret == NVML_SUCCESS ? temp : 0u, nvmlErrorString(ret))}};
        };

        NVML_UINT_Q(nvmlDeviceGetFanSpeed, "fan")
        NVML_UINT_Q(nvmlDeviceGetMinorNumber, "minor")
        query_functions_["--pstate"] = [&](const GPUInfo &info) {
            nvmlPstates_t st;
            nvmlReturn_t ret = nvmlDeviceGetPerformanceState(info.device, &st);
            int ps = (ret == NVML_SUCCESS) ? static_cast<int>(st) : -1;
            return json{{"pstate", makeResult(ret == NVML_SUCCESS, ps, nvmlErrorString(ret))}};
        };
        NVML_UINT_Q(nvmlDeviceGetMaxPcieLinkGeneration, "pciegen")
        NVML_UINT_Q(nvmlDeviceGetMaxPcieLinkWidth, "pciewidth")

        NVML_PWR_Q(nvmlDeviceGetPowerUsage, "power")
        NVML_PWR_Q(nvmlDeviceGetPowerManagementLimit, "plimit")

        query_functions_["--clocks"] = [&](const GPUInfo &info) {
            json clocks;
            bool has_error = false;
            std::string err;
            unsigned sm = 0, mem = 0;
            auto chk = [&](nvmlReturn_t r, const char *label) {
                if (r != NVML_SUCCESS) {
                    has_error = true;
                    if (!err.empty()) err += "; ";
                    err += std::string(label) + ": " + nvmlErrorString(r);
                }
            };
            chk(nvmlDeviceGetClockInfo(info.device, NVML_CLOCK_SM, &sm), "SM Clock");
            chk(nvmlDeviceGetClockInfo(info.device, NVML_CLOCK_MEM, &mem), "Memory Clock");
            clocks["gpu_clock_mhz"] = sm;
            clocks["memory_clock_mhz"] = mem;
            return json{{"clocks", makeResult(!has_error, clocks, err.c_str())}};
        };

        query_functions_["--mem"] = [&](const GPUInfo &info) {
            nvmlMemory_t m;
            nvmlReturn_t r = nvmlDeviceGetMemoryInfo(info.device, &m);
            json d;
            if (r == NVML_SUCCESS) {
                d["memory_used_mib"] = m.used / (1024 * 1024);
                d["memory_total_mib"] = m.total / (1024 * 1024);
                d["memory_usage_percent"] = 100.0 * double(m.used) / double(m.total);
            } else {
                d["memory_used_mib"] = 0;
                d["memory_total_mib"] = 0;
                d["memory_usage_percent"] = 0.0;
            }
            return json{{"mem", makeResult(r == NVML_SUCCESS, d, nvmlErrorString(r))}};
        };

        query_functions_["--util"] = [&](const GPUInfo &info) {
            nvmlUtilization_t u;
            nvmlReturn_t r = nvmlDeviceGetUtilizationRates(info.device, &u);
            json d;
            if (r == NVML_SUCCESS) {
                d["gpu_utilization_percent"] = u.gpu;
                d["memory_utilization_percent"] = u.memory;
            } else {
                d["gpu_utilization_percent"] = 0;
                d["memory_utilization_percent"] = 0;
            }
            return json{{"util", makeResult(r == NVML_SUCCESS, d, nvmlErrorString(r))}};
        };

        query_functions_["--ecc"] = [&](const GPUInfo &info) {
            json d;
            bool has_error = false;
            std::string err;
            unsigned long long ce = 0, ue = 0;
            auto chk_ecc = [&](nvmlReturn_t r, const char *lbl, unsigned long long &out) {
                if (r == NVML_SUCCESS) out = out;
                else {
                    has_error = true;
                    if (!err.empty()) err += "; ";
                    err += std::string(lbl) + ": " + nvmlErrorString(r);
                }
            };
            chk_ecc(nvmlDeviceGetTotalEccErrors(info.device, NVML_MEMORY_ERROR_TYPE_CORRECTED, NVML_VOLATILE_ECC, &ce),
                    "Corrected Errors", ce);
            chk_ecc(nvmlDeviceGetTotalEccErrors(info.device, NVML_MEMORY_ERROR_TYPE_UNCORRECTED, NVML_VOLATILE_ECC,
                                                &ue), "Uncorrected Errors", ue);
            d["ecc_corrected_errors"] = ce;
            d["ecc_uncorrected_errors"] = ue;
            return json{{"ecc", makeResult(!has_error, d, err.c_str())}};
        };

#undef NVML_STR_Q
#undef NVML_SYS_STR_Q
#undef NVML_UINT_Q
#undef NVML_PWR_Q
    }
};

class BashMethod {
public:
    static void registerQueryFunctions(std::map<std::string, std::function<json(const GPUInfo &)>> &query_functions) {
        auto adapter = [](auto func) {
            return [func](const GPUInfo &info) { return func(info.idx); };
        };

#define REGISTER_SIMPLE_QUERY(name, query) query_functions[name] = adapter([](int idx) { \
                std::string raw = #name;                                                         \
                std::string clean = raw.substr(3, raw.length() - 4);                             \
                return simple_query(idx, query, clean);                                          \
                });

        REGISTER_SIMPLE_QUERY("--name", "gpu_name")
        REGISTER_SIMPLE_QUERY("--uuid", "uuid")
        REGISTER_SIMPLE_QUERY("--vbios", "vbios_version")
        REGISTER_SIMPLE_QUERY("--temp", "temperature.gpu")
        REGISTER_SIMPLE_QUERY("--serial", "serial")
        REGISTER_SIMPLE_QUERY("--pstate", "pstate")
        REGISTER_SIMPLE_QUERY("--power", "power.draw")
        REGISTER_SIMPLE_QUERY("--plimit", "power.limit")
        REGISTER_SIMPLE_QUERY("--driver", "driver_version")
        REGISTER_SIMPLE_QUERY("--ecc", "ecc.mode.current")
        REGISTER_SIMPLE_QUERY("--fan", "fan.speed")

        query_functions["--pciewidth"] = adapter(get_pciewidth);
        query_functions["--pciegen"] = adapter(get_pciegen);
        query_functions["--minor"] = adapter(get_minor);
        query_functions["--mem"] = adapter(get_mem);
        query_functions["--clocks"] = adapter(get_clocks);
        query_functions["--util"] = adapter(get_utilization);
    }

private:
    struct CommandResult {
        std::string output;
        int exit_code;
    };

    static std::string trim(const std::string &str) {
        auto start = std::find_if_not(str.begin(), str.end(), [](int c) {
            return std::isspace(c);
        });
        auto end = std::find_if_not(str.rbegin(), str.rend(), [](int c) {
            return std::isspace(c);
        }).base();
        return (start < end) ? std::string(start, end) : "";
    }

    static CommandResult execute(const std::string &cmd) {
        std::array<char, 1024> buffer{};
        std::string result;
        FILE *pipe = popen(cmd.c_str(), "r");
        if (!pipe) throw std::runtime_error("popen() failed!");

        while (fgets(buffer.data(), buffer.size(), pipe))
            result += buffer.data();

        int status = pclose(pipe);
        int exit_code = (WIFEXITED(status)) ? WEXITSTATUS(status) : -1;
        return {trim(result), exit_code};
    }

    static json create_json(const std::string &attribute_name,
                            const std::string &value,
                            int return_code) {
        bool success = (return_code == 0 && value != "[N/A]");
        return json{
                {attribute_name, {
                        {"value", success ? value : ""},
                        {"has_error", !success},
                        {"error", success ? "" : (value == "[N/A]" ?
                                                  "Value not available" : value)}}}
        };
    }

    static json create_json_from_json(const std::string &attribute_name, const json &value_json) {
        return json{
                {attribute_name, {
                        {"value", value_json},
                        {"has_error", false},
                        {"error", ""}}}};
    }

    static json simple_query(int index, const std::string &query, const std::string &attr_name) {
        std::string cmd = "nvidia-smi -i " + std::to_string(index) +
                          " --query-gpu=" + query +
                          " --format=csv,noheader,nounits";
        CommandResult result = execute(cmd);
        return create_json(attr_name, result.output, result.exit_code);
    }

    template<typename T1, typename T2, typename F>
    static json complex_query(int index, const std::string &query,
                              const std::string &attr_name, F parser) {
        std::string cmd = "nvidia-smi -i " + std::to_string(index) +
                          " --query-gpu=" + query +
                          " --format=csv,noheader,nounits";
        CommandResult result = execute(cmd);

        if (result.exit_code != 0)
            return create_json(attr_name, result.output, result.exit_code);

        std::istringstream iss(result.output);
        T1 val1;
        T2 val2;
        char comma;
        if (!(iss >> val1 >> comma >> val2))
            return create_json(attr_name, "Parse error: " + result.output, -1);

        return create_json_from_json(attr_name, parser(val1, val2));
    }

    static json get_pciewidth(int _) {
        return create_json("pciewidth", "Not Supported", 1);
    }

    static json get_pciegen(int _) {
        return create_json("pciegen", "Not Supported", 1);
    }

    static json get_minor(int _) {
        return create_json("minor", "Not Supported", 1);
    }

    static json get_mem(int index) {
        auto parser = [](float total, float used) -> json {
            float usage_percent = (total > 0) ? (used / total) * 100.0f : 0.0f;
            return json{
                    {"memory_total_mib",     static_cast<int>(total)},
                    {"memory_used_mib",      static_cast<int>(used)},
                    {"memory_usage_percent", usage_percent}
            };
        };
        return complex_query<float, float>(index, "memory.total,memory.used", "mem", parser);
    }

    static json get_clocks(int index) {
        auto parser = [](int gpu_clock, int mem_clock) -> json {
            return json{
                    {"gpu_clock_mhz",    gpu_clock},
                    {"memory_clock_mhz", mem_clock}
            };
        };
        return complex_query<int, int>(index, "clocks.gr,clocks.mem", "clocks", parser);
    }

    static json get_utilization(int index) {
        auto parser = [](int gpu_util, int mem_util) -> json {
            return json{
                    {"gpu_utilization_percent",    gpu_util},
                    {"memory_utilization_percent", mem_util}
            };
        };
        return complex_query<int, int>(index, "utilization.gpu,utilization.memory", "util", parser);
    }
};

enum class QueryMethod {
    NVML, BASH
};


class GPUQuery {
    QueryMethod method_;
    bool initialized_ = false;
    std::map<std::string, std::function<json(const GPUInfo &)>> query_functions_;

    json executeQuery(unsigned index, const std::vector<std::string> &flags) {
        GPUInfo info{};
        info.idx = static_cast<int>(index);

        if (method_ == QueryMethod::NVML) {
            nvmlReturn_t ret = nvmlDeviceGetHandleByIndex(index, &info.device);
            if (ret != NVML_SUCCESS) {
                return json{{"error", makeErrorJson(nvmlErrorString(ret))}};
            }
        }

        json gpuJson;
        if (std::find(flags.begin(), flags.end(), "--all") != flags.end()) {
            for (const auto &[flag, func]: query_functions_) {
                if (flag != "--count") {
                    json result = func(info);
                    gpuJson.update(result);
                }
            }
        } else {
            for (const auto &flag: flags) {
                if (query_functions_.count(flag) && flag != "--count") {
                    json result = query_functions_[flag](info);
                    gpuJson.update(result);
                }
            }
        }
        return gpuJson;
    }

    static json makeErrorJson(const std::string &msg) {
        return json{
                {"value",     nullptr},
                {"has_error", true},
                {"error",     msg}
        };
    }

public:
    explicit GPUQuery(QueryMethod method) : method_(method) {
        if (method_ == QueryMethod::NVML) {
            NvmlMethod::registerQueryFunctions(query_functions_);
        } else {
            BashMethod::registerQueryFunctions(query_functions_);
        }
    }

    ~GPUQuery() {
        if (initialized_ && method_ == QueryMethod::NVML) {
            nvmlShutdown();
        }
    }

    bool initialize() {
        if (method_ == QueryMethod::NVML) {
            nvmlReturn_t ret = nvmlInit();
            if (ret == NVML_SUCCESS) {
                initialized_ = true;
                return true;
            }
            return false;
        }
        return true;
    }

    unsigned getGPUCount() {
        if (method_ == QueryMethod::NVML) {
            unsigned count = 0;
            nvmlReturn_t ret = nvmlDeviceGetCount(&count);
            return (ret == NVML_SUCCESS) ? count : 0;
        } else {
            const char *cmd = "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l";
            std::array<char, 1024> buffer{};
            unsigned count = 0;

            FILE *pipe = popen(cmd, "r");
            if (!pipe) return 0;

            if (fgets(buffer.data(), buffer.size(), pipe)) {
                count = std::strtoul(buffer.data(), nullptr, 10);
            }
            pclose(pipe);
            return count;
        }
    }

    json queryGPU(int targetGpu, const std::vector<std::string> &flags) {
        json result;
        unsigned count = getGPUCount();

        bool countRequested = std::find(flags.begin(), flags.end(), "--count") != flags.end();
        if (countRequested) {
            result["count"] = count;
        }

        bool needPerGPU = std::any_of(flags.begin(), flags.end(), [](const std::string &flag) {
            return flag != "--count";
        });

        if (count == 0) {
            if (needPerGPU) {
                result["error"] = "No NVIDIA GPUs found";
            }
            return result;
        }

        if (!needPerGPU) {
            return result;
        }

        if (targetGpu >= static_cast<int>(count)) {
            return json{{"error", "Invalid GPU index: " + std::to_string(targetGpu)}};
        }

        if (targetGpu >= 0) {
            result["gpus"][std::to_string(targetGpu)] = executeQuery(targetGpu, flags);
        } else {
            for (unsigned i = 0; i < count; ++i) {
                result["gpus"][std::to_string(i)] = executeQuery(i, flags);
            }
        }
        return result;
    }
};

bool validateFlags(const std::vector<std::string> &flags, const std::vector<std::string> &validFlags) {
    return std::all_of(flags.begin(), flags.end(), [&](const auto &flag) {
        return std::find(validFlags.begin(), validFlags.end(), flag) != validFlags.end();
    });
}

bool handleGpuTarget(int &i, int argc, char *argv[], int &targetGpu) {
    if (i + 1 >= argc) return false;
    try {
        targetGpu = std::stoi(argv[++i]);
        return true;
    }
    catch (...) { return false; }
}

bool parseArgs(int argc, char *argv[], int &targetGpu, std::vector<std::string> &flags,
               const std::vector<std::string> &validFlags) {
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--gpu") {
            if (!handleGpuTarget(i, argc, argv, targetGpu)) return false;
        } else if (arg.rfind("--", 0) == 0) {
            if (!validateFlags({arg}, validFlags)) return false;
            flags.push_back(arg);
        } else return false;
    }
    return true;
}

void printUsage(const char *prog) {
    std::cout << "Usage: " << prog << " [--bash|--nvml] [--gpu <idx>] [OPTION]...\n"
              << "Query Methods:\n"
              << "  --bash        Use nvidia-smi commands for querying\n"
              << "  --nvml        Use NVML library for querying (default)\n\n"
              << "Options:\n"
              << "  --count       Show GPU count\n  --name        Show GPU name\n"
              << "  --temp        Show GPU temperature\n  --clocks      Show GPU and memory clocks\n"
              << "  --power       Show power usage\n  --plimit      Show power limit\n"
              << "  --mem         Show memory usage\n  --util        Show GPU and memory utilization\n"
              << "  --uuid        Show GPU UUID\n  --fan         Show fan speed\n"
              << "  --minor       Show minor number\n"
              << "  --serial      Show serial number\n  --vbios       Show VBIOS version\n"
              << "  --driver      Show driver version\n  --ecc         Show ECC error counts\n"
              << "  --pstate      Show performance state\n  --pciegen     Show PCIe generation\n"
              << "  --pciewidth   Show PCIe width\n  --all         Show all information\n";
}

int main(int argc, char *argv[]) {
    static const std::vector<std::string> validFlags = {
            "--count", "--name", "--temp", "--clocks", "--power", "--plimit", "--mem", "--util",
            "--uuid", "--fan", "--minor", "--serial", "--vbios", "--driver", "--ecc",
            "--pstate", "--pciegen", "--pciewidth", "--all"
    };

    QueryMethod method = QueryMethod::NVML;
    std::vector<char *> filteredArgs;
    filteredArgs.push_back(argv[0]);

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--bash") {
            method = QueryMethod::BASH;
        } else if (arg == "--nvml") {
            method = QueryMethod::NVML;
        } else {
            filteredArgs.push_back(argv[i]);
        }
    }

    unsigned long newArgc = filteredArgs.size();
    char **newArgv = filteredArgs.data();

    int targetGpu = -1;
    std::vector<std::string> flags;
    if (!parseArgs(int(newArgc), newArgv, targetGpu, flags, validFlags)) {
        printUsage(argv[0]);
        return -1;
    }
    if (flags.empty()) {
        printUsage(argv[0]);
        return 0;
    }

    GPUQuery tool(method);
    if (!tool.initialize()) {
        std::cerr << "Failed to initialize NVIDIA query tool" << std::endl;
        return -1;
    }
    std::cout << tool.queryGPU(targetGpu, flags).dump(4) << std::endl;
    return 0;
}
