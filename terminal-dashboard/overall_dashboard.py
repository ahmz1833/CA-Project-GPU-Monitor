import curses
import time
import requests
import re
from collections import defaultdict, deque

URL = "http://185.176.35.77:9555/gpu/metric?method=sim"
METRIC_LINE_RE = re.compile(r'^([\w:]+)\{([^}]*)\}\s+([0-9.eE+-]+)$')

utilization_history = defaultdict(lambda: deque(maxlen=60))

SPARK_CHARS_DENSE = '⠀⡀⡄⡆⡇⣇⣧⣷⣿'  # Braille patterns - very dense
SPARK_CHARS_NORMAL = '▁▂▃▄▅▆▇█'        # Standard blocks
SPARK_CHARS_SIMPLE = '·-=≡█'            # Simple ASCII-safe
SPARK_CHARS_MINIMAL = '_-^*'             # Minimal for very small

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
            return {"error": f"HTTP {response.status_code}"}
        return parse_prometheus_metrics(response.text)
    except Exception as e:
        return {"error": str(e)}

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

def get_utilization_color(util):
    """Get color pair based on utilization percentage"""
    if util >= 90:
        return curses.color_pair(3)  # Red for high usage
    elif util >= 70:
        return curses.color_pair(2)  # Yellow for medium usage
    elif util >= 30:
        return curses.color_pair(1)  # Green for moderate usage
    else:
        return curses.color_pair(4)  # Blue for low usage

def draw_header(stdscr, width, config):
    """Draw header based on terminal size"""
    if config['header_style'] == 'full':
        title = " GPU MONITOR DASHBOARD - Real-time Performance Tracking "
        border_char = config['size'] == 'large' and '═' or '='
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(0, 0, title.center(width, border_char)[:width - 1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
    elif config['header_style'] == 'medium':
        title = " GPU MONITOR "
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(0, 0, title.center(width, '=')[:width - 1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
    elif config['header_style'] == 'compact':
        stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(0, 0, "GPU Monitor"[:width - 1])
        stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
    else:  # minimal
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
        # Full graph display
        util_color = get_utilization_color(util_percent)
        stdscr.addstr(row, col, " Utilization: ")
        stdscr.attron(util_color | curses.A_BOLD)
        stdscr.addstr(f"{util_percent:5.1f}%")
        stdscr.attroff(util_color | curses.A_BOLD)

        # Status indicator
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

def draw_screen(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_GREEN, -1)    # Low/Good
    curses.init_pair(2, curses.COLOR_YELLOW, -1)   # Medium/Warning
    curses.init_pair(3, curses.COLOR_RED, -1)      # High/Critical
    curses.init_pair(4, curses.COLOR_CYAN, -1)     # Headers
    curses.init_pair(4, curses.COLOR_CYAN, -1)     # Idle/Low

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        config = get_display_config(max_x, max_y)

        draw_header(stdscr, max_x, config)

        if config['size'] == 'large':
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(1, 0, f" Terminal: {max_x}x{max_y} │ Mode: {config['size'].upper()} │ Press 'q' to quit "[:max_x - 1])
            stdscr.attroff(curses.color_pair(5))

        data = fetch_data()

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
            footer = "q:quit"
        elif config['size'] == 'small':
            footer = " Press 'q' to quit "
        else:
            footer = " Press 'q' to quit | Updates every 2 seconds | Adaptive display "

        stdscr.addstr(max_y - 1, 0, footer.ljust(max_x)[:max_x - 1])
        stdscr.attroff(curses.color_pair(4))

        stdscr.refresh()

        try:
            if stdscr.getch() == ord("q"):
                break
        except:
            pass

        time.sleep(2)

if __name__ == "__main__":
    curses.wrapper(draw_screen)