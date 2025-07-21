import curses
import time
import requests
import re
import locale
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List

URL = "http://185.176.35.77:9555/gpu/metric?method=sim"
METRIC_LINE_RE = re.compile(r'^([\w:]+)\{([^}]*)\}\s+([0-9.eE+-]+)$')
MAX_DATA_POINTS = 2000

@dataclass
class GpuData:
    name: str = ""
    uuid: str = ""
    utilization_history: List[float] = field(default_factory=list)
    temperature_c: float = 0.0
    clock_mhz: float = 0.0
    mem_clock_mhz: float = 0.0
    power_watts: float = 0.0
    memory_usage_percent: float = 0.0
    health: str = ""

utilization_history = defaultdict(lambda: deque(maxlen=60))

detailed_view_mode = False

SPARK_CHARS_DENSE = '⠀⡀⡄⡆⡇⣇⣧⣷⣿'
SPARK_CHARS_NORMAL = '▁▂▃▄▅▆▇█'
SPARK_CHARS_SIMPLE = '·-=≡█'
SPARK_CHARS_MINIMAL = '_-^*'

BOX_CHARS = {
    'large': {
        'horizontal': '═',
        'vertical': '║',
        'top_left': '╔',
        'top_right': '╗',
        'bottom_left': '╚',
        'bottom_right': '╝',
        'cross': '╬'
    },
    'medium': {
        'horizontal': '─',
        'vertical': '│',
        'top_left': '┌',
        'top_right': '┐',
        'bottom_left': '└',
        'bottom_right': '┘',
        'cross': '┼'
    },
    'small': {
        'horizontal': '-',
        'vertical': '|',
        'top_left': '+',
        'top_right': '+',
        'bottom_left': '+',
        'bottom_right': '+',
        'cross': '+'
    }
}

def get_display_config(width, height):
    """Determine display configuration based on terminal size"""
    if width >= 120 and height >= 30:
        return {
            'size': 'large',
            'spark_chars': SPARK_CHARS_DENSE,
            'graph_width': min(100, width - 20),
            'show_detailed_stats': True,
            'show_graphs': True,
            'show_borders': True,
            'compact_mode': False,
            'header_style': 'full'
        }
    elif width >= 80 and height >= 20:
        return {
            'size': 'medium',
            'spark_chars': SPARK_CHARS_NORMAL,
            'graph_width': min(60, width - 15),
            'show_detailed_stats': True,
            'show_graphs': True,
            'show_borders': True,
            'compact_mode': False,
            'header_style': 'medium'
        }
    elif width >= 60 and height >= 15:
        return {
            'size': 'small',
            'spark_chars': SPARK_CHARS_SIMPLE,
            'graph_width': min(40, width - 10),
            'show_detailed_stats': False,
            'show_graphs': True,
            'show_borders': False,
            'compact_mode': True,
            'header_style': 'compact'
        }
    else:
        return {
            'size': 'minimal',
            'spark_chars': SPARK_CHARS_MINIMAL,
            'graph_width': min(20, width - 5),
            'show_detailed_stats': False,
            'show_graphs': False,
            'show_borders': False,
            'compact_mode': True,
            'header_style': 'minimal'
        }

def fetch_data():
    try:
        response = requests.get(URL, timeout=5)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "raw": ""}
        return {"data": parse_prometheus_metrics(response.text), "raw": response.text}
    except Exception as e:
        return {"error": str(e), "raw": ""}

def parse_prometheus_metrics(text):
    gpu_metrics = defaultdict(dict)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        match = METRIC_LINE_RE.match(line)
        if match:
            metric, labels_str, value = match.groups()
            labels = dict(part.split('=') for part in labels_str.split(',') if '=' in part)
            labels = {k.strip(): v.strip('"') for k, v in labels.items()}
            gpu_name = labels.get("gpu_name", "Unknown")
            gpu_index = labels.get("gpu_index", "?")
            key = f"{gpu_index} - {gpu_name}"
            gpu_metrics[key][metric] = value
            gpu_metrics[key]["gpu_health"] = labels.get("gpu_health", "")
    return gpu_metrics

