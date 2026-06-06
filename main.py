"""
Hệ thống Điểm Danh Khuôn Mặt — Raspberry Pi 4
Thiết kế lại: giao diện chuyên nghiệp, tối ưu hiệu năng Raspi, thân thiện cảm ứng.
"""

import sys
import os
import cv2
import json
import re
import numpy as np
import subprocess
import platform
import traceback
from datetime import datetime, date, timedelta
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QDialog, QLineEdit,
    QFormLayout, QTabWidget, QComboBox, QTimeEdit, QSpinBox, QDateEdit,
    QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QStackedWidget, QSizePolicy, QGridLayout,
    QProgressBar, QTextEdit, QGroupBox, QStatusBar,
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QTime, QSize, QDate, QRect,
    QPropertyAnimation, QEasingCurve,
)
from PyQt6.QtGui import (
    QImage, QPixmap, QFont, QColor, QPalette, QPainter,
    QLinearGradient, QBrush, QPen, QCursor, QFontDatabase,
    QRadialGradient,
)

import database as db
import face_module as fm
import export_module as em

try:
    import lcd_status
except Exception:
    lcd_status = None

try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

# ─── Phiên bản & hằng số ─────────────────────────────────────────────────────
APP_VERSION   = "2.0.0"
LCD_COMMAND_PATH = Path("/tmp/classroom_app_command.json")
LCD_STATE_PATH   = Path("/tmp/classroom_app_state.json")

# ─── Bảng màu ─────────────────────────────────────────────────────────────────
C = {
    "bg":        "#060D14",
    "surface":   "#0B1622",
    "surface2":  "#111F2E",
    "surface3":  "#1A3045",
    "accent":    "#00D4FF",
    "accent2":   "#0099BB",
    "accent3":   "#003D52",
    "green":     "#00E676",
    "green_dim": "#004D26",
    "yellow":    "#FFD600",
    "yellow_dim":"#4A3B00",
    "red":       "#FF3D3D",
    "red_dim":   "#4A0000",
    "text":      "#E8F4FC",
    "text_dim":  "#6B90A8",
    "text_mid":  "#9DC3D8",
    "border":    "#1E3A52",
    "border2":   "#0D2235",
}

# ─── Stylesheet toàn cục ──────────────────────────────────────────────────────
QSS = f"""
QMainWindow, QDialog {{
    background-color: {C['bg']};
    color: {C['text']};
}}
* {{
    font-family: 'DejaVu Sans', 'Noto Sans', sans-serif;
    font-size: 13px;
    color: {C['text']};
}}
QWidget {{
    background-color: transparent;
}}

/* ── Card frames ─────────────────────────────── */
QFrame#card {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 12px;
}}
QFrame#card_hi {{
    background-color: {C['surface2']};
    border: 1px solid {C['accent3']};
    border-radius: 12px;
}}
QFrame#sidebar {{
    background-color: {C['surface']};
    border-right: 1px solid {C['border']};
    border-radius: 0px;
}}
QFrame#topbar {{
    background-color: {C['surface']};
    border-bottom: 1px solid {C['border']};
}}
QFrame#divider {{
    background-color: {C['border']};
    max-height: 1px;
    min-height: 1px;
}}

/* ── Buttons ─────────────────────────────────── */
QPushButton {{
    background-color: {C['surface2']};
    color: {C['text_mid']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
}}
QPushButton:hover {{
    background-color: {C['surface3']};
    border-color: {C['accent']};
    color: {C['accent']};
}}
QPushButton:pressed {{
    background-color: {C['accent3']};
    border-color: {C['accent']};
}}
QPushButton:disabled {{
    opacity: 0.38;
    border-color: {C['border2']};
    color: {C['text_dim']};
}}

QPushButton#primary {{
    background-color: {C['accent']};
    color: {C['bg']};
    border: none;
    font-weight: 800;
    font-size: 13px;
}}
QPushButton#primary:hover {{
    background-color: #33DDFF;
    color: {C['bg']};
}}
QPushButton#primary:pressed {{
    background-color: {C['accent2']};
}}

QPushButton#success {{
    background-color: {C['green_dim']};
    color: {C['green']};
    border: 1px solid {C['green']};
    font-weight: 800;
}}
QPushButton#success:hover {{
    background-color: {C['green']};
    color: {C['bg']};
}}

QPushButton#danger {{
    background-color: {C['red_dim']};
    color: {C['red']};
    border: 1px solid {C['red']};
    font-weight: 700;
}}
QPushButton#danger:hover {{
    background-color: {C['red']};
    color: white;
}}

QPushButton#warning {{
    background-color: {C['yellow_dim']};
    color: {C['yellow']};
    border: 1px solid {C['yellow']};
    font-weight: 700;
}}
QPushButton#warning:hover {{
    background-color: {C['yellow']};
    color: {C['bg']};
}}

QPushButton#nav {{
    background-color: transparent;
    color: {C['text_dim']};
    border: none;
    border-radius: 10px;
    text-align: left;
    padding: 13px 16px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav:hover {{
    background-color: {C['surface2']};
    color: {C['text']};
}}
QPushButton#nav_active {{
    background-color: {C['accent3']};
    color: {C['accent']};
    border: none;
    border-left: 3px solid {C['accent']};
    border-radius: 0 10px 10px 0;
    text-align: left;
    padding: 13px 13px 13px 16px;
    font-size: 13px;
    font-weight: 700;
}}

/* ── Inputs ──────────────────────────────────── */
QLineEdit, QTextEdit {{
    background-color: {C['surface2']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 9px 13px;
    color: {C['text']};
    selection-background-color: {C['accent3']};
}}
QLineEdit {{
    min-height: 30px;
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {C['accent']};
    background-color: {C['surface3']};
}}

QComboBox {{
    background-color: {C['surface2']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 9px 13px;
    color: {C['text']};
    min-height: 30px;
}}
QComboBox:focus {{ border-color: {C['accent']}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {C['surface2']};
    border: 1px solid {C['border']};
    color: {C['text']};
    selection-background-color: {C['surface3']};
    selection-color: {C['accent']};
    outline: none;
}}

QSpinBox, QTimeEdit {{
    background-color: {C['surface2']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 6px 12px;
    color: {C['text']};
    min-height: 32px;
    min-width: 120px;
}}
QSpinBox:focus, QTimeEdit:focus {{ border-color: {C['accent']}; }}
QSpinBox::up-button, QSpinBox::down-button,
QTimeEdit::up-button, QTimeEdit::down-button {{
    width: 20px;
    background-color: {C['surface3']};
    border-left: 1px solid {C['border']};
}}

/* ── Tables ──────────────────────────────────── */
QTableWidget {{
    background-color: {C['surface']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    gridline-color: {C['border2']};
    outline: none;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {C['surface3']};
    color: {C['accent']};
}}
QTableWidget::item:alternate {{
    background-color: {C['surface2']};
}}
QHeaderView::section {{
    background-color: {C['surface2']};
    color: {C['text_dim']};
    border: none;
    border-bottom: 1px solid {C['border']};
    padding: 10px 10px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QHeaderView::section:first {{
    border-radius: 8px 0 0 0;
}}

/* ── Scroll bars ─────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['border']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['accent2']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {C['border']};
    border-radius: 3px;
}}

/* ── Tabs ────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: 10px;
    background-color: {C['surface']};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {C['surface2']};
    color: {C['text_dim']};
    padding: 10px 22px;
    border: 1px solid {C['border2']};
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    margin-right: 3px;
    font-size: 12px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background-color: {C['surface']};
    color: {C['accent']};
    border-color: {C['border']};
    border-bottom: 2px solid {C['accent']};
}}
QTabBar::tab:hover:!selected {{
    background-color: {C['surface3']};
    color: {C['text']};
}}

/* ── ProgressBar ─────────────────────────────── */
QProgressBar {{
    background-color: {C['surface2']};
    border: 1px solid {C['border']};
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C['accent2']}, stop:1 {C['accent']});
    border-radius: 5px;
}}

/* ── GroupBox ────────────────────────────────── */
QGroupBox {{
    border: 1px solid {C['border']};
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 700;
    font-size: 12px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: {C['accent']};
    background-color: {C['bg']};
}}

/* ── StatusBar ───────────────────────────────── */
QStatusBar {{
    background-color: {C['surface']};
    color: {C['text_dim']};
    border-top: 1px solid {C['border']};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ── MessageBox ──────────────────────────────── */
QMessageBox {{
    background-color: {C['surface']};
}}
QMessageBox QLabel {{
    color: {C['text']};
    font-size: 13px;
}}
"""


# ─── Helper widgets ────────────────────────────────────────────────────────────

def make_label(text="", size=13, bold=False, color=None, align=None):
    lbl = QLabel(text)
    style = f"font-size: {size}px;"
    if bold:
        style += " font-weight: 700;"
    if color:
        style += f" color: {color};"
    lbl.setStyleSheet(style)
    if align:
        lbl.setAlignment(align)
    return lbl


def hline():
    f = QFrame()
    f.setObjectName("divider")
    f.setFrameShape(QFrame.Shape.HLine)
    return f


