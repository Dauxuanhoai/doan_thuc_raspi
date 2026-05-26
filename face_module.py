import cv2
import numpy as np
import os
import json
import unicodedata
from PIL import Image

# Sử dụng OpenCV LBPH face recognizer (không cần dlib, chạy được trên Raspi4)
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), "face_data")
os.makedirs(ENCODINGS_DIR, exist_ok=True)

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

# Global face recognizer
_recognizer = None
_label_map = {}  # label_id -> student_id
_student_names = {}  # student_id -> name
_is_trained = False

def get_face_cascade():
    return FACE_CASCADE

def detect_faces(frame_gray):
    """Phát hiện khuôn mặt trong ảnh grayscale"""
    faces = FACE_CASCADE.detectMultiScale(
        frame_gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return faces if len(faces) > 0 else []

def extract_face_region(frame_gray, x, y, w, h, size=(100, 100)):
    """Cắt và resize vùng khuôn mặt"""
    face_roi = frame_gray[y:y+h, x:x+w]
    face_resized = cv2.resize(face_roi, size)
    return face_resized

def extract_encoding_from_image(img_path):
    """
    Trích xuất 'encoding' từ ảnh - dùng LBPH histogram làm feature vector.
    Trả về list (JSON serializable) hoặc None nếu không tìm thấy mặt.
    """
    img = cv2.imread(img_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detect_faces(gray)
    if len(faces) == 0:
        return None
    # Lấy khuôn mặt lớn nhất
    x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
    face = extract_face_region(gray, x, y, w, h, (100, 100))

    # Dùng histogram LBP tự tính để không cần gói opencv-contrib.
    encoding = _compute_lbp_histogram(face)
    return encoding.tolist()

def extract_encoding_from_frame(frame_gray, x, y, w, h):
    """Trích xuất encoding từ frame camera"""
    face = extract_face_region(frame_gray, x, y, w, h)
    encoding = _compute_lbp_histogram(face)
    return encoding.tolist()

def _compute_lbp_histogram(face_gray):
    """Tính LBP histogram cho face region"""
    radius = 1
    n_points = 8
    lbp = np.zeros_like(face_gray, dtype=np.uint8)
    for i in range(radius, face_gray.shape[0] - radius):
        for j in range(radius, face_gray.shape[1] - radius):
            center = face_gray[i, j]
            binary = 0
            for k in range(n_points):
                angle = 2 * np.pi * k / n_points
                xi = i + int(round(radius * np.sin(angle)))
                xj = j + int(round(radius * np.cos(angle)))
                if face_gray[xi, xj] >= center:
                    binary |= (1 << k)
            lbp[i, j] = binary

    # Chia thành grid 5x5 và tính histogram từng ô
    h, w = lbp.shape
    grid_h, grid_w = h // 5, w // 5
    hist_all = []
    for gi in range(5):
        for gj in range(5):
            cell = lbp[gi*grid_h:(gi+1)*grid_h, gj*grid_w:(gj+1)*grid_w]
            hist, _ = np.histogram(cell.ravel(), bins=32, range=(0, 256))
            hist = hist.astype(np.float32)
            norm = np.linalg.norm(hist)
            if norm > 0:
                hist /= norm
            hist_all.extend(hist.tolist())
    return np.array(hist_all, dtype=np.float32)

def load_recognizer():
    """Load/rebuild face recognizer từ database"""
    global _recognizer, _label_map, _student_names, _is_trained

    import database as db
    students = db.get_students_with_encoding()

    if not students:
        _is_trained = False
        return False

    faces = []
    labels = []
    _label_map = {}
    _student_names = {}

    for idx, s in enumerate(students):
        enc = np.array(s["encoding"], dtype=np.float32)
        faces.append(enc)
        labels.append(idx)
        _label_map[idx] = s["student_id"]
        _student_names[s["student_id"]] = s["name"]

    # Dùng custom cosine similarity thay vì LBPH recognizer
    _recognizer = {"faces": faces, "labels": labels}
    _is_trained = True
    return True

def recognize_face(encoding, threshold=0.75):
    """
    So sánh encoding với database.
    Trả về (student_id, name, confidence) hoặc (None, None, 0)
    """
    global _recognizer, _is_trained

    if not _is_trained or _recognizer is None:
        return None, None, 0.0

    query = np.array(encoding, dtype=np.float32)
    best_score = -1
    best_label = -1

    for i, face_enc in enumerate(_recognizer["faces"]):
        # Cosine similarity
        dot = np.dot(query, face_enc)
        norm_q = np.linalg.norm(query)
        norm_f = np.linalg.norm(face_enc)
        if norm_q > 0 and norm_f > 0:
            score = dot / (norm_q * norm_f)
        else:
            score = 0.0
        if score > best_score:
            best_score = score
            best_label = _recognizer["labels"][i]

    if best_score >= threshold and best_label in _label_map:
        sid = _label_map[best_label]
        name = _student_names.get(sid, "Unknown")
        confidence = round(best_score * 100, 1)
        return sid, name, confidence

    return None, None, round(best_score * 100, 1)

def ascii_label(text):
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.encode("ascii", "ignore").decode("ascii") or "Unknown"

def save_student_photo(student_id, img_array_bgr, suffix=""):
    """Lưu ảnh sinh viên"""
    safe_suffix = f"_{suffix}" if suffix else ""
    path = os.path.join(PHOTOS_DIR, f"{student_id}{safe_suffix}.jpg")
    cv2.imwrite(path, img_array_bgr)
    return path

def get_student_photo_path(student_id):
    path = os.path.join(PHOTOS_DIR, f"{student_id}.jpg")
    return path if os.path.exists(path) else None

def draw_face_box(frame, x, y, w, h, name=None, confidence=0, status="unknown"):
    """Vẽ hộp nhận diện lên frame"""
    colors = {
        "present": (0, 220, 100),
        "unknown": (0, 140, 255),
        "absent": (0, 60, 220),
        "scanning": (0, 200, 220),
    }
    color = colors.get(status, (200, 200, 200))

    # Bo góc hộp
    thickness = 2
    corner_len = 15
    # Top-left
    cv2.line(frame, (x, y), (x + corner_len, y), color, thickness + 1)
    cv2.line(frame, (x, y), (x, y + corner_len), color, thickness + 1)
    # Top-right
    cv2.line(frame, (x+w, y), (x+w - corner_len, y), color, thickness + 1)
    cv2.line(frame, (x+w, y), (x+w, y + corner_len), color, thickness + 1)
    # Bottom-left
    cv2.line(frame, (x, y+h), (x + corner_len, y+h), color, thickness + 1)
    cv2.line(frame, (x, y+h), (x, y+h - corner_len), color, thickness + 1)
    # Bottom-right
    cv2.line(frame, (x+w, y+h), (x+w - corner_len, y+h), color, thickness + 1)
    cv2.line(frame, (x+w, y+h), (x+w, y+h - corner_len), color, thickness + 1)

    if name:
        label = f"{ascii_label(name)} ({confidence:.0f}%)"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x, y - th - 8), (x + tw + 8, y), color, -1)
        cv2.putText(frame, label, (x + 4, y - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
