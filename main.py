"""eTOP - System Monitor for Pimoroni Explorer (RP2350)
An htop-style system monitor showing CPU, memory, disk, temp, and voltage.
"""

import gc
import os
import time
import machine
import explorer
from explorer import display, button_a, button_b, button_c, button_x, button_y, button_z

# --- Color Palette (RGB565) ---
BLACK = 0
WHITE = 65535
DARK_GRAY = display.create_pen(40, 40, 40)
MID_GRAY = display.create_pen(80, 80, 80)
GREEN = display.create_pen(0, 255, 0)
DARK_GREEN = display.create_pen(0, 100, 0)
YELLOW = display.create_pen(255, 255, 0)
RED = display.create_pen(255, 50, 0)
CYAN = display.create_pen(0, 220, 255)
TITLE_BG = display.create_pen(0, 30, 0)
BAR_BG = display.create_pen(30, 30, 30)

# --- Display Constants ---
WIDTH, HEIGHT = display.get_bounds()
BAR_HEIGHT = 10
BAR_X = 8
BAR_W = WIDTH - 16
SECTION_HEIGHT = 36

# --- State ---
brightness = 0.8
view = "main"  # "main" or "adc" or "info"
boot_ticks = time.ticks_ms()


# --- Helpers ---

def get_bar_color(pct):
    """Return green/yellow/red pen based on percentage."""
    if pct < 50:
        r = int(pct * 5.1)
        return display.create_pen(r, 255, 0)
    elif pct < 80:
        g = int(255 - (pct - 50) * 8.5)
        return display.create_pen(255, g, 0)
    else:
        return display.create_pen(255, max(0, int(50 - (pct - 80) * 2.5)), 0)


def draw_bar(x, y, w, h, pct, color):
    """Draw a progress bar with background."""
    display.set_pen(BAR_BG)
    display.rectangle(x, y, w, h)
    filled = max(0, min(w, int(w * pct / 100)))
    if filled > 0:
        display.set_pen(color)
        display.rectangle(x, y, filled, h)


def draw_hline(y, color=DARK_GRAY):
    """Draw a horizontal divider."""
    display.set_pen(color)
    display.line(0, y, WIDTH, y)


def format_bytes(n):
    """Format bytes to human-readable K/M."""
    if n >= 1048576:
        return "{:.1f}M".format(n / 1048576)
    elif n >= 1024:
        return "{:.0f}K".format(n / 1024)
    return str(n)


def format_uptime(ms):
    """Format milliseconds to HHh MMm SSs."""
    s = ms // 1000
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return "{:02d}h {:02d}m {:02d}s".format(h, m, sec)


def read_temp():
    """Read internal temperature sensor (RP2350 ADC4)."""
    sensor = machine.ADC(4)
    reading = sensor.read_u16()
    voltage = reading * 3.3 / 65535
    # RP2350 temp formula: T = 27 - (V - 0.706) / 0.001721
    return 27 - (voltage - 0.706) / 0.001721


def read_vsys():
    """Read VSYS supply voltage via ADC29."""
    vsys_adc = machine.ADC(29)
    reading = vsys_adc.read_u16()
    # VSYS has a voltage divider (3:1), so multiply by 3
    return reading * 3.3 / 65535 * 3


def draw_section(y, label, value_str, pct, color=None):
    """Draw a labeled section with value and progress bar."""
    if color is None:
        color = get_bar_color(pct)

    # Label and value on first line
    display.set_font("bitmap8")
    display.set_pen(WHITE)
    display.text(label, BAR_X, y + 2, scale=2)
    display.set_pen(MID_GRAY)
    # Right-align value
    vw = display.measure_text(value_str, scale=2)
    display.text(value_str, WIDTH - 8 - vw, y + 2, scale=2)

    # Progress bar on second line
    pct_str = "{:3d}%".format(int(pct))
    bar_w = BAR_W - 40
    draw_bar(BAR_X, y + 22, bar_w, BAR_HEIGHT, pct, color)

    # Percentage text to the right of bar
    display.set_pen(color)
    display.text(pct_str, BAR_X + bar_w + 4, y + 20, scale=2)


def draw_title():
    """Draw the title bar."""
    display.set_pen(TITLE_BG)
    display.rectangle(0, 0, WIDTH, 20)
    display.set_font("bitmap8")
    display.set_pen(GREEN)
    display.text("eTOP", 8, 3, scale=2)
    display.set_pen(DARK_GREEN)
    display.text("System Monitor", 56, 3, scale=2)
    draw_hline(20)


def draw_button_legend():
    """Draw the button legend at bottom."""
    y = HEIGHT - 16
    draw_hline(y - 2)
    display.set_font("bitmap8")
    display.set_pen(CYAN)
    if view == "main":
        display.text("A:Info B:GC C:ADC", 4, y, scale=1)
        display.text("X/Y:Brt Z:Exit", WIDTH - 90, y, scale=1)
    elif view == "adc":
        display.text("C:Back", 4, y, scale=1)
        display.text("X/Y:Brt Z:Exit", WIDTH - 90, y, scale=1)
    elif view == "info":
        display.text("A:Back B:GC", 4, y, scale=1)
        display.text("X/Y:Brt Z:Exit", WIDTH - 90, y, scale=1)


