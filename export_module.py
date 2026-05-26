import os
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference
from datetime import datetime, date
import database as db

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def _border(style="thin"):
    s = Side(style=style)
    return Border(left=s, right=s, top=s, bottom=s)

def _header_fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

STATUS_VI = {
    "present": "Có mặt",
    "absent": "Vắng",
    "half": "Học 1/2",
    "scanning": "Đang quét",
}

STATUS_COLOR = {
    "present": "C6EFCE",  # xanh lá nhạt
    "absent": "FFC7CE",   # đỏ nhạt
    "half": "FFEB9C",     # vàng nhạt
    "scanning": "BDD7EE", # xanh dương nhạt
}


def export_by_date(target_date: str) -> str:
    """Xuất điểm danh theo ngày ra file Excel"""
    settings = db.get_all_settings()
    class_name = settings.get("class_name", "Lớp học")
    total_periods = int(settings.get("total_periods", 3))

    sessions = db.get_sessions_by_date(target_date)
    if not sessions:
        return None, "Không có buổi học nào trong ngày này"

    students = db.get_all_students()
    if not students:
        return None, "Chưa có sinh viên nào"

    # Map session_id by period
    session_map = {s["period"]: s for s in sessions}

    wb = Workbook()
    ws = wb.active
    ws.title = f"Điểm danh {target_date}"

    # ── Header Block ──────────────────────────────────────────────────────────
    ws.merge_cells("A1:H1")
    ws["A1"] = f"📋 BẢNG ĐIỂM DANH - {class_name.upper()}"
    ws["A1"].font = Font(name="Calibri", bold=True, size=16, color="FFFFFF")
    ws["A1"].fill = _header_fill("1A3C5E")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:H2")
    ws["A2"] = f"Ngày: {_format_date_vi(target_date)}   |   Xuất lúc: {datetime.now().strftime('%H:%M %d/%m/%Y')}"
    ws["A2"].font = Font(name="Calibri", size=11, color="FFFFFF", italic=True)
    ws["A2"].fill = _header_fill("2E6DA4")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    # ── Column Headers ────────────────────────────────────────────────────────
    headers = ["STT", "Mã SV", "Họ và Tên"]
    for p in range(1, total_periods + 1):
        s = session_map.get(p)
        time_str = ""
        if s:
            time_str = f"\n({s['start_time']}–{s['end_time']})"
        headers.append(f"Tiết {p}{time_str}")
    headers += ["Có mặt", "Vắng", "Học 1/2", "Tỉ lệ (%)"]

    col_count = len(headers)
    # Extend merge if needed
    ws.merge_cells(f"A1:{get_column_letter(col_count)}1")
    ws.merge_cells(f"A2:{get_column_letter(col_count)}2")

    row3 = ws.row_dimensions[3]
    row3.height = 40
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=h)
        cell.font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
        cell.fill = _header_fill("34495E")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = _border()

    # ── Data Rows ─────────────────────────────────────────────────────────────
    for row_idx, student in enumerate(students, start=1):
        sid = student["student_id"]
        data_row = [row_idx, sid, student["name"]]
        present_cnt = 0
        absent_cnt = 0
        half_cnt = 0

        for p in range(1, total_periods + 1):
            sess = session_map.get(p)
            if sess:
                att_list = db.get_attendance_by_session(sess["id"])
                att = next((a for a in att_list if a["student_id"] == sid), None)
                status = att["status"] if att else "absent"
            else:
                status = "-"
            data_row.append(STATUS_VI.get(status, "-"))
            if status == "present":
                present_cnt += 1
            elif status == "absent":
                absent_cnt += 1
            elif status == "half":
                half_cnt += 1

        total = present_cnt + absent_cnt + half_cnt + (0.5 * half_cnt)
        ratio = round((present_cnt + half_cnt * 0.5) / total_periods * 100, 1) if total_periods > 0 else 0
        data_row += [present_cnt, absent_cnt, half_cnt, f"{ratio}%"]

        excel_row = row_idx + 3
        ws.row_dimensions[excel_row].height = 20
        fill_color = "F0F4F8" if row_idx % 2 == 0 else "FFFFFF"

        for col_idx, val in enumerate(data_row, start=1):
            cell = ws.cell(row=excel_row, column=col_idx, value=val)
            cell.font = Font(name="Calibri", size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = _border("thin")

            # Màu ô trạng thái tiết học
            col_is_period = 3 < col_idx <= 3 + total_periods
            if col_is_period:
                for stat_key, stat_vi in STATUS_VI.items():
                    if val == stat_vi:
                        cell.fill = PatternFill("solid", fgColor=STATUS_COLOR[stat_key])
                        break
            elif col_idx > 3 + total_periods:
                cell.fill = PatternFill("solid", fgColor=fill_color)
            else:
                cell.fill = PatternFill("solid", fgColor=fill_color)

            # Tỉ lệ màu
            if col_idx == col_count:
                try:
                    pct = float(str(val).replace("%", ""))
                    if pct >= 80:
                        cell.font = Font(name="Calibri", size=10, bold=True, color="276221")
                    elif pct >= 50:
                        cell.font = Font(name="Calibri", size=10, bold=True, color="9C5700")
                    else:
                        cell.font = Font(name="Calibri", size=10, bold=True, color="9C0006")
                except:
                    pass

    # ── Summary Row ───────────────────────────────────────────────────────────
    summary_row = len(students) + 4
    ws.row_dimensions[summary_row].height = 22
    ws.cell(summary_row, 1, "TỔNG").font = Font(bold=True, color="FFFFFF")
    ws.merge_cells(f"A{summary_row}:C{summary_row}")
    ws[f"A{summary_row}"].fill = _header_fill("1A3C5E")
    ws[f"A{summary_row}"].alignment = Alignment(horizontal="center", vertical="center")
    ws[f"A{summary_row}"].font = Font(name="Calibri", bold=True, color="FFFFFF")

    for p_col in range(4, 4 + total_periods):
        col_data = [ws.cell(r, p_col).value for r in range(4, 4 + len(students))]
        present_total = col_data.count("Có mặt")
        ws.cell(summary_row, p_col, f"{present_total}/{len(students)}").font = Font(bold=True)
        ws.cell(summary_row, p_col).alignment = Alignment(horizontal="center")
        ws.cell(summary_row, p_col).fill = _header_fill("BDD7EE")
        ws.cell(summary_row, p_col).border = _border()

    # ── Column Widths ─────────────────────────────────────────────────────────
    col_widths = [6, 14, 28] + [14] * total_periods + [10, 8, 10, 10]
    for i, w in enumerate(col_widths, start=1):
        if i <= col_count:
            ws.column_dimensions[get_column_letter(i)].width = w

    # ── Chart Sheet ───────────────────────────────────────────────────────────
    _add_summary_chart(wb, students, sessions, total_periods, target_date)

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_row = summary_row + 2
    ws.cell(legend_row, 1, "CHÚ THÍCH:").font = Font(bold=True, size=10)
    for i, (stat, color) in enumerate(STATUS_COLOR.items()):
        r = legend_row + i
        ws.cell(r, 1, STATUS_VI[stat])
        ws.cell(r, 1).fill = PatternFill("solid", fgColor=color)
        ws.cell(r, 1).border = _border()
        ws.cell(r, 1).alignment = Alignment(horizontal="center")

    filename = f"diemdanh_{target_date}.xlsx"
    filepath = os.path.join(EXPORT_DIR, filename)
    wb.save(filepath)
    return filepath, f"Xuất thành công: {filename}"


def _add_summary_chart(wb, students, sessions, total_periods, target_date):
    """Thêm sheet biểu đồ thống kê"""
    ws2 = wb.create_sheet("📊 Thống kê")
    ws2["A1"] = "Sinh viên"
    ws2["B1"] = "Có mặt"
    ws2["C1"] = "Vắng"
    ws2["D1"] = "Học 1/2"
    ws2["A1"].font = Font(bold=True)
    ws2["B1"].font = Font(bold=True)
    ws2["C1"].font = Font(bold=True)
    ws2["D1"].font = Font(bold=True)

    session_map = {s["period"]: s for s in sessions}

    for row_idx, student in enumerate(students, start=2):
        sid = student["student_id"]
        ws2.cell(row_idx, 1, student["name"])
        p = a = h = 0
        for period in range(1, total_periods + 1):
            sess = session_map.get(period)
            if sess:
                att_list = db.get_attendance_by_session(sess["id"])
                att = next((x for x in att_list if x["student_id"] == sid), None)
                status = att["status"] if att else "absent"
                if status == "present": p += 1
                elif status == "absent": a += 1
                elif status == "half": h += 1
        ws2.cell(row_idx, 2, p)
        ws2.cell(row_idx, 3, a)
        ws2.cell(row_idx, 4, h)

    if len(students) > 0:
        chart = BarChart()
        chart.type = "col"
        chart.title = f"Thống kê điểm danh {target_date}"
        chart.y_axis.title = "Số tiết"
        chart.x_axis.title = "Sinh viên"
        chart.style = 10
        chart.width = 20
        chart.height = 14

        data = Reference(ws2, min_col=2, max_col=4, min_row=1, max_row=len(students)+1)
        cats = Reference(ws2, min_col=1, min_row=2, max_row=len(students)+1)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.series[0].graphicalProperties.solidFill = "2ECC71"
        chart.series[1].graphicalProperties.solidFill = "E74C3C"
        if len(chart.series) > 2:
            chart.series[2].graphicalProperties.solidFill = "F39C12"

        ws2.add_chart(chart, "F2")


def export_monthly_report(year: int, month: int) -> str:
    """Xuất báo cáo tháng"""
    stats = db.get_monthly_stats(year, month)
    settings = db.get_all_settings()
    class_name = settings.get("class_name", "Lớp học")

    wb = Workbook()
    ws = wb.active
    ws.title = f"Báo cáo T{month}/{year}"

    ws.merge_cells("A1:G1")
    ws["A1"] = f"BÁO CÁO THÁNG {month}/{year} - {class_name.upper()}"
    ws["A1"].font = Font(name="Calibri", bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = _header_fill("1A3C5E")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    headers = ["STT", "Mã SV", "Họ và Tên", "Có mặt", "Vắng", "Học 1/2", "Tỉ lệ (%)"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(2, col, h)
        cell.font = Font(bold=True, color="FFFFFF", name="Calibri")
        cell.fill = _header_fill("34495E")
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _border()

    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 28
    for col in "DEFG":
        ws.column_dimensions[col].width = 12

    for row_idx, s in enumerate(stats, 1):
        total = s["total_sessions"] if s["total_sessions"] else 1
        ratio = round((s["present_count"] + s["half_count"] * 0.5) / total * 100, 1)
        row_data = [row_idx, s["student_id"], s["name"],
                    s["present_count"], s["absent_count"], s["half_count"], f"{ratio}%"]
        fill = "F0F4F8" if row_idx % 2 == 0 else "FFFFFF"
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row_idx + 2, col, val)
            cell.font = Font(name="Calibri", size=10)
            cell.alignment = Alignment(horizontal="center")
            cell.border = _border()
            cell.fill = PatternFill("solid", fgColor=fill)

    filename = f"baocao_thang_{month:02d}_{year}.xlsx"
    filepath = os.path.join(EXPORT_DIR, filename)
    wb.save(filepath)
    return filepath, f"Xuất thành công: {filename}"


def _format_date_vi(date_str):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        days_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        return f"{days_vi[d.weekday()]}, {d.day:02d}/{d.month:02d}/{d.year}"
    except:
        return date_str
