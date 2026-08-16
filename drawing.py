"""
Drawing primitives and A4 tiling engine.

All draw_* functions operate on reportlab Canvas in cm coordinates.
tile_and_save() takes a draw callback and slices the virtual canvas into A4 pages.
"""
import math
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import black, red, blue, gray
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from constants import PAGE_MARGIN_CM, PRINTABLE_W_CM, PRINTABLE_H_CM


# ============================================================
# THAI FONT SETUP
# ============================================================
# Register a TTF that supports Thai glyphs so PDF labels render correctly.
# Patterns must reference the registered names through the THAI_FONT /
# THAI_FONT_BOLD constants — never a hardcoded "Tahoma", because on a
# machine with no Thai font installed these fall back to Helvetica and a
# hardcoded name would raise KeyError deep inside reportlab instead.
_FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\tahoma.ttf",   r"C:\Windows\Fonts\tahomabd.ttf",
     "Tahoma", "Tahoma-Bold"),
    (r"C:\Windows\Fonts\leelawad.ttf", r"C:\Windows\Fonts\leelawdb.ttf",
     "Leelawadee", "Leelawadee-Bold"),
    ("/usr/share/fonts/truetype/tlwg/Loma.ttf",
     "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf",
     "Loma", "Loma-Bold"),
    ("/usr/share/fonts/truetype/tlwg/Garuda.ttf",
     "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf",
     "Garuda", "Garuda-Bold"),
    ("/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
     "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
     "NotoSansThai", "NotoSansThai-Bold"),
    ("/System/Library/Fonts/Supplemental/Thonburi.ttc", "",
     "Thonburi", "Thonburi-Bold"),
]

# Filled in by _register_thai_font(); Helvetica is the no-Thai-font fallback.
THAI_FONT = "Helvetica"
THAI_FONT_BOLD = "Helvetica-Bold"
FONT_WARNING = ""


def _register_thai_font():
    """Register the first available Thai TTF. Falls back to Helvetica.

    Returns a warning string (empty when a Thai font was found) so callers
    can tell the user why their PDF shows boxes instead of Thai text.
    """
    global THAI_FONT, THAI_FONT_BOLD, FONT_WARNING
    for reg_path, bold_path, name, bold_name in _FONT_CANDIDATES:
        if not os.path.exists(reg_path):
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, reg_path))
            if bold_path and os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            else:
                pdfmetrics.registerFont(TTFont(bold_name, reg_path))
            THAI_FONT, THAI_FONT_BOLD = name, bold_name
            FONT_WARNING = ""
            return FONT_WARNING
        except Exception:
            continue

    FONT_WARNING = (
        "ไม่พบฟอนต์ภาษาไทยในเครื่องนี้ — ข้อความไทยใน PDF จะแสดงไม่ถูกต้อง "
        "(ใช้ Helvetica แทน) ติดตั้งฟอนต์ เช่น Tahoma / Leelawadee / "
        "Noto Sans Thai แล้วสร้างใหม่อีกครั้ง"
    )
    return FONT_WARNING


_register_thai_font()


def font_warning() -> str:
    """Empty string when Thai rendering is fine, otherwise an explanation."""
    return FONT_WARNING


def grid_ref(col: int, row: int) -> str:
    """Convert (col, row) to Excel-style grid ref: (0,0) -> 'A1'."""
    return f"{chr(ord('A') + col)}{row + 1}"


# ============================================================
# DRAWING PRIMITIVES
# ============================================================
def draw_grain_line(c, x1, y1, x2, y2):
    """Double-headed arrow indicating fabric grain direction."""
    c.setLineWidth(0.6)
    c.setStrokeColor(black)
    c.line(x1 * cm, y1 * cm, x2 * cm, y2 * cm)

    angle = math.atan2(y2 - y1, x2 - x1)
    ah_len = 0.4
    ah_angle = math.pi / 7
    for ex, ey, a in [(x2, y2, angle), (x1, y1, angle + math.pi)]:
        lx = ex - ah_len * math.cos(a - ah_angle)
        ly = ey - ah_len * math.sin(a - ah_angle)
        rx = ex - ah_len * math.cos(a + ah_angle)
        ry = ey - ah_len * math.sin(a + ah_angle)
        c.line(ex * cm, ey * cm, lx * cm, ly * cm)
        c.line(ex * cm, ey * cm, rx * cm, ry * cm)

    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    c.saveState()
    c.translate(mx * cm, my * cm)
    c.rotate(math.degrees(angle))
    c.setFont(THAI_FONT, 7)
    c.drawCentredString(0, 0.15 * cm, "เส้นใย")
    c.restoreState()


