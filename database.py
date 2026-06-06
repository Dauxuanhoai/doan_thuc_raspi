import sqlite3
import os
import json
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), "classroom.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            face_encoding TEXT,
            photo_path TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TEXT NOT NULL,
            period INTEGER NOT NULL,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT 'pending',
            UNIQUE(session_date, period)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            status TEXT DEFAULT 'absent',
            check_in_time TEXT,
            last_seen_time TEXT,
            scan_count INTEGER DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            UNIQUE(student_id, session_id)
        )
    """)

    cols = {r["name"] for r in c.execute("PRAGMA table_info(attendance)").fetchall()}
    if "last_seen_time" not in cols:
        c.execute("ALTER TABLE attendance ADD COLUMN last_seen_time TEXT")
        c.execute("UPDATE attendance SET last_seen_time=check_in_time WHERE check_in_time IS NOT NULL")

    c.execute("""
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            session_id INTEGER,
            scan_time TEXT DEFAULT (datetime('now','localtime')),
            result TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance(session_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_scan_logs_student_session ON scan_logs(student_id, session_id)")

    # Default settings
    defaults = {
        "period_1_start": "07:00",
        "period_1_end": "08:30",
        "break_start": "08:30",
        "break_end": "08:45",
        "period_2_start": "08:45",
        "period_2_end": "10:15",
        "period_3_start": "10:30",
        "period_3_end": "12:00",
        "period_4_start": "13:00",
        "period_4_end": "14:30",
        "period_5_start": "14:45",
        "period_5_end": "16:15",
        "period_6_start": "16:30",
        "period_6_end": "18:00",
        "scan_interval_seconds": "30",
        "absent_threshold": "3",
        "grace_period_minutes": "5",
        "class_name": "Lớp học thông minh",
        "total_periods": "3",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Clean records left behind by older versions that deleted students only from
    # the students table. This keeps student management and reports consistent.
    c.execute("""
        DELETE FROM attendance
        WHERE NOT EXISTS (
            SELECT 1 FROM students WHERE students.student_id = attendance.student_id
        )
    """)
    c.execute("""
        DELETE FROM scan_logs
        WHERE student_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM students WHERE students.student_id = scan_logs.student_id
          )
    """)

    conn.commit()
    conn.close()

# ─── Students ────────────────────────────────────────────────────────────────

def add_student(student_id, name, photo_path=None, face_encoding=None):
    conn = get_connection()
    try:
        enc_str = json.dumps(face_encoding) if face_encoding is not None else None
        conn.execute(
            "INSERT INTO students (student_id, name, photo_path, face_encoding) VALUES (?, ?, ?, ?)",
            (student_id, name, photo_path, enc_str)
        )
        conn.commit()
        return True, "Thêm sinh viên thành công"
    except sqlite3.IntegrityError:
        return False, "Mã sinh viên đã tồn tại"
    finally:
        conn.close()

def update_student_encoding(student_id, face_encoding, photo_path=None):
    conn = get_connection()
    enc_str = json.dumps(face_encoding)
    if photo_path:
        conn.execute(
            "UPDATE students SET face_encoding=?, photo_path=? WHERE student_id=?",
            (enc_str, photo_path, student_id)
        )
    else:
        conn.execute(
            "UPDATE students SET face_encoding=? WHERE student_id=?",
            (enc_str, student_id)
        )
    conn.commit()
    conn.close()

def update_student(student_id, name=None, photo_path=None, face_encoding=None, keep_encoding=False):
    conn = get_connection()
    fields = []
    values = []

    if name is not None:
        fields.append("name=?")
        values.append(name)
    if photo_path is not None:
        fields.append("photo_path=?")
        values.append(photo_path)
    if not keep_encoding:
        fields.append("face_encoding=?")
        values.append(json.dumps(face_encoding) if face_encoding is not None else None)

    if fields:
        values.append(student_id)
        conn.execute(
            f"UPDATE students SET {', '.join(fields)} WHERE student_id=?",
            values
        )
        conn.commit()
    conn.close()

def get_all_students():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_student(student_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_student(student_id):
    conn = get_connection()
    conn.execute("DELETE FROM scan_logs WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
    conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))
    conn.commit()
    conn.close()

def get_students_with_encoding():
    conn = get_connection()
    rows = conn.execute(
        "SELECT student_id, name, face_encoding FROM students WHERE face_encoding IS NOT NULL"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        enc = json.loads(r["face_encoding"])
        if enc is None:
            continue
        result.append({"student_id": r["student_id"], "name": r["name"], "encoding": enc})
    return result

# ─── Sessions ────────────────────────────────────────────────────────────────

def get_or_create_session(session_date, period):
    conn = get_connection()
    settings = get_all_settings()
    start_key = f"period_{period}_start"
    end_key = f"period_{period}_end"
    start_t = settings.get(start_key, "07:00")
    end_t = settings.get(end_key, "08:30")
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_date=? AND period=?",
        (session_date, period)
    ).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO sessions (session_date, period, start_time, end_time) VALUES (?, ?, ?, ?)",
            (session_date, period, start_t, end_t)
        )
        conn.commit()
    else:
        conn.execute(
            "UPDATE sessions SET start_time=?, end_time=? WHERE id=?",
            (start_t, end_t, row["id"])
        )
        conn.commit()
    row = conn.execute(
        "SELECT * FROM sessions WHERE session_date=? AND period=?",
        (session_date, period)
    ).fetchone()
    conn.close()
    return dict(row)

def get_sessions_by_date(session_date):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE session_date=? ORDER BY period",
        (session_date,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session(session_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_session_status(session_id, status):
    conn = get_connection()
    conn.execute("UPDATE sessions SET status=? WHERE id=?", (status, session_id))
    conn.commit()
    conn.close()

# ─── Attendance ───────────────────────────────────────────────────────────────

def mark_present(student_id, session_id, check_in_time=None):
    if not check_in_time:
        check_in_time = datetime.now().strftime("%H:%M:%S")
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM attendance WHERE student_id=? AND session_id=?",
        (student_id, session_id)
    ).fetchone()
    old_status = existing["status"] if existing else None
    if existing:
        first_seen = existing["check_in_time"] or check_in_time
        new_status = "half" if old_status == "half" else "present"
        conn.execute(
            """
            UPDATE attendance
            SET status=?, check_in_time=?, last_seen_time=?, scan_count=0
            WHERE student_id=? AND session_id=?
            """,
            (new_status, first_seen, check_in_time, student_id, session_id)
        )
    else:
        conn.execute(
            """
            INSERT INTO attendance (student_id, session_id, status, check_in_time, last_seen_time, scan_count)
            VALUES (?, ?, 'present', ?, ?, 0)
            """,
            (student_id, session_id, check_in_time, check_in_time)
        )
    conn.commit()
    conn.close()
    return old_status

def increment_absent_scan(student_id, session_id):
    """Tăng số lần quét không thấy mặt → nếu >= threshold thì đánh vắng"""
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM attendance WHERE student_id=? AND session_id=?",
        (student_id, session_id)
    ).fetchone()
    settings = get_all_settings()
    threshold = int(settings.get("absent_threshold", 3))

    if existing:
        new_count = existing["scan_count"] + 1
        if existing["status"] in ("present", "half", "excused"):
            conn.close()
            return existing["status"]
        new_status = "absent" if new_count >= threshold else "scanning"
        conn.execute(
            "UPDATE attendance SET scan_count=?, status=? WHERE student_id=? AND session_id=?",
            (new_count, new_status, student_id, session_id)
        )
    else:
        new_count = 1
        new_status = "absent" if new_count >= threshold else "scanning"
        conn.execute(
            "INSERT INTO attendance (student_id, session_id, status, scan_count) VALUES (?, ?, ?, ?)",
            (student_id, session_id, new_status, new_count)
        )
    conn.commit()
    conn.close()
    return new_status

def increment_present_miss(student_id, session_id):
    """Tăng số lần vắng liên tiếp cho sinh viên đã có mặt; đủ ngưỡng thì chuyển 1/2 buổi."""
    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM attendance WHERE student_id=? AND session_id=?",
        (student_id, session_id)
    ).fetchone()
    if not existing:
        conn.close()
        return None, 0

    settings = get_all_settings()
    threshold = int(settings.get("absent_threshold", 3))
    status = existing["status"]
    if status != "present":
        conn.close()
        return status, int(existing["scan_count"] or 0)

    new_count = int(existing["scan_count"] or 0) + 1
    new_status = "half" if new_count >= threshold else "present"
    conn.execute(
        "UPDATE attendance SET scan_count=?, status=? WHERE student_id=? AND session_id=?",
        (new_count, new_status, student_id, session_id)
    )
    conn.commit()
    conn.close()
    return new_status, new_count

