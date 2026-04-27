"""Baby romper: one-piece bodysuit with straps and snap crotch closure."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray, red

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save)


def generate(size_label: str, seam_allowance: float = 1.0) -> str:
    spec = get_size(size_label)

    chest_half = spec["chest"] / 4 + 2.0
    bodice_h = spec["length"] * 0.55
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 4.0
    crotch_w = 6.0

    neck_drop = 4.0
    neck_w = spec["neck_circ"] / 6 + 0.3
    armhole_drop = 5.0
    armhole_w = 2.5
    shoulder = 2.5

    leg_opening = spec["hip"] / 8 + 3.0
    strap_w = 3.0
    strap_len = spec["strap_len"] + 2

    sa = seam_allowance
    gap = 2.0

    total_w = max(chest_half, strap_len) + sa * 2 + 3
    total_h = (bodice_h + rise) * 2 + strap_w + sa * 6 + gap * 2 + 4

    def draw(c):
        y_cursor = 2.0

        # --- Front (bodice + crotch combined) ---
        fx, fy = 2.0, y_cursor
        _draw_romper_body(c, fx, fy, chest_half, bodice_h, rise, crotch_w,
                          neck_w, neck_drop, shoulder, armhole_w, armhole_drop,
                          leg_opening, "front")
        c.setFont("Tahoma-Bold", 10)
        c.drawString((fx + 0.5) * cm, (fy + bodice_h + rise * 0.1) * cm,
                     "1. Front - ตัด 1 ชิ้นบนรอยพับ")
        c.setFont("Tahoma", 7)
        c.drawString((fx + 0.5) * cm, (fy + bodice_h + rise * 0.05) * cm,
                     f"Size {size_label}")
        draw_fold_edge(c, fx, fy, fx, fy + bodice_h + rise)
        draw_grain_line(c,
                        fx + chest_half * 0.7, fy + bodice_h * 0.3,
                        fx + chest_half * 0.7, fy + bodice_h * 0.8)
        draw_notch(c, fx + chest_half, fy + bodice_h + rise * 0.7,
                   angle_deg=180)

        # snap markers on crotch
        c.setFillColor(red)
        for i in range(3):
            snap_x = fx + crotch_w * 0.3 + i * 1.3
            c.circle(snap_x * cm, (fy + 0.5) * cm, 0.15 * cm, fill=1)
        c.setFillColor(black)
        c.setFont("Tahoma", 6)
        c.setFillColor(red)
        c.drawString((fx + crotch_w + 0.3) * cm, (fy + 0.3) * cm,
                     "3 snaps")
        c.setFillColor(black)

        y_cursor = fy + bodice_h + rise + sa * 2 + gap

        # --- Back ---
        bx, by = 2.0, y_cursor
        _draw_romper_body(c, bx, by, chest_half, bodice_h, rise, crotch_w,
                          neck_w, neck_drop * 0.3, shoulder, armhole_w,
                          armhole_drop, leg_opening, "back")
        c.setFont("Tahoma-Bold", 10)
        c.drawString((bx + 0.5) * cm, (by + bodice_h + rise * 0.1) * cm,
                     "2. Back - ตัด 1 ชิ้นบนรอยพับ")
        draw_fold_edge(c, bx, by, bx, by + bodice_h + rise)
        draw_grain_line(c,
                        bx + chest_half * 0.7, by + bodice_h * 0.3,
                        bx + chest_half * 0.7, by + bodice_h * 0.8)

        y_cursor = by + bodice_h + rise + sa * 2 + gap

        # --- Strap ---
        sx, sy = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.rect(sx * cm, sy * cm, strap_len * cm, strap_w * cm)
        c.setFont("Tahoma-Bold", 9)
        c.drawString((sx + 0.5) * cm, (sy + strap_w * 0.55) * cm,
                     "3. Strap - ตัด 2 ชิ้น")
        c.setFont("Tahoma", 7)
        c.drawString((sx + 0.5) * cm, (sy + strap_w * 0.2) * cm,
                     f"{strap_len:.1f} x {strap_w:.1f}cm  (fold, sew, turn)")
        draw_grain_line(c,
                        sx + 2, sy + strap_w / 2,
                        sx + strap_len - 2, sy + strap_w / 2)
        draw_sa_rect_envelope(c, sx, sy, strap_len, strap_w, sa)

    instructions = [
        f"ชุดหมี - {size_label}",
        "",
        "วัสดุ:",
        "  - 0.7-0.9 m cotton lawn, double gauze, or light cotton",
        "  - Matching thread + 1 m bias tape",
        "  - 3 KAM snaps (crotch opening)",
        "  - 20 cm of 0.5cm elastic for leg openings",
        "",
        "ลำดับการเย็บ:",
        "  1. Cut: 1 front on fold, 1 back on fold, 2 straps",
        "  2. Make straps: fold RST, sew, turn, press",
        "  3. Sew side seams RST",
        "  4. Finish neckline + armholes with bias tape",
        "  5. Attach straps between front and back at back",
        "  6. Gather leg openings slightly + bind with bias",
        "  7. Install snaps at crotch (3 snaps along bottom edge)",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} cm",
    ]

    file_path = os.path.abspath(f"romper_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "ชุดหมี", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Romper pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"ตัวเสื้อ {chest_half * 2:.1f}x{bodice_h:.1f}cm | "
            f"Rise {rise:.1f}cm")


def _draw_romper_body(c, x, y, half_w, bodice_h, rise, crotch_w,
                       neck_w, neck_drop, shoulder, arm_w, arm_drop,
                       leg_opening, side):
    """Romper body outline (bodice on top + crotch extension on bottom)."""
    total_h = bodice_h + rise
    top = y + total_h
    mid = y + rise  # where bodice meets rise
    crotch_bottom = y

    c.setStrokeColor(black)
    c.setLineWidth(1.3)

    # bottom crotch edge (straight short segment at left edge = fold, extends to crotch_w)
    c.line(x * cm, crotch_bottom * cm,
           (x + crotch_w) * cm, crotch_bottom * cm)
    # leg opening curve (from crotch corner up and out to hip)
    draw_bezier_edge(c,
                     x + crotch_w, crotch_bottom,
                     x + crotch_w + 2, crotch_bottom + 1.5,
                     x + half_w - 2, mid - rise * 0.4,
                     x + half_w, mid)
    # side seam (bodice)
    c.line((x + half_w) * cm, mid * cm,
           (x + half_w) * cm, (top - arm_drop) * cm)
    # armhole
    draw_bezier_edge(c,
                     x + half_w, top - arm_drop,
                     x + half_w - 0.3, top - arm_drop * 0.4,
                     x + half_w - arm_w, top - 0.2,
                     x + neck_w + shoulder, top)
    # shoulder (strap attachment)
    c.line((x + neck_w + shoulder) * cm, top * cm,
           (x + neck_w) * cm, top * cm)
    # neckline
    draw_bezier_edge(c,
                     x + neck_w, top,
                     x + neck_w * 0.5, top,
                     x, top - neck_drop * 0.5,
                     x, top - neck_drop)
    # center front/back (fold)
    c.line(x * cm, (top - neck_drop) * cm, x * cm, crotch_bottom * cm)

    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.rect((x - 1) * cm, (y - 1) * cm,
           (half_w + 2) * cm, (total_h + 2) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)
