"""Baby kimono wrap top — no buttons, side ties, crossover front."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save)


def generate(size_label: str, seam_allowance: float = 1.0) -> str:
    spec = get_size(size_label)

    chest_half = spec["chest"] / 4 + 2.0
    body_len = spec["length"] * 0.9
    neck_drop_back = 2.0
    neck_drop_front = 10.0
    neck_width = spec["neck_circ"] / 6
    shoulder_w = spec["shoulder"]

    sleeve_cap_w = spec["arm_len"] * 0.3 + spec["shoulder"]
    sleeve_len = spec["arm_len"] * 0.5
    sleeve_cuff = spec["arm_len"] * 0.25 + 3.0

    sa = seam_allowance
    gap = 2.0

    total_w = max(chest_half + 2, sleeve_cap_w) + sa * 2 + 2
    total_h = (body_len + body_len + sleeve_len) + sa * 6 + gap * 2 + 4

    def draw(c):
        y_cursor = 2.0

        # --- Back bodice (cut on fold at left) ---
        bx, by = 2.0, y_cursor
        _draw_kimono_back(c, bx, by, chest_half, body_len,
                          neck_width, neck_drop_back, shoulder_w)
        c.setFont("Tahoma-Bold", 10)
        c.drawString((bx + 0.5) * cm, (by + body_len * 0.85) * cm,
                     "1. Back - ตัด 1 ชิ้นบนรอยพับ")
        c.setFont("Tahoma", 7)
        c.drawString((bx + 0.5) * cm, (by + body_len * 0.8) * cm,
                     f"Size {size_label}  |  {chest_half:.1f} x {body_len:.1f}cm")
        draw_grain_line(c,
                        bx + chest_half * 0.6, by + body_len * 0.2,
                        bx + chest_half * 0.6, by + body_len * 0.6)
        draw_fold_edge(c, bx, by, bx, by + body_len)
        draw_notch(c, bx + chest_half, by + body_len * 0.5, angle_deg=180)

        y_cursor = by + body_len + sa * 2 + gap

        # --- Front bodice (cut 2 mirrored, deep crossover neckline) ---
        fx, fy = 2.0, y_cursor
        _draw_kimono_front(c, fx, fy, chest_half, body_len,
                           neck_width, neck_drop_front, shoulder_w)
        c.setFont("Tahoma-Bold", 10)
        c.drawString((fx + 0.5) * cm, (fy + body_len * 0.85) * cm,
                     "2. Front - ตัด 2 ชิ้น (mirror)")
        c.setFont("Tahoma", 7)
        c.drawString((fx + 0.5) * cm, (fy + body_len * 0.8) * cm,
                     "Right front overlaps left at closure")
        draw_grain_line(c,
                        fx + chest_half * 0.6, fy + body_len * 0.2,
                        fx + chest_half * 0.6, fy + body_len * 0.6)
        draw_notch(c, fx + chest_half, fy + body_len * 0.5, angle_deg=180)

        y_cursor = fy + body_len + sa * 2 + gap

        # --- Sleeve (cut 2) ---
        sx, sy = 2.0, y_cursor
        _draw_sleeve(c, sx, sy, sleeve_cap_w, sleeve_len, sleeve_cuff)
        c.setFont("Tahoma-Bold", 10)
        c.drawString((sx + 0.5) * cm, (sy + sleeve_len * 0.85) * cm,
                     "3. Sleeve - ตัด 2 ชิ้น")
        c.setFont("Tahoma", 7)
        c.drawString((sx + 0.5) * cm, (sy + sleeve_len * 0.78) * cm,
                     f"Cap {sleeve_cap_w:.1f}cm | Cuff {sleeve_cuff:.1f}cm "
                     f"| Length {sleeve_len:.1f}cm")
        draw_grain_line(c,
                        sx + sleeve_cap_w / 2, sy + 1,
                        sx + sleeve_cap_w / 2, sy + sleeve_len - 1)
        # notch at sleeve cap center (match to shoulder seam)
        draw_notch(c, sx + sleeve_cap_w / 2, sy + sleeve_len, angle_deg=270)

    instructions = [
        f"KIMONO WRAP TOP - {size_label}",
        "",
        "วัสดุ:",
        "  - 0.5-0.7 m of 115 cm cotton lawn, flannel, or jersey",
        "  - Matching thread + bias tape 1.5 m",
        "  - 2 small snaps OR 60 cm cotton ribbon for ties",
        "",
        "ลำดับการเย็บ:",
        "  1. Cut: 1 back on fold, 2 fronts mirrored, 2 sleeves",
        "  2. Sew back to fronts at shoulder seams, RST",
        "  3. Attach sleeves to armholes, matching notches",
        "  4. Sew underarm + side seams in one continuous line",
        "  5. Bind neckline + front opening with bias tape",
        "  6. Hem sleeve cuffs and bottom",
        "  7. Attach inside tie + outside tie OR 2 snaps",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} ซม",
    ]

    file_path = os.path.abspath(f"kimono_top_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "เสื้อป้ายผูกข้าง", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Kimono top pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Body: {chest_half * 2:.1f}x{body_len:.1f}cm  |  "
            f"Sleeve: {sleeve_len:.1f}cm long")


def _draw_kimono_back(c, x, y, half_w, h, neck_w, neck_drop, shoulder):
    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    # bottom
    c.line(x * cm, y * cm, (x + half_w) * cm, y * cm)
    # side
    c.line((x + half_w) * cm, y * cm,
           (x + half_w) * cm, (y + h - 2) * cm)
    # armhole (slight slope to shoulder)
    draw_bezier_edge(c,
                     x + half_w, y + h - 2,
                     x + half_w - 0.5, y + h - 0.5,
                     x + half_w - 1.5, y + h,
                     x + neck_w + shoulder, y + h)
    # shoulder
    c.line((x + neck_w + shoulder) * cm, (y + h) * cm,
           (x + neck_w) * cm, (y + h) * cm)
    # neckline (shallow curve)
    draw_bezier_edge(c,
                     x + neck_w, y + h,
                     x + neck_w * 0.5, y + h,
                     x + 0.3, y + h - neck_drop * 0.5,
                     x, y + h - neck_drop)

    # SA envelope (rect approximation)
    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.line(x * cm, (y - 1) * cm, (x + half_w + 1) * cm, (y - 1) * cm)
    c.line((x + half_w + 1) * cm, (y - 1) * cm,
           (x + half_w + 1) * cm, (y + h + 1) * cm)
    c.line((x + half_w + 1) * cm, (y + h + 1) * cm, x * cm, (y + h + 1) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)


def _draw_kimono_front(c, x, y, half_w, h, neck_w, neck_drop, shoulder):
    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    # bottom
    c.line(x * cm, y * cm, (x + half_w) * cm, y * cm)
    # side (right = fold-like for mirror)
    c.line((x + half_w) * cm, y * cm,
           (x + half_w) * cm, (y + h - 2) * cm)
    # armhole
    draw_bezier_edge(c,
                     x + half_w, y + h - 2,
                     x + half_w - 0.5, y + h - 0.5,
                     x + half_w - 1.5, y + h,
                     x + neck_w + shoulder, y + h)
    # shoulder
    c.line((x + neck_w + shoulder) * cm, (y + h) * cm,
           (x + neck_w) * cm, (y + h) * cm)
    # deep crossover neckline - curves from shoulder down and across
    draw_bezier_edge(c,
                     x + neck_w, y + h,
                     x + neck_w, y + h - neck_drop * 0.3,
                     x + half_w * 0.3, y + h - neck_drop * 0.7,
                     x, y + h - neck_drop)
    # center front (going down to hem)
    c.line(x * cm, (y + h - neck_drop) * cm, x * cm, y * cm)

    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.rect((x - 1) * cm, (y - 1) * cm,
           (half_w + 2) * cm, (h + 2) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)


def _draw_sleeve(c, x, y, cap_w, length, cuff_w):
    """Sleeve shape: trapezoid with curved sleeve cap at top."""
    inset = (cap_w - cuff_w) / 2
    cuff_l = x + inset
    cuff_r = x + inset + cuff_w

    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    # cuff
    c.line(cuff_l * cm, y * cm, cuff_r * cm, y * cm)
    # sides (angled)
    c.line(cuff_l * cm, y * cm, x * cm, (y + length - 2) * cm)
    c.line(cuff_r * cm, y * cm, (x + cap_w) * cm, (y + length - 2) * cm)
    # sleeve cap curve
    draw_bezier_edge(c,
                     x, y + length - 2,
                     x + cap_w * 0.25, y + length + 1,
                     x + cap_w * 0.75, y + length + 1,
                     x + cap_w, y + length - 2)

    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.rect((x - 1) * cm, (y - 1) * cm,
           (cap_w + 2) * cm, (length + 2.5) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)
