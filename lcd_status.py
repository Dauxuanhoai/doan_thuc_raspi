
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


class LcdStatusDisplay:
    def __init__(self, fb_path="/dev/fb1", width=480, height=320):
        self.fb_path = fb_path
        self.width = width
        self.height = height
        self.enabled = os.path.exists(fb_path)
        self._last_payload = None
        self.font_big = self._font(34, True)
        self.font_mid = self._font(24, True)
        self.font = self._font(20, False)
        self.font_small = self._font(16, False)

    def _font(self, size, bold=False):
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
        for path in paths:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    def update(self, data):
        if not self.enabled:
            return
        payload = tuple(sorted((str(k), str(v)) for k, v in data.items()))
        if payload == self._last_payload:
            return
        self._last_payload = payload
        image = self._render(data)
        self._write_rgb565(image)

    def _render(self, data):
        img = Image.new("RGB", (self.width, self.height), (8, 12, 18))
        d = ImageDraw.Draw(img)
        for y in range(self.height):
            d.line((0, y, self.width, y), fill=(10, 18 + y // 7, 28 + y // 12))

        accent = (0, 212, 255)
        green = (0, 230, 118)
        yellow = (255, 214, 0)
        red = (255, 82, 82)
        text = (232, 244, 253)
        dim = (127, 168, 201)
        card = (22, 32, 48)
        border = (52, 77, 100)

        class_name = str(data.get("class_name", "Lop hoc"))[:30]
        status = str(data.get("status", "San sang"))
        period = data.get("period")
        now = str(data.get("time") or datetime.now().strftime("%H:%M:%S"))
        date = str(data.get("date") or datetime.now().strftime("%d/%m/%Y"))
        total = int(data.get("total", 0) or 0)
        present = int(data.get("present", 0) or 0)
        absent = int(data.get("absent", 0) or 0)
        half = int(data.get("half", 0) or 0)
        last_seen = str(data.get("last_seen", "") or "")

        d.rounded_rectangle((10, 10, 470, 66), radius=8, fill=card, outline=border, width=2)
        d.text((24, 18), class_name, fill=text, font=self.font_mid)
        d.text((360, 18), now, fill=accent, font=self.font_mid)
        d.text((362, 44), date, fill=dim, font=self.font_small)

        badge_color = green if "Dang" in status or "San" in status else yellow
        d.rounded_rectangle((10, 76, 470, 126), radius=8, fill=(16, 37, 42), outline=badge_color, width=2)
        label = f"Tiet {period} - {status}" if period else status
        d.text((24, 88), label[:34], fill=badge_color, font=self.font_mid)

        boxes = [
            ("CO MAT", present, green, 10, 140, 150),
            ("VANG", absent, red, 165, 140, 305),
            ("1/2", half, yellow, 320, 140, 470),
        ]
        for title, value, color, x1, y1, x2 in boxes:
            d.rounded_rectangle((x1, y1, x2, 222), radius=8, fill=card, outline=border, width=2)
            d.text((x1 + 14, y1 + 10), title, fill=dim, font=self.font_small)
            d.text((x1 + 14, y1 + 34), str(value), fill=color, font=self.font_big)

        d.rounded_rectangle((10, 236, 470, 306), radius=8, fill=card, outline=border, width=2)
        d.text((24, 244), f"Tong sinh vien: {total}", fill=text, font=self.font)
        if last_seen:
            wrapped = textwrap.shorten(last_seen, width=34, placeholder="...")
            d.text((24, 274), f"Vua thay: {wrapped}", fill=green, font=self.font_small)
        else:
            d.text((24, 274), "Dang cho nhan dien khuon mat", fill=dim, font=self.font_small)
        return img

    def _write_rgb565(self, img):
        out = bytearray()
        for r, g, b in img.getdata():
            value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            out.append(value & 0xFF)
            out.append((value >> 8) & 0xFF)
        with open(self.fb_path, "wb") as fb:
            fb.write(out)
