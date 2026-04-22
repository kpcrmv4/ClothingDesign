"""
Baby Fashion Engine - MCP Server for children's clothing patterns (0-24m).

Generates printable A4-tiled PDF sewing patterns with professional markers
(grain lines, notches, fold edges, registration grid) and curved edges for
necklines, armholes, and crotch seams.

Run:
    pip install mcp reportlab
    python baby_pattern_server.py

Register in claude_desktop_config.json to use from Claude Desktop.
"""

from mcp.server.fastmcp import FastMCP
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import black, red, blue, gray
import os
import math

mcp = FastMCP("BabyFashionEngine_Complete")

# ============================================================
# SIZE CHART (all measurements in cm)
# ============================================================
SIZE_CHART = {
    "0-3m":  {"chest": 41, "length": 30, "waist": 42, "hip": 44, "back_w": 18,
              "shoulder": 6.5, "neck_circ": 23, "arm_len": 16, "rise_f": 14,
              "rise_b": 16, "head": 38, "strap_len": 16, "ruffle_h": 6},
    "3-6m":  {"chest": 43, "length": 33, "waist": 44, "hip": 46, "back_w": 19,
              "shoulder": 7.0, "neck_circ": 24, "arm_len": 18, "rise_f": 15,
              "rise_b": 17, "head": 42, "strap_len": 18, "ruffle_h": 7},
    "6-9m":  {"chest": 45, "length": 36, "waist": 46, "hip": 48, "back_w": 20,
              "shoulder": 7.5, "neck_circ": 25, "arm_len": 20, "rise_f": 16,
              "rise_b": 18, "head": 44, "strap_len": 20, "ruffle_h": 8},
    "9-12m": {"chest": 47, "length": 39, "waist": 48, "hip": 50, "back_w": 21,
              "shoulder": 8.0, "neck_circ": 26, "arm_len": 22, "rise_f": 17,
              "rise_b": 19, "head": 46, "strap_len": 22, "ruffle_h": 9},
    "12-18m":{"chest": 49, "length": 42, "waist": 50, "hip": 52, "back_w": 22,
              "shoulder": 8.5, "neck_circ": 27, "arm_len": 24, "rise_f": 18,
              "rise_b": 20, "head": 48, "strap_len": 24, "ruffle_h": 10},
    "18-24m":{"chest": 51, "length": 45, "waist": 52, "hip": 54, "back_w": 23,
              "shoulder": 9.0, "neck_circ": 28, "arm_len": 26, "rise_f": 19,
              "rise_b": 21, "head": 49, "strap_len": 26, "ruffle_h": 11},
}

# ============================================================
# PAGE GEOMETRY
# ============================================================
PAGE_MARGIN_CM = 1.0
PRINTABLE_W_CM = 19.0   # A4 width 21cm - 2cm total margins
PRINTABLE_H_CM = 27.7   # A4 height 29.7cm - 2cm total margins


def _grid_ref(col: int, row: int) -> str:
    """Convert (col, row) to Excel-style grid ref: (0,0) -> 'A1', (1,2) -> 'B3'."""
    return f"{chr(ord('A') + col)}{row + 1}"


# ============================================================
# DRAWING PRIMITIVES (operate in cm on virtual canvas)
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
    """V-shaped notch mark on a seam edge. angle_deg = direction notch points into piece."""
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
        c.setDash(4, 3)
    c.bezier(x1 * cm, y1 * cm, cx1 * cm, cy1 * cm,
             cx2 * cm, cy2 * cm, x2 * cm, y2 * cm)
    if dashed:
        c.setDash(1, 0)


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


def draw_page_header(c, title, size_label, grid_ref, page_num, total_pages):
    """Top-of-page header bar with pattern info."""
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(black)
    c.drawString(1 * cm, 28.8 * cm, f"{title}  |  Size: {size_label}")
    c.setFont("Helvetica", 9)
    c.drawRightString(20 * cm, 28.8 * cm,
                      f"Grid {grid_ref}   Page {page_num}/{total_pages}")
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
        c.drawString(20.1 * cm, 14.3 * cm, _grid_ref(col + 1, row))
    if col > 0:
        tri(0.5, 14.85, "left")
        c.drawString(0.3 * cm, 14.3 * cm, _grid_ref(col - 1, row))
    if row < rows - 1:
        tri(10.5, 0.5, "down")
        c.drawCentredString(10.5 * cm, 0.1 * cm, _grid_ref(col, row + 1))
    if row > 0:
        tri(10.5, 29.2, "up")
        c.drawCentredString(10.5 * cm, 28.9 * cm, _grid_ref(col, row - 1))

    c.setStrokeColor(black)
    c.setFillColor(black)