def draw_notch(c, x, y, angle_deg=90, size=0.4):
    """V-shaped notch mark on a seam edge."""
    a = math.radians(angle_deg)
    tip_x = x + size * math.cos(a)
    tip_y = y + size * math.sin(a)
    wing = math.radians(25)
    lx = x + size * 0.5 * math.cos(a - wing)
    ly = y + size * 0.5 * math.sin(a - wing)
    rx = x + size * 0.5 * math.cos(a + wing)
    ry = y + size * 0.5 * math.sin(a + wing)
    c.setLineWidth(0.8)
    c.setStrokeColor(black)
    c.line(x * cm, y * cm, tip_x * cm, tip_y * cm)
    c.line(lx * cm, ly * cm, rx * cm, ry * cm)


def draw_fold_edge(c, x1, y1, x2, y2):
    """Chain-dot line indicating 'cut on fold' edge."""
    c.setStrokeColor(blue)
    c.setLineWidth(0.8)
    c.setDash([12, 3, 2, 3], 0)
    c.line(x1 * cm, y1 * cm, x2 * cm, y2 * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)

    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    angle = math.atan2(y2 - y1, x2 - x1)
    c.saveState()
    c.translate(mx * cm, my * cm)
    c.rotate(math.degrees(angle))
    c.setFillColor(blue)
    c.setFont(THAI_FONT_BOLD, 7)
    c.drawCentredString(0, 0.2 * cm, "ตัดบนรอยพับ")
    c.setFillColor(black)
    c.restoreState()


def draw_bezier_edge(c, x1, y1, cx1, cy1, cx2, cy2, x2, y2, dashed=False):
    """Cubic bezier curve (e.g. for neckline, armhole, crotch)."""
    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    if dashed:
        c.setDash([4, 3], 0)
    c.bezier(x1 * cm, y1 * cm, cx1 * cm, cy1 * cm,
             cx2 * cm, cy2 * cm, x2 * cm, y2 * cm)
    if dashed:
        c.setDash([], 0)


def draw_sa_rect_envelope(c, x, y, w, h, sa):
    """Dashed rectangular SA envelope around a piece."""
    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.rect((x - sa) * cm, (y - sa) * cm,
           (w + sa * 2) * cm, (h + sa * 2) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)


def draw_calibration(c, x=1.0, y=22.0):
    """5x5 cm test square + 10cm measurement bar. Call once on page 1."""
    c.setStrokeColor(black)
    c.setLineWidth(1.0)
    c.rect(x * cm, y * cm, 5 * cm, 5 * cm)
    c.setFont(THAI_FONT_BOLD, 10)
    c.drawCentredString((x + 2.5) * cm, (y + 2.3) * cm, "5 x 5 ซม.")
    c.setFont(THAI_FONT, 7)
    c.drawCentredString((x + 2.5) * cm, (y + 1.6) * cm,
                        "วัดสี่เหลี่ยมนี้เพื่อตรวจสอบสเกลก่อนตัด")

    bar_y = y - 1.5
    c.line(x * cm, bar_y * cm, (x + 10) * cm, bar_y * cm)
    for i in range(11):
        tick_h = 0.4 if i % 5 == 0 else 0.2
        c.line((x + i) * cm, bar_y * cm, (x + i) * cm, (bar_y - tick_h) * cm)
    c.setFont(THAI_FONT, 6)
    c.drawString(x * cm, (bar_y - 0.7) * cm, "0")
    c.drawCentredString((x + 5) * cm, (bar_y - 0.7) * cm, "5 ซม.")
    c.drawRightString((x + 10) * cm, (bar_y - 0.7) * cm, "10 ซม.")


def draw_page_header(c, title, size_label, ref, page_num, total_pages):
    """Top-of-page header bar with pattern info."""
    c.setFont(THAI_FONT_BOLD, 10)
    c.setFillColor(black)
    c.drawString(1 * cm, 28.8 * cm, f"{title}  |  ไซส์: {size_label}")
    c.setFont(THAI_FONT, 9)
    c.drawRightString(20 * cm, 28.8 * cm,
                      f"ช่อง {ref}   หน้า {page_num}/{total_pages}")
    c.setLineWidth(0.3)
    c.setStrokeColor(gray)
    c.line(1 * cm, 28.6 * cm, 20 * cm, 28.6 * cm)
    c.setStrokeColor(black)


