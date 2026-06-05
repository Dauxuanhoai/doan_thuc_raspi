#!/usr/bin/env python3
import fcntl
import json
import os
import re
import select
import signal
import struct
import subprocess
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

APP_DIR = Path("/home/hoaidau/doan_thuc_raspi")
APP_MAIN = APP_DIR / "main.py"
APP_LOG = APP_DIR / "app.log"
FB_PATH = "/dev/fb1"
TOUCH_PATH = "/dev/input/event0"
COMMAND_PATH = Path("/tmp/classroom_app_command.json")
STATE_PATH = Path("/tmp/classroom_app_state.json")
RUNUSER = "/usr/sbin/runuser" if os.path.exists("/usr/sbin/runuser") else "runuser"
W, H = 480, 320

EV_KEY = 1
EV_ABS = 3
EV_SYN = 0
BTN_TOUCH = 330
ABS_X = 0
ABS_Y = 1
ABS_PRESSURE = 24
EVENT_FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

# ADS7846 calibration from /etc/X11/xorg.conf.d/99-calibration.conf.
CAL_X_MIN = 268
CAL_X_MAX = 3880
CAL_Y_MIN = 3936
CAL_Y_MAX = 227
SWAP_AXES = True


def run(cmd, timeout=8):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return out.strip()
    except Exception as exc:
        return str(exc)


def popen_detached(cmd, cwd=None, stdout_path=None):
    stdout = open(stdout_path, "ab", buffering=0) if stdout_path else subprocess.DEVNULL
    return subprocess.Popen(cmd, cwd=cwd, stdout=stdout, stderr=stdout, stdin=subprocess.DEVNULL,
                            start_new_session=True)


class Touch:
    def __init__(self, path=TOUCH_PATH):
        self.path = path
        self.fd = None
        self.raw_x = 0
        self.raw_y = 0
        self.down = False
        self.seen_abs = False
        self.open()

    def open(self):
        try:
            self.fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        except Exception:
            self.fd = None

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def poll(self, timeout=0):
        if self.fd is None:
            self.open()
            time.sleep(0.1)
            return None
        r, _, _ = select.select([self.fd], [], [], timeout)
        if not r:
            return None
        point = None
        try:
            while True:
                data = os.read(self.fd, EVENT_SIZE)
                if len(data) < EVENT_SIZE:
                    break
                _, _, ev_type, code, value = struct.unpack(EVENT_FORMAT, data)
                if ev_type == EV_ABS:
                    if code == ABS_X:
                        self.raw_x = value
                        self.seen_abs = True
                    elif code == ABS_Y:
                        self.raw_y = value
                        self.seen_abs = True
                    elif code == ABS_PRESSURE:
                        self.down = value > 0
                elif ev_type == EV_KEY and code == BTN_TOUCH:
                    self.down = bool(value)
                elif ev_type == EV_SYN and (self.down or self.seen_abs):
                    point = self.map_point()
                    self.seen_abs = False
        except BlockingIOError:
            pass
        except OSError:
            self.close()
        return point

    def map_axis(self, value, lo, hi, size):
        if hi == lo:
            return 0
        pos = (value - lo) / (hi - lo)
        pos = max(0.0, min(1.0, pos))
        return int(pos * (size - 1))

    def map_point(self):
        rx, ry = self.raw_x, self.raw_y
        if SWAP_AXES:
            sx, sy = ry, rx
        else:
            sx, sy = rx, ry
        x = self.map_axis(sx, CAL_X_MIN, CAL_X_MAX, W)
        y = self.map_axis(sy, CAL_Y_MIN, CAL_Y_MAX, H)
        return W - 1 - x, H - 1 - y


