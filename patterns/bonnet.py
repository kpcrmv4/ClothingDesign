"""Traditional baby bonnet: crown + brim band + ties."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save,
                     THAI_FONT, THAI_FONT_BOLD)


def generate(size_label: str, seam_allowance: float = 1.0,
             output_dir: str = ".") -> str:
    spec = get_size(size_label)

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

        cx = 1.0 + sa + face_w
        cy_bottom = y_cursor
        cy_top = cy_bottom + crown_h

        c.setStrokeColor(black)
        c.setLineWidth(1.3)

        draw_bezier_edge(c,
                         cx - face_w, cy_bottom,
                         cx - face_w * 0.5, cy_bottom - 0.3,
                         cx + face_w * 0.5, cy_bottom - 0.3,
                         cx + face_w, cy_bottom)

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
        c.line((cx - back_w / 2) * cm, cy_top * cm,
               (cx + back_w / 2) * cm, cy_top * cm)
        draw_fold_edge(c, cx - back_w / 2, cy_top, cx + back_w / 2, cy_top)

        c.setFont(THAI_FONT_BOLD, 10)
        c.drawCentredString(cx * cm, (cy_bottom + crown_h * 0.55) * cm,
                            "1. Crown - ตัด 2 ชิ้นบนรอยพับ")
        c.setFont(THAI_FONT, 7)
        c.drawCentredString(cx * cm, (cy_bottom + crown_h * 0.45) * cm,
                            f"face {face_w * 2:.1f}cm | back {back_w:.1f}cm | "
                            f"depth {crown_h:.1f}cm")

        draw_grain_line(c,
                        cx, cy_bottom + crown_h * 0.15,
                        cx, cy_bottom + crown_h * 0.35)

        draw_notch(c, cx, cy_bottom, angle_deg=90)

        y_cursor = cy_top + sa * 2 + 2

        bx = 1.0 + sa
        by = y_cursor
        c.setLineWidth(1.3)
        draw_bezier_edge(c,
                         bx, by + band_h,
                         bx + band_l * 0.25, by + band_h + 0.3,
                         bx + band_l * 0.75, by + band_h + 0.3,
                         bx + band_l, by + band_h)
        c.line(bx * cm, by * cm, (bx + band_l) * cm, by * cm)
        c.line(bx * cm, by * cm, bx * cm, (by + band_h) * cm)
        c.line((bx + band_l) * cm, by * cm,
               (bx + band_l) * cm, (by + band_h) * cm)

        c.setFont(THAI_FONT_BOLD, 10)
        c.drawString((bx + 0.5) * cm, (by + band_h * 0.6) * cm,
                     "2. Brim Band - ตัด 2 ชิ้น")
        c.setFont(THAI_FONT, 7)
        c.drawString((bx + 0.5) * cm, (by + band_h * 0.3) * cm,
                     f"{band_l:.1f} x {band_h:.1f} cm  (interline for structure)")
        draw_grain_line(c,
                        bx + band_l * 0.5, by + 0.8,
                        bx + band_l * 0.5, by + band_h - 0.8)
        draw_notch(c, bx + band_l / 2, by + band_h, angle_deg=270)
        draw_sa_rect_envelope(c, bx, by, band_l, band_h, sa)

        y_cursor = by + band_h + sa * 2 + 2

        tx = 1.0 + sa
        ty = y_cursor
        c.setLineWidth(1.3)
        c.rect(tx * cm, ty * cm, tie_l * cm, tie_w * cm)
        c.setFont(THAI_FONT_BOLD, 9)
        c.drawString((tx + 0.5) * cm, (ty + tie_w * 0.55) * cm,
                     "3. Tie - ตัด 2 ชิ้น")
        c.setFont(THAI_FONT, 7)
        c.drawString((tx + 0.5) * cm, (ty + tie_w * 0.2) * cm,
                     f"{tie_l:.1f} x {tie_w:.1f} cm  (fold lengthwise, sew, turn)")
        draw_grain_line(c,
                        tx + 2, ty + tie_w / 2,
                        tx + tie_l - 2, ty + tie_w / 2)
        draw_sa_rect_envelope(c, tx, ty, tie_l, tie_w, sa)

    instructions = [
        f"หมวก - {size_label}",
        "",
        "วัสดุ:",
        "  - 0.3 m fashion fabric (quilting cotton, linen)",
        "  - 0.3 m lining (soft cotton lawn)",
        "  - 20 x 10 cm fusible interfacing (for brim)",
        "",
        "ลำดับการเย็บ:",
        "  1. ตัด 2 ชิ้น crown pieces on fold (outer + lining)",
        "  2. ตัด 2 ชิ้น brim bands + 1 interfacing, fuse to one band",
        "  3. ตัด 2 ชิ้น ties",
        "  4. Make ties: fold lengthwise RST, sew, turn, press",
        "  5. Sandwich ties at front ends of brim band",
        "  6. Sew brim bands RST along curved top, turn, press",
        "  7. Gather bottom edge of crown to match brim length",
        "  8. Attach crown to brim (outer fabric only)",
        "  9. Attach lining crown, turn through, hand-sew closing gap",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} ซม",
    ]

    file_path = os.path.abspath(os.path.join(output_dir, f"bonnet_pattern_{size_label}.pdf"))
    total_pages = tile_and_save(file_path, "หมวก", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Bonnet pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Face opening: {face_w * 2:.1f}cm")