def draw_registration_marks(c, col, row, cols, rows):
    """Triangular registration marks on page edges for aligning adjacent tiles."""
    c.setStrokeColor(red)
    c.setFillColor(red)
    c.setLineWidth(0.4)

    def tri(cx, cy, direction):
        size = 0.3
        if direction == "right":
            pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size)]
        elif direction == "left":
            pts = [(cx, cy - size), (cx - size, cy), (cx, cy + size)]
        elif direction == "up":
            pts = [(cx - size, cy), (cx, cy + size), (cx + size, cy)]
        else:
            pts = [(cx - size, cy), (cx, cy - size), (cx + size, cy)]
        p = c.beginPath()
        p.moveTo(pts[0][0] * cm, pts[0][1] * cm)
        for px, py in pts[1:]:
            p.lineTo(px * cm, py * cm)
        p.close()
        c.drawPath(p, stroke=1, fill=1)

    if col < cols - 1:
        tri(20.5, 14.85, "right")
        c.setFont(THAI_FONT, 6)
        c.drawString(20.1 * cm, 14.3 * cm, grid_ref(col + 1, row))
    if col > 0:
        tri(0.5, 14.85, "left")
        c.drawString(0.3 * cm, 14.3 * cm, grid_ref(col - 1, row))
    if row < rows - 1:
        tri(10.5, 0.5, "down")
        c.drawCentredString(10.5 * cm, 0.1 * cm, grid_ref(col, row + 1))
    if row > 0:
        tri(10.5, 29.2, "up")
        c.drawCentredString(10.5 * cm, 28.9 * cm, grid_ref(col, row - 1))

    c.setStrokeColor(black)
    c.setFillColor(black)


# ============================================================
# TILING (virtual canvas -> A4 pages)
# ============================================================
def tile_and_save(output_path, title, size_label, total_w_cm, total_h_cm,
                  draw_fn, instructions=None):
    """Render draw_fn(c) on a virtual canvas sliced across A4 pages."""
    cols = max(1, math.ceil(total_w_cm / PRINTABLE_W_CM))
    rows = max(1, math.ceil(total_h_cm / PRINTABLE_H_CM))
    total_pattern_pages = cols * rows
    total_pages = total_pattern_pages + (1 if instructions else 0)

    c = canvas.Canvas(output_path, pagesize=A4)

    if instructions:
        _draw_instruction_page(c, title, size_label, cols, rows, instructions)
        c.showPage()

    for row in range(rows):
        for col in range(cols):
            page_num = (1 if instructions else 0) + row * cols + col + 1
            ref = grid_ref(col, row)
            draw_page_header(c, title, size_label, ref, page_num, total_pages)

            if row == 0 and col == 0:
                draw_calibration(c)

            c.saveState()
            offset_x = PAGE_MARGIN_CM - col * PRINTABLE_W_CM
            offset_y = PAGE_MARGIN_CM - row * PRINTABLE_H_CM
            c.translate(offset_x * cm, offset_y * cm)

            c.saveState()
            clip = c.beginPath()
            clip.moveTo((col * PRINTABLE_W_CM) * cm,
                        (row * PRINTABLE_H_CM) * cm)
            clip.lineTo(((col + 1) * PRINTABLE_W_CM) * cm,
                        (row * PRINTABLE_H_CM) * cm)
            clip.lineTo(((col + 1) * PRINTABLE_W_CM) * cm,
                        ((row + 1) * PRINTABLE_H_CM) * cm)
            clip.lineTo((col * PRINTABLE_W_CM) * cm,
                        ((row + 1) * PRINTABLE_H_CM) * cm)
            clip.close()
            c.clipPath(clip, stroke=0, fill=0)

            draw_fn(c)

            c.restoreState()
            c.restoreState()

            draw_registration_marks(c, col, row, cols, rows)
            c.showPage()

    c.save()
    return total_pages


def _draw_instruction_page(c, title, size_label, cols, rows, instructions):
    """Cover page with title, tiling info, sewing steps."""
    c.setFont(THAI_FONT_BOLD, 18)
    c.drawString(2 * cm, 27 * cm, title)
    c.setFont(THAI_FONT, 12)
    c.drawString(2 * cm, 26 * cm, f"ไซส์: {size_label}")
    c.drawString(2 * cm, 25.3 * cm,
                 f"การต่อหน้า: {cols} คอลัมน์ x {rows} แถว "
                 f"= {cols * rows} แผ่น A4")

    c.setLineWidth(0.5)
    c.line(2 * cm, 24.8 * cm, 19 * cm, 24.8 * cm)

    c.setFont(THAI_FONT_BOLD, 12)
    c.drawString(2 * cm, 24 * cm, "วิธีประกอบและเย็บ")
    c.setFont(THAI_FONT, 10)
    y = 23.2
    for line in instructions:
        if y < 3:
            c.showPage()
            y = 27
        c.drawString(2 * cm, y * cm, line)
        y -= 0.55

    c.setFont(THAI_FONT, 9)
    c.drawString(2 * cm, 1.5 * cm,
                 "พิมพ์ที่สเกล 100% (ห้ามใช้ 'fit to page') "
                 "ตรวจสอบสี่เหลี่ยม 5x5 ซม. ในหน้า 1 ก่อนเริ่มตัด")
