#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <curl/curl.h>
#include <ncurses.h>
#include <thread>
#include <chrono>
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <clocale>
#include <regex>


const std::string URL = "http://185.176.35.77:9555/gpu/metric?method=sim";
const int FETCH_INTERVAL_SECONDS = 1; 
const int MAX_DATA_POINTS = 2000;  

struct GpuData {
    std::string name;
    std::string uuid;
    std::vector<double> utilization_history;
    double temperature_c = 0.0;
    double clock_mhz = 0.0;
    double mem_clock_mhz = 0.0;
    double power_watts = 0.0;
};

size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

std::string fetchData(CURL* curl) {
    std::string readBuffer;
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, URL.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);
        CURLcode res = curl_easy_perform(curl);
        if(res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
            return "";
        }
    }
    return readBuffer;
}

void parseAllGpuData(const std::string& rawData, std::map<std::string, GpuData>& all_gpus) {
    std::stringstream ss(rawData);
    std::string line;

    const std::regex metric_regex(R"DELIM(([^\{]+)\{([^}]+)\}\s+([0-9.]+))DELIM");
    const std::regex name_regex(R"DELIM(name="([^"]*)")DELIM");
    const std::regex uuid_regex(R"DELIM(uuid="([^"]*)")DELIM");

    while (std::getline(ss, line)) {
        std::smatch metric_matches;
        if (std::regex_search(line, metric_matches, metric_regex) && metric_matches.size() == 4) {
            std::string metric_name = metric_matches[1].str();
            std::string labels_block = metric_matches[2].str();
            double value = std::stod(metric_matches[3].str());

            std::smatch uuid_matches;
            if (std::regex_search(labels_block, uuid_matches, uuid_regex) && uuid_matches.size() == 2) {
                std::string uuid = uuid_matches[1].str();

            
                if (all_gpus.find(uuid) == all_gpus.end()) {
                    all_gpus[uuid].uuid = uuid;
                    std::smatch name_matches;
                    if (std::regex_search(labels_block, name_matches, name_regex) && name_matches.size() == 2) {
                        all_gpus[uuid].name = name_matches[1].str();
                    }
                }
                
                // Update the specific metric
                if (metric_name == "gpu_utilization_percent") {
                    all_gpus[uuid].utilization_history.push_back(value);
                    if (all_gpus[uuid].utilization_history.size() > MAX_DATA_POINTS) {
                        all_gpus[uuid].utilization_history.erase(all_gpus[uuid].utilization_history.begin());
                    }
                } else if (metric_name == "gpu_temperature_celsius") {
                    all_gpus[uuid].temperature_c = value;
                } else if (metric_name == "gpu_clock_mhz") {
                    all_gpus[uuid].clock_mhz = value;
                } else if (metric_name == "gpu_memory_clock_mhz") {
                    all_gpus[uuid].mem_clock_mhz = value;
                } else if (metric_name == "gpu_power_watts") {
                    all_gpus[uuid].power_watts = value;
                }
            }
        }
    }
}


void drawUI(const std::map<std::string, GpuData>& all_data, const std::string& lastStatus) {
    clear();

    int rows, cols;
    getmaxyx(stdscr, rows, cols);

    
    if (has_colors()) attron(COLOR_PAIR(1));
    box(stdscr, 0, 0);
    mvprintw(0, 2, "[ GPU-Specific Terminal Monitor ]");
    mvprintw(0, cols - 22, "[ Press 'q' to quit ]");
    if (has_colors()) attroff(COLOR_PAIR(1));
    
    if (has_colors()) attron(COLOR_PAIR(3));
    mvprintw(rows - 1, 2, "Status: %s", lastStatus.c_str());
    if (has_colors()) attroff(COLOR_PAIR(3));

    if (all_data.empty()) {
        if (has_colors()) attron(COLOR_PAIR(3));
        mvprintw(rows / 2, (cols - 20) / 2, "Collecting data...");
        if (has_colors()) attroff(COLOR_PAIR(3));
        return;
    }

    
    int num_gpus = all_data.size();
    int available_rows = rows - 2;
    if (num_gpus == 0) return;
    int height_per_chart = available_rows / num_gpus;

    if (height_per_chart < 6) { 
        mvprintw(rows / 2, (cols - 35) / 2, "Terminal too small for %d charts!", num_gpus);
        return;
    }

    int chart_y_offset = 1;
    for (const auto& pair : all_data) {
        const GpuData& gpu = pair.second;
        const std::vector<double>& data = gpu.utilization_history;

        int plot_start_y = chart_y_offset;
        int plot_height = height_per_chart - 3;
        int plot_width = cols - 10;
        int plot_start_x = 8;

        
        if (has_colors()) attron(COLOR_PAIR(4));
        mvprintw(plot_start_y, plot_start_x, "%.*s", plot_width - 2, gpu.name.c_str());
        if (has_colors()) attroff(COLOR_PAIR(4));

        
        std::stringstream info_ss;
        info_ss << std::fixed << std::setprecision(1) << gpu.temperature_c << "C | "
                << std::setprecision(0) << gpu.clock_mhz << " MHz | "
                << gpu.mem_clock_mhz << " MHz (Mem) | "
                << std::setprecision(1) << gpu.power_watts << "W";
        if (has_colors()) attron(COLOR_PAIR(3));
        mvprintw(plot_start_y + 1, plot_start_x, "%.*s", plot_width -2, info_ss.str().c_str());
        if (has_colors()) attroff(COLOR_PAIR(3));

        
        double minVal = 0.0;
        double maxVal = 100.0;

        
        if (has_colors()) attron(COLOR_PAIR(3));
        mvvline(plot_start_y + 2, plot_start_x - 1, ACS_VLINE, plot_height);
        mvprintw(plot_start_y + 2, 0, "%6.1f%%", maxVal);
        mvprintw(plot_start_y + 2 + plot_height / 2, 0, "%6.1f%%", (minVal + maxVal) / 2.0);
        mvprintw(plot_start_y + 2 + plot_height - 1, 0, "%6.1f%%", minVal);
        if (has_colors()) attroff(COLOR_PAIR(3));

        
        mvhline(chart_y_offset + height_per_chart - 1, 1, ACS_HLINE, cols - 2);

        
        std::vector<std::vector<int>> braille_buffer(plot_height, std::vector<int>(plot_width, 0));
        int data_offset = (data.size() > (size_t)plot_width) ? (data.size() - plot_width) : 0;
        double value_range = maxVal - minVal;
        if (value_range < 1e-9) value_range = 1.0;

        for (int i = 0; i < plot_width && (i + data_offset) < data.size(); ++i) {
            double value = data[i + data_offset];
            value = std::max(minVal, std::min(maxVal, value));
            int high_res_y = (int)(((value - minVal) / value_range) * (plot_height * 4 - 1));
            int char_y = high_res_y / 4;
            int dot_y = high_res_y % 4;
            if (char_y < 0 || char_y >= plot_height) continue;
            for(int j = 0; j < char_y; ++j) braille_buffer[j][i] = 0b1111;
            for(int j = 0; j <= dot_y; ++j) braille_buffer[char_y][i] |= (1 << j);
        }
        
        for (int y = 0; y < plot_height; ++y) {
            for (int x = 0; x < plot_width; ++x) {
                int bits = braille_buffer[plot_height - 1 - y][x];
                if (bits > 0) {
                    float percentage = (float)y / plot_height;
                    if (has_colors()) {
                        if (percentage > 0.75) attron(COLOR_PAIR(2)); // Green
                        else if (percentage > 0.4) attron(COLOR_PAIR(5)); // Yellow
                        else attron(COLOR_PAIR(6)); // Red
                    }
                    mvprintw(plot_start_y + 2 + y, plot_start_x + x, "%lc", (wint_t)(0x2800 | bits));
                    if (has_colors()) {
                        if (percentage > 0.75) attroff(COLOR_PAIR(2));
                        else if (percentage > 0.4) attroff(COLOR_PAIR(5));
                        else attroff(COLOR_PAIR(6));
                    }
                }
            }
        }
        chart_y_offset += height_per_chart;
    }
    move(rows - 1, cols - 1);
}



int main() {
    setlocale(LC_ALL, "");
    curl_global_init(CURL_GLOBAL_DEFAULT);
    CURL* curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Failed to initialize libcurl" << std::endl;
        return 1;
    }

    
    std::map<std::string, GpuData> all_gpu_data;
    std::string lastGlobalStatus = "Initializing...";

    initscr();
    cbreak();
    noecho();
    curs_set(0);
    nodelay(stdscr, TRUE);
    keypad(stdscr, TRUE);

    if (has_colors()) {
        start_color();
        init_pair(1, COLOR_CYAN, COLOR_BLACK);
        init_pair(2, COLOR_GREEN, COLOR_BLACK);     // Plot color (high)
        init_pair(3, COLOR_WHITE, COLOR_BLACK);
        init_pair(4, COLOR_MAGENTA, COLOR_BLACK);
        init_pair(5, COLOR_YELLOW, COLOR_BLACK);    // Plot color (medium)
        init_pair(6, COLOR_RED, COLOR_BLACK);       // Plot color (low)
    }

    while (true) {
        if (getch() == 'q') break;

        std::string raw_data = fetchData(curl);
        if (!raw_data.empty()) {
            try {
                
                parseAllGpuData(raw_data, all_gpu_data);
                if (all_gpu_data.empty()) {
                    lastGlobalStatus = "Warning: No GPU metrics found in data.";
                } else {
                    lastGlobalStatus = "OK. Fetched data for " + std::to_string(all_gpu_data.size()) + " GPUs.";
                }

            } catch (const std::exception& e) {
                lastGlobalStatus = std::string("Parse Error: ") + e.what();
            }
        } else {
            lastGlobalStatus = "Error: Failed to fetch data from URL.";
        }
        
        drawUI(all_gpu_data, lastGlobalStatus);
        refresh();

        std::this_thread::sleep_for(std::chrono::seconds(FETCH_INTERVAL_SECONDS));
    }

    endwin();
    curl_easy_cleanup(curl);
    curl_global_cleanup();

    return 0;
}
