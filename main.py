import sys
import os
import cv2
import json
import numpy as np
import subprocess
import platform
from datetime import datetime, date, time, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QDialog, QLineEdit,
    QFormLayout, QTabWidget, QComboBox, QTimeEdit, QSpinBox,
    QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QStackedWidget, QSizePolicy, QGridLayout,
    QProgressBar, QTextEdit, QCheckBox, QGroupBox, QSplitter,
    QStatusBar, QToolTip
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QTime, QSize, QPropertyAnimation,
    QEasingCurve, QRect, QDate, QDateTime
)
from PyQt6.QtGui import (
    QImage, QPixmap, QFont, QColor, QPalette, QIcon,
    QPainter, QLinearGradient, QBrush, QPen, QCursor,
    QFontDatabase
)
import database as db
import face_module as fm
import export_module as em

try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

# ─── Constants ────────────────────────────────────────────────────────────────
APP_VERSION = "1.0.0"

DARK = {
    "bg":          "#0F1923",
    "surface":     "#162030",
    "surface2":    "#1E2D3D",
    "surface3":    "#243447",
    "accent":      "#00D4FF",
    "accent2":     "#0099CC",
    "green":       "#00E676",
    "yellow":      "#FFD600",
    "red":         "#FF5252",
    "text":        "#E8F4FD",
    "text_dim":    "#7FA8C9",
    "border":      "#2A3F55",
    "card":        "#172535",
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {DARK['bg']};
    color: {DARK['text']};
}}
QWidget {{
    background-color: transparent;
    color: {DARK['text']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QFrame#card {{
    background-color: {DARK['card']};
    border: 1px solid {DARK['border']};
    border-radius: 12px;
}}
QFrame#sidebar {{
    background-color: {DARK['surface']};
    border-right: 1px solid {DARK['border']};
}}
QPushButton {{
    background-color: {DARK['surface2']};
    color: {DARK['text']};
    border: 1px solid {DARK['border']};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {DARK['surface3']};
    border-color: {DARK['accent']};
    color: {DARK['accent']};
}}
QPushButton:pressed {{
    background-color: {DARK['accent2']};
}}
QPushButton#primary {{
    background-color: {DARK['accent']};
    color: {DARK['bg']};
    border: none;
    font-weight: 700;
}}
QPushButton#primary:hover {{
    background-color: #33DDFF;
}}
QPushButton#danger {{
    background-color: #3D1515;
    color: {DARK['red']};
    border: 1px solid {DARK['red']};
}}
QPushButton#danger:hover {{
    background-color: {DARK['red']};
    color: white;
}}
QPushButton#success {{
    background-color: #0A3020;
    color: {DARK['green']};
    border: 1px solid {DARK['green']};
}}
QPushButton#success:hover {{
    background-color: {DARK['green']};
    color: {DARK['bg']};
}}
QPushButton#sidebar_btn {{
    background-color: transparent;
    color: {DARK['text_dim']};
    border: none;
    border-radius: 10px;
    text-align: left;
    padding: 12px 16px;
    font-size: 13px;
}}
QPushButton#sidebar_btn:hover {{
    background-color: {DARK['surface2']};
    color: {DARK['text']};
}}
QPushButton#sidebar_btn_active {{
    background-color: {DARK['surface3']};
    color: {DARK['accent']};
    border: none;
    border-left: 3px solid {DARK['accent']};
    border-radius: 0px;
    text-align: left;
    padding: 12px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QLineEdit, QTextEdit {{
    background-color: {DARK['surface2']};
    border: 1px solid {DARK['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {DARK['text']};
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {DARK['accent']};
}}
QComboBox {{
    background-color: {DARK['surface2']};
    border: 1px solid {DARK['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {DARK['text']};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {DARK['surface2']};
    border: 1px solid {DARK['border']};
    color: {DARK['text']};
    selection-background-color: {DARK['surface3']};
}}
QSpinBox, QTimeEdit {{
    background-color: {DARK['surface2']};
    border: 1px solid {DARK['border']};
    border-radius: 8px;
    padding: 4px 10px;
    color: {DARK['text']};
    min-height: 30px;
    min-width: 130px;
}}
QSpinBox::up-button, QSpinBox::down-button,
QTimeEdit::up-button, QTimeEdit::down-button {{
    width: 18px;
    background-color: {DARK['surface3']};
    border-left: 1px solid {DARK['border']};
}}
QSpinBox::up-arrow, QSpinBox::down-arrow,
QTimeEdit::up-arrow, QTimeEdit::down-arrow {{
    width: 8px;
    height: 8px;
}}
QTableWidget {{
    background-color: {DARK['surface']};
    border: 1px solid {DARK['border']};
    border-radius: 8px;
    gridline-color: {DARK['border']};
    color: {DARK['text']};
}}
QTableWidget::item {{
    padding: 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {DARK['surface3']};
    color: {DARK['accent']};
}}
QHeaderView::section {{
    background-color: {DARK['surface2']};
    color: {DARK['text_dim']};
    border: none;
    border-bottom: 1px solid {DARK['border']};
    padding: 10px 8px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}}
QScrollBar:vertical {{
    background: {DARK['surface']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {DARK['border']};
    border-radius: 3px;
    min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{
    background: {DARK['accent']};
}}
QScrollBar:horizontal {{
    background: {DARK['surface']};
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {DARK['border']};
    border-radius: 3px;
}}
QTabWidget::pane {{
    border: 1px solid {DARK['border']};
    border-radius: 8px;
    background-color: {DARK['surface']};
}}
QTabBar::tab {{
    background-color: {DARK['surface2']};
    color: {DARK['text_dim']};
    padding: 10px 20px;
    border: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {DARK['surface3']};
    color: {DARK['accent']};
    font-weight: 600;
}}
QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    color: {DARK['text']};
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {DARK['text_dim']};
}}
QLabel#stat_value {{
    font-size: 28px;
    font-weight: 800;
    color: {DARK['accent']};
}}
QLabel#stat_label {{
    font-size: 11px;
    color: {DARK['text_dim']};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QStatusBar {{
    background-color: {DARK['surface']};
    color: {DARK['text_dim']};
    border-top: 1px solid {DARK['border']};
}}
QGroupBox {{
    border: 1px solid {DARK['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
    color: {DARK['text_dim']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {DARK['accent']};
}}
"""

# ─── Camera Thread ────────────────────────────────────────────────────────────

class CameraThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    face_detected = pyqtSignal(str, str, float)  # student_id, name, confidence
    status_update = pyqtSignal(str)

    def __init__(self, mode="monitor"):
        super().__init__()
        self.mode = mode  # "monitor" | "capture"
        self.running = False
        self.current_session_id = None
        self._scan_cooldown = {}
        self._last_face_boxes = []
        self._last_face_ts = 0
        self._last_process_ts = 0
        self._process_interval = 0.18 if mode == "monitor" else 0.28
        self._display_interval = 0.04
        self._last_display_ts = 0
        self._detect_scale = 0.6

    def set_session(self, session_id):
        self.current_session_id = session_id

    def _open_camera(self):
        width = 480 if self.mode == "monitor" else 640
        height = 360 if self.mode == "monitor" else 480

        if platform.system() == "Linux" and Picamera2 is not None:
            try:
                picam = Picamera2()
                config = picam.create_preview_configuration(
                    main={"format": "RGB888", "size": (width, height)}
                )
                picam.configure(config)
                picam.start()
                return "picamera2", picam
            except Exception as exc:
                print(f"Picamera2 loi: {exc}. Dang thu USB camera...")

        backend = cv2.CAP_V4L2 if platform.system() == "Linux" else cv2.CAP_DSHOW
        cap = cv2.VideoCapture(0, backend)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            cap.release()
            return None, None
        return "opencv", cap

    def _read_camera_frame(self, camera_type, camera):
        if camera_type == "picamera2":
            rgb = camera.capture_array()
            return True, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        return camera.read()

    def _close_camera(self, camera_type, camera):
        if not camera:
            return
        if camera_type == "picamera2":
            camera.stop()
            camera.close()
        else:
            camera.release()

    def run(self):
        self.running = True
        camera_type, camera = self._open_camera()

        if camera is None:
            self.status_update.emit("⚠ Không thể mở camera")
            self.running = False
            return

        while self.running:
            ret, frame = self._read_camera_frame(camera_type, camera)
            if not ret:
                self.msleep(20)
                continue
            frame = cv2.flip(frame, 1)

            now_ts = datetime.now().timestamp()
            if now_ts - self._last_process_ts >= self._process_interval:
                self._last_process_ts = now_ts
                small = cv2.resize(frame, None, fx=self._detect_scale, fy=self._detect_scale)
                gray_small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                faces_small = fm.detect_faces(gray_small)
                self._last_face_boxes = []
                self._last_face_ts = now_ts

                for (sx, sy, sw, sh) in faces_small:
                    x = int(sx / self._detect_scale)
                    y = int(sy / self._detect_scale)
                    w = int(sw / self._detect_scale)
                    h = int(sh / self._detect_scale)

                    if self.mode == "capture":
                        self._last_face_boxes.append((x, y, w, h, None, 0, "scanning"))
                        continue

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    enc = fm.extract_encoding_from_frame(gray, x, y, w, h)
                    sid, name, conf = fm.recognize_face(enc)

                    if sid:
                        last_scan = self._scan_cooldown.get(sid, 0)
                        if now_ts - last_scan > self._scan_cooldown.get(f"{sid}_interval", 5):
                            self._scan_cooldown[sid] = now_ts
                            self.face_detected.emit(sid, name, conf)
                            if self.current_session_id:
                                db.mark_present(sid, self.current_session_id)
                                db.log_scan(sid, self.current_session_id, "present")
                        self._last_face_boxes.append((x, y, w, h, name, conf, "present"))
                    else:
                        self._last_face_boxes.append((x, y, w, h, "Unknown", conf, "unknown"))

            if now_ts - self._last_face_ts <= 1.2:
                for x, y, w, h, name, conf, status in self._last_face_boxes:
                    fm.draw_face_box(frame, x, y, w, h, name, conf, status)

            if now_ts - self._last_display_ts >= self._display_interval:
                self._last_display_ts = now_ts
                self.frame_ready.emit(frame)
            self.msleep(10)

        self._close_camera(camera_type, camera)

    def stop(self):
        self.running = False
        self.wait(2000)


# ─── Dialogs ──────────────────────────────────────────────────────────────────

class AddStudentDialog(QDialog):
    student_added = pyqtSignal()

    def __init__(self, parent=None, student_data=None):
        super().__init__(parent)
        self.student_data = student_data
        self.captured_frame = None
        self.pose_frames = {}
        self.current_pose = "front"
        self.latest_frame = None
        self.preview_frozen = False
        self.camera_thread = None
        self.setWindowTitle("Thêm Sinh Viên" if not student_data else "Chỉnh Sửa Sinh Viên")
        self.setMinimumSize(760, 620)
        self.setStyleSheet(STYLESHEET + f"QDialog {{ background-color: {DARK['bg']}; }}")
        self._setup_ui()
        if student_data:
            self._fill_data()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Left: Camera
        left = QVBoxLayout()
        cam_label = QLabel("Anh khuon mat")
        cam_label.setStyleSheet(f"color: {DARK['accent']}; font-size: 14px; font-weight: 700;")
        left.addWidget(cam_label)

        self.camera_view = QLabel()
        self.camera_view.setFixedSize(280, 210)
        self.camera_view.setStyleSheet(f"""
            background-color: {DARK['surface']};
            border: 2px dashed {DARK['border']};
            border-radius: 10px;
        """)
        self.camera_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_view.setText("Chua co anh")
        left.addWidget(self.camera_view)

        self.pose_combo = QComboBox()
        self.pose_combo.addItem("Chinh dien", "front")
        self.pose_combo.addItem("Nghieng trai", "left")
        self.pose_combo.addItem("Nghieng phai", "right")
        self.pose_combo.currentIndexChanged.connect(self._change_pose)
        left.addWidget(self.pose_combo)

        btn_cam = QPushButton("Bat Camera")
        btn_cam.setObjectName("primary")
        btn_cam.clicked.connect(self._toggle_camera)
        self.btn_cam = btn_cam
        left.addWidget(btn_cam)

        btn_capture = QPushButton("Chup Anh")
        btn_capture.clicked.connect(self._capture)
        self.btn_capture = btn_capture
        btn_capture.setEnabled(False)
        left.addWidget(btn_capture)

        btn_upload = QPushButton("Tai Anh Len")
        btn_upload.clicked.connect(self._upload_photo)
        left.addWidget(btn_upload)

        self.face_status = QLabel("Can 3 anh: chinh dien, trai, phai")
        self.face_status.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 11px;")
        self.face_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left.addWidget(self.face_status)
        left.addStretch()
        layout.addLayout(left)

        # Right: Form
        right = QVBoxLayout()
        form_title = QLabel("Thong Tin Sinh Vien")
        form_title.setStyleSheet(f"color: {DARK['accent']}; font-size: 14px; font-weight: 700;")
        right.addWidget(form_title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("Ví dụ: SV001, 21IT001...")
        form.addRow("Ma Sinh Vien *", self.id_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Họ và tên đầy đủ")
        form.addRow("Ho va Ten *", self.name_edit)

        right.addLayout(form)
        right.addSpacing(20)

        # Note
        note = QLabel("Yeu cau anh:\n- 1 anh chinh dien\n- 1 anh nghieng trai\n- 1 anh nghieng phai\n- Du sang, khong deo khau trang")
        note.setStyleSheet(f"""
            background-color: {DARK['surface2']};
            border: 1px solid {DARK['border']};
            border-radius: 8px;
            color: {DARK['text_dim']};
            padding: 12px;
            font-size: 12px;
        """)
        right.addWidget(note)
        right.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Huy")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Luu Sinh Vien")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        right.addLayout(btn_layout)
        layout.addLayout(right)

    def _fill_data(self):
        self.id_edit.setText(self.student_data["student_id"])
        self.id_edit.setEnabled(False)
        self.name_edit.setText(self.student_data["name"])
        if self.student_data.get("photo_path") and os.path.exists(self.student_data["photo_path"]):
            img = cv2.imread(self.student_data["photo_path"])
            self._show_cv_frame(img)
            self.pose_frames["front"] = img

    def _change_pose(self):
        self.current_pose = self.pose_combo.currentData()
        self.preview_frozen = False
        self.btn_capture.setText("Chup Anh")
        if self.current_pose in self.pose_frames:
            self.captured_frame = self.pose_frames[self.current_pose]
            self._show_cv_frame(self.captured_frame)
        self._update_pose_status()

    def _update_pose_status(self):
        labels = {"front": "chinh dien", "left": "trai", "right": "phai"}
        done = [labels[k] for k in ("front", "left", "right") if k in self.pose_frames]
        missing = [labels[k] for k in ("front", "left", "right") if k not in self.pose_frames]
        if missing:
            self.face_status.setText(f"Da co: {', '.join(done) if done else 'chua co'} | Thieu: {', '.join(missing)}")
            self.face_status.setStyleSheet(f"color: {DARK['yellow']}; font-size: 11px;")
        else:
            self.face_status.setText("Da du 3 anh khuon mat")
            self.face_status.setStyleSheet(f"color: {DARK['green']}; font-size: 11px;")

    def _toggle_camera(self):
        if self.camera_thread and self.camera_thread.running:
            self.camera_thread.stop()
            self.camera_thread = None
            self.btn_cam.setText("Bat Camera")
            self.btn_capture.setEnabled(False)
            self.preview_frozen = False
            self.btn_capture.setText("Chup Anh")
        else:
            self.camera_thread = CameraThread(mode="capture")
            self.camera_thread.frame_ready.connect(self._update_preview)
            self.camera_thread.status_update.connect(self._on_capture_camera_status)
            self.camera_thread.start()
            self.btn_cam.setText("Tat Camera")
            self.btn_capture.setEnabled(True)

    def _update_preview(self, frame):
        if self.preview_frozen:
            return
        self.latest_frame = frame.copy()
        self._show_cv_frame(frame)

    def _show_cv_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            280, 210, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.camera_view.setPixmap(pix)

    def _capture(self):
        if self.preview_frozen:
            self.preview_frozen = False
            self.btn_capture.setText("Chup Anh")
            self.face_status.setText("Dang xem camera")
            self.face_status.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 11px;")
            return

        if self.latest_frame is None:
            QMessageBox.warning(
                self,
                "Chưa có khung hình",
                "Camera chưa sẵn sàng. Vui lòng bật camera và chờ hình ảnh hiện lên rồi chụp lại."
            )
            return

        frame = self.latest_frame.copy()
        self.captured_frame = frame
        self.pose_frames[self.current_pose] = frame
        self.preview_frozen = True
        self.btn_capture.setText("Chup Lai")
        self._show_cv_frame(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = fm.detect_faces(gray)
        if len(faces) > 0:
            self._update_pose_status()
        else:
            self.pose_frames.pop(self.current_pose, None)
            self.face_status.setText("Khong phat hien khuon mat")
            self.face_status.setStyleSheet(f"color: {DARK['yellow']}; font-size: 11px;")

    def _upload_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh sinh viên", "",
            "Ảnh (*.jpg *.jpeg *.png *.bmp)"
        )
        if path:
            img = cv2.imread(path)
            if img is not None:
                self.captured_frame = img
                self.pose_frames[self.current_pose] = img
                self._show_cv_frame(img)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = fm.detect_faces(gray)
                if len(faces) > 0:
                    self._update_pose_status()
                else:
                    self.pose_frames.pop(self.current_pose, None)
                    self.face_status.setText("Khong phat hien khuon mat")
                    self.face_status.setStyleSheet(f"color: {DARK['yellow']}; font-size: 11px;")

    def _on_capture_camera_status(self, msg):
        self.face_status.setText(msg)
        self.face_status.setStyleSheet(f"color: {DARK['red']}; font-size: 11px;")
        self.btn_cam.setText("Bat Camera")
        self.btn_capture.setEnabled(False)
        self.camera_thread = None

    def _save(self):
        sid = self.id_edit.text().strip()
        name = self.name_edit.text().strip()

        if not sid or not name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng điền đầy đủ Mã SV và Họ tên!")
            return

        photo_path = None
        face_encoding = None

        if not self.student_data and db.get_student(sid):
            QMessageBox.warning(self, "Trung ma", "Ma sinh vien da ton tai, khong the them lai.")
            return

        frames_to_save = [self.pose_frames[k] for k in ("front", "left", "right") if k in self.pose_frames]
        if not self.student_data and len(frames_to_save) < 3:
            QMessageBox.warning(self, "Thieu anh", "Vui long chup/tai du 3 anh: chinh dien, nghieng trai, nghieng phai.")
            return

        encodings = []
        for pose, frame in self.pose_frames.items():
            saved = fm.save_student_photo(sid, frame, pose)
            if pose == "front":
                photo_path = saved
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = fm.detect_faces(gray)
            if len(faces) > 0:
                x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
                encodings.append(fm.extract_encoding_from_frame(gray, x, y, w, h))

        if encodings:
            face_encoding = np.mean(np.array(encodings, dtype=np.float32), axis=0).tolist()
        elif not self.student_data:
            QMessageBox.warning(self, "Loi anh", "Khong trich xuat duoc khuon mat tu anh.")
            return

        if self.student_data:
            db.update_student(
                sid,
                name=name,
                photo_path=photo_path,
                face_encoding=face_encoding,
                keep_encoding=self.captured_frame is None
            )
            ok, msg = True, "Cập nhật thành công"
        else:
            ok, msg = db.add_student(sid, name, photo_path, face_encoding)

        if ok:
            if self.camera_thread:
                self.camera_thread.stop()
            fm.load_recognizer()
            self.student_added.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        super().closeEvent(event)

    def reject(self):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        super().reject()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙ Cài Đặt Hệ Thống")
        self.setMinimumSize(720, 680)
        self.setStyleSheet(STYLESHEET + f"QDialog {{ background-color: {DARK['bg']}; }}")
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("⚙  Cài Đặt Hệ Thống")
        title.setObjectName("title")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setMinimumHeight(500)

        # ── Tab: Thời gian ────────────────────────────────────────────────────
        time_widget = QWidget()
        time_widget.setStyleSheet(f"background-color: {DARK['surface']};")
        tf = QFormLayout(time_widget)
        tf.setSpacing(14)
        tf.setContentsMargins(16, 16, 16, 16)

        self.class_name_edit = QLineEdit()
        self.class_name_edit.setMinimumHeight(34)
        tf.addRow("Tên lớp học:", self.class_name_edit)

        self.total_periods = QSpinBox()
        self.total_periods.setRange(1, 6)
        self.total_periods.setValue(3)
        self.total_periods.setMinimumHeight(34)
        self.total_periods.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.total_periods.valueChanged.connect(self._sync_period_fields)
        tf.addRow("Số tiết/ngày:", self.total_periods)

        tf.addRow(QLabel(""))
        self.p1_title = QLabel("── Tiết 1 ──────────────────────")
        tf.addRow(self.p1_title)

        self.p1_start = QTimeEdit()
        self.p1_end = QTimeEdit()
        self.p1_start_lbl = QLabel("Giờ bắt đầu Tiết 1:")
        self.p1_end_lbl = QLabel("Giờ kết thúc Tiết 1:")
        tf.addRow(self.p1_start_lbl, self.p1_start)
        tf.addRow(self.p1_end_lbl, self.p1_end)

        self.break_title = QLabel("── Nghỉ giải lao ─────────────")
        tf.addRow(self.break_title)
        self.break_start = QTimeEdit()
        self.break_end = QTimeEdit()
        self.break_start_lbl = QLabel("Giờ bắt đầu nghỉ:")
        self.break_end_lbl = QLabel("Giờ kết thúc nghỉ:")
        tf.addRow(self.break_start_lbl, self.break_start)
        tf.addRow(self.break_end_lbl, self.break_end)

        self.p2_title = QLabel("── Tiết 2 ──────────────────────")
        tf.addRow(self.p2_title)
        self.p2_start = QTimeEdit()
        self.p2_end = QTimeEdit()
        self.p2_start_lbl = QLabel("Giờ bắt đầu Tiết 2:")
        self.p2_end_lbl = QLabel("Giờ kết thúc Tiết 2:")
        tf.addRow(self.p2_start_lbl, self.p2_start)
        tf.addRow(self.p2_end_lbl, self.p2_end)

        self.p3_title = QLabel("── Tiết 3 ──────────────────────")
        tf.addRow(self.p3_title)
        self.p3_start = QTimeEdit()
        self.p3_end = QTimeEdit()
        self.p3_start_lbl = QLabel("Giờ bắt đầu Tiết 3:")
        self.p3_end_lbl = QLabel("Giờ kết thúc Tiết 3:")
        tf.addRow(self.p3_start_lbl, self.p3_start)
        tf.addRow(self.p3_end_lbl, self.p3_end)

        self.p4_title = QLabel("── Tiết 4 ──────────────────────")
        tf.addRow(self.p4_title)
        self.p4_start = QTimeEdit()
        self.p4_end = QTimeEdit()
        self.p4_start_lbl = QLabel("Giờ bắt đầu Tiết 4:")
        self.p4_end_lbl = QLabel("Giờ kết thúc Tiết 4:")
        tf.addRow(self.p4_start_lbl, self.p4_start)
        tf.addRow(self.p4_end_lbl, self.p4_end)

        self.p5_title = QLabel("── Tiết 5 ──────────────────────")
        tf.addRow(self.p5_title)
        self.p5_start = QTimeEdit()
        self.p5_end = QTimeEdit()
        self.p5_start_lbl = QLabel("Giờ bắt đầu Tiết 5:")
        self.p5_end_lbl = QLabel("Giờ kết thúc Tiết 5:")
        tf.addRow(self.p5_start_lbl, self.p5_start)
        tf.addRow(self.p5_end_lbl, self.p5_end)

        self.p6_title = QLabel("── Tiết 6 ──────────────────────")
        tf.addRow(self.p6_title)
        self.p6_start = QTimeEdit()
        self.p6_end = QTimeEdit()
        self.p6_start_lbl = QLabel("Giờ bắt đầu Tiết 6:")
        self.p6_end_lbl = QLabel("Giờ kết thúc Tiết 6:")
        tf.addRow(self.p6_start_lbl, self.p6_start)
        tf.addRow(self.p6_end_lbl, self.p6_end)

        self.period_widgets = {
            1: (self.p1_title, self.p1_start_lbl, self.p1_start, self.p1_end_lbl, self.p1_end),
            2: (self.p2_title, self.p2_start_lbl, self.p2_start, self.p2_end_lbl, self.p2_end),
            3: (self.p3_title, self.p3_start_lbl, self.p3_start, self.p3_end_lbl, self.p3_end),
            4: (self.p4_title, self.p4_start_lbl, self.p4_start, self.p4_end_lbl, self.p4_end),
            5: (self.p5_title, self.p5_start_lbl, self.p5_start, self.p5_end_lbl, self.p5_end),
            6: (self.p6_title, self.p6_start_lbl, self.p6_start, self.p6_end_lbl, self.p6_end),
        }

        for time_edit in (
            self.p1_start, self.p1_end, self.break_start, self.break_end,
            self.p2_start, self.p2_end, self.p3_start, self.p3_end,
            self.p4_start, self.p4_end, self.p5_start, self.p5_end,
            self.p6_start, self.p6_end
        ):
            time_edit.setDisplayFormat("HH:mm")
            time_edit.setFixedHeight(36)
            time_edit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)

        time_scroll = QScrollArea()
        time_scroll.setWidgetResizable(True)
        time_scroll.setWidget(time_widget)
        time_scroll.setStyleSheet(f"background-color: {DARK['surface']}; border: none;")
        tabs.addTab(time_scroll, "🕐 Thời Gian")

        # ── Tab: Điểm danh ────────────────────────────────────────────────────
        att_widget = QWidget()
        att_widget.setStyleSheet(f"background-color: {DARK['surface']};")
        af = QFormLayout(att_widget)
        af.setSpacing(14)
        af.setContentsMargins(16, 16, 16, 16)

        self.scan_interval = QSpinBox()
        self.scan_interval.setRange(5, 300)
        self.scan_interval.setSuffix(" giây")
        self.scan_interval.setMinimumHeight(34)
        self.scan_interval.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        af.addRow("Chu kỳ quét:", self.scan_interval)

        self.absent_threshold = QSpinBox()
        self.absent_threshold.setRange(1, 10)
        self.absent_threshold.setSuffix(" lần")
        self.absent_threshold.setMinimumHeight(34)
        self.absent_threshold.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        af.addRow("Ngưỡng đánh vắng:", self.absent_threshold)

        self.grace_period = QSpinBox()
        self.grace_period.setRange(0, 30)
        self.grace_period.setSuffix(" phút")
        self.grace_period.setMinimumHeight(34)
        self.grace_period.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        af.addRow("Thời gian ân hạn vào lớp:", self.grace_period)

        note = QLabel(
            "📌 Ngưỡng đánh vắng: số lần quét không thấy\n"
            "mặt liên tiếp sẽ đánh là vắng mặt.\n\n"
            "📌 Thời gian ân hạn: sinh viên đến trễ trong\n"
            "khoảng này vẫn được tính là có mặt."
        )
        note.setStyleSheet(f"""
            background-color: {DARK['surface2']};
            border: 1px solid {DARK['border']};
            border-radius: 8px;
            color: {DARK['text_dim']};
            padding: 12px;
            font-size: 12px;
        """)
        af.addRow(note)
        tabs.addTab(att_widget, "📋 Điểm Danh")

        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("💾  Lưu Cài Đặt")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _load_settings(self):
        s = db.get_all_settings()
        self.class_name_edit.setText(s.get("class_name", ""))
        self.total_periods.setValue(int(s.get("total_periods", 3)))
        self.p1_start.setTime(QTime.fromString(s.get("period_1_start", "07:00"), "HH:mm"))
        self.p1_end.setTime(QTime.fromString(s.get("period_1_end", "08:30"), "HH:mm"))
        self.break_start.setTime(QTime.fromString(s.get("break_start", "08:30"), "HH:mm"))
        self.break_end.setTime(QTime.fromString(s.get("break_end", "08:45"), "HH:mm"))
        self.p2_start.setTime(QTime.fromString(s.get("period_2_start", "08:45"), "HH:mm"))
        self.p2_end.setTime(QTime.fromString(s.get("period_2_end", "10:15"), "HH:mm"))
        self.p3_start.setTime(QTime.fromString(s.get("period_3_start", "10:30"), "HH:mm"))
        self.p3_end.setTime(QTime.fromString(s.get("period_3_end", "12:00"), "HH:mm"))
        self.p4_start.setTime(QTime.fromString(s.get("period_4_start", "13:00"), "HH:mm"))
        self.p4_end.setTime(QTime.fromString(s.get("period_4_end", "14:30"), "HH:mm"))
        self.p5_start.setTime(QTime.fromString(s.get("period_5_start", "14:45"), "HH:mm"))
        self.p5_end.setTime(QTime.fromString(s.get("period_5_end", "16:15"), "HH:mm"))
        self.p6_start.setTime(QTime.fromString(s.get("period_6_start", "16:30"), "HH:mm"))
        self.p6_end.setTime(QTime.fromString(s.get("period_6_end", "18:00"), "HH:mm"))
        self.scan_interval.setValue(int(s.get("scan_interval_seconds", 30)))
        self.absent_threshold.setValue(int(s.get("absent_threshold", 3)))
        self.grace_period.setValue(int(s.get("grace_period_minutes", 5)))
        self._sync_period_fields()

    def _sync_period_fields(self):
        total = self.total_periods.value()
        break_visible = total >= 2
        for widget in (self.break_title, self.break_start_lbl, self.break_start, self.break_end_lbl, self.break_end):
            widget.setVisible(break_visible)
        for period, widgets in self.period_widgets.items():
            for widget in widgets:
                widget.setVisible(period <= total)

    def _save(self):
        db.save_settings_bulk({
            "class_name": self.class_name_edit.text(),
            "total_periods": str(self.total_periods.value()),
            "period_1_start": self.p1_start.time().toString("HH:mm"),
            "period_1_end": self.p1_end.time().toString("HH:mm"),
            "break_start": self.break_start.time().toString("HH:mm"),
            "break_end": self.break_end.time().toString("HH:mm"),
            "period_2_start": self.p2_start.time().toString("HH:mm"),
            "period_2_end": self.p2_end.time().toString("HH:mm"),
            "period_3_start": self.p3_start.time().toString("HH:mm"),
            "period_3_end": self.p3_end.time().toString("HH:mm"),
            "period_4_start": self.p4_start.time().toString("HH:mm"),
            "period_4_end": self.p4_end.time().toString("HH:mm"),
            "period_5_start": self.p5_start.time().toString("HH:mm"),
            "period_5_end": self.p5_end.time().toString("HH:mm"),
            "period_6_start": self.p6_start.time().toString("HH:mm"),
            "period_6_end": self.p6_end.time().toString("HH:mm"),
            "scan_interval_seconds": str(self.scan_interval.value()),
            "absent_threshold": str(self.absent_threshold.value()),
            "grace_period_minutes": str(self.grace_period.value()),
        })
        QMessageBox.information(self, "Thành công", "Đã lưu cài đặt!")
        self.accept()


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        db.init_db()
        fm.load_recognizer()

        self.setWindowTitle(f"🎓 Hệ Thống Kiểm Soát Lớp Học v{APP_VERSION}")
        self.setMinimumSize(1200, 780)
        self.setStyleSheet(STYLESHEET)

        self.camera_thread = None
        self.current_session_id = None
        self.session_active = False
        self._att_timer = None
        self._absence_timer = None
        self._last_seen_students = {}
        self._missed_scan_counts = {}
        self._last_displayed_name = ""
        self._last_displayed_face_ts = 0

        self._setup_ui()
        self._sync_period_combo()
        self._setup_status_bar()
        self._start_clock()
        self._refresh_student_list()
        self._refresh_dashboard()

    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {DARK['bg']};")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(80)
        logo_frame.setStyleSheet(f"background-color: {DARK['surface2']}; border-bottom: 1px solid {DARK['border']};")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 12, 16, 12)
        logo_title = QLabel("🎓 ClassRoom AI")
        logo_title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {DARK['accent']};")
        logo_sub = QLabel("Smart Attendance System")
        logo_sub.setStyleSheet(f"font-size: 10px; color: {DARK['text_dim']};")
        logo_layout.addWidget(logo_title)
        logo_layout.addWidget(logo_sub)
        sidebar_layout.addWidget(logo_frame)

        sidebar_layout.addSpacing(8)

        nav_label = QLabel("  ĐIỀU HƯỚNG")
        nav_label.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 10px; letter-spacing: 2px; padding: 4px 16px;")
        sidebar_layout.addWidget(nav_label)

        self.nav_buttons = []
        nav_items = [
            ("🏠", "Dashboard", 0),
            ("📹", "Camera & Điểm Danh", 1),
            ("👥", "Quản Lý Sinh Viên", 2),
            ("📊", "Báo Cáo", 3),
            ("⚙", "Cài Đặt", 4),
        ]

        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("sidebar_btn" if idx != 0 else "sidebar_btn_active")
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Clock display
        self.clock_label = QLabel("00:00:00")
        self.clock_label.setStyleSheet(f"""
            font-size: 20px; font-weight: 700;
            color: {DARK['accent']};
            padding: 8px 16px;
            text-align: center;
        """)
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.clock_label)

        self.date_label = QLabel(datetime.now().strftime("%d/%m/%Y"))
        self.date_label.setStyleSheet(f"font-size: 11px; color: {DARK['text_dim']}; padding: 0 16px 12px;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.date_label)

        main_layout.addWidget(sidebar)

        # ── Content Area ───────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {DARK['bg']};")
        main_layout.addWidget(self.stack)

        self.stack.addWidget(self._create_dashboard_page())   # 0
        self.stack.addWidget(self._create_camera_page())      # 1
        self.stack.addWidget(self._create_students_page())    # 2
        self.stack.addWidget(self._create_reports_page())     # 3
        self.stack.addWidget(self._create_settings_page())    # 4

    def _create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("🏠  Dashboard")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()
        settings = db.get_all_settings()
        class_name_lbl = QLabel(settings.get("class_name", ""))
        class_name_lbl.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 14px;")
        hdr.addWidget(class_name_lbl)
        layout.addLayout(hdr)

        # Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.stat_cards = {}
        stats_data = [
            ("total_students", "👥", "Tổng Sinh Viên", "0", DARK['accent']),
            ("present_today", "✅", "Có Mặt Hôm Nay", "0", DARK['green']),
            ("absent_today", "❌", "Vắng Hôm Nay", "0", DARK['red']),
            ("sessions_today", "📋", "Tiết Học Hôm Nay", "0", DARK['yellow']),
        ]

        for key, icon, label, val, color in stats_data:
            card = QFrame()
            card.setObjectName("card")
            card.setFixedHeight(100)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)

            top = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 22px;")
            top.addWidget(icon_lbl)
            top.addStretch()
            num_lbl = QLabel(val)
            num_lbl.setStyleSheet(f"font-size: 30px; font-weight: 800; color: {color};")
            top.addWidget(num_lbl)
            card_layout.addLayout(top)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 11px; color: {DARK['text_dim']}; letter-spacing: 1px;")
            card_layout.addWidget(lbl)

            self.stat_cards[key] = num_lbl
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # Bottom: Recent attendance + Active session
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        # Recent
        recent_card = QFrame()
        recent_card.setObjectName("card")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(16, 16, 16, 16)
        recent_title = QLabel("📋  Điểm Danh Gần Đây")
        recent_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DARK['accent']};")
        recent_layout.addWidget(recent_title)

        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Giờ", "Sinh Viên", "Tiết", "Trạng Thái"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.recent_table.verticalHeader().setVisible(False)
        recent_layout.addWidget(self.recent_table)
        bottom.addWidget(recent_card, 2)

        # Session status
        session_card = QFrame()
        session_card.setObjectName("card")
        session_card.setFixedWidth(280)
        session_layout = QVBoxLayout(session_card)
        session_layout.setContentsMargins(16, 16, 16, 16)
        session_title = QLabel("🎯  Tiết Học Hiện Tại")
        session_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DARK['accent']};")
        session_layout.addWidget(session_title)

        self.session_status_lbl = QLabel("Chưa bắt đầu tiết học")
        self.session_status_lbl.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 12px; padding: 8px 0;")
        self.session_status_lbl.setWordWrap(True)
        session_layout.addWidget(self.session_status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {DARK['surface2']};
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {DARK['accent']};
                border-radius: 4px;
            }}
        """)
        self.progress_bar.setValue(0)
        session_layout.addWidget(self.progress_bar)

        self.attendance_summary_lbl = QLabel("")
        self.attendance_summary_lbl.setStyleSheet(f"color: {DARK['text']}; font-size: 12px;")
        self.attendance_summary_lbl.setWordWrap(True)
        session_layout.addWidget(self.attendance_summary_lbl)
        session_layout.addStretch()

        btn_go_cam = QPushButton("📹  Vào Điểm Danh")
        btn_go_cam.setObjectName("primary")
        btn_go_cam.clicked.connect(lambda: self._switch_page(1))
        session_layout.addWidget(btn_go_cam)

        bottom.addWidget(session_card)
        layout.addLayout(bottom)
        return page

    def _create_camera_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("📹  Camera & Điểm Danh")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        self.btn_settings_cam = QPushButton("⚙  Cài Đặt")
        self.btn_settings_cam.clicked.connect(self._open_settings)
        hdr.addWidget(self.btn_settings_cam)
        layout.addLayout(hdr)

        # Session selector
        session_bar = QFrame()
        session_bar.setObjectName("card")
        session_bar.setFixedHeight(70)
        sb_layout = QHBoxLayout(session_bar)
        sb_layout.setContentsMargins(16, 8, 16, 8)

        sb_layout.addWidget(QLabel("📅 Ngày:"))
        self.date_combo = QComboBox()
        today = date.today().isoformat()
        self.date_combo.addItem(f"Hôm nay ({today})", today)
        sb_layout.addWidget(self.date_combo)

        sb_layout.addWidget(QLabel("   📌 Tiết:"))
        self.period_combo = QComboBox()
        for i in range(1, 4):
            self.period_combo.addItem(f"Tiết {i}", i)
        sb_layout.addWidget(self.period_combo)

        self.btn_start_session = QPushButton("▶  Bắt Đầu Tiết")
        self.btn_start_session.setObjectName("success")
        self.btn_start_session.clicked.connect(self._toggle_session)
        sb_layout.addWidget(self.btn_start_session)

        self.session_info_lbl = QLabel("Chưa có tiết học nào đang chạy")
        self.session_info_lbl.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 12px;")
        sb_layout.addWidget(self.session_info_lbl)
        sb_layout.addStretch()

        layout.addWidget(session_bar)

        # Main: Camera + Attendance List
        content = QHBoxLayout()
        content.setSpacing(16)

        # Camera feed
        cam_card = QFrame()
        cam_card.setObjectName("card")
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(12, 12, 12, 12)

        cam_title_row = QHBoxLayout()
        cam_title = QLabel("📷  Camera Feed")
        cam_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DARK['accent']};")
        cam_title_row.addWidget(cam_title)
        cam_title_row.addStretch()

        self.cam_status_badge = QLabel("● OFFLINE")
        self.cam_status_badge.setStyleSheet(f"color: {DARK['red']}; font-size: 11px; font-weight: 700;")
        cam_title_row.addWidget(self.cam_status_badge)
        cam_layout.addLayout(cam_title_row)

        self.camera_label = QLabel()
        self.camera_label.setFixedSize(540, 405)
        self.camera_label.setStyleSheet(f"""
            background-color: {DARK['surface']};
            border: 2px solid {DARK['border']};
            border-radius: 8px;
        """)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setText("📷\n\nCamera chưa được bật\nBắt đầu tiết học để kích hoạt camera")
        cam_layout.addWidget(self.camera_label)

        # Scan log
        self.scan_log_label = QLabel("Nhật ký quét: —")
        self.scan_log_label.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 11px; padding: 4px;")
        cam_layout.addWidget(self.scan_log_label)

        content.addWidget(cam_card)

        # Attendance list panel
        att_panel = QFrame()
        att_panel.setObjectName("card")
        att_panel.setFixedWidth(320)
        att_layout = QVBoxLayout(att_panel)
        att_layout.setContentsMargins(12, 12, 12, 12)

        att_title = QLabel("📋  Bảng Điểm Danh")
        att_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DARK['accent']};")
        att_layout.addWidget(att_title)

        # Mini stats
        mini_stats = QHBoxLayout()
        self.mini_present = self._mini_stat("0", "Có mặt", DARK['green'])
        self.mini_absent = self._mini_stat("0", "Vắng", DARK['red'])
        self.mini_half = self._mini_stat("0", "1/2 buổi", DARK['yellow'])
        mini_stats.addWidget(self.mini_present[0])
        mini_stats.addWidget(self.mini_absent[0])
        mini_stats.addWidget(self.mini_half[0])
        att_layout.addLayout(mini_stats)

        self.att_table = QTableWidget(0, 3)
        self.att_table.setHorizontalHeaderLabels(["Họ Tên", "Trạng Thái", "Giờ"])
        self.att_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.att_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.att_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.att_table.setColumnWidth(1, 80)
        self.att_table.setColumnWidth(2, 60)
        self.att_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.att_table.verticalHeader().setVisible(False)
        att_layout.addWidget(self.att_table)

        btn_refresh_att = QPushButton("🔄  Làm Mới")
        btn_refresh_att.clicked.connect(self._refresh_attendance_table)
        att_layout.addWidget(btn_refresh_att)

        content.addWidget(att_panel)
        layout.addLayout(content)

        return page

    def _mini_stat(self, value, label, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background-color: {DARK['surface2']};
            border: 1px solid {DARK['border']};
            border-radius: 8px;
            padding: 4px;
        """)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(8, 6, 8, 6)
        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {color};")
        v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_lbl = QLabel(label)
        l_lbl.setStyleSheet(f"font-size: 10px; color: {DARK['text_dim']};")
        l_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(v_lbl)
        vl.addWidget(l_lbl)
        return frame, v_lbl

    def _create_students_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("👥  Quản Lý Sinh Viên")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Tìm kiếm sinh viên...")
        self.search_edit.setFixedWidth(240)
        self.search_edit.textChanged.connect(self._filter_students)
        hdr.addWidget(self.search_edit)

        btn_add = QPushButton("➕  Thêm Sinh Viên")
        btn_add.setObjectName("primary")
        btn_add.setMinimumWidth(170)
        btn_add.clicked.connect(self._add_student)
        hdr.addWidget(btn_add)
        layout.addLayout(hdr)

        # Stats row
        stats_row = QHBoxLayout()
        self.sv_total_lbl = QLabel("Tổng: 0 sinh viên")
        self.sv_total_lbl.setStyleSheet(f"color: {DARK['text_dim']};")
        self.sv_encoded_lbl = QLabel("Đã đăng ký khuôn mặt: 0")
        self.sv_encoded_lbl.setStyleSheet(f"color: {DARK['green']};")
        stats_row.addWidget(self.sv_total_lbl)
        stats_row.addWidget(self.sv_encoded_lbl)
        stats_row.addStretch()
        layout.addLayout(stats_row)

        # Table
        self.students_table = QTableWidget(0, 6)
        self.students_table.setHorizontalHeaderLabels([
            "Ảnh", "Mã SV", "Họ và Tên", "Khuôn Mặt", "Ngày Thêm", "Thao Tác"
        ])
        header = self.students_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.students_table.setColumnWidth(0, 72)
        self.students_table.setColumnWidth(3, 150)
        self.students_table.setColumnWidth(4, 125)
        self.students_table.setColumnWidth(5, 170)
        self.students_table.verticalHeader().setDefaultSectionSize(60)
        self.students_table.verticalHeader().setMinimumSectionSize(60)
        self.students_table.verticalHeader().setVisible(False)
        self.students_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.students_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.students_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.setWordWrap(False)
        self.students_table.setShowGrid(False)
        layout.addWidget(self.students_table)

        return page

    def _create_reports_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("📊  Báo Cáo & Xuất File")
        title.setObjectName("title")
        hdr.addWidget(title)
        layout.addLayout(hdr)

        tabs = QTabWidget()

        # ── Tab: Xuất theo ngày ───────────────────────────────────────────────
        day_tab = QWidget()
        dl = QVBoxLayout(day_tab)
        dl.setContentsMargins(20, 20, 20, 20)

        day_form = QHBoxLayout()
        day_form.addWidget(QLabel("📅 Chọn ngày:"))
        self.export_date = QComboBox()
        self._populate_date_combo()
        day_form.addWidget(self.export_date)
        day_form.addWidget(QLabel("Định dạng:"))
        self.export_format = QComboBox()
        self.export_format.addItem("Excel (.xlsx)", "xlsx")
        self.export_format.addItem("PDF (.pdf)", "pdf")
        day_form.addWidget(self.export_format)
        day_form.addStretch()
        dl.addLayout(day_form)

        btn_export_day = QPushButton("📥  Xuất Báo Cáo Theo Ngày")
        btn_export_day.setObjectName("primary")
        btn_export_day.setFixedWidth(240)
        btn_export_day.clicked.connect(self._export_by_date)
        dl.addWidget(btn_export_day)

        self.export_preview = QTableWidget(0, 5)
        self.export_preview.setHorizontalHeaderLabels(["Mã SV", "Họ Tên", "Tiết 1", "Tiết 2", "Tiết 3"])
        self.export_preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.export_preview.verticalHeader().setVisible(False)
        dl.addWidget(QLabel("👁  Xem trước:"))
        dl.addWidget(self.export_preview)

        btn_preview = QPushButton("🔍  Xem Trước Dữ Liệu")
        btn_preview.clicked.connect(self._preview_attendance)
        dl.addWidget(btn_preview)

        tabs.addTab(day_tab, "📅 Theo Ngày")

        # ── Tab: Báo cáo tháng ────────────────────────────────────────────────
        month_tab = QWidget()
        ml = QVBoxLayout(month_tab)
        ml.setContentsMargins(20, 20, 20, 20)

        month_form = QHBoxLayout()
        month_form.addWidget(QLabel("📅 Tháng:"))
        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f"Tháng {m}", m)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        month_form.addWidget(self.month_combo)

        month_form.addWidget(QLabel("Năm:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(datetime.now().year)
        month_form.addWidget(self.year_spin)
        month_form.addWidget(QLabel("Định dạng:"))
        self.month_export_format = QComboBox()
        self.month_export_format.addItem("Excel (.xlsx)", "xlsx")
        self.month_export_format.addItem("PDF (.pdf)", "pdf")
        month_form.addWidget(self.month_export_format)
        month_form.addStretch()
        ml.addLayout(month_form)

        btn_export_month = QPushButton("📥  Xuất Báo Cáo Tháng")
        btn_export_month.setObjectName("primary")
        btn_export_month.setFixedWidth(220)
        btn_export_month.clicked.connect(self._export_monthly)
        ml.addWidget(btn_export_month)
        ml.addStretch()

        tabs.addTab(month_tab, "📆 Báo Cáo Tháng")

        layout.addWidget(tabs)
        return page

    def _create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("⚙  Cài Đặt")
        title.setObjectName("title")
        layout.addWidget(title)

        btn_open = QPushButton("⚙  Mở Cài Đặt Chi Tiết")
        btn_open.setObjectName("primary")
        btn_open.setFixedWidth(220)
        btn_open.clicked.connect(self._open_settings)
        layout.addWidget(btn_open)

        # Show current settings
        self.settings_display = QTextEdit()
        self.settings_display.setReadOnly(True)
        self.settings_display.setStyleSheet(f"""
            background-color: {DARK['surface']};
            border: 1px solid {DARK['border']};
            border-radius: 8px;
            color: {DARK['text']};
            font-family: 'Consolas', monospace;
            font-size: 12px;
            padding: 12px;
        """)
        layout.addWidget(self.settings_display)
        self._refresh_settings_display()
        return page

    # ── Status Bar ─────────────────────────────────────────────────────────────

    def _setup_status_bar(self):
        self.statusBar().showMessage("✅ Hệ thống sẵn sàng  |  " + datetime.now().strftime("%d/%m/%Y"))

    # ── Clock ──────────────────────────────────────────────────────────────────

    def _start_clock(self):
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

    def _update_clock(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%d/%m/%Y"))
        self._sync_current_time_state(now)
        if self.session_active:
            self._auto_check_session_time(now)

    def _time_minutes(self, hhmm):
        t = datetime.strptime(hhmm, "%H:%M").time()
        return t.hour * 60 + t.minute

    def _get_time_state(self, now=None):
        now = now or datetime.now()
        minute = now.hour * 60 + now.minute
        settings = db.get_all_settings()
        total = int(settings.get("total_periods", 3))
        for period in range(1, total + 1):
            start = settings.get(f"period_{period}_start")
            end = settings.get(f"period_{period}_end")
            if start and end and self._time_minutes(start) <= minute < self._time_minutes(end):
                return {"type": "period", "period": period, "start": start, "end": end}
        if total >= 2:
            b_start = settings.get("break_start", "08:30")
            b_end = settings.get("break_end", "08:45")
            if self._time_minutes(b_start) <= minute < self._time_minutes(b_end):
                return {"type": "break", "start": b_start, "end": b_end}
        return {"type": "off"}

    def _sync_current_time_state(self, now=None):
        if not hasattr(self, "session_info_lbl") or self.session_active:
            return
        state = self._get_time_state(now)
        if state["type"] == "period":
            idx = self.period_combo.findData(state["period"])
            if idx >= 0:
                self.period_combo.setCurrentIndex(idx)
            self.session_info_lbl.setText(f"Đang trong khung Tiết {state['period']} ({state['start']} → {state['end']})")
            self.session_info_lbl.setStyleSheet(f"color: {DARK['accent']}; font-size: 12px;")
        elif state["type"] == "break":
            self.session_info_lbl.setText(f"Đang ra chơi ({state['start']} → {state['end']})")
            self.session_info_lbl.setStyleSheet(f"color: {DARK['yellow']}; font-size: 12px;")
        else:
            self.session_info_lbl.setText("Hiện không có tiết")
            self.session_info_lbl.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 12px;")

    def _sync_period_combo(self):
        if not hasattr(self, "period_combo"):
            return
        settings = db.get_all_settings()
        total = int(settings.get("total_periods", 3))
        current = self.period_combo.currentData()
        self.period_combo.clear()
        for i in range(1, total + 1):
            self.period_combo.addItem(f"Tiết {i}", i)
        if current:
            idx = self.period_combo.findData(current)
            if idx >= 0:
                self.period_combo.setCurrentIndex(idx)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_buttons):
            btn.setObjectName("sidebar_btn_active" if i == idx else "sidebar_btn")
            btn.setStyle(btn.style())

        if idx == 0:
            self._refresh_dashboard()
        elif idx == 2:
            self._refresh_student_list()
        elif idx == 4:
            self._refresh_settings_display()

    # ── Dashboard ──────────────────────────────────────────────────────────────

    def _refresh_dashboard(self):
        students = db.get_all_students()
        today = date.today().isoformat()
        sessions = db.get_sessions_by_date(today)

        self.stat_cards["total_students"].setText(str(len(students)))
        self.stat_cards["sessions_today"].setText(str(len(sessions)))

        present = absent = 0
        for s in sessions:
            att = db.get_attendance_by_session(s["id"])
            for a in att:
                if a["status"] == "present":
                    present += 1
                elif a["status"] == "absent":
                    absent += 1

        self.stat_cards["present_today"].setText(str(present))
        self.stat_cards["absent_today"].setText(str(absent))

        if self.session_active and self.current_session_id:
            att = db.get_attendance_by_session(self.current_session_id)
            total = len(students)
            p = sum(1 for a in att if a["status"] == "present")
            self.session_status_lbl.setText(f"🟢 Tiết đang chạy — {p}/{total} sinh viên có mặt")
            self.attendance_summary_lbl.setText(
                f"Có mặt: {p}  |  Vắng: {total - p}"
            )
            if total > 0:
                self.progress_bar.setValue(int(p / total * 100))

    # ── Camera & Session ───────────────────────────────────────────────────────

    def _toggle_session(self):
        if not self.session_active:
            self._start_session()
        else:
            self._end_session()

    def _start_session(self):
        state = self._get_time_state()
        if state["type"] != "period":
            msg = "Đang ra chơi, không cần điểm danh." if state["type"] == "break" else "Hiện không có tiết trong khung giờ đã cài đặt."
            self.session_info_lbl.setText(msg)
            self.session_info_lbl.setStyleSheet(f"color: {DARK['yellow']}; font-size: 12px;")
            self.camera_label.setText(f"📷\n\n{msg}")
            self.cam_status_badge.setText("● OFFLINE")
            self.cam_status_badge.setStyleSheet(f"color: {DARK['red']}; font-size: 11px; font-weight: 700;")
            return

        today = date.today().isoformat()
        period = state["period"]
        idx = self.period_combo.findData(period)
        if idx >= 0:
            self.period_combo.setCurrentIndex(idx)
        session = db.get_or_create_session(today, period)
        self.current_session_id = session["id"]
        self.session_active = True

        settings = db.get_all_settings()
        self.btn_start_session.setText("⏹  Kết Thúc Tiết")
        self.btn_start_session.setObjectName("danger")
        self.btn_start_session.setStyle(self.btn_start_session.style())
        self.session_info_lbl.setText(
            f"🟢 Đang chạy — Tiết {period}  ({session['start_time']} → {session['end_time']})"
        )
        self.session_info_lbl.setStyleSheet(f"color: {DARK['green']}; font-size: 12px;")

        # Start camera
        self.camera_thread = CameraThread(mode="monitor")
        self.camera_thread.set_session(self.current_session_id)
        self.camera_thread.frame_ready.connect(self._update_camera_frame)
        self.camera_thread.face_detected.connect(self._on_face_detected)
        self.camera_thread.status_update.connect(self._on_cam_status)
        self.camera_thread.start()

        self.cam_status_badge.setText("● ĐANG MỞ")
        self.cam_status_badge.setStyleSheet(f"color: {DARK['yellow']}; font-size: 11px; font-weight: 700;")
        self.camera_label.setText("📷\n\nĐang mở camera...")
        db.update_session_status(self.current_session_id, "active")

        self._refresh_attendance_table()
        self.statusBar().showMessage(f"▶ Tiết {period} bắt đầu — {datetime.now().strftime('%H:%M:%S')}")

        # Auto refresh attendance every 5s
        self._att_timer = QTimer(self)
        self._att_timer.timeout.connect(self._refresh_attendance_table)
        self._att_timer.start(5000)

        scan_interval = int(settings.get("scan_interval_seconds", 30))
        self._last_seen_students = {}
        self._missed_scan_counts = {}
        self._absence_timer = QTimer(self)
        self._absence_timer.timeout.connect(self._scan_absent_students)
        self._absence_timer.start(max(5, scan_interval) * 1000)

    def _end_session(self):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None

        if self.current_session_id:
            db.finalize_absent_for_session(self.current_session_id)
            db.update_session_status(self.current_session_id, "completed")

        self.session_active = False
        self.btn_start_session.setText("▶  Bắt Đầu Tiết")
        self.btn_start_session.setObjectName("success")
        self.btn_start_session.setStyle(self.btn_start_session.style())
        self.session_info_lbl.setText("Tiết học đã kết thúc")
        self.session_info_lbl.setStyleSheet(f"color: {DARK['text_dim']}; font-size: 12px;")
        self.cam_status_badge.setText("● OFFLINE")
        self.cam_status_badge.setStyleSheet(f"color: {DARK['red']}; font-size: 11px; font-weight: 700;")
        self.camera_label.setText("📷\n\nCamera đã tắt")
        if hasattr(self, '_att_timer'):
            self._att_timer.stop()
        if self._absence_timer:
            self._absence_timer.stop()
        self._refresh_attendance_table()
        self._refresh_dashboard()
        self.statusBar().showMessage(f"⏹ Tiết học kết thúc — {datetime.now().strftime('%H:%M:%S')}")

    def _update_camera_frame(self, frame):
        self.cam_status_badge.setText("● LIVE")
        self.cam_status_badge.setStyleSheet(f"color: {DARK['green']}; font-size: 11px; font-weight: 700;")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            540, 405, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.camera_label.setPixmap(pix)

    def _on_face_detected(self, student_id, name, confidence):
        self._last_seen_students[student_id] = datetime.now()
        self._missed_scan_counts[student_id] = 0
        self._last_displayed_name = f"{name} ({student_id})"
        self._last_displayed_face_ts = datetime.now().timestamp()
        self.scan_log_label.setText(
            f"✅ {datetime.now().strftime('%H:%M:%S')} — {name} ({student_id}) — {confidence:.0f}% khớp"
        )
        self.scan_log_label.setStyleSheet(f"color: {DARK['green']}; font-size: 11px; padding: 4px;")

    def _on_cam_status(self, msg):
        self.scan_log_label.setText(msg)
        self.scan_log_label.setStyleSheet(f"color: {DARK['red']}; font-size: 11px; padding: 4px;")
        self.cam_status_badge.setText("● LỖI CAMERA")
        self.cam_status_badge.setStyleSheet(f"color: {DARK['red']}; font-size: 11px; font-weight: 700;")
        self.camera_label.setText(f"📷\n\n{msg}\nKiểm tra quyền camera hoặc đóng app đang dùng camera.")
        if self.session_active:
            self.session_active = False
            self.btn_start_session.setText("▶  Bắt Đầu Tiết")
            self.btn_start_session.setObjectName("success")
            self.btn_start_session.setStyle(self.btn_start_session.style())
            self.session_info_lbl.setText("Camera không mở được")
            self.session_info_lbl.setStyleSheet(f"color: {DARK['red']}; font-size: 12px;")
        if self._att_timer:
            self._att_timer.stop()
        if self._absence_timer:
            self._absence_timer.stop()

    def _auto_check_session_time(self, now):
        """Kiểm tra và tự động đánh vắng theo thời gian"""
        if not self.session_active:
            return
        state = self._get_time_state(now)
        current_period = self.period_combo.currentData()
        if state["type"] != "period" or state.get("period") != current_period:
            self._end_session()
            self._sync_current_time_state(now)

    def _scan_absent_students(self):
        if not self.session_active or not self.current_session_id:
            return

        settings = db.get_all_settings()
        grace_minutes = int(settings.get("grace_period_minutes", 5))
        scan_interval = int(settings.get("scan_interval_seconds", 30))
        threshold = int(settings.get("absent_threshold", 3))
        session_rows = db.get_attendance_by_session(self.current_session_id)
        attendance_map = {a["student_id"]: a for a in session_rows}

        session = None
        for item in db.get_sessions_by_date(date.today().isoformat()):
            if item["id"] == self.current_session_id:
                session = item
                break

        start_dt = end_dt = None
        if session:
            start_dt = datetime.combine(
                date.today(),
                datetime.strptime(session["start_time"], "%H:%M").time()
            )
            end_dt = datetime.combine(
                date.today(),
                datetime.strptime(session["end_time"], "%H:%M").time()
            )
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            if (datetime.now() - start_dt).total_seconds() < grace_minutes * 60:
                return

        session_seconds = (end_dt - start_dt).total_seconds() if start_dt and end_dt else 90 * 60
        half_absent_seconds = max(scan_interval * threshold, session_seconds * 0.35)

        now = datetime.now()
        changed = False
        for student in db.get_all_students():
            sid = student["student_id"]
            last_seen = self._last_seen_students.get(sid)
            if last_seen and (now - last_seen).total_seconds() <= scan_interval:
                self._missed_scan_counts[sid] = 0
                continue

            self._missed_scan_counts[sid] = self._missed_scan_counts.get(sid, 0) + 1
            att = attendance_map.get(sid)
            current_status = att["status"] if att else None
            if current_status == "present":
                last_seen_dt = self._last_seen_students.get(sid)
                if not last_seen_dt and att:
                    last_seen_text = att.get("last_seen_time") or att.get("check_in_time")
                    if last_seen_text:
                        last_seen_dt = datetime.combine(
                            date.today(),
                            datetime.strptime(last_seen_text, "%H:%M:%S").time()
                        )

                away_seconds = (now - last_seen_dt).total_seconds() if last_seen_dt else session_seconds
                if self._missed_scan_counts[sid] >= threshold and away_seconds >= half_absent_seconds:
                    db.mark_half_attendance(sid, self.current_session_id)
                    db.log_scan(sid, self.current_session_id, "half")
                    changed = True
                continue
            if current_status == "half":
                continue

            new_status = db.increment_absent_scan(sid, self.current_session_id)
            db.log_scan(sid, self.current_session_id, new_status)
            changed = True

        if changed:
            self._refresh_attendance_table()

    def _refresh_attendance_table(self):
        if not self.current_session_id:
            return
        att_list = db.get_attendance_by_session(self.current_session_id)
        students = db.get_all_students()
        self.att_table.setRowCount(0)

        status_map = {a["student_id"]: a for a in att_list}
        present = absent = half = 0

        for student in students:
            sid = student["student_id"]
            att = status_map.get(sid)
            status = att["status"] if att else "absent"
            check_in = att["check_in_time"] if att else "—"

            if status == "present": present += 1
            elif status == "absent": absent += 1
            elif status == "half": half += 1

            row = self.att_table.rowCount()
            self.att_table.insertRow(row)
            self.att_table.setRowHeight(row, 30)

            name_item = QTableWidgetItem(student["name"])
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.att_table.setItem(row, 0, name_item)

            status_vi = {"present": "Có mặt", "absent": "Vắng", "half": "1/2", "scanning": "Đang quét"}
            status_colors = {
                "present": DARK['green'],
                "absent": DARK['red'],
                "half": DARK['yellow'],
                "scanning": DARK['accent'],
            }
            s_item = QTableWidgetItem(status_vi.get(status, status))
            s_item.setForeground(QColor(status_colors.get(status, DARK['text'])))
            s_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.att_table.setItem(row, 1, s_item)

            t_item = QTableWidgetItem(check_in or "—")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            t_item.setForeground(QColor(DARK['text_dim']))
            self.att_table.setItem(row, 2, t_item)

        self.mini_present[1].setText(str(present))
        self.mini_absent[1].setText(str(absent))
        self.mini_half[1].setText(str(half))

    # ── Students ───────────────────────────────────────────────────────────────

    def _refresh_student_list(self, filter_text=""):
        students = db.get_all_students()
        if filter_text:
            students = [s for s in students if
                        filter_text.lower() in s["name"].lower() or
                        filter_text.lower() in s["student_id"].lower()]

        total = len(db.get_all_students())
        encoded = sum(1 for s in db.get_all_students() if s.get("face_encoding"))
        self.sv_total_lbl.setText(f"Tổng: {total} sinh viên")
        self.sv_encoded_lbl.setText(f"✅ Đã đăng ký khuôn mặt: {encoded}")

        self.students_table.setRowCount(0)
        for student in students:
            row = self.students_table.rowCount()
            self.students_table.insertRow(row)
            self.students_table.setRowHeight(row, 60)

            # Avatar
            photo_path = student.get("photo_path")
            avatar_lbl = QLabel()
            avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_lbl.setFixedSize(56, 56)
            if photo_path and os.path.exists(photo_path):
                pix = QPixmap(photo_path).scaled(
                    50, 50,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                avatar_lbl.setPixmap(pix)
                avatar_lbl.setStyleSheet(f"background-color: {DARK['surface2']}; border-radius: 4px;")
            else:
                avatar_lbl.setText("👤")
                avatar_lbl.setStyleSheet(f"font-size: 24px; background-color: {DARK['surface2']}; border-radius: 22px;")
            self.students_table.setCellWidget(row, 0, avatar_lbl)

            id_item = QTableWidgetItem(student["student_id"])
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setForeground(QColor(DARK['accent']))
            self.students_table.setItem(row, 1, id_item)

            name_item = QTableWidgetItem(student["name"])
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.students_table.setItem(row, 2, name_item)

            has_enc = student.get("face_encoding") is not None
            enc_item = QTableWidgetItem("✅ Đã đăng ký" if has_enc else "⚠ Chưa có")
            enc_item.setForeground(QColor(DARK['green'] if has_enc else DARK['yellow']))
            enc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.students_table.setItem(row, 3, enc_item)

            date_str = student.get("created_at", "")[:10]
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setForeground(QColor(DARK['text_dim']))
            self.students_table.setItem(row, 4, date_item)

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(6, 8, 6, 8)
            action_layout.setSpacing(8)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_edit = QPushButton("✎")
            btn_edit.setFixedSize(36, 34)
            btn_edit.setToolTip("Chỉnh sửa sinh viên")
            btn_edit.clicked.connect(lambda _, s=student: self._edit_student(s))

            btn_del = QPushButton("×")
            btn_del.setFixedSize(36, 34)
            btn_del.setObjectName("danger")
            btn_del.setToolTip("Xóa sinh viên")
            btn_del.clicked.connect(lambda _, sid=student["student_id"]: self._delete_student(sid))

            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_del)
            self.students_table.setCellWidget(row, 5, action_widget)

        self.students_table.resizeColumnToContents(1)

    def _filter_students(self, text):
        self._refresh_student_list(text)

    def _add_student(self):
        dlg = AddStudentDialog(self)
        dlg.student_added.connect(self._refresh_student_list)
        dlg.exec()

    def _edit_student(self, student_data):
        dlg = AddStudentDialog(self, student_data=student_data)
        dlg.student_added.connect(self._refresh_student_list)
        dlg.exec()

    def _delete_student(self, student_id):
        reply = QMessageBox.question(
            self, "Xác Nhận Xóa",
            f"Bạn có chắc muốn xóa sinh viên {student_id}?\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_student(student_id)
            fm.load_recognizer()
            self._refresh_student_list()

    # ── Reports ────────────────────────────────────────────────────────────────

    def _populate_date_combo(self):
        self.export_date.clear()
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT DISTINCT session_date FROM sessions ORDER BY session_date DESC LIMIT 30"
        ).fetchall()
        conn.close()
        today = date.today().isoformat()
        if not any(r["session_date"] == today for r in rows):
            self.export_date.addItem(f"Hôm nay ({today})", today)
        for r in rows:
            d = r["session_date"]
            self.export_date.addItem(d, d)
        if self.export_date.count() == 0:
            self.export_date.addItem(f"Hôm nay ({today})", today)

    def _preview_attendance(self):
        target_date = self.export_date.currentData()
        if not target_date:
            return
        settings = db.get_all_settings()
        total_periods = int(settings.get("total_periods", 3))
        sessions = db.get_sessions_by_date(target_date)
        session_map = {s["period"]: s for s in sessions}
        students = db.get_all_students()

        headers = ["Mã SV", "Họ Tên"] + [f"Tiết {p}" for p in range(1, total_periods + 1)]
        self.export_preview.setColumnCount(len(headers))
        self.export_preview.setHorizontalHeaderLabels(headers)
        self.export_preview.setRowCount(0)

        for student in students:
            row = self.export_preview.rowCount()
            self.export_preview.insertRow(row)
            self.export_preview.setItem(row, 0, QTableWidgetItem(student["student_id"]))
            self.export_preview.setItem(row, 1, QTableWidgetItem(student["name"]))
            for p in range(1, total_periods + 1):
                sess = session_map.get(p)
                if sess:
                    att_list = db.get_attendance_by_session(sess["id"])
                    att = next((a for a in att_list if a["student_id"] == student["student_id"]), None)
                    status = att["status"] if att else "absent"
                else:
                    status = "—"
                status_vi = {"present": "✅ Có mặt", "absent": "❌ Vắng", "half": "⚡ 1/2", "—": "—"}
                item = QTableWidgetItem(status_vi.get(status, status))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.export_preview.setItem(row, p + 1, item)

    def _export_by_date(self):
        target_date = self.export_date.currentData()
        if not target_date:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ngày!")
            return
        export_format = self.export_format.currentData() if hasattr(self, "export_format") else "xlsx"
        if export_format == "pdf":
            filepath, msg = em.export_by_date_pdf(target_date)
        else:
            filepath, msg = em.export_by_date(target_date)
        if filepath:
            reply = QMessageBox.information(
                self, "✅ Xuất Thành Công",
                f"{msg}\n\nFile: {filepath}\n\nMở file không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_file(filepath)
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def _export_monthly(self):
        month = self.month_combo.currentData()
        year = self.year_spin.value()
        export_format = self.month_export_format.currentData() if hasattr(self, "month_export_format") else "xlsx"
        if export_format == "pdf":
            filepath, msg = em.export_monthly_report_pdf(year, month)
        else:
            filepath, msg = em.export_monthly_report(year, month)
        if filepath:
            QMessageBox.information(self, "✅ Xuất Thành Công", f"{msg}\n\nFile: {filepath}")
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def _open_file(self, filepath):
        if sys.platform.startswith("win"):
            os.startfile(filepath)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])

    # ── Settings ───────────────────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        self._sync_period_combo()
        self._sync_current_time_state()
        self._refresh_settings_display()

    def _refresh_settings_display(self):
        s = db.get_all_settings()
        text = "📋  CẤU HÌNH HIỆN TẠI\n" + "─" * 40 + "\n"
        labels = {
            "class_name": "Tên lớp",
            "total_periods": "Số tiết/ngày",
            "period_1_start": "Tiết 1 bắt đầu",
            "period_1_end": "Tiết 1 kết thúc",
            "break_start": "Nghỉ giải lao bắt đầu",
            "break_end": "Nghỉ giải lao kết thúc",
            "period_2_start": "Tiết 2 bắt đầu",
            "period_2_end": "Tiết 2 kết thúc",
            "period_3_start": "Tiết 3 bắt đầu",
            "period_3_end": "Tiết 3 kết thúc",
            "period_4_start": "Tiết 4 bắt đầu",
            "period_4_end": "Tiết 4 kết thúc",
            "period_5_start": "Tiết 5 bắt đầu",
            "period_5_end": "Tiết 5 kết thúc",
            "period_6_start": "Tiết 6 bắt đầu",
            "period_6_end": "Tiết 6 kết thúc",
            "scan_interval_seconds": "Chu kỳ quét (giây)",
            "absent_threshold": "Ngưỡng đánh vắng (lần)",
            "grace_period_minutes": "Thời gian ân hạn (phút)",
        }
        for k, v in labels.items():
            text += f"  {v:35s}: {s.get(k, '')}\n"
        if hasattr(self, 'settings_display'):
            self.settings_display.setText(text)

    def closeEvent(self, event):
        if self.camera_thread:
            self.camera_thread.stop()
        event.accept()


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ClassRoom AI")
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(DARK['bg']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(DARK['text']))
    palette.setColor(QPalette.ColorRole.Base, QColor(DARK['surface']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DARK['surface2']))
    palette.setColor(QPalette.ColorRole.Text, QColor(DARK['text']))
    palette.setColor(QPalette.ColorRole.Button, QColor(DARK['surface2']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(DARK['text']))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