def parse_all_gpu_data(raw_data: str, all_gpus: Dict[str, GpuData]) -> None:
    """Parse all relevant metrics and populate the GpuData structs for detailed view"""
    lines = raw_data.strip().split('\n')

    metric_pattern = re.compile(r'([^\{]+)\{([^}]+)\}\s+([0-9.]+)')
    name_pattern = re.compile(r'name="([^"]*)"')
    uuid_pattern = re.compile(r'uuid="([^"]*)"')
    gpu_index_pattern = re.compile(r'gpu_index="([^"]*)"')

    for line in lines:
        metric_match = metric_pattern.search(line)
        if metric_match:
            metric_name = metric_match.group(1)
            labels_block = metric_match.group(2)
            value = float(metric_match.group(3))

            uuid_match = uuid_pattern.search(labels_block)
            if uuid_match:
                uuid = uuid_match.group(1)
            else:
                index_match = gpu_index_pattern.search(labels_block)
                if index_match:
                    uuid = f"gpu_{index_match.group(1)}"
                else:
                    continue

            if uuid not in all_gpus:
                all_gpus[uuid] = GpuData()
                all_gpus[uuid].uuid = uuid
                name_match = name_pattern.search(labels_block)
                if name_match:
                    all_gpus[uuid].name = name_match.group(1)
                else:
                    index_match = gpu_index_pattern.search(labels_block)
                    if index_match:
                        all_gpus[uuid].name = f"GPU {index_match.group(1)}"

            if metric_name == "gpu_utilization_percent":
                all_gpus[uuid].utilization_history.append(value)
                if len(all_gpus[uuid].utilization_history) > MAX_DATA_POINTS:
                    all_gpus[uuid].utilization_history.pop(0)
            elif metric_name == "gpu_temperature_celsius":
                all_gpus[uuid].temperature_c = value
            elif metric_name == "gpu_clock_mhz":
                all_gpus[uuid].clock_mhz = value
            elif metric_name == "gpu_memory_clock_mhz":
                all_gpus[uuid].mem_clock_mhz = value
            elif metric_name == "gpu_power_watts":
                all_gpus[uuid].power_watts = value
            elif metric_name == "gpu_memory_usage_percent":
                all_gpus[uuid].memory_usage_percent = value

def get_utilization_color(util):
    """Get color pair based on utilization percentage"""
    if util >= 90:
        return curses.color_pair(3)
    elif util >= 70:
        return curses.color_pair(2)
    elif util >= 30:
        return curses.color_pair(1)
    else:
        return curses.color_pair(4)

