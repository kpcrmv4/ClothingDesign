"""Elastic-waist bloomers / diaper cover with curved crotch."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, tile_and_save)


def generate(size_label: str, seam_allowance: float = 1.0) -> str:
    spec = get_size(size_label)

    waist_half = spec["waist"] / 2 + 4.0
    hip_half = spec["hip"] / 2 + 4.0
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
    inseam = 3.0

    sa = seam_allowance
    total_w = hip_half + sa * 2 + 2
    total_h = rise + inseam + sa * 2 + 3

    def draw(c):
        x0 = 1.0 + sa
        y0 = 1.0 + sa + inseam

        waist_l = (x0, y0 + rise)
        waist_r = (x0 + waist_half, y0 + rise)
        hip_r = (x0 + hip_half, y0 + rise * 0.3)
        crotch = (x0 + waist_half * 0.15, y0)
        leg_inner = (x0 + waist_half * 0.15, y0 - inseam)
        leg_outer = (x0 + hip_half, y0 + rise * 0.15)

        c.setStrokeColor(black)
        c.setLineWidth(1.3)

        c.line(waist_l[0] * cm, waist_l[1] * cm,
               waist_r[0] * cm, waist_r[1] * cm)

        draw_bezier_edge(c,
                         waist_r[0], waist_r[1],
                         waist_r[0] + 0.3, waist_r[1] - rise * 0.3,
                         hip_r[0], hip_r[1] + rise * 0.1,
                         hip_r[0], hip_r[1])
        c.line(hip_r[0] * cm, hip_r[1] * cm,
               leg_outer[0] * cm, leg_outer[1] * cm)

        draw_bezier_edge(c,
                         leg_outer[0], leg_outer[1],
                         leg_outer[0] - 3, leg_outer[1] - 1.5,
                         leg_inner[0] + 3, leg_inner[1] + 0.5,
                         leg_inner[0], leg_inner[1])

        c.line(leg_inner[0] * cm, leg_inner[1] * cm,
               crotch[0] * cm, crotch[1] * cm)

        draw_bezier_edge(c,
                         crotch[0], crotch[1],
                         crotch[0] - 1.0, crotch[1] + 0.5,
                         waist_l[0] + 0.5, waist_l[1] - rise * 0.6,
                         waist_l[0], waist_l[1] - rise * 0.4)

        c.line(waist_l[0] * cm, (waist_l[1] - rise * 0.4) * cm,
               waist_l[0] * cm, waist_l[1] * cm)

        draw_fold_edge(c, waist_l[0], waist_l[1] - rise * 0.4,
                       waist_l[0], waist_l[1])

        c.setFont("Tahoma-Bold", 11)
        c.drawString((x0 + 2) * cm, (y0 + rise * 0.6) * cm,
                     "Bloomers - ตัด 2 ชิ้นบนรอยพับ")
        c.setFont("Tahoma", 8)
        c.drawString((x0 + 2) * cm, (y0 + rise * 0.55) * cm,
                     f"Size {size_label}  |  rise {rise:.1f}cm  |  "
                     f"waist {waist_half * 2:.1f}cm")
        c.setFont("Tahoma", 7)
        c.drawString((x0 + 2) * cm, (y0 + rise * 0.5) * cm,
                     "Elastic casings: fold 1.5cm at waist + leg openings")

        draw_grain_line(c,
                        x0 + waist_half * 0.6, y0 + rise * 0.2,
                        x0 + waist_half * 0.6, y0 + rise * 0.8)

        draw_notch(c, crotch[0], crotch[1], angle_deg=45)
        draw_notch(c, leg_inner[0], leg_inner[1], angle_deg=135)
        draw_notch(c, waist_l[0] + waist_half / 2, waist_r[1], angle_deg=270)

        c.setDash([4, 3], 0)
        c.setLineWidth(0.5)
        c.setStrokeColor(gray)
        c.rect((x0 - sa) * cm, (y0 - inseam - sa) * cm,
               (hip_half + sa * 2) * cm,
               (rise + inseam + sa * 2) * cm)
        c.setDash([], 0)
        c.setStrokeColor(black)

    instructions = [
        f"กางเกงใน Bloomers - {size_label}",
        "",
        "วัสดุ:",
        "  - 0.5 m of 115cm knit or woven cotton",
        "  - 1 cm wide elastic: 2 x leg (approx. 30cm each) + 1 waist",
        "  - Waist elastic length = child's waist - 2 cm",
        "",
        "ลำดับการเย็บ:",
        "  1. ตัด 2 ชิ้น pieces on fold (front + back identical)",
        "  2. Sew crotch seams RST (front to back) on both sides",
        "  3. Sew inseam + leg curve as one continuous seam",
        "  4. Fold waist edge 1.5 cm, sew leaving 3cm gap",
        "  5. Thread waist elastic through casing, close gap",
        "  6. Fold each leg opening 1.2 cm, thread leg elastic",
        "  7. Overlap elastic ends 1 cm, sew securely",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} cm",
    ]

    file_path = os.path.abspath(f"bloomers_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "กางเกงใน", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Bloomers pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Rise: {rise:.1f}cm  |  Waist half: {waist_half:.1f}cm")