# ============================================================
# TILING (virtual canvas -> A4 pages)
# ============================================================
def tile_and_save(output_path, title, size_label, total_w_cm, total_h_cm,
                  draw_fn, instructions=None):
    """
    Render `draw_fn(c)` on a virtual canvas sized (total_w_cm x total_h_cm),
    sliced across A4 pages. `draw_fn` should use cm coordinates.
    If `instructions` (list of str) is given, prepend a cover page.
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
            grid_ref = _grid_ref(col, row)
            draw_page_header(c, title, size_label, grid_ref, page_num, total_pages)

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
    """Cover page: title, fabric info, sewing steps."""
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


# ============================================================
# PATTERN TOOLS
# ============================================================
@mcp.tool()
def generate_full_dress_pattern(size_label: str, seam_allowance: float = 1.0) -> str:
    """
    Sleeveless baby dress with curved neckline/armhole, shoulder straps, and
    gathered ruffle hem. Bodice is cut on fold at center front/back.

    Pieces: 1 bodice (cut 2 on fold), 2 straps (cut 2), 1 ruffle (cut 2, gather).
    """
    if size_label not in SIZE_CHART:
        return f"Error: size '{size_label}' not found. Available: {list(SIZE_CHART)}"

    spec = SIZE_CHART[size_label]

    bodice_w = spec["chest"] / 4 + 2.0
    bodice_h = spec["length"]
    neck_drop = 3.0
    neck_width = spec["neck_circ"] / 6
    armhole_drop = 5.5
    armhole_width = 2.5
    shoulder_w = spec["shoulder"]

    strap_w = 3.0
    strap_h = spec["strap_len"]

    ruffle_w = bodice_w * 2 * 1.5
    ruffle_h = spec["ruffle_h"]

    sa = seam_allowance
    gap = 2.0

    total_w = max(bodice_w, ruffle_w, strap_w) + sa * 2 + 2
    total_h = (bodice_h + strap_h + ruffle_h) + sa * 6 + gap * 2 + 4

    def draw(c):
        y_cursor = 2.0

        # --- Bodice (cut 2 on fold at left edge) ---
        bx, by = 2.0, y_cursor
        _draw_dress_bodice(c, bx, by, bodice_w, bodice_h,
                           neck_width, neck_drop, shoulder_w,
                           armhole_width, armhole_drop, sa)
        c.setFont("Helvetica-Bold", 10)
        c.drawString((bx + 0.3) * cm, (by + bodice_h - 1) * cm,
                     "1. Bodice  -  Cut 2 on fold")
        c.setFont("Helvetica", 8)
        c.drawString((bx + 0.3) * cm, (by + bodice_h - 1.7) * cm,
                     f"Finished: {bodice_w:.1f} x {bodice_h:.1f} cm")
        draw_grain_line(c, bx + bodice_w * 0.7, by + 2,
                        bx + bodice_w * 0.7, by + bodice_h - 2)
        draw_fold_edge(c, bx, by, bx, by + bodice_h)
        draw_notch(c, bx + bodice_w, by + bodice_h * 0.5, angle_deg=180)

        y_cursor = by + bodice_h + sa * 2 + gap

        # --- Strap ---
        sx, sy = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.rect(sx * cm, sy * cm, strap_w * cm, strap_h * cm)
        c.setDash(4, 3)
        c.setLineWidth(0.5)
        c.rect((sx - sa) * cm, (sy - sa) * cm,
               (strap_w + sa * 2) * cm, (strap_h + sa * 2) * cm)
        c.setDash(1, 0)
        c.setFont("Helvetica-Bold", 9)
        c.drawString((sx + 0.2) * cm, (sy + strap_h - 0.7) * cm,
                     "2. Strap - Cut 2")
        c.setFont("Helvetica", 7)
        c.drawString((sx + 0.2) * cm, (sy + strap_h - 1.3) * cm,
                     f"{strap_w:.1f} x {strap_h:.1f} cm")
        draw_grain_line(c, sx + strap_w / 2, sy + 1,
                        sx + strap_w / 2, sy + strap_h - 1)

        y_cursor = sy + strap_h + sa * 2 + gap

        # --- Ruffle ---
        rx, ry = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.rect(rx * cm, ry * cm, ruffle_w * cm, ruffle_h * cm)
        c.setDash(4, 3)
        c.setLineWidth(0.5)
        c.rect((rx - sa) * cm, (ry - sa) * cm,
               (ruffle_w + sa * 2) * cm, (ruffle_h + sa * 2) * cm)
        c.setDash(1, 0)
        c.setFont("Helvetica-Bold", 9)
        c.drawString((rx + 0.2) * cm, (ry + ruffle_h - 0.7) * cm,
                     "3. Ruffle - Cut 2 (gather top edge)")
        c.setFont("Helvetica", 7)
        c.drawString((rx + 0.2) * cm, (ry + ruffle_h - 1.3) * cm,
                     f"{ruffle_w:.1f} x {ruffle_h:.1f} cm  (1.5x hem width)")
        draw_grain_line(c, rx + ruffle_w / 2 - 2, ry + ruffle_h / 2,
                        rx + ruffle_w / 2 + 2, ry + ruffle_h / 2)
        for frac in (0.25, 0.5, 0.75):
            draw_notch(c, rx + ruffle_w * frac, ry + ruffle_h, angle_deg=270)

    instructions = [
        f"BABY DRESS - {size_label}",
        "",
        "Materials:",
        "  - Light cotton or linen, approx. 0.6-0.8 m of 115cm fabric",
        "  - Matching thread, 2-3 small buttons or snaps (optional)",
        "",
        "Legend:",
        "  Solid line    = cutting line",
        "  Dashed line   = seam allowance (add when cutting)",
        "  Blue chain    = cut on fold, do not cut this edge",
        "  V-notch       = match these marks across pieces",
        "  Arrow 'GRAIN' = align with fabric lengthwise grain",
        "",
        "Sewing order:",
        "  1. Cut 2 bodices on fold (front + back)",
        "  2. Cut 2 straps",
        "  3. Cut 2 ruffles",
        "  4. Sew bodice shoulder seams (front to back at strap points)",
        "  5. Fold straps lengthwise RST, sew, turn, press",
        "  6. Attach straps between front + back at shoulder",
        "  7. Sew side seams of bodice",
        "  8. Gather ruffle top edge to match bodice hem",
        "  9. Attach ruffle to bodice hem, RST",
        " 10. Hem ruffle bottom with narrow rolled hem",
        " 11. Finish neckline + armholes with bias binding",
        "",
        f"Seam allowance included: {seam_allowance} cm on all edges",
    ]

    file_path = os.path.abspath(f"dress_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "Baby Dress", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Dress pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Bodice: {bodice_w:.1f}x{bodice_h:.1f} cm  |  "
            f"Ruffle: {ruffle_w:.1f}x{ruffle_h:.1f} cm")


def _draw_dress_bodice(c, x, y, w, h, neck_w, neck_drop, shoulder_w,
                        arm_w, arm_drop, sa):
    """Draw one bodice piece with curved neckline and armhole. Left edge = fold."""
    # corners
    bl = (x, y)
    br = (x + w, y)
    tr = (x + w, y + h)
    tl = (x, y + h)

    # neckline on top edge starts at (x, y+h - neck_drop) curves to (x + neck_w, y+h)
    neck_start = (x, y + h - neck_drop)
    neck_end = (x + neck_w, y + h)

    # armhole: from shoulder_inner (x + shoulder_w, y+h) curves down to underarm
    # simplification: treat shoulder_w as full shoulder on the piece
    shoulder_tip = (x + neck_w + shoulder_w, y + h)
    # clip shoulder_tip to within w
    shoulder_tip = (min(shoulder_tip[0], x + w - 0.5), y + h)
    underarm = (x + w, y + h - arm_drop)

    c.setLineWidth(1.3)
    c.setStrokeColor(black)
    # side seam (right)
    c.line(br[0] * cm, br[1] * cm, underarm[0] * cm, underarm[1] * cm)
    # bottom hem
    c.line(bl[0] * cm, bl[1] * cm, br[0] * cm, br[1] * cm)
    # shoulder
    c.line(neck_end[0] * cm, neck_end[1] * cm,
           shoulder_tip[0] * cm, shoulder_tip[1] * cm)

    # neckline curve (scooped)
    draw_bezier_edge(c,
                     neck_start[0], neck_start[1],
                     neck_start[0] + neck_w * 0.3, neck_start[1],
                     neck_end[0], neck_end[1] - neck_drop * 0.3,
                     neck_end[0], neck_end[1])

    # armhole curve (scye)
    draw_bezier_edge(c,
                     shoulder_tip[0], shoulder_tip[1],
                     shoulder_tip[0] + (underarm[0] - shoulder_tip[0]) * 0.2,
                     shoulder_tip[1] - arm_drop * 0.4,
                     underarm[0] - arm_w * 0.5,
                     underarm[1] + arm_drop * 0.3,
                     underarm[0], underarm[1])

    # seam allowance outline (offset simplified: rectangular envelope minus fold edge)
    c.setDash(4, 3)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    # right side + bottom + top envelope, skip fold edge
    c.line(x * cm, (y - sa) * cm, (x + w + sa) * cm, (y - sa) * cm)
    c.line((x + w + sa) * cm, (y - sa) * cm, (x + w + sa) * cm, (y + h + sa) * cm)
    c.line((x + w + sa) * cm, (y + h + sa) * cm, x * cm, (y + h + sa) * cm)
    c.setDash(1, 0)
    c.setStrokeColor(black)


@mcp.tool()
def generate_bib_pattern(size_label: str, seam_allowance: float = 0.7) -> str:
    """
    Classic drool bib with keyhole neck and rounded body.
    One pattern piece, cut 2 (front + back lining).
    Great beginner project.
    """
    if size_label not in SIZE_CHART:
        return f"Error: size '{size_label}' not found. Available: {list(SIZE_CHART)}"

    spec = SIZE_CHART[size_label]

    body_w = spec["neck_circ"] * 0.9
    body_h = body_w * 1.1
    neck_r = spec["neck_circ"] / (2 * math.pi) + 0.5
    opening_w = neck_r * 0.8

    sa = seam_allowance
    total_w = body_w + sa * 2 + 2
    total_h = body_h + sa * 2 + 3

    def draw(c):
        cx = 1.0 + sa + body_w / 2
        bottom_y = 1.0 + sa
        top_y = bottom_y + body_h

        left_x = cx - body_w / 2
        right_x = cx + body_w / 2

        c.setStrokeColor(black)
        c.setLineWidth(1.3)

        # bottom curve - scalloped rounded bottom
        draw_bezier_edge(c,
                         left_x, bottom_y + body_h * 0.3,
                         left_x, bottom_y,
                         right_x, bottom_y,
                         right_x, bottom_y + body_h * 0.3)

        # side curves going up to shoulder "tabs"
        draw_bezier_edge(c,
                         left_x, bottom_y + body_h * 0.3,
                         left_x - 0.5, bottom_y + body_h * 0.6,
                         left_x + 1.0, top_y - 1.5,
                         cx - opening_w - 1.5, top_y - 1.0)
        draw_bezier_edge(c,
                         right_x, bottom_y + body_h * 0.3,
                         right_x + 0.5, bottom_y + body_h * 0.6,
                         right_x - 1.0, top_y - 1.5,
                         cx + opening_w + 1.5, top_y - 1.0)

        # top curve + neck opening (keyhole)
        draw_bezier_edge(c,
                         cx - opening_w - 1.5, top_y - 1.0,
                         cx - opening_w, top_y,
                         cx - opening_w, top_y,
                         cx - opening_w, top_y - neck_r * 0.3)
        # left side of neck hole
        draw_bezier_edge(c,
                         cx - opening_w, top_y - neck_r * 0.3,
                         cx - opening_w * 0.6, top_y - neck_r * 1.4,
                         cx - neck_r * 0.9, top_y - neck_r * 1.8,
                         cx, top_y - neck_r * 1.8)
        # right side of neck hole
        draw_bezier_edge(c,
                         cx, top_y - neck_r * 1.8,
                         cx + neck_r * 0.9, top_y - neck_r * 1.8,
                         cx + opening_w * 0.6, top_y - neck_r * 1.4,
                         cx + opening_w, top_y - neck_r * 0.3)
        # right shoulder top
        draw_bezier_edge(c,
                         cx + opening_w, top_y - neck_r * 0.3,
                         cx + opening_w, top_y,
                         cx + opening_w, top_y,
                         cx + opening_w + 1.5, top_y - 1.0)

        # keyhole slit (back opening for snap)
        c.setDash(3, 2)
        c.line(cx * cm, (top_y - neck_r * 1.8) * cm,
               cx * cm, (top_y - neck_r * 1.8 - 2.0) * cm)
        c.setDash(1, 0)

        # labels
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(cx * cm, (bottom_y + body_h * 0.55) * cm,
                            "Bib - Cut 2")
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx * cm, (bottom_y + body_h * 0.48) * cm,
                            f"Size {size_label}")
        c.drawCentredString(cx * cm, (bottom_y + body_h * 0.42) * cm,
                            "1 main fabric + 1 absorbent backing (terry)")

        draw_grain_line(c, cx, bottom_y + body_h * 0.1,
                        cx, bottom_y + body_h * 0.25)

        # snap placement markers
        c.setFillColor(red)
        c.circle(cx * cm, (top_y - neck_r * 1.8 - 2.2) * cm, 0.15 * cm, fill=1)
        c.setFillColor(black)
        c.setFont("Helvetica", 7)
        c.setFillColor(red)
        c.drawString((cx + 0.3) * cm, (top_y - neck_r * 1.8 - 2.3) * cm,
                     "snap")
        c.setFillColor(black)

    instructions = [
        f"BABY BIB - {size_label}",
        "",
        "Materials:",
        "  - 1 piece cotton or quilting fabric (front)",
        "  - 1 piece terry / bamboo / fleece (absorbent backing)",
        "  - 1 KAM snap set OR 20 cm velcro",
        "  - Approx. 25 x 25 cm of each fabric",
        "",
        "Sewing order:",
        "  1. Cut 1 front + 1 backing using the pattern",
        "  2. Place RST (right sides together)",
        "  3. Sew around all edges leaving a 5cm gap at bottom",
        "  4. Clip curves, turn right side out through gap",
        "  5. Press flat, topstitch 3mm from edge (closes gap)",
        "  6. Install snap at back neck slit",
        "",
        f"Seam allowance included: {seam_allowance} cm",
        "Tip: use a smaller SA (0.5-0.7cm) for easier curve sewing.",
    ]

    file_path = os.path.abspath(f"bib_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "Baby Bib", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Bib pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Body: {body_w:.1f} x {body_h:.1f} cm")


@mcp.tool()
def generate_bloomers_pattern(size_label: str, seam_allowance: float = 1.0) -> str:
    """
    Elastic-waist bloomers / diaper cover with curved crotch seam.
    One pattern piece (cut 2), includes front and back in one piece mirrored at side.
    Elastic casings at waist and leg openings.
    """
    if size_label not in SIZE_CHART:
        return f"Error: size '{size_label}' not found. Available: {list(SIZE_CHART)}"

    spec = SIZE_CHART[size_label]

    waist_half = spec["waist"] / 2 + 4.0
    hip_half = spec["hip"] / 2 + 4.0
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
    leg_opening = spec["hip"] / 4 + 3.0
    inseam = 3.0

    sa = seam_allowance
    total_w = hip_half + sa * 2 + 2
    total_h = rise + inseam + sa * 2 + 3

    def draw(c):
        x0 = 1.0 + sa
        y0 = 1.0 + sa + inseam

        # key points
        waist_l = (x0, y0 + rise)
        waist_r = (x0 + waist_half, y0 + rise)
        hip_l = (x0, y0 + rise * 0.3)
        hip_r = (x0 + hip_half, y0 + rise * 0.3)
        crotch = (x0 + waist_half * 0.15, y0)
        leg_inner = (x0 + waist_half * 0.15, y0 - inseam)
        leg_outer = (x0 + hip_half, y0 + rise * 0.15)

        c.setStrokeColor(black)
        c.setLineWidth(1.3)

        # waist edge (straight, fold at left)
        c.line(waist_l[0] * cm, waist_l[1] * cm,
               waist_r[0] * cm, waist_r[1] * cm)

        # side seam from waist down to hip to leg
        draw_bezier_edge(c,
                         waist_r[0], waist_r[1],
                         waist_r[0] + 0.3, waist_r[1] - rise * 0.3,
                         hip_r[0], hip_r[1] + rise * 0.1,
                         hip_r[0], hip_r[1])
        # continue to leg opening outer
        c.line(hip_r[0] * cm, hip_r[1] * cm,
               leg_outer[0] * cm, leg_outer[1] * cm)

        # leg opening curve (outer to inner crotch)
        draw_bezier_edge(c,
                         leg_outer[0], leg_outer[1],
                         leg_outer[0] - 3, leg_outer[1] - 1.5,
                         leg_inner[0] + 3, leg_inner[1] + 0.5,
                         leg_inner[0], leg_inner[1])

        # inseam (short, vertical)
        c.line(leg_inner[0] * cm, leg_inner[1] * cm,
               crotch[0] * cm, crotch[1] * cm)

        # crotch curve to center-front/back fold
        draw_bezier_edge(c,
                         crotch[0], crotch[1],
                         crotch[0] - 1.0, crotch[1] + 0.5,
                         waist_l[0] + 0.5, waist_l[1] - rise * 0.6,
                         waist_l[0], waist_l[1] - rise * 0.4)

        # center fold edge
        c.line(waist_l[0] * cm, (waist_l[1] - rise * 0.4) * cm,
               waist_l[0] * cm, waist_l[1] * cm)

        draw_fold_edge(c, waist_l[0], waist_l[1] - rise * 0.4,
                       waist_l[0], waist_l[1])

        # labels
        c.setFont("Helvetica-Bold", 11)
        c.drawString((x0 + 2) * cm, (y0 + rise * 0.6) * cm,
                     "Bloomers - Cut 2 on fold")
        c.setFont("Helvetica", 8)
        c.drawString((x0 + 2) * cm, (y0 + rise * 0.55) * cm,
                     f"Size {size_label}  |  rise {rise:.1f}cm  |  "
                     f"waist {waist_half * 2:.1f}cm")
        c.setFont("Helvetica", 7)
        c.drawString((x0 + 2) * cm, (y0 + rise * 0.5) * cm,
                     "Elastic casings: fold 1.5cm at waist + leg openings")

        # grain line
        draw_grain_line(c,
                        x0 + waist_half * 0.6, y0 + rise * 0.2,
                        x0 + waist_half * 0.6, y0 + rise * 0.8)

        # notches: crotch match point + leg opening match
        draw_notch(c, crotch[0], crotch[1], angle_deg=45)
        draw_notch(c, leg_inner[0], leg_inner[1], angle_deg=135)
        # waist center notch
        draw_notch(c, waist_l[0] + waist_half / 2, waist_r[1], angle_deg=270)

        # seam allowance envelope (dashed)
        c.setDash(4, 3)
        c.setLineWidth(0.5)
        c.setStrokeColor(gray)
        c.rect((x0 - sa) * cm, (y0 - inseam - sa) * cm,
               (hip_half + sa * 2) * cm,
               (rise + inseam + sa * 2) * cm)
        c.setDash(1, 0)
        c.setStrokeColor(black)

    instructions = [
        f"BABY BLOOMERS / DIAPER COVER - {size_label}",
        "",
        "Materials:",
        "  - 0.5 m of 115cm knit or woven cotton",
        "  - 1 cm wide elastic: 2 x leg (approx. 30cm each) + 1 waist",
        "  - Waist elastic length = child's waist - 2 cm",
        "",
        "Sewing order:",
        "  1. Cut 2 pieces on fold (front + back identical)",
        "  2. Sew crotch seams RST (front to back) on both sides",
        "  3. Sew inseam + leg curve as one continuous seam",
        "  4. Fold waist edge 1.5 cm, sew leaving 3cm gap",
        "  5. Thread waist elastic through casing, close gap",
        "  6. Fold each leg opening 1.2 cm, thread leg elastic",
        "  7. Overlap elastic ends 1 cm, sew securely",
        "",
        f"Seam allowance included: {seam_allowance} cm",
    ]

    file_path = os.path.abspath(f"bloomers_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "Baby Bloomers", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Bloomers pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Rise: {rise:.1f}cm  |  Waist half: {waist_half:.1f}cm")


@mcp.tool()
def generate_bonnet_pattern(size_label: str, seam_allowance: float = 1.0) -> str:
    """
    Traditional baby bonnet with 3 pieces: crown (curved dome), brim band,
    and a pair of ties. Tilts back to show face.
    """
    if size_label not in SIZE_CHART:
        return f"Error: size '{size_label}' not found. Available: {list(SIZE_CHART)}"

    spec = SIZE_CHART[size_label]

    face_w = spec["head"] / 2 - 2.0
    crown_h = spec["head"] / 4 + 2.0
    back_w = spec["head"] / 3

    band_l = face_w * 2 + 2.0
    band_h = 5.0

    tie_w = 2.5
    tie_l = 25.0

    sa = seam_allowance
    total_w = max(face_w * 2 + 2, band_l, tie_l) + sa * 2 + 2
    total_h = crown_h + band_h + tie_w + sa * 6 + 8

    def draw(c):
        y_cursor = 2.0

        # --- Crown (teardrop / half-oval, cut on fold at back) ---
        cx = 1.0 + sa + face_w
        cy_bottom = y_cursor
        cy_top = cy_bottom + crown_h

        c.setStrokeColor(black)
        c.setLineWidth(1.3)

        # face edge (bottom) - slight curve
        draw_bezier_edge(c,
                         cx - face_w, cy_bottom,
                         cx - face_w * 0.5, cy_bottom - 0.3,
                         cx + face_w * 0.5, cy_bottom - 0.3,
                         cx + face_w, cy_bottom)

        # side curves up to back fold
        draw_bezier_edge(c,
                         cx - face_w, cy_bottom,
                         cx - face_w - 1.0, cy_bottom + crown_h * 0.5,
                         cx - back_w / 2 - 0.5, cy_top - 0.3,
                         cx - back_w / 2, cy_top)
        draw_bezier_edge(c,
                         cx + face_w, cy_bottom,
                         cx + face_w + 1.0, cy_bottom + crown_h * 0.5,
                         cx + back_w / 2 + 0.5, cy_top - 0.3,
                         cx + back_w / 2, cy_top)
        # back fold edge
        c.line((cx - back_w / 2) * cm, cy_top * cm,
               (cx + back_w / 2) * cm, cy_top * cm)
        draw_fold_edge(c, cx - back_w / 2, cy_top, cx + back_w / 2, cy_top)

        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(cx * cm, (cy_bottom + crown_h * 0.55) * cm,
                            "1. Crown - Cut 2 on fold")
        c.setFont("Helvetica", 7)
        c.drawCentredString(cx * cm, (cy_bottom + crown_h * 0.45) * cm,
                            f"face {face_w * 2:.1f}cm | back {back_w:.1f}cm | "
                            f"depth {crown_h:.1f}cm")

        draw_grain_line(c,
                        cx, cy_bottom + crown_h * 0.15,
                        cx, cy_bottom + crown_h * 0.35)

        # notches: center face, side match points
        draw_notch(c, cx, cy_bottom, angle_deg=90)
        draw_notch(c, cx - face_w * 0.5,
                   cy_bottom - 0.15 + 0.2, angle_deg=90)
        draw_notch(c, cx + face_w * 0.5,
                   cy_bottom - 0.15 + 0.2, angle_deg=90)

        y_cursor = cy_top + sa * 2 + 2

        # --- Brim band (curved rectangle) ---
        bx = 1.0 + sa
        by = y_cursor
        c.setLineWidth(1.3)
        # top curves slightly (follows crown face)
        draw_bezier_edge(c,
                         bx, by + band_h,
                         bx + band_l * 0.25, by + band_h + 0.3,
                         bx + band_l * 0.75, by + band_h + 0.3,
                         bx + band_l, by + band_h)
        c.line(bx * cm, by * cm, (bx + band_l) * cm, by * cm)
        c.line(bx * cm, by * cm, bx * cm, (by + band_h) * cm)
        c.line((bx + band_l) * cm, by * cm,
               (bx + band_l) * cm, (by + band_h) * cm)

        c.setFont("Helvetica-Bold", 10)
        c.drawString((bx + 0.5) * cm, (by + band_h * 0.6) * cm,
                     "2. Brim Band - Cut 2")
        c.setFont("Helvetica", 7)
        c.drawString((bx + 0.5) * cm, (by + band_h * 0.3) * cm,
                     f"{band_l:.1f} x {band_h:.1f} cm  (interline for structure)")
        draw_grain_line(c,
                        bx + band_l * 0.5, by + 0.8,
                        bx + band_l * 0.5, by + band_h - 0.8)
        draw_notch(c, bx + band_l / 2, by + band_h, angle_deg=270)
        # SA envelope
        c.setDash(4, 3)
        c.setLineWidth(0.5)
        c.setStrokeColor(gray)
        c.rect((bx - sa) * cm, (by - sa) * cm,
               (band_l + sa * 2) * cm, (band_h + sa * 2) * cm)
        c.setDash(1, 0)
        c.setStrokeColor(black)

        y_cursor = by + band_h + sa * 2 + 2

        # --- Tie ---
        tx = 1.0 + sa
        ty = y_cursor
        c.setLineWidth(1.3)
        c.rect(tx * cm, ty * cm, tie_l * cm, tie_w * cm)
        # angled end
        c.setFont("Helvetica-Bold", 9)
        c.drawString((tx + 0.5) * cm, (ty + tie_w * 0.55) * cm,
                     "3. Tie - Cut 2")
        c.setFont("Helvetica", 7)
        c.drawString((tx + 0.5) * cm, (ty + tie_w * 0.2) * cm,
                     f"{tie_l:.1f} x {tie_w:.1f} cm  (fold lengthwise, sew, turn)")
        draw_grain_line(c,
                        tx + 2, ty + tie_w / 2,
                        tx + tie_l - 2, ty + tie_w / 2)
        c.setDash(4, 3)
        c.setLineWidth(0.5)
        c.setStrokeColor(gray)
        c.rect((tx - sa) * cm, (ty - sa) * cm,
               (tie_l + sa * 2) * cm, (tie_w + sa * 2) * cm)
        c.setDash(1, 0)
        c.setStrokeColor(black)

    instructions = [
        f"BABY BONNET - {size_label}",
        "",
        "Materials:",
        "  - 0.3 m fashion fabric (quilting cotton, linen)",
        "  - 0.3 m lining (soft cotton lawn)",
        "  - 20 x 10 cm fusible interfacing (for brim)",
        "",
        "Sewing order:",
        "  1. Cut 2 crown pieces on fold (outer + lining)",
        "  2. Cut 2 brim bands + 1 interfacing, fuse to one band",
        "  3. Cut 2 ties",
        "  4. Make ties: fold lengthwise RST, sew, turn, press",
        "  5. Sandwich ties at front ends of brim band",
        "  6. Sew brim bands RST along curved top, turn, press",
        "  7. Gather bottom edge of crown to match brim length",
        "  8. Attach crown to brim (outer fabric only)",
        "  9. Attach lining crown, turn through, hand-sew closing gap",
        "",
        f"Seam allowance included: {seam_allowance} cm",
        "Tip: grade/clip seam allowances on curves before turning.",
    ]

    file_path = os.path.abspath(f"bonnet_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "Baby Bonnet", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Bonnet pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Face opening: {face_w * 2:.1f}cm")


@mcp.tool()
def list_available_sizes() -> str:
    """Return the full size chart used by all pattern tools."""
    lines = ["Available sizes (all in cm):", ""]
    headers = ["size", "chest", "length", "waist", "hip", "head",
               "arm_len", "neck_circ"]
    lines.append("  ".join(f"{h:>9}" for h in headers))
    lines.append("  ".join("-" * 9 for _ in headers))
    for size, spec in SIZE_CHART.items():
        row = [size,
               str(spec["chest"]),
               str(spec["length"]),
               str(spec["waist"]),
               str(spec["hip"]),
               str(spec["head"]),
               str(spec["arm_len"]),
               str(spec["neck_circ"])]
        lines.append("  ".join(f"{v:>9}" for v in row))
    lines.append("")
    lines.append("Use these size labels with any generate_*_pattern tool.")
    return "\n".join(lines)


@mcp.tool()
def calculate_fabric_requirement(pattern_type: str, size_label: str) -> str:
    """
    Estimate fabric required for a pattern in common bolt widths (90, 115, 150 cm).
    pattern_type: 'dress', 'bib', 'bloomers', or 'bonnet'.
    """
    if size_label not in SIZE_CHART:
        return f"Error: size '{size_label}' not found. Available: {list(SIZE_CHART)}"

    spec = SIZE_CHART[size_label]

    if pattern_type == "dress":
        bodice_w = spec["chest"] / 4 + 2.0
        bodice_h = spec["length"]
        ruffle_w = bodice_w * 2 * 1.5
        ruffle_h = spec["ruffle_h"]
        strap_area = 3.0 * spec["strap_len"] * 2
        pieces = [
            ("Bodice (x2)", bodice_w * 2, bodice_h),
            ("Ruffle (x2)", ruffle_w, ruffle_h * 2),
        ]
        extra_area_cm2 = strap_area
    elif pattern_type == "bib":
        body_w = spec["neck_circ"] * 0.9
        body_h = body_w * 1.1
        pieces = [("Front + back", body_w, body_h * 2)]
        extra_area_cm2 = 0
    elif pattern_type == "bloomers":
        hip_half = spec["hip"] / 2 + 4.0
        rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
        pieces = [("Front + back (x2)", hip_half, rise * 2)]
        extra_area_cm2 = 0
    elif pattern_type == "bonnet":
        face_w = spec["head"] / 2 - 2.0
        crown_h = spec["head"] / 4 + 2.0
        band_l = face_w * 2 + 2.0
        band_h = 5.0
        pieces = [
            ("Crown (x2)", face_w * 2, crown_h * 2),
            ("Brim (x2)", band_l, band_h * 2),
        ]
        extra_area_cm2 = 2.5 * 25.0 * 2
    else:
        return (f"Error: unknown pattern_type '{pattern_type}'. "
                "Use: dress, bib, bloomers, bonnet.")

    # seam allowance + 10% wastage padding
    sa_pad = 3.0
    total_length_by_width = {}
    for width_cm in (90, 115, 150):
        total_len = 0.0
        for _, pw, ph in pieces:
            effective_w = pw + sa_pad
            if effective_w > width_cm:
                total_len += (ph + sa_pad) * 2
            else:
                total_len += ph + sa_pad
        if extra_area_cm2:
            total_len += (extra_area_cm2 / width_cm) + sa_pad
        total_length_by_width[width_cm] = total_len * 1.10

    lines = [f"Fabric estimate: {pattern_type} size {size_label}",
             "",
             "Pieces:"]
    for name, pw, ph in pieces:
        lines.append(f"  {name}: {pw:.1f} x {ph:.1f} cm")
    if extra_area_cm2:
        lines.append(f"  Small pieces (straps/ties): ~{extra_area_cm2:.0f} cm²")
    lines.append("")
    lines.append("Required length by bolt width (10% wastage included):")
    for w, length in total_length_by_width.items():
        lines.append(f"  {w}cm wide -> {length / 100:.2f} m  ({length:.0f} cm)")
    lines.append("")
    lines.append("Values assume a single-layer layout. "
                 "Cut-on-fold pieces save ~40%, directional prints need more.")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