def draw_main_view():
    """Draw the main system monitor view."""
    draw_title()

    y = 24

    # CPU
    freq_mhz = machine.freq() / 1_000_000
    cpu_pct = min(100, freq_mhz / 1.5)  # Decorative: scale relative to 150MHz
    draw_section(y, "CPU", "{:.0f} MHz".format(freq_mhz), cpu_pct, GREEN)

    y += SECTION_HEIGHT
    draw_hline(y)
    y += 2

    # Memory
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    mem_total = mem_free + mem_alloc
    mem_pct = mem_alloc * 100 / mem_total if mem_total > 0 else 0
    draw_section(y, "MEM", "{}/{}".format(format_bytes(mem_alloc), format_bytes(mem_total)), mem_pct)

    y += SECTION_HEIGHT
    draw_hline(y)
    y += 2

    # Disk
    try:
        st = os.statvfs('/')
        disk_total = st[0] * st[2]
        disk_free = st[0] * st[3]
        disk_used = disk_total - disk_free
        disk_pct = disk_used * 100 / disk_total if disk_total > 0 else 0
        draw_section(y, "DISK", "{}/{}".format(format_bytes(disk_used), format_bytes(disk_total)), disk_pct, CYAN)
    except:
        display.set_pen(WHITE)
        display.text("DISK  N/A", BAR_X, y + 8, scale=2)
        disk_pct = 0

    y += SECTION_HEIGHT
    draw_hline(y)
    y += 2

    # Temperature
    try:
        temp = read_temp()
        # Scale: 20C=0%, 60C=100%
        temp_pct = max(0, min(100, (temp - 20) * 100 / 40))
        draw_section(y, "TEMP", "{:.1f} C".format(temp), temp_pct)
    except:
        display.set_pen(WHITE)
        display.text("TEMP  N/A", BAR_X, y + 8, scale=2)

    y += SECTION_HEIGHT
    draw_hline(y)
    y += 2

    # VSYS & Uptime (no bars, just text)
    display.set_font("bitmap8")
    try:
        vsys = read_vsys()
        display.set_pen(WHITE)
        display.text("VSYS", BAR_X, y + 2, scale=2)
        display.set_pen(GREEN)
        vstr = "{:.2f}V".format(vsys)
        vw = display.measure_text(vstr, scale=2)
        display.text(vstr, WIDTH - 8 - vw, y + 2, scale=2)
    except:
        display.set_pen(WHITE)
        display.text("VSYS  N/A", BAR_X, y + 2, scale=2)

    y += 18

    uptime_ms = time.ticks_diff(time.ticks_ms(), boot_ticks)
    display.set_pen(WHITE)
    display.text("UP", BAR_X, y + 2, scale=2)
    display.set_pen(GREEN)
    ustr = format_uptime(uptime_ms)
    uw = display.measure_text(ustr, scale=2)
    display.text(ustr, WIDTH - 8 - uw, y + 2, scale=2)

    draw_button_legend()


def draw_adc_view():
    """Draw ADC channel monitor view."""
    draw_title()
    display.set_font("bitmap8")
    display.set_pen(CYAN)
    display.text("ADC Channels", 60, 24, scale=2)

    y = 44
    for i in range(6):
        try:
            adc = machine.ADC(40 + i)
            raw = adc.read_u16()
        except:
            raw = 0
        pct = raw * 100 / 65535
        label = "ADC{}".format(i)
        val_str = str(raw)

        display.set_pen(WHITE)
        display.text(label, BAR_X, y + 2, scale=2)

        bar_x = 52
        bar_w = WIDTH - 100
        color = get_bar_color(pct)
        draw_bar(bar_x, y + 4, bar_w, 8, pct, color)

        display.set_pen(MID_GRAY)
        vw = display.measure_text(val_str, scale=2)
        display.text(val_str, WIDTH - 8 - vw, y + 2, scale=2)

        y += 28

    draw_button_legend()


def draw_info_view():
    """Draw detailed system info panel."""
    draw_title()
    display.set_font("bitmap8")
    display.set_pen(CYAN)
    display.text("System Info", 65, 24, scale=2)

    y = 46
    lines = []

    # Platform
    lines.append(("Platform", os.uname().sysname))
    lines.append(("Machine", os.uname().machine[:20]))
    lines.append(("Release", os.uname().release))
    lines.append(("Freq", "{:.0f} MHz".format(machine.freq() / 1_000_000)))

    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    lines.append(("Mem Free", format_bytes(mem_free)))
    lines.append(("Mem Used", format_bytes(mem_alloc)))

    try:
        st = os.statvfs('/')
        lines.append(("Blk Size", str(st[0])))
        lines.append(("Blk Free", str(st[3])))
    except:
        pass

    for label, val in lines:
        display.set_pen(MID_GRAY)
        display.text(label, BAR_X, y, scale=2)
        display.set_pen(WHITE)
        vw = display.measure_text(val, scale=2)
        display.text(val, WIDTH - 8 - vw, y, scale=2)
        y += 20

    draw_button_legend()


# --- Main Loop ---

display.set_backlight(brightness)

while True:
    # Clear
    display.set_pen(BLACK)
    display.clear()

    # Draw active view
    if view == "adc":
        draw_adc_view()
    elif view == "info":
        draw_info_view()
    else:
        draw_main_view()

    display.update()

    # Button handling (active low: 0 = pressed)
    if button_a.value() == 0:
        view = "info" if view != "info" else "main"
        time.sleep_ms(250)  # Debounce

    if button_b.value() == 0:
        gc.collect()
        time.sleep_ms(250)

    if button_c.value() == 0:
        view = "adc" if view != "adc" else "main"
        time.sleep_ms(250)

    if button_x.value() == 0:
        brightness = min(1.0, brightness + 0.1)
        display.set_backlight(brightness)
        time.sleep_ms(150)

    if button_y.value() == 0:
        brightness = max(0.1, brightness - 0.1)
        display.set_backlight(brightness)
        time.sleep_ms(150)

    if button_z.value() == 0:
        display.set_pen(BLACK)
        display.clear()
        display.set_backlight(0)
        display.update()
        break

    time.sleep_ms(200)
