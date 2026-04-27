"""Basic baby t-shirt with crew neck + shoulder snap opening for newborn fit."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray, red

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save)


def generate(size_label: str, seam_allowance: float = 1.0,
             sleeve: str = "short") -> str:
    if sleeve not in ("short", "long"):
        return f"Error: sleeve must be 'short' or 'long', got '{sleeve}'"

    spec = get_size(size_label)

    chest_half = spec["chest"] / 4 + 2.5
    length = spec["length"] * 0.85
    neck_drop_front = 4.0
    neck_drop_back = 1.5
    neck_width = spec["neck_circ"] / 6 + 0.3
    shoulder_w = spec["shoulder"] - 0.5
    armhole_drop = spec["arm_len"] * 0.3 + 4.0

    sleeve_cap_w = spec["arm_len"] * 0.45 + 4.0
    sleeve_len = spec["arm_len"] * 0.35 if sleeve == "short" else spec["arm_len"] * 0.9
    sleeve_cuff = spec["arm_len"] * 0.3 + 3.0

    neckband_l = spec["neck_circ"] * 0.9
    neckband_h = 5.0  # folded = 2.5cm

    sa = seam_allowance
    gap = 2.0

    total_w = max(chest_half, sleeve_cap_w, neckband_l) + sa * 2 + 2
    total_h = (length * 2 + sleeve_len + neckband_h) + sa * 8 + gap * 3 + 4

    def draw(c):
        y_cursor = 2.0

        # --- Front ---
        fx, fy = 2.0, y_cursor
        _draw_tshirt_body(c, fx, fy, chest_half, length,
                          neck_width, neck_drop_front, shoulder_w, armhole_drop)
        c.setFont("Tahoma-Bold", 10)
        c.drawString((fx + 0.5) * cm, (fy + length * 0.85) * cm,
                     "1. Front - ตัด 1 ชิ้นบนรอยพับ")
        c.setFont("Tahoma", 7)
        c.drawString((fx + 0.5) * cm, (fy + length * 0.78) * cm,
                     f"Size {size_label}  |  {chest_half:.1f} x {length:.1f}cm")
        draw_grain_line(c,
                        fx + chest_half * 0.6, fy + length * 0.2,
                        fx + chest_half * 0.6, fy + length * 0.6)
        draw_fold_edge(c, fx, fy, fx, fy + length)
        draw_notch(c, fx + chest_half, fy + length - armhole_drop, angle_deg=180)

        y_cursor = fy + length + sa * 2 + gap

        # --- Back (shallower neckline) ---
        bx, by = 2.0, y_cursor
        _draw_tshirt_body(c, bx, by, chest_half, length,
                          neck_width, neck_drop_back, shoulder_w, armhole_drop)
        # shoulder opening marker (for newborn size)
        c.setDash([3, 2], 0)
        c.setStrokeColor(red)
        c.line((bx + neck_width) * cm, (by + length) * cm,
               (bx + neck_width + shoulder_w) * cm, (by + length) * cm)
        c.setDash([], 0)
        c.setStrokeColor(black)
        c.setFont("Tahoma", 6)
        c.setFillColor(red)
        c.drawString((bx + neck_width) * cm, (by + length - 0.4) * cm,
                     "shoulder opening - 2-3 snaps")
        c.setFillColor(black)

        c.setFont("Tahoma-Bold", 10)
        c.drawString((bx + 0.5) * cm, (by + length * 0.85) * cm,
                     "2. Back - ตัด 1 ชิ้นบนรอยพับ")
        c.setFont("Tahoma", 7)
        c.drawString((bx + 0.5) * cm, (by + length * 0.78) * cm,
                     "Shallower neckline than front")
        draw_grain_line(c,
                        bx + chest_half * 0.6, by + length * 0.2,
                        bx + chest_half * 0.6, by + length * 0.6)
        draw_fold_edge(c, bx, by, bx, by + length)

        y_cursor = by + length + sa * 2 + gap

        # --- Sleeve ---
        sx, sy = 2.0, y_cursor
        _draw_sleeve_tshirt(c, sx, sy, sleeve_cap_w, sleeve_len, sleeve_cuff)
        c.setFont("Tahoma-Bold", 10)
        c.drawString((sx + 0.5) * cm, (sy + sleeve_len * 0.85) * cm,
                     f"3. Sleeve ({sleeve}) - ตัด 2 ชิ้น")
        c.setFont("Tahoma", 7)
        c.drawString((sx + 0.5) * cm, (sy + sleeve_len * 0.78) * cm,
                     f"Cap {sleeve_cap_w:.1f}cm | Len {sleeve_len:.1f}cm | "
                     f"Cuff {sleeve_cuff:.1f}cm")
        draw_grain_line(c,
                        sx + sleeve_cap_w / 2, sy + 1,
                        sx + sleeve_cap_w / 2, sy + sleeve_len - 1)
        draw_notch(c, sx + sleeve_cap_w / 2, sy + sleeve_len, angle_deg=270)

        y_cursor = sy + sleeve_len + sa * 2 + gap

        # --- Neckband (ribbing) ---
        nx, ny = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.rect(nx * cm, ny * cm, neckband_l * cm, neckband_h * cm)
        # fold line
        c.setDash([3, 2], 0)
        c.setStrokeColor(gray)
        c.line(nx * cm, (ny + neckband_h / 2) * cm,
               (nx + neckband_l) * cm, (ny + neckband_h / 2) * cm)
        c.setDash([], 0)
        c.setStrokeColor(black)
        c.setFont("Tahoma-Bold", 10)
        c.drawString((nx + 0.5) * cm, (ny + neckband_h - 1) * cm,
                     "4. Neckband - ตัด 1 ชิ้น ribbing (knit)")
        c.setFont("Tahoma", 7)
        c.drawString((nx + 0.5) * cm, (ny + 0.3) * cm,
                     f"{neckband_l:.1f} x {neckband_h:.1f}cm  "
                     f"(stretch to fit neckline, fold in half lengthwise)")
        draw_sa_rect_envelope(c, nx, ny, neckband_l, neckband_h, sa)

    instructions = [
        f"เสื้อยืดเด็ก (แขน{sleeve}) - {size_label}",
        "",
        "วัสดุ:",
        "  - 0.4-0.6 m cotton jersey (main)",
        "  - 30x10 cm ribbing for neckband (or same jersey stretched)",
        "  - Ballpoint machine needle size 80",
        "  - Matching thread + 2-3 snaps for shoulder opening",
        "",
        "ลำดับการเย็บ:",
        "  1. Cut: 1 front on fold, 1 back on fold, 2 sleeves, 1 neckband",
        "  2. Sew one shoulder seam (full), leave other side for opening",
        "  3. Fold neckband in half, mark quarters",
        "  4. Pin + sew neckband to neckline, stretching to fit",
        "  5. Finish unstitched shoulder edge with bias or folded hem",
        "  6. Install snaps at shoulder opening",
        "  7. Sew remaining shoulder up to neckband, hem it",
        "  8. Attach sleeves to armholes, matching center notch",
        "  9. Sew underarm + side seam in one line",
        " 10. Hem sleeves + bottom (twin needle recommended)",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} cm",
    ]

    file_path = os.path.abspath(f"tshirt_pattern_{size_label}_{sleeve}.pdf")
    total_pages = tile_and_save(file_path, f"เสื้อยืดเด็ก ({sleeve})", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"T-shirt pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Sleeve: {sleeve}  |  "
            f"Pages: {total_pages} A4 sheets")


def _draw_tshirt_body(c, x, y, half_w, h, neck_w, neck_drop, shoulder, arm_drop):
    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    # bottom
    c.line(x * cm, y * cm, (x + half_w) * cm, y * cm)
    # side up to underarm
    c.line((x + half_w) * cm, y * cm,
           (x + half_w) * cm, (y + h - arm_drop) * cm)
    # armhole curve
    draw_bezier_edge(c,
                     x + half_w, y + h - arm_drop,
                     x + half_w - 0.3, y + h - arm_drop * 0.5,
                     x + half_w - 1.0, y + h,
                     x + neck_w + shoulder, y + h)
    # shoulder (straight)
    c.line((x + neck_w + shoulder) * cm, (y + h) * cm,
           (x + neck_w) * cm, (y + h) * cm)
    # neckline curve
    draw_bezier_edge(c,
                     x + neck_w, y + h,
                     x + neck_w * 0.5, y + h,
                     x, y + h - neck_drop * 0.5,
                     x, y + h - neck_drop)

    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.line(x * cm, (y - 1) * cm, (x + half_w + 1) * cm, (y - 1) * cm)
    c.line((x + half_w + 1) * cm, (y - 1) * cm,
           (x + half_w + 1) * cm, (y + h + 1) * cm)
    c.line((x + half_w + 1) * cm, (y + h + 1) * cm, x * cm, (y + h + 1) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)


def _draw_sleeve_tshirt(c, x, y, cap_w, length, cuff_w):
    inset = (cap_w - cuff_w) / 2
    cuff_l = x + inset
    cuff_r = x + inset + cuff_w

    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    c.line(cuff_l * cm, y * cm, cuff_r * cm, y * cm)
    c.line(cuff_l * cm, y * cm, x * cm, (y + length - 1.5) * cm)
    c.line(cuff_r * cm, y * cm, (x + cap_w) * cm, (y + length - 1.5) * cm)
    draw_bezier_edge(c,
                     x, y + length - 1.5,
                     x + cap_w * 0.2, y + length + 0.8,
                     x + cap_w * 0.8, y + length + 0.8,
                     x + cap_w, y + length - 1.5)

    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.rect((x - 1) * cm, (y - 1) * cm,
           (cap_w + 2) * cm, (length + 2) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)