def draw_header(stdscr, width, config):
    """Draw header based on terminal size"""
    mode_indicator = " [DETAILED]" if detailed_view_mode else " [STANDARD]"

    if config['header_style'] == 'full':
        title = f" GPU MONITOR DASHBOARD - Real-time Performance{mode_indicator} "
        border_char = config['size'] == 'large' and '═' or '='
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(0, 0, title.center(width, border_char)[:width - 1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
    elif config['header_style'] == 'medium':
        title = f" GPU MONITOR{mode_indicator} "
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(0, 0, title.center(width, '=')[:width - 1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
    elif config['header_style'] == 'compact':
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(0, 0, f"GPU Monitor{mode_indicator}"[:width - 1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
    else:
        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(0, 0, "GPU"[:width - 1])
        stdscr.attroff(curses.color_pair(4))

def draw_utilization_graph(stdscr, row, col, gpu_id, util_percent, config):
    """Draw utilization graph adapted to terminal size"""
    if not config['show_graphs']:
        return row

    history = utilization_history[gpu_id]
    spark_chars = config['spark_chars']
    graph_width = config['graph_width']

    if config['size'] in ['large', 'medium']:
        util_color = get_utilization_color(util_percent)
        stdscr.addstr(row, col, " Utilization: ")
        stdscr.attron(util_color | curses.A_BOLD)
        stdscr.addstr(f"{util_percent:5.1f}%")
        stdscr.attroff(util_color | curses.A_BOLD)

        if util_percent >= 90:
            status = " [HIGH]"
        elif util_percent >= 70:
            status = " [MED]"
        elif util_percent >= 30:
            status = " [ACT]"
        else:
            status = " [IDLE]"

        stdscr.attron(util_color)
        stdscr.addstr(status)
        stdscr.attroff(util_color)
        row += 1

        if config['size'] == 'large':
            stdscr.addstr(row, col, f" Graph ({len(history)} samples):")
            row += 1

    sparkline = ""
    for util in history:
        if len(history) == 0:
            continue
        idx = min(int((float(util) / 100) * (len(spark_chars) - 1)), len(spark_chars) - 1)
        sparkline += spark_chars[idx]

    if len(sparkline) > graph_width:
        sparkline = sparkline[-graph_width:]
    else:
        sparkline = sparkline.ljust(graph_width)

    if config['size'] in ['large', 'medium']:
        stdscr.addstr(row, col, " ")
    else:
        stdscr.addstr(row, col, "")

    for i, char in enumerate(sparkline):
        hist_idx = max(0, len(history) - graph_width + i)
        if hist_idx < len(history):
            util_val = history[hist_idx]
            char_color = get_utilization_color(util_val)
            stdscr.attron(char_color)
            stdscr.addstr(char)
            stdscr.attroff(char_color)
        else:
            stdscr.addstr(' ')

    if config['compact_mode']:
        stdscr.addstr(f" {util_percent:4.1f}%")

    row += 1

    if config['size'] == 'large':
        stdscr.addstr(row, col, f" Scale: 0% {spark_chars[0]} ... {spark_chars[-1]} 100%")
        row += 1

    return row

def draw_gpu_info(stdscr, row, col, gpu_id, metrics, config):
    """Draw GPU information based on display configuration"""
    box_chars = BOX_CHARS[config['size']]

    if config['show_borders'] and not config['compact_mode']:
        stdscr.attron(curses.A_BOLD | curses.color_pair(4))
        border_line = f"{box_chars['top_left']}{box_chars['horizontal']} GPU {gpu_id} "
        border_line += box_chars['horizontal'] * (min(80, len(border_line) + 50))
        stdscr.addstr(row, col, border_line[:stdscr.getmaxyx()[1] - 1])
        stdscr.attroff(curses.A_BOLD | curses.color_pair(4))
        row += 1
        prefix = f"{box_chars['vertical']} "
    elif config['compact_mode']:
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(row, col, f"GPU {gpu_id}:"[:stdscr.getmaxyx()[1] - 1])
        stdscr.attroff(curses.A_BOLD)
        row += 1
        prefix = ""
    else:
        stdscr.attron(curses.A_BOLD | curses.color_pair(4))
        stdscr.addstr(row, col, f"[GPU {gpu_id}]"[:stdscr.getmaxyx()[1] - 1])
        stdscr.attroff(curses.A_BOLD | curses.color_pair(4))
        row += 1
        prefix = ""

    temperature = float(metrics.get("gpu_temperature_celsius", 0))
    util = float(metrics.get("gpu_utilization_percent", 0))
    mem_util = float(metrics.get("gpu_memory_usage_percent", 0))
    clock = float(metrics.get("gpu_clock_mhz", 0))
    power = float(metrics.get("gpu_power_watts", 0))
    health = metrics.get("gpu_health", "unknown").lower()

    utilization_history[gpu_id].append(util)

    if config['show_detailed_stats']:
        stdscr.addstr(row, col, prefix)

        temp_color = curses.color_pair(3) if temperature > 80 else curses.color_pair(2) if temperature > 60 else curses.color_pair(1)
        stdscr.addstr("Temp: ")
        stdscr.attron(temp_color | curses.A_BOLD)
        stdscr.addstr(f"{temperature:5.1f}°C")
        stdscr.attroff(temp_color | curses.A_BOLD)

        mem_color = get_utilization_color(mem_util)
        stdscr.addstr(" │ Mem: ")
        stdscr.attron(mem_color)
        stdscr.addstr(f"{mem_util:5.1f}%")
        stdscr.attroff(mem_color)

        if config['size'] == 'large':
            stdscr.addstr(f" │ Clock: {clock:4.0f}MHz │ Power: {power:5.1f}W │ Health: ")
            health_color = {"healthy": curses.color_pair(1), "warning": curses.color_pair(2), "critical": curses.color_pair(3)}.get(health, curses.color_pair(0))
            stdscr.attron(health_color | curses.A_BOLD)
            stdscr.addstr(health.capitalize())
            stdscr.attroff(health_color | curses.A_BOLD)

        row += 1
    elif config['size'] == 'minimal':
        stdscr.addstr(row, col, f"T:{temperature:3.0f}° M:{mem_util:3.0f}% ")
        row += 1

    row = draw_utilization_graph(stdscr, row, col, gpu_id, util, config)

    if config['show_borders'] and not config['compact_mode']:
        border_line = box_chars['bottom_left'] + box_chars['horizontal'] * 78 + box_chars['bottom_right']
        stdscr.addstr(row, col, border_line[:stdscr.getmaxyx()[1] - 1])
        row += 1

    return row + 1

def draw_detailed_view(stdscr, all_data: Dict[str, GpuData], last_status: str) -> None:
    """Draw the detailed Braille-based high-resolution charts"""
    stdscr.clear()
    rows, cols = stdscr.getmaxyx()

    try:
        stdscr.attron(curses.color_pair(1))
    except:
        pass
    stdscr.box()
    stdscr.addstr(0, 2, "[ GPU High-Resolution Monitor - DETAILED VIEW ]")
    stdscr.addstr(0, cols - 30, "[ Press 'o' for standard | 'q' quit ]")
    try:
        stdscr.attroff(curses.color_pair(1))
    except:
        pass

    try:
        stdscr.attron(curses.color_pair(3))
    except:
        pass
    status_text = f"Status: {last_status}"
    if len(status_text) > cols - 4:
        status_text = status_text[:cols - 4]
    stdscr.addstr(rows - 1, 2, status_text)
    try:
        stdscr.attroff(curses.color_pair(3))
    except:
        pass

    if not all_data:
        try:
            stdscr.attron(curses.color_pair(3))
        except:
            pass
        stdscr.addstr(rows // 2, (cols - 20) // 2, "Collecting data...")
        try:
            stdscr.attroff(curses.color_pair(3))
        except:
            pass
        return

    num_gpus = len(all_data)
    available_rows = rows - 2
    if num_gpus == 0:
        return
    height_per_chart = available_rows // num_gpus

    if height_per_chart < 6:
        stdscr.addstr(rows // 2, (cols - 35) // 2, f"Terminal too small for {num_gpus} charts!")
        return

    chart_y_offset = 1
    for uuid, gpu in all_data.items():
        data = gpu.utilization_history

        plot_start_y = chart_y_offset
        plot_height = height_per_chart - 3
        plot_width = cols - 10
        plot_start_x = 8

        try:
            stdscr.attron(curses.color_pair(4))
        except:
            pass
        title = gpu.name[:plot_width - 2] if len(gpu.name) > plot_width - 2 else gpu.name
        stdscr.addstr(plot_start_y, plot_start_x, title)
        try:
            stdscr.attroff(curses.color_pair(4))
        except:
            pass

        info_text = f"{gpu.temperature_c:.1f}C | {gpu.clock_mhz:.0f} MHz | {gpu.mem_clock_mhz:.0f} MHz (Mem) | {gpu.power_watts:.1f}W"
        if len(info_text) > plot_width - 2:
            info_text = info_text[:plot_width - 2]
        try:
            stdscr.attron(curses.color_pair(3))
        except:
            pass
        stdscr.addstr(plot_start_y + 1, plot_start_x, info_text)
        try:
            stdscr.attroff(curses.color_pair(3))
        except:
            pass

        min_val = 0.0
        max_val = 100.0

        try:
            stdscr.attron(curses.color_pair(3))
        except:
            pass
        try:
            stdscr.vline(plot_start_y + 2, plot_start_x - 1, curses.ACS_VLINE, plot_height)
        except:
            pass
        stdscr.addstr(plot_start_y + 2, 0, f"{max_val:6.1f}%")
        stdscr.addstr(plot_start_y + 2 + plot_height // 2, 0, f"{(min_val + max_val) / 2.0:6.1f}%")
        stdscr.addstr(plot_start_y + 2 + plot_height - 1, 0, f"{min_val:6.1f}%")
        try:
            stdscr.attroff(curses.color_pair(3))
        except:
            pass

        try:
            stdscr.hline(chart_y_offset + height_per_chart - 1, 1, curses.ACS_HLINE, cols - 2)
        except:
            pass

        braille_buffer = [[0 for _ in range(plot_width)] for _ in range(plot_height)]
        data_offset = max(0, len(data) - plot_width)
        value_range = max_val - min_val
        if value_range < 1e-9:
            value_range = 1.0

        for i in range(plot_width):
            if i + data_offset < len(data):
                value = data[i + data_offset]
                value = max(min_val, min(max_val, value))
                high_res_y = int(((value - min_val) / value_range) * (plot_height * 4 - 1))
                char_y = high_res_y // 4
                dot_y = high_res_y % 4
                if 0 <= char_y < plot_height:
                    for j in range(char_y):
                        braille_buffer[j][i] = 0b1111
                    for j in range(dot_y + 1):
                        braille_buffer[char_y][i] |= (1 << j)

        for y in range(plot_height):
            for x in range(plot_width):
                bits = braille_buffer[plot_height - 1 - y][x]
                if bits > 0:
                    percentage = y / plot_height
                    try:
                        if percentage > 0.75:
                            stdscr.attron(curses.color_pair(1))
                        elif percentage > 0.4:
                            stdscr.attron(curses.color_pair(2))
                        else:
                            stdscr.attron(curses.color_pair(3))
                    except:
                        pass

                    braille_char = chr(0x2800 | bits)
                    try:
                        stdscr.addstr(plot_start_y + 2 + y, plot_start_x + x, braille_char)
                    except:
                        pass

                    try:
                        if percentage > 0.75:
                            stdscr.attroff(curses.color_pair(6))
                        elif percentage > 0.4:
                            stdscr.attroff(curses.color_pair(5))
                        else:
                            stdscr.attroff(curses.color_pair(2))
                    except:
                        pass

        chart_y_offset += height_per_chart

    try:
        stdscr.move(rows - 1, cols - 1)
    except:
        pass

def draw_screen(stdscr):
    global detailed_view_mode

    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_GREEN, -1)    # Low/Good
    curses.init_pair(2, curses.COLOR_YELLOW, -1)   # Medium/Warning
    curses.init_pair(3, curses.COLOR_RED, -1)      # High/Critical
    curses.init_pair(4, curses.COLOR_CYAN, -1)     # Headers
    curses.init_pair(5, curses.COLOR_BLUE, -1)     # Idle/Low
    curses.init_pair(6, curses.COLOR_MAGENTA, -1)  # Additional color

    all_gpu_data: Dict[str, GpuData] = {}
    last_status = "Initializing..."

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        elif key == ord("o") or key == ord("O"):
            detailed_view_mode = not detailed_view_mode

        result = fetch_data()
        if "error" in result:
            last_status = f"Error: {result['error']}"
            data = {}
        else:
            data = result["data"]
            raw_data = result["raw"]
            last_status = f"OK. Fetched data for {len(data)} GPUs."

            if raw_data:
                try:
                    parse_all_gpu_data(raw_data, all_gpu_data)
                except Exception as e:
                    last_status = f"Parse Error: {str(e)}"

        if detailed_view_mode:
            draw_detailed_view(stdscr, all_gpu_data, last_status)
        else:
            max_y, max_x = stdscr.getmaxyx()
            config = get_display_config(max_x, max_y)

            stdscr.clear()
            draw_header(stdscr, max_x, config)

            if config['size'] == 'large':
                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(1, 0, f" Terminal: {max_x}x{max_y} │ Mode: {config['size'].upper()} │ Press 'o' for detailed view │ 'q' to quit "[:max_x - 1])
                stdscr.attroff(curses.color_pair(5))

            if isinstance(data, dict) and "error" in data:
                stdscr.addstr(2, 0, f"Error: {data['error']}"[:max_x - 1])
            else:
                row = 2 if config['size'] != 'large' else 3
                gpus_displayed = 0
                max_gpus = max(1, (max_y - 4) // (6 if config['size'] == 'large' else 4 if config['size'] == 'medium' else 3))

                for gpu_id, metrics in sorted(data.items()):
                    if gpus_displayed >= max_gpus or row >= max_y - 3:
                        break

                    row = draw_gpu_info(stdscr, row, 0, gpu_id, metrics, config)
                    gpus_displayed += 1

            stdscr.attron(curses.color_pair(4))
            if config['size'] == 'minimal':
                footer = "o:detail q:quit"
            elif config['size'] == 'small':
                footer = " 'o' detailed view | 'q' quit "
            else:
                footer = " Press 'o' for detailed view | 'q' to quit | Updates every 2 seconds "

            stdscr.addstr(max_y - 1, 0, footer.ljust(max_x)[:max_x - 1])
            stdscr.attroff(curses.color_pair(4))

        stdscr.refresh()
        time.sleep(2)

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(draw_screen)