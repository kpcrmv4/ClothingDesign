"""Baby sleep sack — sleeveless wearable blanket with front zipper."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray, red

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, tile_and_save,
                     THAI_FONT, THAI_FONT_BOLD)


def generate(size_label: str, seam_allowance: float = 1.0,
             output_dir: str = ".") -> str:
    spec = get_size(size_label)

    chest_half = spec["chest"] / 4 + 6.0
    hem_half = chest_half + 6.0
    total_len = spec["length"] + 20.0
    neck_drop_front = 5.0
    neck_drop_back = 2.0
    neck_w = spec["neck_circ"] / 6 + 0.5
    armhole_drop = spec["arm_len"] * 0.3 + 5.0
    armhole_w = 3.0
    shoulder = 3.0

    sa = seam_allowance
    gap = 2.5

    total_w = max(hem_half, chest_half) + sa * 2 + 2
    total_h = total_len * 2 + sa * 4 + gap + 4

    def draw(c):
        y_cursor = 2.0

        # --- Back (cut 1 on fold) ---
        bx, by = 2.0, y_cursor
        _draw_sack_body(c, bx, by, chest_half, hem_half, total_len,
                        neck_w, neck_drop_back, shoulder,
                        armhole_w, armhole_drop)
        c.setFont(THAI_FONT_BOLD, 11)
        c.drawString((bx + 1) * cm, (by + total_len * 0.5) * cm,
                     "1. Back - ตัด 1 ชิ้นบนรอยพับ")
        c.setFont(THAI_FONT, 7)
        c.drawString((bx + 1) * cm, (by + total_len * 0.45) * cm,
                     f"Size {size_label}")
        c.drawString((bx + 1) * cm, (by + total_len * 0.4) * cm,
                     f"Chest {chest_half * 2:.1f}cm  |  "
                     f"Length {total_len:.1f}cm")
        draw_fold_edge(c, bx, by, bx, by + total_len)
        draw_grain_line(c,
                        bx + chest_half * 0.6, by + total_len * 0.2,
                        bx + chest_half * 0.6, by + total_len * 0.7)
        draw_notch(c, bx + chest_half, by + total_len - armhole_drop,
                   angle_deg=180)

        y_cursor = by + total_len + sa * 2 + gap

        # --- Front (cut 2 for zipper opening, center front = zipper line) ---
        fx, fy = 2.0, y_cursor
        _draw_sack_body(c, fx, fy, chest_half, hem_half, total_len,
                        neck_w, neck_drop_front, shoulder,
                        armhole_w, armhole_drop)
        c.setFont(THAI_FONT_BOLD, 11)
        c.drawString((fx + 1) * cm, (fy + total_len * 0.5) * cm,
                     "2. Front - ตัด 2 ชิ้น (left + right)")
        c.setFont(THAI_FONT, 7)
        c.drawString((fx + 1) * cm, (fy + total_len * 0.45) * cm,
                     "Center front edge = zipper placement")

        # zipper line indicator on center (left edge)
        c.setDash([6, 3], 0)
        c.setStrokeColor(red)
        c.setLineWidth(0.8)
        c.line(fx * cm, (fy + 5) * cm,
               fx * cm, (fy + total_len - neck_drop_front) * cm)
        c.setDash([], 0)
        c.setStrokeColor(black)
        c.setFont(THAI_FONT, 6)
        c.setFillColor(red)
        c.drawString((fx + 0.3) * cm, (fy + total_len - neck_drop_front - 0.6) * cm,
                     "ZIPPER (do NOT cut on fold)")
        c.setFillColor(black)

        draw_grain_line(c,
                        fx + chest_half * 0.6, fy + total_len * 0.2,
                        fx + chest_half * 0.6, fy + total_len * 0.7)
        draw_notch(c, fx + chest_half, fy + total_len - armhole_drop,
                   angle_deg=180)
        # notch at zipper start
        draw_notch(c, fx, fy + 5, angle_deg=0)

    instructions = [
        f"ถุงนอน - {size_label}",
        "",
        "วัสดุ:",
        "  - 1.0-1.5 m cotton jersey, flannel, or muslin (main)",
        "  - 0.5 m backing for warmth (optional, cotton flannel)",
        "  - 1 separating zipper 35-50 cm (or matching length)",
        "  - 2 m bias tape for neckline + armholes",
        "  - Matching thread",
        "",
        "Safety note:",
        "  Do NOT add sleeves, hood, or loose accessories.",
        "  TOG value depends on fabric + filling; check local guidelines.",
        "",
        "ลำดับการเย็บ:",
        "  1. Cut: 1 back on fold, 2 fronts (mirror, center front NOT on fold)",
        "  2. Sew shoulder seams RST",
        "  3. Sew side seams RST",
        "  4. Install separating zipper along center front edges",
        "  5. Bind neckline + armholes with bias tape",
        "  6. Hem bottom with 3cm double-fold hem",
        "  7. Optional: add backing layer before binding for warmth",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} cm",
    ]

    file_path = os.path.abspath(os.path.join(output_dir, f"sleep_sack_pattern_{size_label}.pdf"))
    total_pages = tile_and_save(file_path, "ถุงนอน", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Sleep sack pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Length: {total_len:.1f}cm  |  Chest: {chest_half * 2:.1f}cm")


def _draw_sack_body(c, x, y, chest_half, hem_half, h,
                     neck_w, neck_drop, shoulder, arm_w, arm_drop):
    """A-line sleep sack outline: narrower at chest, wider at hem."""
    c.setStrokeColor(black)
    c.setLineWidth(1.3)

    chest_y = y + h - arm_drop - 2

    # hem (bottom)
    c.line(x * cm, y * cm, (x + hem_half) * cm, y * cm)
    # side seam (angled from hem out to chest in)
    c.line((x + hem_half) * cm, y * cm,
           (x + chest_half) * cm, chest_y * cm)
    # side up to underarm
    c.line((x + chest_half) * cm, chest_y * cm,
           (x + chest_half) * cm, (y + h - arm_drop) * cm)
    # armhole curve
    draw_bezier_edge(c,
                     x + chest_half, y + h - arm_drop,
                     x + chest_half - 0.3, y + h - arm_drop * 0.5,
                     x + chest_half - arm_w, y + h - 0.2,
                     x + neck_w + shoulder, y + h)
    # shoulder
    c.line((x + neck_w + shoulder) * cm, (y + h) * cm,
           (x + neck_w) * cm, (y + h) * cm)
    # neckline
    draw_bezier_edge(c,
                     x + neck_w, y + h,
                     x + neck_w * 0.5, y + h,
                     x, y + h - neck_drop * 0.5,
                     x, y + h - neck_drop)

    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.rect((x - 1) * cm, (y - 1) * cm,
           (hem_half + 2) * cm, (h + 2) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)
