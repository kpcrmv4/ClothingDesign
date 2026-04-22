"""
Drawing primitives and A4 tiling engine.

All draw_* functions operate on reportlab Canvas in cm coordinates.
tile_and_save() takes a draw callback and slices the virtual canvas into A4 pages.
"""
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import black, red, blue, gray

from constants import PAGE_MARGIN_CM, PRINTABLE_W_CM, PRINTABLE_H_CM


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
    c.setFont("Helvetica", 7)
    c.drawCentredString(0, 0.15 * cm, "GRAIN")
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
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(0, 0.2 * cm, "CUT ON FOLD")
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
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString((x + 2.5) * cm, (y + 2.3) * cm, "5 x 5 cm")
    c.setFont("Helvetica", 7)
    c.drawCentredString((x + 2.5) * cm, (y + 1.6) * cm,
                        "Measure this square to verify print scale.")

    bar_y = y - 1.5
    c.line(x * cm, bar_y * cm, (x + 10) * cm, bar_y * cm)
    for i in range(11):
        tick_h = 0.4 if i % 5 == 0 else 0.2
        c.line((x + i) * cm, bar_y * cm, (x + i) * cm, (bar_y - tick_h) * cm)
    c.setFont("Helvetica", 6)
    c.drawString(x * cm, (bar_y - 0.7) * cm, "0")
    c.drawCentredString((x + 5) * cm, (bar_y - 0.7) * cm, "5 cm")
    c.drawRightString((x + 10) * cm, (bar_y - 0.7) * cm, "10 cm")


def draw_page_header(c, title, size_label, ref, page_num, total_pages):
    """Top-of-page header bar with pattern info."""
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(black)
    c.drawString(1 * cm, 28.8 * cm, f"{title}  |  Size: {size_label}")
    c.setFont("Helvetica", 9)
    c.drawRightString(20 * cm, 28.8 * cm,
                      f"Grid {ref}   Page {page_num}/{total_pages}")
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
        c.setFont("Helvetica", 6)
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
    """
    Render draw_fn(c) on a virtual canvas sized (total_w_cm x total_h_cm),
    sliced across A4 pages. draw_fn uses cm coordinates.
    """
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
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2 * cm, 27 * cm, title)
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, 26 * cm, f"Size: {size_label}")
    c.drawString(2 * cm, 25.3 * cm,
                 f"Tiling: {cols} columns x {rows} rows "
                 f"= {cols * rows} A4 sheets")

    c.setLineWidth(0.5)
    c.line(2 * cm, 24.8 * cm, 19 * cm, 24.8 * cm)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, 24 * cm, "Assembly & sewing notes")
    c.setFont("Helvetica", 10)
    y = 23.2
    for line in instructions:
        if y < 3:
            c.showPage()
            y = 27
        c.drawString(2 * cm, y * cm, line)
        y -= 0.55

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2 * cm, 1.5 * cm,
                 "Print at 100% scale (no 'fit to page'). "
                 "Verify the 5x5cm square on page 1 before cutting.")