class LcdUi:
    def __init__(self):
        self.touch = Touch()
        self.screen = "home"
        self.buttons = []
        self.networks = []
        self.selected_ssid = ""
        self.password = ""
        self.shift = False
        self.key_page = 0
        self.message = ""
        self.last_scan = 0
        self.last_touch = None
        self.scanning_wifi = False
        self.running = True
        self.font_big = self.load_font(32, True)
        self.font_mid = self.load_font(23, True)
        self.font = self.load_font(18, False)
        self.font_small = self.load_font(15, False)
        self.render(force=True)

    def load_font(self, size, bold=False):
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
        for p in paths:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    def app_pids(self):
        pids = []
        app_path = str(APP_MAIN)
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/cmdline", "rb") as f:
                    args = [p.decode("utf-8", "ignore") for p in f.read().split(b"\0") if p]
            except OSError:
                continue
            if len(args) >= 2 and Path(args[0]).name.startswith("python"):
                try:
                    cwd = os.readlink(f"/proc/{entry}/cwd")
                except OSError:
                    cwd = ""
                if app_path in args or (Path(args[-1]).name == "main.py" and cwd == str(APP_DIR)):
                    pids.append(int(entry))
        return pids

    def app_running(self):
        return bool(self.app_pids())

    def app_state(self):
        if not self.app_running():
            return {"running": False, "session_active": False, "period": None}
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if time.time() - float(data.get("updated_at", 0)) > 5:
                data["session_active"] = False
            data["running"] = True
            return data
        except Exception:
            return {"running": True, "session_active": False, "period": None}

    def write_app_command(self, action):
        data = {"id": time.time(), "action": action}
        tmp = COMMAND_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        tmp.replace(COMMAND_PATH)

    def ip_addr(self):
        out = run(["hostname", "-I"], timeout=2)
        ips = [p for p in out.split() if re.match(r"\d+\.\d+\.\d+\.\d+", p)]
        return ips[0] if ips else "No IP"

    def wifi_name(self):
        out = run(["nmcli", "-t", "-f", "GENERAL.CONNECTION", "dev", "show", "wlan0"], timeout=3)
        if ":" in out:
            return out.split(":", 1)[1] or "Disconnected"
        return "Disconnected"

    def scan_wifi(self):
        if self.scanning_wifi:
            return
        self.scanning_wifi = True
        self.message = "Scanning WiFi..."
        self.last_scan = time.time()
        self.render(force=True)
        try:
            run(["nmcli", "dev", "wifi", "rescan"], timeout=8)
            out = run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list"], timeout=8)
            nets = []
            seen = set()
            for line in out.splitlines():
                parts = line.split(":")
                if not parts or not parts[0]:
                    continue
                ssid = parts[0].replace("\\:", ":").strip()
                if ssid in seen:
                    continue
                seen.add(ssid)
                signal = parts[1] if len(parts) > 1 else ""
                security = parts[2] if len(parts) > 2 else ""
                nets.append({"ssid": ssid, "signal": signal, "security": security})
            self.networks = nets[:8]
            self.message = ""
        finally:
            self.scanning_wifi = False

    def launch_app(self):
        if self.app_running():
            return True
        if not os.path.exists("/tmp/.X11-unix/X0"):
            self.message = "Starting desktop..."
            self.render(force=True)
            run(["systemctl", "start", "lightdm"], timeout=12)
            time.sleep(4)
        APP_LOG.write_text("", encoding="utf-8")
        cmd = [RUNUSER, "-u", "hoaidau", "--", "setsid", "env", "DISPLAY=:0",
               "XAUTHORITY=/home/hoaidau/.Xauthority", "python3", str(APP_MAIN)]
        popen_detached(cmd, cwd=str(APP_DIR), stdout_path=str(APP_LOG))
        for _ in range(20):
            if self.app_running():
                return True
            time.sleep(0.25)
        return self.app_running()

    def start_app(self):
        self.message = "Opening app..."
        self.render(force=True)
        if not self.launch_app():
            self.message = "Cannot open app"
            return
        self.write_app_command("start_session")
        self.message = "Start sent"

    def stop_app(self):
        if not self.app_running():
            self.message = "App not running"
            return
        self.write_app_command("stop_session")
        self.message = "Stop sent"

    def connect_wifi(self):
        ssid = self.selected_ssid
        password = self.password
        self.message = f"Connecting {ssid}..."
        self.render(force=True)
        if password:
            out = run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], timeout=25)
        else:
            out = run(["nmcli", "dev", "wifi", "connect", ssid], timeout=25)
        self.message = "WiFi connected" if "successfully" in out.lower() else out[:54]
        self.password = ""
        self.screen = "home"

    def draw_bg(self, d):
        for y in range(H):
            d.line((0, y, W, y), fill=(8, 14 + y // 10, 24 + y // 15))

    def button(self, d, rect, label, action, fill=(25, 43, 62), outline=(70, 105, 135)):
        x1, y1, x2, y2 = rect
        d.rounded_rectangle(rect, radius=8, fill=fill, outline=outline, width=2)
        tw = d.textlength(label, font=self.font)
        d.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - 18) / 2), label, fill=(235, 245, 250), font=self.font)
        self.buttons.append((rect, action))

    def header(self, d, title):
        d.rounded_rectangle((8, 8, 472, 54), radius=8, fill=(18, 32, 48), outline=(58, 88, 116), width=2)
        d.text((18, 17), title, fill=(0, 212, 255), font=self.font_mid)
        d.text((350, 18), datetime.now().strftime("%H:%M:%S"), fill=(235, 245, 250), font=self.font)

    def render_home(self, d):
        self.header(d, "Classroom Panel")
        state = self.app_state()
        if not state["running"]:
            app = "APP OFF"
            line = "Tap START to open app and begin"
            action_label = "START APP"
            action = "start"
            action_fill = (18, 88, 54)
            app_color = (255, 82, 82)
        elif state.get("session_active"):
            app = "ATTENDANCE ON" if state.get("attendance_active") else "LIVE PREVIEW"
            period = state.get("period") or "-"
            line = f"Period {period} is running" if state.get("attendance_active") else "Camera on, no attendance"
            action_label = "STOP APP"
            action = "stop"
            action_fill = (100, 28, 38)
            app_color = (0, 230, 118)
        else:
            app = "APP READY"
            line = "Tap START to begin attendance"
            action_label = "START APP"
            action = "start"
            action_fill = (18, 88, 54)
            app_color = (255, 214, 0)

        d.rounded_rectangle((12, 64, 468, 146), radius=8, fill=(18, 32, 48), outline=(58, 88, 116), width=2)
        d.text((24, 74), app, fill=app_color, font=self.font_mid)
        d.text((24, 105), line[:36], fill=(235, 245, 250), font=self.font)
        d.text((24, 126), f"WiFi: {self.wifi_name()[:20]}   IP: {self.ip_addr()}", fill=(255, 214, 0), font=self.font_small)

        self.button(d, (14, 154, 466, 220), action_label, action, fill=action_fill)
        self.button(d, (14, 252, 226, 312), "WIFI", "wifi", fill=(25, 52, 82))
        self.button(d, (254, 252, 466, 312), "REFRESH", "refresh")
        if self.message:
            d.text((18, 306), self.message[:44], fill=(255, 214, 0), font=self.font_small)

    def render_wifi(self, d):
        self.header(d, "WiFi Networks")
        self.button(d, (365, 62, 468, 98), "BACK", "home")
        self.button(d, (250, 62, 354, 98), "SCAN", "scan")
        if (not self.networks or time.time() - self.last_scan > 60) and not self.scanning_wifi:
            self.scan_wifi()
        y = 106
        for i, net in enumerate(self.networks[:6]):
            ssid = net["ssid"][:24]
            sig = net["signal"]
            sec = "LOCK" if net["security"] else "OPEN"
            self.button(d, (12, y, 468, y + 34), f"{ssid}  {sig}%  {sec}", ("net", i), fill=(18, 32, 48))
            y += 38
        if self.message:
            d.text((14, 302), self.message[:58], fill=(255, 214, 0), font=self.font_small)

    def render_password(self, d):
        self.header(d, "WiFi Password")
        d.text((14, 62), self.selected_ssid[:34], fill=(235, 245, 250), font=self.font)
        shown = self.password if len(self.password) < 26 else "..." + self.password[-23:]
        d.rounded_rectangle((12, 84, 468, 118), radius=6, fill=(18, 32, 48), outline=(58, 88, 116), width=2)
        d.text((20, 92), shown, fill=(255, 214, 0), font=self.font)

        pages = [
            list("1234567890.-"),
            list("abcdefghijkl"),
            list("mnopqrstuvwxyz"),
            list("ABCDEFGHIJKL"),
            list("MNOPQRSTUVWXYZ"),
            list("@#$%&*_+=!?/"),
        ]
        labels = pages[self.key_page % len(pages)]
        x0, y0 = 12, 126
        key_w, key_h = 72, 38
        gap_x, gap_y = 6, 7
        for i, ch in enumerate(labels[:12]):
            col = i % 6
            row = i // 6
            x = x0 + col * (key_w + gap_x)
            y = y0 + row * (key_h + gap_y)
            self.button(d, (x, y, x + key_w, y + key_h), ch, ("key", ch), fill=(24, 40, 58))

        self.button(d, (12, 218, 88, 258), "MORE", "key_page")
        self.button(d, (96, 218, 188, 258), "SPACE", ("key", " "))
        self.button(d, (196, 218, 282, 258), "DEL", "del")
        self.button(d, (290, 218, 374, 258), "JOIN", "join", fill=(18, 72, 48))
        self.button(d, (382, 218, 468, 258), "BACK", "wifi")

        page_name = ["num", "abc1", "abc2", "ABC1", "ABC2", "sym"][self.key_page % len(pages)]
        d.text((18, 272), f"Page: {page_name}   Tap MORE for more keys", fill=(235, 245, 250), font=self.font_small)

    def render(self, force=False):
        self.buttons = []
        img = Image.new("RGB", (W, H), (8, 14, 24))
        d = ImageDraw.Draw(img)
        self.draw_bg(d)
        if self.screen == "wifi":
            self.render_wifi(d)
        elif self.screen == "password":
            self.render_password(d)
        else:
            self.render_home(d)
        self.write_fb(img)

    def write_fb(self, img):
        out = bytearray()
        for r, g, b in img.getdata():
            v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            out.append(v & 0xFF)
            out.append((v >> 8) & 0xFF)
        with open(FB_PATH, "wb") as fb:
            fb.write(out)

    def handle(self, action):
        if action == "start":
            self.start_app()
        elif action == "stop":
            self.stop_app()
        elif action == "wifi":
            self.screen = "wifi"
            self.scan_wifi()
        elif action == "home":
            self.screen = "home"
        elif action == "refresh":
            self.message = "Refreshed"
        elif action == "scan":
            self.scan_wifi()
        elif isinstance(action, tuple) and action[0] == "net":
            net = self.networks[action[1]]
            self.selected_ssid = net["ssid"]
            if net["security"]:
                self.password = ""
                self.key_page = 0
                self.screen = "password"
            else:
                self.password = ""
                self.connect_wifi()
        elif isinstance(action, tuple) and action[0] == "key":
            self.password += action[1]
        elif action == "shift":
            self.shift = not self.shift
        elif action == "key_page":
            self.key_page = (self.key_page + 1) % 6
        elif action == "del":
            self.password = self.password[:-1]
        elif action == "join":
            self.connect_wifi()
        self.render(force=True)

    def click(self, x, y):
        self.last_touch = (x, y)
        print(f"touch mapped={x},{y} raw={self.touch.raw_x},{self.touch.raw_y}", flush=True)
        for rect, action in list(self.buttons):
            x1, y1, x2, y2 = rect
            pad = 24
            if x1 - pad <= x <= x2 + pad and y1 - pad <= y <= y2 + pad:
                self.handle(action)
                return
        nearest = None
        for rect, action in list(self.buttons):
            x1, y1, x2, y2 = rect
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if nearest is None or dist < nearest[0]:
                nearest = (dist, action)
        if nearest and nearest[0] <= 62:
            self.handle(nearest[1])
            return
        self.message = f"Touch {x},{y}"
        self.render(force=True)

    def loop(self):
        last_render = 0
        while self.running:
            point = self.touch.poll(0.15)
            if point:
                self.click(*point)
                time.sleep(0.2)
            if self.screen == "home" and time.time() - last_render > 2:
                self.render()
                last_render = time.time()


def main():
    ui = LcdUi()
    def stop(signum, frame):
        ui.running = False
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    ui.loop()


if __name__ == "__main__":
    main()