def get_attendance_by_session(session_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.*, s.name, s.student_id as sid, s.photo_path
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.session_id = ?
        ORDER BY s.name
    """, (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_attendance_by_date(session_date):
    conn = get_connection()
    rows = conn.execute("""
        SELECT a.*, s.name, s.student_id as sid,
               se.period, se.session_date
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        JOIN sessions se ON a.session_id = se.id
        WHERE se.session_date = ?
        ORDER BY se.period, s.name
    """, (session_date,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def finalize_absent_for_session(session_id):
    """Đánh vắng tất cả sinh viên chưa có mặt khi kết thúc tiết"""
    conn = get_connection()
    students = conn.execute("SELECT student_id FROM students").fetchall()
    for s in students:
        existing = conn.execute(
            "SELECT * FROM attendance WHERE student_id=? AND session_id=?",
            (s["student_id"], session_id)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO attendance (student_id, session_id, status) VALUES (?, ?, 'absent')",
                (s["student_id"], session_id)
            )
        elif existing["status"] not in ("present", "half", "excused"):
            conn.execute(
                "UPDATE attendance SET status='absent' WHERE student_id=? AND session_id=?",
                (s["student_id"], session_id)
            )
    conn.commit()
    conn.close()

def mark_half_attendance(student_id, session_id):
    conn = get_connection()
    conn.execute(
        "UPDATE attendance SET status='half', scan_count=0 WHERE student_id=? AND session_id=?",
        (student_id, session_id)
    )
    conn.commit()
    conn.close()

def manual_update_attendance(student_id, session_id, status):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM attendance WHERE student_id=? AND session_id=?",
        (student_id, session_id)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE attendance SET status=? WHERE student_id=? AND session_id=?",
            (status, student_id, session_id)
        )
    else:
        conn.execute(
            "INSERT INTO attendance (student_id, session_id, status) VALUES (?, ?, ?)",
            (student_id, session_id, status)
        )
    conn.commit()
    conn.close()

def update_attendance_detail(student_id, session_id, status, check_in_time=None, last_seen_time=None):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM attendance WHERE student_id=? AND session_id=?",
        (student_id, session_id)
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE attendance
            SET status=?, check_in_time=?, last_seen_time=?, scan_count=0
            WHERE student_id=? AND session_id=?
            """,
            (status, check_in_time or None, last_seen_time or None, student_id, session_id)
        )
    else:
        conn.execute(
            """
            INSERT INTO attendance (student_id, session_id, status, check_in_time, last_seen_time, scan_count)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (student_id, session_id, status, check_in_time or None, last_seen_time or None)
        )
    conn.commit()
    conn.close()

def get_attendance_detail(student_id, session_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM attendance WHERE student_id=? AND session_id=?",
        (student_id, session_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

# ─── Scan Log ─────────────────────────────────────────────────────────────────

def log_scan(student_id, session_id, result):
    conn = get_connection()
    conn.execute(
        "INSERT INTO scan_logs (student_id, session_id, result) VALUES (?, ?, ?)",
        (student_id, session_id, result)
    )
    conn.commit()
    conn.close()

def log_scan_at(student_id, session_id, result, scan_time):
    conn = get_connection()
    conn.execute(
        "INSERT INTO scan_logs (student_id, session_id, scan_time, result) VALUES (?, ?, ?, ?)",
        (student_id, session_id, scan_time, result)
    )
    conn.commit()
    conn.close()

def get_scan_logs(student_id, session_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM scan_logs
        WHERE student_id=? AND session_id=? AND result!='scanning'
        ORDER BY scan_time, id
        """,
        (student_id, session_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_scan_log(log_id):
    conn = get_connection()
    conn.execute("DELETE FROM scan_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()

# ─── Settings ─────────────────────────────────────────────────────────────────

def get_all_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def save_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def save_settings_bulk(settings_dict):
    conn = get_connection()
    for k, v in settings_dict.items():
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

# ─── Stats ────────────────────────────────────────────────────────────────────

def get_monthly_stats(year, month):
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.student_id, s.name,
               COUNT(CASE WHEN a.status='present' THEN 1 END) as present_count,
               COUNT(CASE WHEN a.status='absent' THEN 1 END) as absent_count,
               COUNT(CASE WHEN a.status='half' THEN 1 END) as half_count,
               COUNT(se.id) as total_sessions
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
        LEFT JOIN sessions se ON a.session_id = se.id
            AND strftime('%Y', se.session_date) = ?
            AND strftime('%m', se.session_date) = ?
        GROUP BY s.student_id, s.name
        ORDER BY s.name
    """, (str(year), str(month).zfill(2))).fetchall()
    conn.close()
    return [dict(r) for r in rows]