def apply_button_variant(btn, variant):
    styles = {
        "primary": {
            "bg": C["accent"], "fg": C["bg"], "border": C["accent"],
            "hover_bg": "#33DDFF", "hover_fg": C["bg"],
            "pressed_bg": C["accent2"], "weight": 800,
        },
        "success": {
            "bg": C["green_dim"], "fg": C["green"], "border": C["green"],
            "hover_bg": C["green"], "hover_fg": C["bg"],
            "pressed_bg": "#00B85F", "weight": 800,
        },
        "danger": {
            "bg": C["red_dim"], "fg": C["red"], "border": C["red"],
            "hover_bg": C["red"], "hover_fg": "#FFFFFF",
            "pressed_bg": "#B82020", "weight": 700,
        },
    }
    s = styles[variant]
    btn.setObjectName(variant)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {s['bg']};
            color: {s['fg']};
            border: 1px solid {s['border']};
            border-radius: 8px;
            padding: 9px 18px;
            font-weight: {s['weight']};
            font-size: 13px;
            min-height: 22px;
        }}
        QPushButton:hover {{
            background-color: {s['hover_bg']};
            color: {s['hover_fg']};
            border-color: {s['border']};
        }}
        QPushButton:pressed {{
            background-color: {s['pressed_bg']};
            color: {s['hover_fg']};
            border-color: {s['border']};
        }}
        QPushButton:disabled {{
            background-color: {C['surface2']};
            color: {C['text_dim']};
            border-color: {C['border2']};
        }}
    """)


class StatCard(QFrame):
    """Thẻ thống kê với số lớn + nhãn nhỏ."""
    def __init__(self, label, value="0", color=C['accent'], parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.color = color
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"font-size: 34px; font-weight: 800; color: {color}; letter-spacing: -1px;"
        )
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.value_lbl)

        self.label_lbl = QLabel(label.upper())
        self.label_lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {C['text_dim']}; letter-spacing: 2px;"
        )
        layout.addWidget(self.label_lbl)

    def set_value(self, v):
        self.value_lbl.setText(str(v))

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Accent line trên top
        pen = QPen(QColor(self.color))
        pen.setWidth(3)
        p.setPen(pen)
        p.drawLine(18, 0, self.width() - 18, 0)
        p.end()


class BadgePill(QLabel):
    """Nhãn trạng thái pill-shaped."""
    STATUS_STYLE = {
        "present":  (C['green'],  C['green_dim']),
        "absent":   (C['red'],    C['red_dim']),
        "excused":  (C['text_mid'], C['surface3']),
        "half":     (C['yellow'], C['yellow_dim']),
        "scanning": (C['accent'], C['accent3']),
        "live":     (C['green'],  C['green_dim']),
        "off":      (C['text_dim'], C['surface2']),
    }
    VI = {
        "present": "CÓ MẶT", "absent": "VẮNG",
        "excused": "CÓ PHÉP",
        "half": "NỬA BUỔI", "scanning": "ĐANG QUÉT",
        "live": "LIVE", "off": "ĐÃ TẮT",
    }

    def __init__(self, status="off", parent=None):
        super().__init__(parent)
        self.setStatus(status)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def setStatus(self, status):
        fg, bg = self.STATUS_STYLE.get(status, (C['text_dim'], C['surface2']))
        text = self.VI.get(status, status.upper())
        self.setText(text)
        self.setStyleSheet(f"""
            color: {fg};
            background-color: {bg};
            border: 1px solid {fg};
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
        """)


# ─── Camera Thread ─────────────────────────────────────────────────────────────

class CameraThread(QThread):
    frame_ready    = pyqtSignal(np.ndarray)
    face_detected  = pyqtSignal(str, str, float)   # student_id, name, conf
    status_update  = pyqtSignal(str)

    # Tối ưu cho Raspi: giảm độ phân giải + tăng khoảng cách xử lý
    MONITOR_RES  = (480, 360)
    CAPTURE_RES  = (640, 480)
    PROCESS_INTERVAL_MON  = 0.20   # 5 fps xử lý nhận diện
    PROCESS_INTERVAL_CAP  = 0.30
    DISPLAY_INTERVAL      = 0.05   # 20 fps hiển thị
    DETECT_SCALE          = 0.55   # co nhỏ trước khi detect → nhanh hơn

    def __init__(self, mode="monitor"):
        super().__init__()
        self.mode    = mode
        self.running = False
        self.current_session_id  = None
        self._scan_cooldown      = {}
        self._last_face_boxes    = []
        self._last_face_ts       = 0
        self._last_process_ts    = 0
        self._last_display_ts    = 0
        self._pi_interval = (
            self.PROCESS_INTERVAL_MON if mode == "monitor"
            else self.PROCESS_INTERVAL_CAP
        )

    def set_session(self, session_id):
        self.current_session_id = session_id

    # ── Camera open ──────────────────────────────────────────────────────────

    def _open_camera(self):
        w, h = self.MONITOR_RES if self.mode == "monitor" else self.CAPTURE_RES
        if platform.system() == "Linux" and Picamera2 is not None:
            try:
                cam = Picamera2()
                cfg = cam.create_preview_configuration(
                    main={"format": "RGB888", "size": (w, h)},
                    controls={"FrameRate": 25},
                )
                cam.configure(cfg)
                cam.start()
                return "pi", cam
            except Exception as exc:
                print(f"[CameraThread] Picamera2 thất bại: {exc}")

        backend = cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_DSHOW
        cap = cv2.VideoCapture(0, backend)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 25)
        return ("cv", cap) if cap.isOpened() else (None, None)

    def _read(self, ctype, cam):
        if ctype == "pi":
            arr = cam.capture_array()
            return True, cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        return cam.read()

    def _close(self, ctype, cam):
        if not cam:
            return
        try:
            if ctype == "pi":
                cam.stop(); cam.close()
            else:
                cam.release()
        except Exception:
            pass

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        self.running = True
        ctype, cam = self._open_camera()
        if cam is None:
            self.status_update.emit("Không mở được camera")
            self.running = False
            return

        try:
            while self.running:
                ret, frame = self._read(ctype, cam)
                if not ret:
                    self.msleep(15)
                    continue

                # Raspi CSI mount ngược — xoay 180°
                if platform.system() == "Linux":
                    frame = cv2.rotate(frame, cv2.ROTATE_180)

                now = datetime.now().timestamp()

                # ── Nhận diện theo chu kỳ ──────────────────────────────────
                if now - self._last_process_ts >= self._pi_interval:
                    self._last_process_ts = now
                    small = cv2.resize(frame, None,
                                       fx=self.DETECT_SCALE, fy=self.DETECT_SCALE)
                    gray_s = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                    faces_s = fm.detect_faces(gray_s)
                    self._last_face_boxes = []
                    self._last_face_ts = now

                    for sx, sy, sw, sh in faces_s:
                        x = int(sx / self.DETECT_SCALE)
                        y = int(sy / self.DETECT_SCALE)
                        w = int(sw / self.DETECT_SCALE)
                        h = int(sh / self.DETECT_SCALE)

                        if self.mode == "capture":
                            self._last_face_boxes.append((x, y, w, h, None, 0, "scanning"))
                            continue

                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        enc  = fm.extract_encoding_from_frame(gray, x, y, w, h)
                        sid, name, conf = fm.recognize_face(enc)

                        if sid:
                            last_t = self._scan_cooldown.get(sid, 0)
                            if self.current_session_id and now - last_t > 5:
                                self._scan_cooldown[sid] = now
                                old_status = db.mark_present(sid, self.current_session_id)
                                logs = db.get_scan_logs(sid, self.current_session_id)
                                last_result = logs[-1]["result"] if logs else None
                                if old_status != "present" and last_result != "present":
                                    db.log_scan(sid, self.current_session_id, "present")
                                self.face_detected.emit(sid, name, conf)
                            box_st = "present" if self.current_session_id else "scanning"
                            self._last_face_boxes.append((x, y, w, h, sid, conf, box_st))
                        else:
                            self._last_face_boxes.append((x, y, w, h, "Unknown", conf, "unknown"))

                # ── Vẽ box khuôn mặt ──────────────────────────────────────
                if now - self._last_face_ts <= 1.5:
                    for x, y, w, h, name, conf, st in self._last_face_boxes:
                        fm.draw_face_box(frame, x, y, w, h, name, conf, st)

                # ── Phát frame ────────────────────────────────────────────
                if now - self._last_display_ts >= self.DISPLAY_INTERVAL:
                    self._last_display_ts = now
                    self.frame_ready.emit(frame.copy())

                self.msleep(8)

        except Exception as exc:
            self.status_update.emit(f"Camera lỗi: {exc}")
        finally:
            self.running = False
            self._close(ctype, cam)

    def stop(self):
        self.running = False
        if not self.wait(4500):
            print("[CameraThread] Timeout khi dừng thread camera")


# ─── Dialog thêm / sửa sinh viên ─────────────────────────────────────────────

class StudentDialog(QDialog):
    student_saved = pyqtSignal()

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data          = data   # dict or None (add mode)
        self.cam_thread    = None
        self.latest_frame  = None
        self.preview_frozen = False
        self.pose_frames   = {}
        self.current_pose  = "front"

        self.setWindowTitle("Thêm sinh viên" if not data else "Sửa sinh viên")
        self.setMinimumSize(860, 560)
        self.resize(880, 580)
        self.setStyleSheet(QSS + f"QDialog {{ background-color: {C['bg']}; }}")
        self._build()
        if data:
            self._fill(data)
        self._update_pose_ui()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ── Left: camera & pose controls ──────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(10)

        lbl_cam = make_label("Ảnh khuôn mặt", 14, True, C['accent'])
        left.addWidget(lbl_cam)

        self.cam_view = QLabel()
        self.cam_view.setMinimumSize(310, 235)
        self.cam_view.setMaximumSize(370, 265)
        self.cam_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.cam_view.setStyleSheet(f"""
            background-color: {C['surface']};
            border: 2px dashed {C['border']};
            border-radius: 12px;
        """)
        self.cam_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam_view.setText("Chưa có ảnh")
        left.addWidget(self.cam_view)

        # Pose buttons
        pose_row = QHBoxLayout()
        pose_row.setSpacing(6)
        self.pose_btns = {}
        for key, lbl in [("front", "Chính diện"), ("left", "Trái"), ("right", "Phải")]:
            btn = QPushButton(lbl)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda _, p=key: self._set_pose(p))
            pose_row.addWidget(btn)
            self.pose_btns[key] = btn
        left.addLayout(pose_row)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)
        self.btn_cam = QPushButton("Bật camera")
        apply_button_variant(self.btn_cam, "primary")
        self.btn_cam.setMinimumHeight(44)
        self.btn_cam.clicked.connect(self._toggle_cam)
        ctrl_row.addWidget(self.btn_cam)

        self.btn_capture = QPushButton("Chụp ảnh")
        self.btn_capture.setMinimumHeight(44)
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self._capture)
        ctrl_row.addWidget(self.btn_capture)
        left.addLayout(ctrl_row)

        btn_upload = QPushButton("Tải ảnh từ file")
        btn_upload.setMinimumHeight(40)
        btn_upload.clicked.connect(self._upload)
        left.addWidget(btn_upload)

        self.face_status = make_label("Cần 3 góc: chính diện, trái, phải",
                                       11, False, C['text_dim'])
        self.face_status.setWordWrap(True)
        self.face_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left.addWidget(self.face_status)
        left.addStretch()
        root.addLayout(left)

        # ── Right: form ───────────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)

        form_title = make_label("Thông tin sinh viên", 14, True, C['accent'])
        right.addWidget(form_title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setContentsMargins(0, 0, 0, 0)

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("Ví dụ: SV001, 21IT001")
        form.addRow("Mã sinh viên *", self.id_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Họ và tên đầy đủ")
        form.addRow("Họ và tên *", self.name_edit)

        right.addLayout(form)

        hint = QLabel(
            "Mẹo: Chụp đủ 3 góc để tăng độ chính xác nhận diện.\n"
            "Ánh sáng đủ, nhìn thẳng vào camera, không đeo khẩu trang."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"""
            background-color: {C['surface2']};
            border: 1px solid {C['border']};
            border-radius: 8px;
            color: {C['text_dim']};
            padding: 10px 14px;
            font-size: 12px;
        """)
        right.addWidget(hint)
        right.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setMinimumSize(110, 46)
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Lưu sinh viên")
        apply_button_variant(btn_save, "primary")
        btn_save.setMinimumSize(160, 46)
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        right.addLayout(btns)
        root.addLayout(right)

    def _fill(self, d):
        self.id_edit.setText(d["student_id"])
        self.id_edit.setEnabled(False)
        self.name_edit.setText(d["name"])
        pp = d.get("photo_path")
        if pp and os.path.exists(pp):
            img = cv2.imread(pp)
            if img is not None:
                self._show_frame(img)
                self.pose_frames["front"] = img

    def _set_pose(self, pose, init=False):
        self.current_pose = pose
        self.preview_frozen = False
        self.btn_capture.setText("Chụp ảnh")
        if pose in self.pose_frames:
            self._show_frame(self.pose_frames[pose])
        elif not init:
            pass
        self._update_pose_ui()

    def _update_pose_ui(self):
        labels = {"front": "Chính diện", "left": "Trái", "right": "Phải"}
        for key, btn in self.pose_btns.items():
            done = "✓" if key in self.pose_frames else "○"
            sel  = " ◀" if key == self.current_pose else ""
            btn.setText(f"{done} {labels[key]}{sel}")
            btn.setChecked(key == self.current_pose)
            if key in self.pose_frames:
                btn.setStyleSheet(f"color: {C['green']}; border-color: {C['green']};")
            elif key == self.current_pose:
                btn.setStyleSheet(f"color: {C['accent']}; border-color: {C['accent']};")
            else:
                btn.setStyleSheet("")

        done_keys   = [k for k in ("front", "left", "right") if k in self.pose_frames]
        miss_keys   = [k for k in ("front", "left", "right") if k not in self.pose_frames]
        miss_labels = {"front": "chính diện", "left": "trái", "right": "phải"}
        if miss_keys:
            msg = "Thiếu: " + ", ".join(miss_labels[k] for k in miss_keys)
            self.face_status.setStyleSheet(f"color: {C['yellow']}; font-size: 11px;")
        else:
            msg = "✓ Đã đủ 3 ảnh khuôn mặt"
            self.face_status.setStyleSheet(f"color: {C['green']}; font-size: 11px;")
        self.face_status.setText(msg)

    # ── Camera controls ───────────────────────────────────────────────────────

    def _toggle_cam(self):
        if self.cam_thread and self.cam_thread.running:
            self.cam_thread.stop()
            self.cam_thread = None
            self.btn_cam.setText("Bật camera")
            apply_button_variant(self.btn_cam, "primary")
            self.btn_capture.setEnabled(False)
            self.latest_frame = None
            self.cam_view.clear()
            self.cam_view.setText("Camera đã tắt")
        else:
            self.cam_thread = CameraThread(mode="capture")
            self.cam_thread.frame_ready.connect(self._on_frame)
            self.cam_thread.status_update.connect(self._on_cam_err)
            self.cam_thread.start()
            self.btn_cam.setText("Tắt camera")
            apply_button_variant(self.btn_cam, "danger")
            self.btn_capture.setEnabled(True)

    def _on_frame(self, frame):
        if self.sender() is not self.cam_thread or self.preview_frozen:
            return
        self.latest_frame = frame.copy()
        self._show_frame(frame)

    def _show_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            max(240, self.cam_view.width()), max(180, self.cam_view.height()),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.cam_view.setPixmap(pix)

    def _on_cam_err(self, msg):
        self.face_status.setText(f"Lỗi camera: {msg}")
        self.face_status.setStyleSheet(f"color: {C['red']}; font-size: 11px;")
        self.btn_cam.setText("Bật camera")
        apply_button_variant(self.btn_cam, "primary")
        self.btn_capture.setEnabled(False)
        self.cam_thread = None

    def _capture(self):
        if self.preview_frozen:
            self.preview_frozen = False
            self.btn_capture.setText("Chụp ảnh")
            self.face_status.setText("Đang xem camera...")
            self.face_status.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px;")
            return
        if self.latest_frame is None:
            QMessageBox.warning(self, "Chưa có hình", "Camera chưa sẵn sàng.")
            return
        frame = self.latest_frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = fm.detect_faces(gray)
        if len(faces) == 0:
            self.face_status.setText("Không phát hiện khuôn mặt — thử lại.")
            self.face_status.setStyleSheet(f"color: {C['red']}; font-size: 11px;")
            return
        self.pose_frames[self.current_pose] = frame
        self.preview_frozen = True
        self.btn_capture.setText("Chụp lại")
        self._show_frame(frame)
        self._update_pose_ui()

    def _upload(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh sinh viên", "", "Ảnh (*.jpg *.jpeg *.png *.bmp)"
        )
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            return
        gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = fm.detect_faces(gray)
        if len(faces) == 0:
            QMessageBox.warning(self, "Không có mặt", "Không tìm thấy khuôn mặt trong ảnh.")
            return
        self.pose_frames[self.current_pose] = img
        self._show_frame(img)
        self._update_pose_ui()

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        sid  = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        if not sid or not name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng điền Mã SV và Họ tên!")
            return
        if not self.data and db.get_student(sid):
            QMessageBox.warning(self, "Trùng mã", "Mã sinh viên đã tồn tại.")
            return
        if not self.data and len(self.pose_frames) < 3:
            QMessageBox.warning(self, "Thiếu ảnh", "Cần đủ 3 góc: chính diện, trái, phải.")
            return

        encodings  = []
        photo_path = None
        for pose, frame in self.pose_frames.items():
            saved = fm.save_student_photo(sid, frame, pose)
            if pose == "front":
                photo_path = saved
            gray, faces = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), fm.detect_faces(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            )
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                gray_f = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                try:
                    encodings.append(fm.extract_encoding_from_frame(gray_f, x, y, w, h))
                except Exception as exc:
                    QMessageBox.warning(self, "Lỗi encoding", str(exc))
                    return

        face_encoding = (
            np.mean(np.array(encodings, dtype=np.float32), axis=0).tolist()
            if encodings else None
        )

        if self.data:
            db.update_student(sid, name=name, photo_path=photo_path,
                              face_encoding=face_encoding,
                              keep_encoding=(len(encodings) == 0))
        else:
            ok, msg = db.add_student(sid, name, photo_path, face_encoding)
            if not ok:
                QMessageBox.critical(self, "Lỗi", msg)
                return

        if self.cam_thread:
            self.cam_thread.stop()
        fm.load_recognizer()
        self.student_saved.emit()
        self.accept()

    def closeEvent(self, event):
        if self.cam_thread:
            self.cam_thread.stop()
        super().closeEvent(event)

    def reject(self):
        if self.cam_thread:
            self.cam_thread.stop()
        super().reject()


# ─── Settings Dialog ──────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt hệ thống")
        self.setMinimumSize(660, 540)
        self.setStyleSheet(QSS + f"QDialog {{ background-color: {C['bg']}; }}")
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        root.addWidget(make_label("Cài đặt hệ thống", 18, True))

        tabs = QTabWidget()

        # ── Tab thời gian ─────────────────────────────────────────────────
        tw = QWidget()
        tw.setStyleSheet(f"background-color: {C['surface']};")
        tf = QFormLayout(tw)
        tf.setSpacing(13)
        tf.setContentsMargins(18, 18, 18, 18)

        self.class_name = QLineEdit()
        tf.addRow("Tên lớp học:", self.class_name)

        self.total_p = QSpinBox()
        self.total_p.setRange(1, 6)
        self.total_p.setValue(3)
        self.total_p.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.total_p.valueChanged.connect(self._sync_period_visibility)
        tf.addRow("Số tiết / ngày:", self.total_p)

        tf.addRow(make_label(""))
        # Dynamic period fields
        self.p_widgets = {}
        for p in range(1, 7):
            t_lbl  = make_label(f"── Tiết {p} ──────────────")
            ts     = QTimeEdit(); ts.setDisplayFormat("HH:mm"); ts.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
            te     = QTimeEdit(); te.setDisplayFormat("HH:mm"); te.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
            ts_lbl = make_label(f"Bắt đầu Tiết {p}:")
            te_lbl = make_label(f"Kết thúc Tiết {p}:")
            self.p_widgets[p] = (t_lbl, ts_lbl, ts, te_lbl, te)
            tf.addRow(t_lbl)
            tf.addRow(ts_lbl, ts)
            tf.addRow(te_lbl, te)
            if p == 1:
                self.brk_title  = make_label("── Nghỉ giải lao ─────────")
                self.brk_s      = QTimeEdit(); self.brk_s.setDisplayFormat("HH:mm"); self.brk_s.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
                self.brk_e      = QTimeEdit(); self.brk_e.setDisplayFormat("HH:mm"); self.brk_e.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
                self.brk_s_lbl  = make_label("Bắt đầu nghỉ:")
                self.brk_e_lbl  = make_label("Kết thúc nghỉ:")
                tf.addRow(self.brk_title)
                tf.addRow(self.brk_s_lbl, self.brk_s)
                tf.addRow(self.brk_e_lbl, self.brk_e)

        tscroll = QScrollArea()
        tscroll.setWidgetResizable(True)
        tscroll.setWidget(tw)
        tscroll.setStyleSheet(f"background-color: {C['surface']}; border: none;")
        tabs.addTab(tscroll, "Thời gian")

        # ── Tab điểm danh ─────────────────────────────────────────────────
        aw = QWidget()
        aw.setStyleSheet(f"background-color: {C['surface']};")
        af = QFormLayout(aw)
        af.setSpacing(13)
        af.setContentsMargins(18, 18, 18, 18)

        self.scan_ivl = QSpinBox(); self.scan_ivl.setRange(5, 300); self.scan_ivl.setSuffix(" giây")
        self.scan_ivl.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        af.addRow("Chu kỳ quét vắng:", self.scan_ivl)

        self.abs_thr = QSpinBox(); self.abs_thr.setRange(1, 10); self.abs_thr.setSuffix(" lần")
        self.abs_thr.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        af.addRow("Ngưỡng đánh vắng:", self.abs_thr)

        self.grace = QSpinBox(); self.grace.setRange(0, 30); self.grace.setSuffix(" phút")
        self.grace.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        af.addRow("Ân hạn vào lớp:", self.grace)

        note = QLabel(
            "Ngưỡng đánh vắng: số lần quét camera không thấy mặt\n"
            "liên tiếp trước khi hệ thống đánh dấu vắng.\n\n"
            "Ân hạn: SV đến trong khoảng này sau khi tiết bắt đầu\n"
            "vẫn được tính có mặt."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"""
            background-color: {C['surface2']};
            border: 1px solid {C['border']};
            border-radius: 8px;
            color: {C['text_dim']};
            padding: 12px 14px;
            font-size: 12px;
        """)
        af.addRow(note)
        tabs.addTab(aw, "Điểm danh")

        root.addWidget(tabs)

        btns = QHBoxLayout()
        btns.addStretch()
        bc = QPushButton("Hủy")
        bc.setMinimumSize(110, 44)
        bc.clicked.connect(self.reject)
        bs = QPushButton("Lưu cài đặt")
        bs.setObjectName("primary")
        bs.setMinimumSize(160, 44)
        bs.clicked.connect(self._save)
        btns.addWidget(bc)
        btns.addWidget(bs)
        root.addLayout(btns)

    def _load(self):
        s = db.get_all_settings()
        self.class_name.setText(s.get("class_name", ""))
        self.total_p.setValue(int(s.get("total_periods", 3)))
        for p in range(1, 7):
            _, _, ts, _, te = self.p_widgets[p]
            ts.setTime(QTime.fromString(s.get(f"period_{p}_start", "07:00"), "HH:mm"))
            te.setTime(QTime.fromString(s.get(f"period_{p}_end",   "08:30"), "HH:mm"))
        self.brk_s.setTime(QTime.fromString(s.get("break_start", "08:30"), "HH:mm"))
        self.brk_e.setTime(QTime.fromString(s.get("break_end",   "08:45"), "HH:mm"))
        self.scan_ivl.setValue(int(s.get("scan_interval_seconds", 30)))
        self.abs_thr.setValue(int(s.get("absent_threshold", 3)))
        self.grace.setValue(int(s.get("grace_period_minutes", 5)))
        self._sync_period_visibility()

    def _sync_period_visibility(self):
        total = self.total_p.value()
        for p, wl in self.p_widgets.items():
            for w in wl:
                w.setVisible(p <= total)
        show_brk = total >= 2
        for w in (self.brk_title, self.brk_s_lbl, self.brk_s, self.brk_e_lbl, self.brk_e):
            w.setVisible(show_brk)

    def _save(self):
        d = {
            "class_name":    self.class_name.text(),
            "total_periods": str(self.total_p.value()),
            "break_start":   self.brk_s.time().toString("HH:mm"),
            "break_end":     self.brk_e.time().toString("HH:mm"),
            "scan_interval_seconds": str(self.scan_ivl.value()),
            "absent_threshold":      str(self.abs_thr.value()),
            "grace_period_minutes":  str(self.grace.value()),
        }
        for p in range(1, 7):
            _, _, ts, _, te = self.p_widgets[p]
            d[f"period_{p}_start"] = ts.time().toString("HH:mm")
            d[f"period_{p}_end"]   = te.time().toString("HH:mm")
        db.save_settings_bulk(d)
        QMessageBox.information(self, "Thành công", "Đã lưu cài đặt.")
        self.accept()


class AttendanceDetailDialog(QDialog):
    STATUS_LABELS = {
        "present": "Có mặt",
        "half": "1/2 buổi",
        "absent": "Vắng",
        "excused": "Vắng có phép",
        "scanning": "Đang quét",
    }
    EVENT_LABELS = {
        "present": "Vào / có mặt",
        "half": "Ra ngoài / 1/2 buổi",
        "absent": "Vắng",
        "excused": "Vắng có phép",
    }

    def __init__(self, parent, student, session_id, editable=True):
        super().__init__(parent)
        self.student = student
        self.session_id = session_id
        self.session = db.get_session(session_id) or {}
        self.editable = editable
        self.setWindowTitle(f"Chi tiết điểm danh - {student['student_id']}")
        self.setMinimumSize(620, 520)
        self.setStyleSheet(QSS + f"QDialog {{ background-color: {C['bg']}; }}")
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = make_label(
            f"{self.student['student_id']} - {self.student['name']}",
            17, True, C['accent']
        )
        root.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        self.status_combo = QComboBox()
        for value, label in self.STATUS_LABELS.items():
            self.status_combo.addItem(label, value)
        self.check_in_edit = QLineEdit()
        self.check_in_edit.setPlaceholderText("HH:MM:SS")
        self.last_seen_edit = QLineEdit()
        self.last_seen_edit.setPlaceholderText("HH:MM:SS")
        form.addRow("Trạng thái:", self.status_combo)
        form.addRow("Giờ vào đầu:", self.check_in_edit)
        form.addRow("Lần thấy gần nhất:", self.last_seen_edit)
        root.addLayout(form)
        if not self.editable:
            self.status_combo.setEnabled(False)
            self.check_in_edit.setReadOnly(True)
            self.last_seen_edit.setReadOnly(True)

        root.addWidget(make_label("Timeline trong tiết", 13, True, C['accent']))
        self.log_table = QTableWidget(0, 3)
        self.log_table.setHorizontalHeaderLabels(["Giờ", "Sự kiện", "Ghi chú"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.log_table.setColumnWidth(0, 150)
        self.log_table.setColumnWidth(1, 160)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self.log_table, 1)

        if self.editable:
            add_row = QHBoxLayout()
            add_row.setSpacing(8)
            self.event_combo = QComboBox()
            for value, label in self.EVENT_LABELS.items():
                self.event_combo.addItem(label, value)
            self.event_time = QLineEdit(datetime.now().strftime("%H:%M:%S"))
            self.event_time.setPlaceholderText("HH:MM:SS")
            btn_add = QPushButton("Thêm mốc")
            apply_button_variant(btn_add, "primary")
            btn_add.clicked.connect(self._add_event)
            btn_del = QPushButton("Xóa mốc chọn")
            btn_del.clicked.connect(self._delete_selected_event)
            add_row.addWidget(self.event_combo)
            add_row.addWidget(self.event_time)
            add_row.addWidget(btn_add)
            add_row.addWidget(btn_del)
            root.addLayout(add_row)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Đóng")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)
        if self.editable:
            btn_save = QPushButton("Lưu chỉnh sửa")
            apply_button_variant(btn_save, "success")
            btn_save.clicked.connect(self._save)
            btns.addWidget(btn_save)
        root.addLayout(btns)

    def _load(self):
        att = db.get_attendance_detail(self.student["student_id"], self.session_id)
        status = att["status"] if att else "absent"
        idx = self.status_combo.findData(status)
        self.status_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.check_in_edit.setText((att or {}).get("check_in_time") or "")
        self.last_seen_edit.setText((att or {}).get("last_seen_time") or "")
        self._load_logs()

    def _load_logs(self):
        logs = db.get_scan_logs(self.student["student_id"], self.session_id)
        self.log_table.setRowCount(0)
        for log in logs:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            self.log_table.setRowHeight(row, 34)
            time_item = QTableWidgetItem(str(log["scan_time"]))
            time_item.setData(Qt.ItemDataRole.UserRole, log["id"])
            self.log_table.setItem(row, 0, time_item)
            label = self.EVENT_LABELS.get(log["result"], log["result"])
            self.log_table.setItem(row, 1, QTableWidgetItem(label))
            note = "Tự động" if log["result"] in ("present", "half", "absent") else ""
            self.log_table.setItem(row, 2, QTableWidgetItem(note))

    def _scan_time_text(self):
        txt = self.event_time.text().strip() or datetime.now().strftime("%H:%M:%S")
        if len(txt) == 5:
            txt += ":00"
        session_date = self.session.get("session_date") or date.today().isoformat()
        return f"{session_date} {txt}"

    def _add_event(self):
        result = self.event_combo.currentData()
        db.log_scan_at(
            self.student["student_id"],
            self.session_id,
            result,
            self._scan_time_text(),
        )
        if result == "present" and not self.check_in_edit.text().strip():
            self.check_in_edit.setText(self.event_time.text().strip())
        self._load_logs()

    def _delete_selected_event(self):
        row = self.log_table.currentRow()
        if row < 0:
            return
        item = self.log_table.item(row, 0)
        log_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if log_id:
            db.delete_scan_log(log_id)
            self._load_logs()

    def _save(self):
        old = db.get_attendance_detail(self.student["student_id"], self.session_id)
        new_status = self.status_combo.currentData()
        db.update_attendance_detail(
            self.student["student_id"],
            self.session_id,
            new_status,
            self.check_in_edit.text().strip(),
            self.last_seen_edit.text().strip(),
        )
        if (old or {}).get("status") != new_status:
            db.log_scan_at(
                self.student["student_id"],
                self.session_id,
                new_status,
                f"{self.session.get('session_date') or date.today().isoformat()} {datetime.now().strftime('%H:%M:%S')}",
            )
        self.accept()


class AdminLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ok = False
        self.setWindowTitle("Đăng nhập chỉnh sửa")
        self.setFixedSize(460, 300)
        self.setStyleSheet(QSS + f"QDialog {{ background-color: {C['bg']}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)
        root.addWidget(make_label("Cần quyền admin để chỉnh điểm danh", 14, True, C['accent']))

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        self.user_edit = QLineEdit()
        self.user_edit.setText("admin")
        self.user_edit.setMinimumHeight(44)
        self.user_edit.setMinimumWidth(260)
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setMinimumHeight(44)
        self.pass_edit.setMinimumWidth(260)
        self.pass_edit.returnPressed.connect(self._login)
        form.addRow("User:", self.user_edit)
        form.addRow("Mật khẩu:", self.pass_edit)
        root.addLayout(form)

        self.msg = make_label("", 11, False, C['red'])
        root.addWidget(self.msg)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setMinimumSize(110, 44)
        btn_cancel.clicked.connect(self.reject)
        btn_login = QPushButton("Đăng nhập")
        apply_button_variant(btn_login, "primary")
        btn_login.setMinimumSize(150, 44)
        btn_login.clicked.connect(self._login)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_login)
        root.addLayout(btns)

    def _login(self):
        if self.user_edit.text().strip() == "admin" and self.pass_edit.text() == "123456":
            self.ok = True
            self.accept()
        else:
            self.msg.setText("Sai user hoặc mật khẩu.")


# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        db.init_db()
        fm.load_recognizer()

        self.setWindowTitle(f"Hệ thống Điểm Danh Khuôn Mặt  v{APP_VERSION}")
        self.setMinimumSize(900, 520)
        scr = QApplication.primaryScreen()
        if scr:
            geo = scr.availableGeometry()
            self.resize(min(1280, geo.width()), min(800, geo.height()))

        self.setStyleSheet(QSS)

        # State
        self.cam_thread         = None
        self.current_session_id = None
        self.session_active     = False
        self._att_timer         = None
        self._absence_timer     = None
        self._last_seen         = {}      # sid → datetime
        self._missed_count      = {}      # sid → int
        self._last_absence_check = None
        self._last_face_name    = ""
        self._last_face_ts      = 0.0
        self._admin_unlocked    = False
        self._lcd               = (
            lcd_status.LcdStatusDisplay()
            if lcd_status and os.environ.get("CLASSROOM_APP_LCD") == "1"
            else None
        )

        self._build_ui()
        self._sync_period_combo()
        self._start_clock()
        if self._lcd:
            self._start_lcd_timer()
        self._start_lcd_bridge()
        self._refresh_student_list()
        self._refresh_dashboard()
        self._write_lcd_state()

    # ─────────────────────────────────────────────────────────────────────────
    # UI BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {C['bg']};")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content())

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = QFrame()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(168)
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo
        logo = QFrame()
        logo.setFixedHeight(72)
        logo.setStyleSheet(f"background-color: {C['surface2']}; border-bottom: 1px solid {C['border']};")
        ll = QVBoxLayout(logo)
        ll.setContentsMargins(16, 12, 16, 12)
        ll.setSpacing(2)
        ll.addWidget(make_label("● Điểm Danh AI", 15, True, C['accent']))
        ll.addWidget(make_label("Nhận diện khuôn mặt", 10, False, C['text_dim']))
        lay.addWidget(logo)

        lay.addSpacing(10)
        lay.addWidget(make_label("  ĐIỀU HƯỚNG", 9, True, C['text_dim']))
        lay.addSpacing(4)

        self.nav_btns = []
        nav = [
            ("○  Tổng quan",   0),
            ("◈  Điểm danh",   1),
            ("☰  Sinh viên",   2),
            ("▤  Báo cáo",     3),
            ("⚙  Cài đặt",    4),
        ]
        for label, idx in nav:
            btn = QPushButton(label)
            btn.setObjectName("nav" if idx != 0 else "nav_active")
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            lay.addWidget(btn)
            self.nav_btns.append(btn)

        lay.addStretch()
        lay.addWidget(hline())

        # Clock
        self.clock_lbl = make_label("00:00:00", 22, True, C['accent'],
                                     Qt.AlignmentFlag.AlignCenter)
        self.clock_lbl.setContentsMargins(0, 10, 0, 2)
        self.date_lbl  = make_label(datetime.now().strftime("%d/%m/%Y"),
                                     11, False, C['text_dim'],
                                     Qt.AlignmentFlag.AlignCenter)
        self.date_lbl.setContentsMargins(0, 0, 0, 14)
        lay.addWidget(self.clock_lbl)
        lay.addWidget(self.date_lbl)
        return sb

    # ── Content stack ─────────────────────────────────────────────────────────

    def _build_content(self):
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {C['bg']};")
        self.stack.addWidget(self._page_dashboard())   # 0
        self.stack.addWidget(self._page_camera())      # 1
        self.stack.addWidget(self._page_students())    # 2
        self.stack.addWidget(self._page_reports())     # 3
        self.stack.addWidget(self._page_settings())    # 4
        return self.stack

    # ── Page helpers ──────────────────────────────────────────────────────────

    def _page_header(self, title):
        """Trả về (QWidget header, QLabel title) để thêm nút bên phải."""
        hdr = QFrame()
        hdr.setObjectName("topbar")
        hdr.setFixedHeight(56)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(18, 0, 18, 0)
        lbl = make_label(title, 17, True)
        lay.addWidget(lbl)
        lay.addStretch()
        return hdr, lay

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 0: Dashboard
    # ─────────────────────────────────────────────────────────────────────────

    def _page_dashboard(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr, hdr_lay = self._page_header("Tổng quan")
        root.addWidget(hdr)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(18, 18, 18, 18)
        body_lay.setSpacing(16)

        # Stat cards
        card_row = QHBoxLayout()
        card_row.setSpacing(12)
        self.stat_cards = {}
        for key, label, color in [
            ("total_students", "Tổng sinh viên",  C['accent']),
            ("present_today",  "Có mặt hôm nay",  C['green']),
            ("absent_today",   "Vắng hôm nay",    C['red']),
            ("sessions_today", "Tiết học hôm nay", C['yellow']),
        ]:
            card = StatCard(label, "0", color)
            card.setMinimumHeight(95)
            self.stat_cards[key] = card
            card_row.addWidget(card)
        body_lay.addLayout(card_row)

        # Bottom
        bottom = QHBoxLayout()
        bottom.setSpacing(14)

        # Editable attendance overview
        rec_frame = QFrame(); rec_frame.setObjectName("card")
        rec_frame.setMinimumWidth(720)
        rec_lay = QVBoxLayout(rec_frame)
        rec_lay.setContentsMargins(18, 16, 18, 16)
        rec_lay.setSpacing(12)
        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(make_label("Tổng quan điểm danh", 13, True, C['accent']))
        top.addStretch()
        top.addWidget(make_label("Ngày:", 11, False, C['text_dim']))
        self.overview_date = QDateEdit()
        self.overview_date.setDisplayFormat("yyyy-MM-dd")
        self.overview_date.setCalendarPopup(True)
        self.overview_date.setMinimumSize(145, 40)
        self.overview_date.setDate(QDate.currentDate())
        self.overview_date.dateChanged.connect(lambda _: self._refresh_overview_table())
        top.addWidget(self.overview_date)
        top.addWidget(make_label("Tiết:", 11, False, C['text_dim']))
        self.overview_period = QComboBox()
        self.overview_period.setMinimumSize(105, 40)
        self.overview_period.currentIndexChanged.connect(lambda _: self._refresh_overview_table())
        top.addWidget(self.overview_period)
        rec_lay.addLayout(top)

        self.overview_table = QTableWidget(0, 5)
        self.overview_table.setHorizontalHeaderLabels(["Mã SV", "Sinh viên", "Trạng thái", "Sửa", "Chi tiết"])
        h = self.overview_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.overview_table.setColumnWidth(2, 140)
        self.overview_table.setColumnWidth(3, 110)
        self.overview_table.setColumnWidth(4, 120)
        self.overview_table.verticalHeader().setDefaultSectionSize(64)
        self.overview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.overview_table.verticalHeader().setVisible(False)
        self.overview_table.setAlternatingRowColors(True)
        rec_lay.addWidget(self.overview_table)
        bottom.addWidget(rec_frame, 3)

        # Session status card
        sess_frame = QFrame(); sess_frame.setObjectName("card_hi")
        sess_frame.setFixedWidth(280)
        sess_lay = QVBoxLayout(sess_frame)
        sess_lay.setContentsMargins(18, 16, 18, 16)
        sess_lay.setSpacing(10)
        sess_lay.addWidget(make_label("Tiết học hiện tại", 13, True, C['accent']))

        self.dash_sess_lbl = make_label("Chưa có tiết học", 12, False, C['text_dim'])
        self.dash_sess_lbl.setWordWrap(True)
        sess_lay.addWidget(self.dash_sess_lbl)

        self.dash_progress = QProgressBar()
        self.dash_progress.setValue(0)
        sess_lay.addWidget(self.dash_progress)

        self.dash_summary = make_label("", 12)
        self.dash_summary.setWordWrap(True)
        sess_lay.addWidget(self.dash_summary)
        sess_lay.addStretch()

        btn_go = QPushButton("→  Vào Điểm Danh")
        btn_go.setObjectName("primary")
        btn_go.setMinimumHeight(44)
        btn_go.clicked.connect(lambda: self._switch_page(1))
        sess_lay.addWidget(btn_go)
        bottom.addWidget(sess_frame)

        body_lay.addLayout(bottom)
        root.addWidget(body)
        return page

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 1: Camera / Điểm danh
    # ─────────────────────────────────────────────────────────────────────────

    def _page_camera(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr, hdr_lay = self._page_header("Camera & Điểm danh")
        btn_cfg = QPushButton("⚙ Cài đặt")
        btn_cfg.setMinimumHeight(36)
        btn_cfg.clicked.connect(self._open_settings)
        hdr_lay.addWidget(btn_cfg)
        root.addWidget(hdr)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 14, 14, 14)
        body_lay.setSpacing(12)

        # ── Session control bar ───────────────────────────────────────────
        sbar = QFrame(); sbar.setObjectName("card")
        sbar.setMaximumHeight(100)
        sb_lay = QVBoxLayout(sbar)
        sb_lay.setContentsMargins(16, 10, 16, 10)
        sb_lay.setSpacing(8)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(10)
        ctrl.addWidget(make_label("Ngày:", 12))
        self.date_combo = QComboBox()
        today = date.today().isoformat()
        self.date_combo.addItem(f"Hôm nay ({today})", today)
        self.date_combo.setMinimumWidth(175)
        ctrl.addWidget(self.date_combo)

        ctrl.addWidget(make_label("Tiết:", 12))
        self.period_combo = QComboBox()
        for i in range(1, 4):
            self.period_combo.addItem(f"Tiết {i}", i)
        self.period_combo.setMinimumWidth(90)
        ctrl.addWidget(self.period_combo)

        self.btn_session = QPushButton("▶  Bắt đầu")
        self.btn_session.setObjectName("success")
        self.btn_session.setMinimumSize(140, 46)
        self.btn_session.clicked.connect(self._toggle_session)
        ctrl.addWidget(self.btn_session)
        ctrl.addStretch()
        sb_lay.addLayout(ctrl)

        self.sess_info = make_label("Chưa có tiết học đang chạy", 12, False, C['text_dim'])
        self.sess_info.setWordWrap(True)
        sb_lay.addWidget(self.sess_info)
        body_lay.addWidget(sbar)

        # ── Main split: camera + list ─────────────────────────────────────
        split = QHBoxLayout()
        split.setSpacing(14)

        # Camera card
        cam_card = QFrame(); cam_card.setObjectName("card")
        cam_lay = QVBoxLayout(cam_card)
        cam_lay.setContentsMargins(14, 12, 14, 12)
        cam_lay.setSpacing(10)

        cam_top = QHBoxLayout()
        cam_top.setSpacing(10)
        cam_top.addWidget(make_label("Camera", 13, True, C['accent']))
        cam_top.addStretch()

        self.cam_badge = BadgePill("off")
        self.cam_badge.setMinimumWidth(80)
        cam_top.addWidget(self.cam_badge)

        self.btn_cam = QPushButton("Bật camera")
        apply_button_variant(self.btn_cam, "primary")
        self.btn_cam.setMinimumSize(140, 44)
        self.btn_cam.clicked.connect(self._toggle_cam_preview)
        cam_top.addWidget(self.btn_cam)
        cam_lay.addLayout(cam_top)

        self.cam_feed = QLabel()
        self.cam_feed.setMinimumSize(380, 280)
        self.cam_feed.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.cam_feed.setStyleSheet(f"""
            background-color: {C['surface']};
            border: 2px solid {C['border']};
            border-radius: 10px;
        """)
        self.cam_feed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam_feed.setText("Camera đang tắt\nBấm 'Bật camera' để bắt đầu")
        cam_lay.addWidget(self.cam_feed)

        self.scan_log = make_label("Nhật ký quét: —", 11, False, C['text_dim'])
        self.scan_log.setContentsMargins(4, 2, 4, 2)
        cam_lay.addWidget(self.scan_log)
        split.addWidget(cam_card, 3)

        # Attendance panel
        att_panel = QFrame(); att_panel.setObjectName("card")
        att_panel.setMinimumWidth(270)
        att_panel.setMaximumWidth(330)
        att_lay = QVBoxLayout(att_panel)
        att_lay.setContentsMargins(12, 12, 12, 12)
        att_lay.setSpacing(10)
        att_lay.addWidget(make_label("Bảng điểm danh", 13, True, C['accent']))

        # Mini counters
        mini_row = QHBoxLayout()
        mini_row.setSpacing(8)
        self.mc_present, self.mc_present_v = self._mini_counter("Có mặt", C['green'])
        self.mc_absent,  self.mc_absent_v  = self._mini_counter("Vắng",   C['red'])
        self.mc_half,    self.mc_half_v    = self._mini_counter("½ buổi", C['yellow'])
        mini_row.addWidget(self.mc_present)
        mini_row.addWidget(self.mc_absent)
        mini_row.addWidget(self.mc_half)
        att_lay.addLayout(mini_row)

        self.att_table = QTableWidget(0, 3)
        self.att_table.setHorizontalHeaderLabels(["Họ tên", "TT", "Giờ"])
        self.att_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.att_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.att_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.att_table.setColumnWidth(1, 76)
        self.att_table.setColumnWidth(2, 58)
        self.att_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.att_table.verticalHeader().setVisible(False)
        self.att_table.setAlternatingRowColors(True)
        self.att_table.cellDoubleClicked.connect(self._open_attendance_detail)
        att_lay.addWidget(self.att_table)

        btn_ref = QPushButton("Làm mới")
        btn_ref.setMinimumHeight(38)
        btn_ref.clicked.connect(self._refresh_att_table)
        att_lay.addWidget(btn_ref)
        split.addWidget(att_panel, 2)

        body_lay.addLayout(split)
        root.addWidget(body)
        return page

    def _mini_counter(self, label, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background-color: {C['surface2']};
            border: 1px solid {C['border']};
            border-radius: 8px;
        """)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(8, 7, 8, 7)
        vl.setSpacing(2)
        v = make_label("0", 20, True, color, Qt.AlignmentFlag.AlignCenter)
        l = make_label(label, 9, True, C['text_dim'], Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(v)
        vl.addWidget(l)
        return frame, v

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 2: Sinh viên
    # ─────────────────────────────────────────────────────────────────────────

    def _page_students(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr, hdr_lay = self._page_header("Quản lý Sinh viên")
        root.addWidget(hdr)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(14, 14, 14, 14)
        body_lay.setSpacing(12)

        # Toolbar
        tb = QFrame(); tb.setObjectName("card")
        tb.setMinimumHeight(86)
        tb.setMaximumHeight(92)
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(16, 12, 16, 12)
        tl.setSpacing(16)

        btn_add = QPushButton("Thêm")
        apply_button_variant(btn_add, "primary")
        btn_add.setMinimumSize(180, 48)
        btn_add.clicked.connect(self._add_student)
        tl.addWidget(btn_add)

        self.sv_total = make_label("Tổng: 0", 12, False, C['text_dim'])
        self.sv_total.setMinimumWidth(88)
        tl.addWidget(self.sv_total)
        self.sv_face_count = make_label("Đã nhận diện: 0", 12, True, C['green'])
        self.sv_face_count.setMinimumWidth(150)
        tl.addWidget(self.sv_face_count)
        tl.addStretch()

        self.sv_search = QLineEdit()
        self.sv_search.setPlaceholderText("Tìm kiếm sinh viên...")
        self.sv_search.setMinimumWidth(240)
        self.sv_search.setMaximumWidth(280)
        self.sv_search.setMinimumHeight(44)
        self.sv_search.textChanged.connect(self._filter_students)
        tl.addWidget(self.sv_search)
        body_lay.addWidget(tb)

        # Table
        self.sv_table = QTableWidget(0, 5)
        self.sv_table.setHorizontalHeaderLabels(["Ảnh", "Mã SV", "Họ và tên", "Khuôn mặt", "Thao tác"])
        h = self.sv_table.horizontalHeader()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.sv_table.setColumnWidth(0, 76)
        self.sv_table.setColumnWidth(3, 145)
        self.sv_table.setColumnWidth(4, 190)
        self.sv_table.verticalHeader().setDefaultSectionSize(72)
        self.sv_table.verticalHeader().setVisible(False)
        self.sv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sv_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sv_table.setAlternatingRowColors(True)
        self.sv_table.setShowGrid(False)
        body_lay.addWidget(self.sv_table)

        root.addWidget(body)
        return page

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 3: Báo cáo
    # ─────────────────────────────────────────────────────────────────────────

    def _page_reports(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr, _ = self._page_header("Báo cáo & Xuất file")
        root.addWidget(hdr)

        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(14, 14, 14, 14)
        bl.setSpacing(14)

        # ── Báo cáo ngày ──────────────────────────────────────────────────
        day_card = QFrame(); day_card.setObjectName("card")
        dl = QVBoxLayout(day_card)
        dl.setContentsMargins(16, 14, 16, 14)
        dl.setSpacing(12)
        dl.addWidget(make_label("Báo cáo theo ngày", 14, True, C['accent']))

        df = QHBoxLayout()
        df.addWidget(make_label("Ngày:"))
        self.export_date = QComboBox()
        self.export_date.setEditable(True)
        self._populate_export_dates()
        df.addWidget(self.export_date)
        dl.addLayout(df)

        btn_prev = QPushButton("Xem trước dữ liệu")
        btn_prev.setMinimumHeight(42)
        btn_prev.clicked.connect(self._preview_attendance)
        dl.addWidget(btn_prev)

        db_row = QHBoxLayout()
        db_row.setSpacing(8)
        btn_xlsx = QPushButton("Xuất Excel")
        btn_xlsx.setObjectName("primary")
        btn_xlsx.setMinimumHeight(44)
        btn_xlsx.clicked.connect(lambda: self._export_day("xlsx"))
        btn_pdf = QPushButton("Xuất PDF")
        apply_button_variant(btn_pdf, "success")
        btn_pdf.setMinimumHeight(44)
        btn_pdf.clicked.connect(lambda: self._export_day("pdf"))
        db_row.addWidget(btn_xlsx)
        db_row.addWidget(btn_pdf)
        dl.addLayout(db_row)

        self.prev_table = QTableWidget(0, 5)
        self.prev_table.setHorizontalHeaderLabels(["Mã SV", "Họ tên", "Tiết 1", "Tiết 2", "Tiết 3"])
        self.prev_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prev_table.verticalHeader().setVisible(False)
        self.prev_table.setAlternatingRowColors(True)
        self.prev_table.cellDoubleClicked.connect(self._open_report_attendance_detail)
        dl.addWidget(self.prev_table, 1)
        bl.addWidget(day_card, 3)

        # ── Báo cáo tháng ─────────────────────────────────────────────────
        mon_card = QFrame(); mon_card.setObjectName("card")
        ml = QVBoxLayout(mon_card)
        ml.setContentsMargins(16, 14, 16, 14)
        ml.setSpacing(12)
        ml.addWidget(make_label("Báo cáo tháng", 14, True, C['accent']))

        mf = QGridLayout()
        mf.setSpacing(10)
        mf.addWidget(make_label("Tháng:"), 0, 0)
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f"Tháng {m}", m)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        mf.addWidget(self.month_combo, 0, 1)
        mf.addWidget(make_label("Năm:"), 1, 0)
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2035)
        self.year_spin.setValue(datetime.now().year)
        self.year_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        mf.addWidget(self.year_spin, 1, 1)
        ml.addLayout(mf)

        btn_mxlsx = QPushButton("Xuất Excel tháng")
        btn_mxlsx.setObjectName("primary")
        btn_mxlsx.setMinimumHeight(46)
        btn_mxlsx.clicked.connect(lambda: self._export_month("xlsx"))
        ml.addWidget(btn_mxlsx)
        btn_mpdf = QPushButton("Xuất PDF tháng")
        apply_button_variant(btn_mpdf, "success")
        btn_mpdf.setMinimumHeight(46)
        btn_mpdf.clicked.connect(lambda: self._export_month("pdf"))
        ml.addWidget(btn_mpdf)
        ml.addStretch()
        bl.addWidget(mon_card, 1)

        root.addWidget(body)
        return page

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 4: Cài đặt
    # ─────────────────────────────────────────────────────────────────────────

    def _page_settings(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)

        hdr, hdr_lay = self._page_header("Cài đặt")
        btn_open = QPushButton("Mở cài đặt chi tiết")
        btn_open.setObjectName("primary")
        btn_open.setMinimumSize(200, 40)
        btn_open.clicked.connect(self._open_settings)
        hdr_lay.addWidget(btn_open)
        root.addWidget(hdr)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(14, 14, 14, 14)
        self.settings_display = QTextEdit()
        self.settings_display.setReadOnly(True)
        self.settings_display.setStyleSheet(f"""
            background-color: {C['surface']};
            border: 1px solid {C['border']};
            border-radius: 10px;
            color: {C['text']};
            font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
            font-size: 12px;
            padding: 14px;
        """)
        bl.addWidget(self.settings_display)
        root.addWidget(body)
        self._refresh_settings_display()
        return page

    # ─────────────────────────────────────────────────────────────────────────
    # CLOCK & TIME STATE
    # ─────────────────────────────────────────────────────────────────────────

    def _start_clock(self):
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(1000)

    def _tick(self):
        now = datetime.now()
        self.clock_lbl.setText(now.strftime("%H:%M:%S"))
        self.date_lbl.setText(now.strftime("%d/%m/%Y"))
        self._sync_time_state(now)
        if self.session_active:
            self._auto_end_check(now)

    def _time_min(self, hhmm):
        t = datetime.strptime(hhmm, "%H:%M").time()
        return t.hour * 60 + t.minute

    def _get_time_state(self, now=None):
        now = now or datetime.now()
        m   = now.hour * 60 + now.minute
        s   = db.get_all_settings()
        tp  = int(s.get("total_periods", 3))
        for p in range(1, tp + 1):
            ps = s.get(f"period_{p}_start")
            pe = s.get(f"period_{p}_end")
            if ps and pe and self._time_min(ps) <= m < self._time_min(pe):
                return {"type": "period", "period": p, "start": ps, "end": pe}
        if tp >= 2:
            bs = s.get("break_start", "08:30")
            be = s.get("break_end",   "08:45")
            if self._time_min(bs) <= m < self._time_min(be):
                return {"type": "break", "start": bs, "end": be}
        return {"type": "off"}

    def _sync_time_state(self, now=None):
        if self.session_active:
            return
        if not hasattr(self, "sess_info"):
            return
        state = self._get_time_state(now)
        if state["type"] == "period":
            idx = self.period_combo.findData(state["period"])
            if idx >= 0:
                self.period_combo.setCurrentIndex(idx)
            self.sess_info.setText(
                f"Đang trong Tiết {state['period']} ({state['start']} → {state['end']})"
            )
            self.sess_info.setStyleSheet(f"color: {C['accent']}; font-size: 12px;")
        elif state["type"] == "break":
            self.sess_info.setText(f"Đang ra chơi ({state['start']} → {state['end']})")
            self.sess_info.setStyleSheet(f"color: {C['yellow']}; font-size: 12px;")
        else:
            self.sess_info.setText("Ngoài khung giờ học")
            self.sess_info.setStyleSheet(f"color: {C['text_dim']}; font-size: 12px;")

    def _sync_period_combo(self):
        s = db.get_all_settings()
        total = int(s.get("total_periods", 3))
        for combo_name in ("period_combo", "overview_period"):
            if not hasattr(self, combo_name):
                continue
            combo = getattr(self, combo_name)
            cur = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for i in range(1, total + 1):
                combo.addItem(f"Tiết {i}", i)
            if cur:
                idx = combo.findData(cur)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    # ─────────────────────────────────────────────────────────────────────────
    # NAVIGATION
    # ─────────────────────────────────────────────────────────────────────────

    def _switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setObjectName("nav_active" if i == idx else "nav")
            btn.setStyle(btn.style())
        if idx == 0:
            self._refresh_dashboard()
        elif idx == 2:
            self._refresh_student_list()
        elif idx == 4:
            self._refresh_settings_display()

    def _ensure_admin(self):
        if self._admin_unlocked:
            return True
        dlg = AdminLoginDialog(self)
        if dlg.exec() and dlg.ok:
            self._admin_unlocked = True
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # DASHBOARD
    # ─────────────────────────────────────────────────────────────────────────

    def _refresh_dashboard(self):
        students = db.get_all_students()
        today    = date.today().isoformat()
        sessions = db.get_sessions_by_date(today)

        self.stat_cards["total_students"].set_value(len(students))
        self.stat_cards["sessions_today"].set_value(len(sessions))

        present = absent = 0
        for s in sessions:
            for a in db.get_attendance_by_session(s["id"]):
                if a["status"] == "present": present += 1
                elif a["status"] == "absent": absent  += 1
        self.stat_cards["present_today"].set_value(present)
        self.stat_cards["absent_today"].set_value(absent)

        self._refresh_overview_table()

        # Session summary
        if self.session_active and self.current_session_id:
            att  = db.get_attendance_by_session(self.current_session_id)
            p    = sum(1 for a in att if a["status"] == "present")
            tot  = len(students)
            self.dash_sess_lbl.setText(f"Tiết đang chạy — {p}/{tot} có mặt")
            self.dash_sess_lbl.setStyleSheet(f"color: {C['green']}; font-size: 12px;")
            self.dash_summary.setText(f"Có mặt: {p}  |  Vắng: {tot - p}")
            if tot > 0:
                self.dash_progress.setValue(int(p / tot * 100))
        else:
            self.dash_sess_lbl.setText("Chưa có tiết học đang chạy")
            self.dash_sess_lbl.setStyleSheet(f"color: {C['text_dim']}; font-size: 12px;")
            self.dash_summary.setText("")
            self.dash_progress.setValue(0)

    def _overview_selection(self, sid, create=False):
        tdate = self.overview_date.date().toString("yyyy-MM-dd")
        period = self.overview_period.currentData() or 1
        student = db.get_student(sid)
        sess = db.get_or_create_session(tdate, period) if create else None
        if not sess:
            for s in db.get_sessions_by_date(tdate):
                if s["period"] == period:
                    sess = s
                    break
        return student, sess, tdate, period

    def _refresh_overview_table(self):
        if not hasattr(self, "overview_table"):
            return
        tdate = self.overview_date.date().toString("yyyy-MM-dd")
        period = self.overview_period.currentData() or 1
        sess = next((s for s in db.get_sessions_by_date(tdate) if s["period"] == period), None)
        att_map = {}
        if sess:
            att_map = {a["student_id"]: a for a in db.get_attendance_by_session(sess["id"])}

        labels = {"present": "Có mặt", "absent": "Vắng", "half": "1/2", "excused": "Có phép", "scanning": "..."}
        colors = {"present": C['green'], "absent": C['red'], "half": C['yellow'], "excused": C['text_mid'], "scanning": C['accent']}
        self.overview_table.setRowCount(0)
        for sv in db.get_all_students():
            sid = sv["student_id"]
            att = att_map.get(sid)
            stat = att["status"] if att else "absent"
            row = self.overview_table.rowCount()
            self.overview_table.insertRow(row)
            self.overview_table.setRowHeight(row, 64)
            id_it = QTableWidgetItem(sid)
            id_it.setData(Qt.ItemDataRole.UserRole, sid)
            self.overview_table.setItem(row, 0, id_it)
            name_it = QTableWidgetItem(sv["name"])
            name_it.setData(Qt.ItemDataRole.UserRole, sid)
            self.overview_table.setItem(row, 1, name_it)
            st_it = QTableWidgetItem(labels.get(stat, stat))
            st_it.setForeground(QColor(colors.get(stat, C['text_dim'])))
            st_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            st_it.setData(Qt.ItemDataRole.UserRole, sid)
            self.overview_table.setItem(row, 2, st_it)

            btn_edit = QPushButton("Sửa")
            btn_edit.setFixedSize(82, 34)
            btn_edit.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['surface2']};
                    color: {C['text_mid']};
                    border: 1px solid {C['border']};
                    border-radius: 7px;
                    padding: 3px 8px;
                    font-weight: 700;
                    min-height: 0px;
                }}
                QPushButton:hover {{ color: {C['accent']}; border-color: {C['accent']}; }}
            """)
            btn_edit.clicked.connect(lambda _, x=sid: self._edit_overview_attendance(x))
            edit_w = QWidget()
            edit_lay = QHBoxLayout(edit_w)
            edit_lay.setContentsMargins(8, 4, 8, 4)
            edit_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_lay.addWidget(btn_edit)
            self.overview_table.setCellWidget(row, 3, edit_w)

            btn_detail = QPushButton("Chi tiết")
            btn_detail.setFixedSize(92, 34)
            btn_detail.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['surface2']};
                    color: {C['text_mid']};
                    border: 1px solid {C['border']};
                    border-radius: 7px;
                    padding: 3px 8px;
                    font-weight: 700;
                    min-height: 0px;
                }}
                QPushButton:hover {{ color: {C['accent']}; border-color: {C['accent']}; }}
            """)
            btn_detail.clicked.connect(lambda _, x=sid: self._open_overview_detail(x))
            detail_w = QWidget()
            detail_lay = QHBoxLayout(detail_w)
            detail_lay.setContentsMargins(8, 4, 8, 4)
            detail_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            detail_lay.addWidget(btn_detail)
            self.overview_table.setCellWidget(row, 4, detail_w)

    def _edit_overview_attendance(self, sid):
        if not self._ensure_admin():
            return
        student, sess, tdate, period = self._overview_selection(sid, create=True)
        if not student or not sess:
            return
        box = QMessageBox(self)
        box.setWindowTitle("Sửa điểm danh")
        box.setText(f"{student['student_id']} - {student['name']}\nNgày {tdate}, Tiết {period}")
        btn_abs = box.addButton("Vắng", QMessageBox.ButtonRole.AcceptRole)
        btn_pre = box.addButton("Có mặt", QMessageBox.ButtonRole.AcceptRole)
        btn_half = box.addButton("1/2 buổi", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("Hủy", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked not in (btn_abs, btn_pre, btn_half):
            return
        status = "absent"
        if clicked == btn_pre:
            status = "present"
        elif clicked == btn_half:
            status = "half"
        att = db.get_attendance_detail(sid, sess["id"])
        check_in = (att or {}).get("check_in_time") or ("00:00:00" if status == "present" else None)
        last_seen = (att or {}).get("last_seen_time") or check_in
        db.update_attendance_detail(sid, sess["id"], status, check_in, last_seen)
        db.log_scan_at(sid, sess["id"], status, f"{tdate} {datetime.now().strftime('%H:%M:%S')}")
        self._refresh_overview_table()
        self._refresh_dashboard()

    def _open_overview_detail(self, sid):
        student, sess, tdate, period = self._overview_selection(sid, create=False)
        if not student:
            return
        if not sess:
            QMessageBox.information(
                self, "Chưa có dữ liệu",
                f"{student['student_id']} - {student['name']}\nNgày {tdate}, Tiết {period}: Vắng / chưa có mốc ra vào."
            )
            return
        dlg = AttendanceDetailDialog(self, student, sess["id"], editable=False)
        if dlg.exec():
            self._refresh_dashboard()
            self._refresh_att_table()

    # ─────────────────────────────────────────────────────────────────────────
    # CAMERA
    # ─────────────────────────────────────────────────────────────────────────

    def _start_cam_preview(self):
        if self.cam_thread and self.cam_thread.running:
            return
        self.cam_thread = CameraThread(mode="monitor")
        if self.current_session_id:
            self.cam_thread.set_session(self.current_session_id)
        self.cam_thread.frame_ready.connect(self._on_frame)
        self.cam_thread.face_detected.connect(self._on_face)
        self.cam_thread.status_update.connect(self._on_cam_err)
        self.cam_thread.start()
        self.cam_badge.setStatus("scanning")
        self.btn_cam.setText("Tắt camera")
        apply_button_variant(self.btn_cam, "danger")
        self.cam_feed.setText("Đang mở camera...")

    def _stop_cam_preview(self):
        if self.cam_thread:
            th = self.cam_thread
            self.cam_thread = None
            try: th.frame_ready.disconnect(self._on_frame)
            except Exception: pass
            try: th.face_detected.disconnect(self._on_face)
            except Exception: pass
            try: th.status_update.disconnect(self._on_cam_err)
            except Exception: pass
            th.stop()
        self.cam_badge.setStatus("off")
        self.btn_cam.setText("Bật camera")
        apply_button_variant(self.btn_cam, "primary")
        self.cam_feed.clear()
        self.cam_feed.setPixmap(QPixmap())
        self.cam_feed.setText("Camera đang tắt\nBấm 'Bật camera' để bắt đầu")
        self.scan_log.setText("Nhật ký quét: —")
        self.scan_log.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px;")

    def _toggle_cam_preview(self):
        if self.cam_thread and self.cam_thread.running:
            self._stop_cam_preview()
        else:
            self._start_cam_preview()

    def _on_frame(self, frame):
        if self.sender() is not self.cam_thread:
            return
        self.cam_badge.setStatus("live")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            max(380, self.cam_feed.width()), max(280, self.cam_feed.height()),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.cam_feed.setPixmap(pix)

    def _on_face(self, sid, name, conf):
        self._last_seen[sid]   = datetime.now()
        self._missed_count[sid] = 0
        self._last_face_name   = f"{name} ({sid})"
        self._last_face_ts     = datetime.now().timestamp()
        self.scan_log.setText(
            f"{datetime.now().strftime('%H:%M:%S')} — {name} ({sid}) — {conf:.0f}% khớp"
        )
        self.scan_log.setStyleSheet(f"color: {C['green']}; font-size: 11px;")
        if hasattr(self, "stack") and self.stack.currentIndex() == 0:
            self._refresh_dashboard()
        self._update_lcd()

    def _on_cam_err(self, msg):
        if self.sender() is self.cam_thread:
            self.cam_thread = None
        self._stop_cam_preview()
        self.cam_feed.setText(f"{msg}\nKiểm tra camera hoặc quyền truy cập.")
        self.scan_log.setText(msg)
        self.scan_log.setStyleSheet(f"color: {C['red']}; font-size: 11px;")
        if self.session_active:
            self.session_active = False
            self.btn_session.setText("▶  Bắt đầu")
            self.btn_session.setObjectName("success")
            self.btn_session.setStyle(self.btn_session.style())
            self.sess_info.setText("Camera không mở được")
            self.sess_info.setStyleSheet(f"color: {C['red']}; font-size: 12px;")
        if self._att_timer:     self._att_timer.stop()
        if self._absence_timer: self._absence_timer.stop()

    # ─────────────────────────────────────────────────────────────────────────
    # SESSION
    # ─────────────────────────────────────────────────────────────────────────

    def _toggle_session(self):
        if self.session_active:
            self._end_session()
        else:
            self._start_session()

    def _start_session(self):
        today = date.today().isoformat()
        state = self._get_time_state()
        period = (
            state["period"] if state["type"] == "period"
            else (self.period_combo.currentData() or 1)
        )
        sess = db.get_or_create_session(today, period) if state["type"] == "period" else None
        self.current_session_id = sess["id"] if sess else None
        self.session_active = True

        self.btn_session.setText("■  Kết thúc")
        self.btn_session.setObjectName("danger")
        self.btn_session.setStyle(self.btn_session.style())

        if sess:
            self.sess_info.setText(
                f"Đang điểm danh — Tiết {period} ({sess['start_time']} → {sess['end_time']})"
            )
            self.sess_info.setStyleSheet(f"color: {C['green']}; font-size: 12px;")
        else:
            self.sess_info.setText("Camera đang bật — Ngoài giờ tiết, không ghi điểm danh")
            self.sess_info.setStyleSheet(f"color: {C['yellow']}; font-size: 12px;")

        if self.cam_thread and self.cam_thread.running:
            self.cam_thread.set_session(self.current_session_id)
        else:
            self._start_cam_preview()
            if self.cam_thread:
                self.cam_thread.set_session(self.current_session_id)

        if self.current_session_id:
            db.update_session_status(self.current_session_id, "active")
            self.scan_log.setText("Điểm danh tự động đang chạy...")
            self.scan_log.setStyleSheet(f"color: {C['green']}; font-size: 11px;")

        self._refresh_att_table()
        self.statusBar().showMessage(f"Bắt đầu tiết — {datetime.now().strftime('%H:%M:%S')}")
        self._update_lcd()
        self._write_lcd_state()

        settings = db.get_all_settings()
        self._att_timer = QTimer(self)
        self._att_timer.timeout.connect(self._refresh_att_table)
        self._att_timer.start(5000)

        ivl = int(settings.get("scan_interval_seconds", 30))
        self._last_seen.clear()
        self._missed_count.clear()
        self._last_absence_check = datetime.now()
        if self.current_session_id:
            self._absence_timer = QTimer(self)
            self._absence_timer.timeout.connect(self._scan_absent)
            self._absence_timer.start(max(5, ivl) * 1000)

    def _end_session(self):
        if self.cam_thread:
            self.cam_thread.set_session(None)
        if self.current_session_id:
            db.finalize_absent_for_session(self.current_session_id)
            db.update_session_status(self.current_session_id, "completed")

        self.session_active = False
        self.btn_session.setText("▶  Bắt đầu")
        self.btn_session.setObjectName("success")
        self.btn_session.setStyle(self.btn_session.style())
        self.sess_info.setText("Tiết học đã kết thúc")
        self.sess_info.setStyleSheet(f"color: {C['text_dim']}; font-size: 12px;")

        if self.cam_thread and self.cam_thread.running:
            self.scan_log.setText("Đã kết thúc. Camera vẫn đang bật để xem trước.")
        else:
            self._stop_cam_preview()

        if self._att_timer:     self._att_timer.stop()
        if self._absence_timer: self._absence_timer.stop()

        self._refresh_att_table()
        self._refresh_dashboard()
        self.statusBar().showMessage(f"Kết thúc tiết — {datetime.now().strftime('%H:%M:%S')}")
        self._update_lcd()
        self._write_lcd_state()

    def _auto_end_check(self, now):
        if not self.current_session_id:
            return
        state = self._get_time_state(now)
        if state["type"] != "period" or state.get("period") != self.period_combo.currentData():
            self._end_session()
            self._sync_time_state(now)

    # ─────────────────────────────────────────────────────────────────────────
    # ABSENCE SCAN
    # ─────────────────────────────────────────────────────────────────────────

    def _scan_absent(self):
        if not self.session_active or not self.current_session_id:
            return
        settings = db.get_all_settings()
        grace    = int(settings.get("grace_period_minutes", 5))
        ivl      = int(settings.get("scan_interval_seconds", 30))
        thr      = int(settings.get("absent_threshold", 3))

        rows    = db.get_attendance_by_session(self.current_session_id)
        att_map = {a["student_id"]: a for a in rows}

        sess = None
        for s in db.get_sessions_by_date(date.today().isoformat()):
            if s["id"] == self.current_session_id:
                sess = s; break

        start_dt = end_dt = None
        if sess:
            start_dt = datetime.combine(date.today(),
                       datetime.strptime(sess["start_time"], "%H:%M").time())
            end_dt   = datetime.combine(date.today(),
                       datetime.strptime(sess["end_time"],   "%H:%M").time())
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            if (datetime.now() - start_dt).total_seconds() < grace * 60:
                return

        now       = datetime.now()
        last_check = self._last_absence_check or (now - timedelta(seconds=ivl))
        changed   = False

        for student in db.get_all_students():
            sid      = student["student_id"]
            last_seen = self._last_seen.get(sid)
            if last_seen and last_seen > last_check:
                self._missed_count[sid] = 0
                continue

            self._missed_count[sid] = self._missed_count.get(sid, 0) + 1
            att    = att_map.get(sid)
            status = att["status"] if att else None

            if status == "present":
                new_st, miss_count = db.increment_present_miss(sid, self.current_session_id)
                self._missed_count[sid] = miss_count
                if new_st == "half":
                    db.log_scan(sid, self.current_session_id, "half")
                    self.scan_log.setText(f"{sid} vắng đủ {thr} lần — chuyển 1/2 buổi")
                    self.scan_log.setStyleSheet(f"color: {C['yellow']}; font-size: 11px;")
                    changed = True
                continue
            if status == "half":
                continue
            if status == "excused":
                continue

            new_st = db.increment_absent_scan(sid, self.current_session_id)
            if new_st != status and new_st != "scanning":
                db.log_scan(sid, self.current_session_id, new_st)
            changed = True

        if changed:
            self._refresh_att_table()
        self._last_absence_check = now

    # ─────────────────────────────────────────────────────────────────────────
    # ATTENDANCE TABLE
    # ─────────────────────────────────────────────────────────────────────────

    def _refresh_att_table(self):
        if not self.current_session_id:
            return
        att_list = db.get_attendance_by_session(self.current_session_id)
        students = db.get_all_students()
        att_map  = {a["student_id"]: a for a in att_list}
        self.att_table.setRowCount(0)
        present = absent = half = 0

        for s in students:
            sid  = s["student_id"]
            att  = att_map.get(sid)
            stat = att["status"] if att else "absent"
            cin  = att["check_in_time"] if att else "—"

            if stat == "present": present += 1
            elif stat == "absent": absent  += 1
            elif stat == "half":   half    += 1

            row = self.att_table.rowCount()
            self.att_table.insertRow(row)
            self.att_table.setRowHeight(row, 30)

            name_item = QTableWidgetItem(s["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, sid)
            self.att_table.setItem(row, 0, name_item)

            stat_vi = {"present": "Có mặt", "absent": "Vắng", "half": "½", "excused": "Có phép", "scanning": "…"}
            stat_col = {
                "present": C['green'], "absent": C['red'],
                "half": C['yellow'], "excused": C['text_mid'], "scanning": C['accent'],
            }
            si = QTableWidgetItem(stat_vi.get(stat, stat))
            si.setData(Qt.ItemDataRole.UserRole, sid)
            si.setForeground(QColor(stat_col.get(stat, C['text_dim'])))
            si.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.att_table.setItem(row, 1, si)

            ti = QTableWidgetItem(cin or "—")
            ti.setData(Qt.ItemDataRole.UserRole, sid)
            ti.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ti.setForeground(QColor(C['text_dim']))
            self.att_table.setItem(row, 2, ti)

        self.mc_present_v.setText(str(present))
        self.mc_absent_v.setText(str(absent))
        self.mc_half_v.setText(str(half))
        self._update_lcd()

    def _open_attendance_detail(self, row, col):
        if not self.current_session_id:
            return
        if not self._ensure_admin():
            return
        item = self.att_table.item(row, col) or self.att_table.item(row, 0)
        sid = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not sid:
            return
        student = db.get_student(sid)
        if not student:
            return
        dlg = AttendanceDetailDialog(self, student, self.current_session_id)
        if dlg.exec():
            self._refresh_att_table()
            self._refresh_dashboard()

    # ─────────────────────────────────────────────────────────────────────────
    # STUDENTS
    # ─────────────────────────────────────────────────────────────────────────

    def _refresh_student_list(self, filter_text=""):
        all_sv  = db.get_all_students()
        total   = len(all_sv)
        encoded = sum(1 for s in all_sv if s.get("face_encoding"))
        self.sv_total.setText(f"Tổng: {total}")
        self.sv_face_count.setText(f"Đã nhận diện: {encoded}")

        shown = [
            s for s in all_sv
            if not filter_text
            or filter_text.lower() in s["name"].lower()
            or filter_text.lower() in s["student_id"].lower()
        ]
        self.sv_table.setRowCount(0)
        for s in shown:
            row = self.sv_table.rowCount()
            self.sv_table.insertRow(row)
            self.sv_table.setRowHeight(row, 72)

            # Avatar
            av = QLabel()
            av.setAlignment(Qt.AlignmentFlag.AlignCenter)
            av.setFixedSize(60, 60)
            pp = s.get("photo_path")
            if pp and os.path.exists(pp):
                pix = QPixmap(pp).scaled(56, 56,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation)
                av.setPixmap(pix)
                av.setStyleSheet(f"background-color: {C['surface2']}; border-radius: 5px;")
            else:
                av.setText(s["name"][:2].upper())
                av.setStyleSheet(f"""
                    font-size: 15px; font-weight: 800;
                    color: {C['accent']};
                    background-color: {C['surface2']};
                    border-radius: 22px;
                """)
            self.sv_table.setCellWidget(row, 0, av)

            id_it = QTableWidgetItem(s["student_id"])
            id_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_it.setForeground(QColor(C['accent']))
            self.sv_table.setItem(row, 1, id_it)
            self.sv_table.setItem(row, 2, QTableWidgetItem(s["name"]))

            has_enc = s.get("face_encoding") is not None
            enc_it  = QTableWidgetItem("✓ Đã đăng ký" if has_enc else "✗ Chưa có")
            enc_it.setForeground(QColor(C['green'] if has_enc else C['yellow']))
            enc_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sv_table.setItem(row, 3, enc_it)

            # Action buttons
            act_w  = QWidget()
            act_lay = QHBoxLayout(act_w)
            act_lay.setContentsMargins(10, 9, 10, 9)
            act_lay.setSpacing(10)
            act_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_e = QPushButton("Sửa")
            btn_e.setFixedSize(78, 38)
            btn_e.clicked.connect(lambda _, sv=s: self._edit_student(sv))

            btn_d = QPushButton("Xóa")
            apply_button_variant(btn_d, "danger")
            btn_d.setFixedSize(78, 38)
            btn_d.clicked.connect(lambda _, sid=s["student_id"]: self._delete_student(sid))

            act_lay.addWidget(btn_e)
            act_lay.addWidget(btn_d)
            self.sv_table.setCellWidget(row, 4, act_w)

        self.sv_table.resizeColumnToContents(1)

    def _filter_students(self, text):
        self._refresh_student_list(text)

    def _add_student(self):
        was_on = bool(self.cam_thread and self.cam_thread.running)
        if was_on:
            self._stop_cam_preview()
        try:
            dlg = StudentDialog(self)
            dlg.student_saved.connect(self._refresh_student_list)
            dlg.exec()
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi", str(exc))
        finally:
            if was_on:
                self._start_cam_preview()

    def _edit_student(self, sv):
        was_on = bool(self.cam_thread and self.cam_thread.running)
        if was_on:
            self._stop_cam_preview()
        try:
            dlg = StudentDialog(self, data=sv)
            dlg.student_saved.connect(self._refresh_student_list)
            dlg.exec()
        except Exception as exc:
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi", str(exc))
        finally:
            if was_on:
                self._start_cam_preview()

    def _delete_student(self, sid):
        r = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Xóa sinh viên {sid}?\nHành động không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r == QMessageBox.StandardButton.Yes:
            db.delete_student(sid)
            fm.load_recognizer()
            self._refresh_student_list()

    # ─────────────────────────────────────────────────────────────────────────
    # REPORTS
    # ─────────────────────────────────────────────────────────────────────────

    def _populate_export_dates(self):
        self.export_date.clear()
        today = date.today().isoformat()
        try:
            conn = db.get_connection()
            rows = conn.execute(
                "SELECT DISTINCT session_date FROM sessions ORDER BY session_date DESC LIMIT 30"
            ).fetchall()
            conn.close()
            if not any(r["session_date"] == today for r in rows):
                self.export_date.addItem(f"Hôm nay ({today})", today)
            for r in rows:
                d = r["session_date"]
                self.export_date.addItem(d, d)
        except Exception:
            self.export_date.addItem(f"Hôm nay ({today})", today)
        if self.export_date.count() == 0:
            self.export_date.addItem(f"Hôm nay ({today})", today)

    def _selected_export_date(self):
        txt = self.export_date.currentText().strip()
        m = re.search(r"\d{4}-\d{2}-\d{2}", txt)
        if m:
            return m.group(0)
        data = self.export_date.currentData()
        return data or txt

    def _preview_attendance(self):
        tdate = self._selected_export_date()
        if not tdate:
            return
        s       = db.get_all_settings()
        tp      = int(s.get("total_periods", 3))
        sessions = db.get_sessions_by_date(tdate)
        sess_map = {se["period"]: se for se in sessions}
        students = db.get_all_students()

        headers = ["Mã SV", "Họ tên"] + [f"Tiết {p}" for p in range(1, tp + 1)]
        self.prev_table.setColumnCount(len(headers))
        self.prev_table.setHorizontalHeaderLabels(headers)
        self.prev_table.setRowCount(0)
        for sv in students:
            row = self.prev_table.rowCount()
            self.prev_table.insertRow(row)
            sid_item = QTableWidgetItem(sv["student_id"])
            sid_item.setData(Qt.ItemDataRole.UserRole, {"sid": sv["student_id"], "date": tdate, "period": None})
            name_item = QTableWidgetItem(sv["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, {"sid": sv["student_id"], "date": tdate, "period": None})
            self.prev_table.setItem(row, 0, sid_item)
            self.prev_table.setItem(row, 1, name_item)
            for p in range(1, tp + 1):
                sess = sess_map.get(p)
                if sess:
                    att = next(
                        (a for a in db.get_attendance_by_session(sess["id"])
                         if a["student_id"] == sv["student_id"]),
                        None
                    )
                    stat = att["status"] if att else "absent"
                else:
                    stat = "—"
                vi = {"present": "Có mặt", "absent": "Vắng", "half": "½", "excused": "Có phép", "—": "-"}
                it = QTableWidgetItem(vi.get(stat, stat))
                it.setData(Qt.ItemDataRole.UserRole, {"sid": sv["student_id"], "date": tdate, "period": p})
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                col = {"present": C['green'], "absent": C['red'], "half": C['yellow'], "excused": C['text_mid']}.get(stat)
                if col:
                    it.setForeground(QColor(col))
                self.prev_table.setItem(row, p + 1, it)

    def _open_report_attendance_detail(self, row, col):
        item = self.prev_table.item(row, col)
        meta = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not meta:
            return
        sid = meta.get("sid")
        period = meta.get("period")
        tdate = meta.get("date") or self._selected_export_date()
        if not sid:
            return
        if period is None:
            QMessageBox.information(self, "Chọn tiết", "Double-click vào ô Tiết để sửa điểm danh.")
            return
        if not self._ensure_admin():
            return
        student = db.get_student(sid)
        if not student:
            return
        sess = db.get_or_create_session(tdate, period)
        dlg = AttendanceDetailDialog(self, student, sess["id"])
        if dlg.exec():
            self._preview_attendance()
            self._refresh_dashboard()

    def _export_day(self, fmt):
        tdate = self._selected_export_date()
        if not tdate:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ngày!")
            return
        if fmt == "pdf":
            fp, msg = em.export_by_date_pdf(tdate)
        else:
            fp, msg = em.export_by_date(tdate)
        if fp:
            r = QMessageBox.information(
                self, "Xuất thành công",
                f"{msg}\n\nFile: {fp}\n\nMở file không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if r == QMessageBox.StandardButton.Yes:
                self._open_file(fp)
        else:
            QMessageBox.warning(self, "Lỗi xuất", msg)

    def _export_month(self, fmt):
        m = self.month_combo.currentData()
        y = self.year_spin.value()
        if fmt == "pdf":
            fp, msg = em.export_monthly_report_pdf(y, m)
        else:
            fp, msg = em.export_monthly_report(y, m)
        if fp:
            QMessageBox.information(self, "Xuất thành công", f"{msg}\n\nFile: {fp}")
        else:
            QMessageBox.warning(self, "Lỗi xuất", msg)

    def _open_file(self, fp):
        if sys.platform.startswith("win"):
            os.startfile(fp)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", fp])
        else:
            subprocess.Popen(["xdg-open", fp])

    # ─────────────────────────────────────────────────────────────────────────
    # SETTINGS
    # ─────────────────────────────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        self._sync_period_combo()
        self._sync_time_state()
        self._refresh_settings_display()

    def _refresh_settings_display(self):
        s   = db.get_all_settings()
        tp  = int(s.get("total_periods", 3))
        lines = [
            "══ CÀI ĐẶT ĐANG DÙNG ═══════════════════",
            "",
            f"  Lớp học          : {s.get('class_name', '')}",
            f"  Số tiết / ngày   : {tp}",
            f"  Chu kỳ quét vắng : {s.get('scan_interval_seconds', '30')} giây",
            f"  Ngưỡng đánh vắng : {s.get('absent_threshold', '3')} lần",
            f"  Ân hạn vào lớp   : {s.get('grace_period_minutes', '5')} phút",
            "",
            "══ THỜI KHÓA BIỂU ═══════════════════════",
        ]
        for p in range(1, tp + 1):
            ps = s.get(f"period_{p}_start", "--:--")
            pe = s.get(f"period_{p}_end",   "--:--")
            lines.append(f"  Tiết {p}           : {ps} — {pe}")
        if tp >= 2:
            lines.append(f"  Nghỉ giải lao    : {s.get('break_start','--:--')} — {s.get('break_end','--:--')}")
        if hasattr(self, "settings_display"):
            self.settings_display.setText("\n".join(lines))

    # ─────────────────────────────────────────────────────────────────────────
    # LCD STATUS
    # ─────────────────────────────────────────────────────────────────────────

    def _start_lcd_timer(self):
        t = QTimer(self)
        t.timeout.connect(self._update_lcd)
        t.start(2000)
        self._update_lcd()

    def _start_lcd_bridge(self):
        t = QTimer(self)
        t.timeout.connect(self._poll_lcd_cmd)
        t.start(500)
        self._last_lcd_cmd_id = None

    def _write_lcd_state(self):
        try:
            st = {
                "running": True,
                "session_active": bool(self.session_active),
                "session_id":     self.current_session_id,
                "period":         self.period_combo.currentData() if hasattr(self, "period_combo") else None,
                "updated_at":     datetime.now().timestamp(),
            }
            tmp = LCD_STATE_PATH.with_suffix(".tmp")
            tmp.write_text(json.dumps(st), encoding="utf-8")
            tmp.replace(LCD_STATE_PATH)
        except Exception:
            pass

    def _poll_lcd_cmd(self):
        if not LCD_COMMAND_PATH.exists():
            self._write_lcd_state()
            return
        try:
            data = json.loads(LCD_COMMAND_PATH.read_text(encoding="utf-8"))
        except Exception:
            return
        cid = data.get("id")
        if cid == self._last_lcd_cmd_id:
            self._write_lcd_state()
            return
        self._last_lcd_cmd_id = cid
        action = data.get("action")
        if action == "start_session" and not self.session_active:
            self._start_session()
        elif action == "stop_session" and self.session_active:
            self._end_session()
        try:
            LCD_COMMAND_PATH.unlink()
        except Exception:
            pass
        self._write_lcd_state()

    def _update_lcd(self):
        if not self._lcd:
            return
        try:
            settings = db.get_all_settings()
            students = db.get_all_students()
            total    = len(students)
            present = absent = half = excused = 0
            period  = self.period_combo.currentData() if hasattr(self, "period_combo") else None
            status  = "Sẵn sàng"
            if self.session_active and self.current_session_id:
                status = "Đang điểm danh"
                for a in db.get_attendance_by_session(self.current_session_id):
                    if a["status"] == "present":  present += 1
                    elif a["status"] == "half":   half    += 1
                    elif a["status"] == "absent":  absent  += 1
                    elif a["status"] == "excused": excused += 1
                absent = max(absent, total - present - half - excused)
            else:
                st = self._get_time_state()
                if   st["type"] == "period": status = f"Chờ tiết {st['period']}"; period = st["period"]
                elif st["type"] == "break":  status = "Đang ra chơi"
                else:                        status = "Ngoài giờ học"
            last = self._last_face_name if datetime.now().timestamp() - self._last_face_ts < 12 else ""
            self._lcd.update({
                "class_name": settings.get("class_name", "Lop hoc"),
                "status": status, "period": period,
                "time":  datetime.now().strftime("%H:%M:%S"),
                "date":  datetime.now().strftime("%d/%m/%Y"),
                "total": total, "present": present, "absent": absent, "half": half,
                "last_seen": last,
            })
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # CLOSE
    # ─────────────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self.cam_thread:
            self.cam_thread.stop()
        if self._lcd:
            try:
                self._lcd.update({"status": "App da tat", "time": datetime.now().strftime("%H:%M:%S")})
            except Exception:
                pass
        event.accept()


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ClassRoom AI")
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor(C['bg']))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(C['text']))
    pal.setColor(QPalette.ColorRole.Base,            QColor(C['surface']))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(C['surface2']))
    pal.setColor(QPalette.ColorRole.Text,            QColor(C['text']))
    pal.setColor(QPalette.ColorRole.Button,          QColor(C['surface2']))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor(C['text']))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(C['accent']))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(C['bg']))
    app.setPalette(pal)
    app.setStyleSheet(QSS)

    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
