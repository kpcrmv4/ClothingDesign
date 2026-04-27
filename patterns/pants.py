"""Baby elastic-waist pants — long or short, curved crotch + side."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_bezier_edge,
                     tile_and_save)


def generate(size_label: str, seam_allowance: float = 1.0,
             style: str = "long") -> str:
    if style not in ("long", "short"):
        return f"Error: style must be 'long' or 'short', got '{style}'"

    spec = get_size(size_label)

    hip_half = spec["hip"] / 4 + 3.0
    waist_half = spec["waist"] / 4 + 2.0
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 3.0

    if style == "long":
        leg_length = spec["length"] * 1.15
        leg_opening = spec["hip"] / 8 + 2.5
    else:
        leg_length = spec["length"] * 0.4
        leg_opening = spec["hip"] / 6 + 3.0

    sa = seam_allowance
    total_w = max(hip_half, leg_opening + 3) + sa * 2 + 3
    total_h = leg_length + rise + sa * 2 + 3

    def draw(c):
        x0 = 1.0 + sa + 1
        y0 = 1.0 + sa

        waist_l = (x0, y0 + leg_length + rise)
        waist_r = (x0 + waist_half, y0 + leg_length + rise)
        hip_r = (x0 + hip_half, y0 + leg_length + rise * 0.5)
        crotch = (x0, y0 + leg_length)
        inseam_tip = (x0 + 3, y0 + leg_length - 1)
        leg_inner = (x0 + (hip_half - leg_opening) / 2 + 1, y0)
        leg_outer = (x0 + (hip_half - leg_opening) / 2 + 1 + leg_opening, y0)
        hem_side_r = (x0 + hip_half * 0.85, y0 + leg_length * 0.1)

        c.setStrokeColor(black)
        c.setLineWidth(1.3)

        # waist
        c.line(waist_l[0] * cm, waist_l[1] * cm,
               waist_r[0] * cm, waist_r[1] * cm)
        # side seam (curved from waist to hip to leg)
        draw_bezier_edge(c,
                         waist_r[0], waist_r[1],
                         waist_r[0] + 0.5, waist_r[1] - rise * 0.3,
                         hip_r[0], hip_r[1] + rise * 0.1,
                         hip_r[0], hip_r[1])
        # outer leg (hip down to leg opening)
        draw_bezier_edge(c,
                         hip_r[0], hip_r[1],
                         hip_r[0] - 0.5, hip_r[1] - leg_length * 0.4,
                         hem_side_r[0] + 0.5, hem_side_r[1] + 2,
                         leg_outer[0], leg_outer[1])
        # hem
        c.line(leg_outer[0] * cm, leg_outer[1] * cm,
               leg_inner[0] * cm, leg_inner[1] * cm)
        # inseam (leg inner to crotch)
        draw_bezier_edge(c,
                         leg_inner[0], leg_inner[1],
                         leg_inner[0] - 0.5, leg_inner[1] + leg_length * 0.3,
                         inseam_tip[0] + 0.5, inseam_tip[1] - 1,
                         inseam_tip[0], inseam_tip[1])
        # crotch curve
        draw_bezier_edge(c,
                         inseam_tip[0], inseam_tip[1],
                         inseam_tip[0] - 1, inseam_tip[1] + 0.5,
                         crotch[0] + 0.5, crotch[1] + 1,
                         crotch[0], crotch[1] + 1.5)
        # center seam (from crotch straight up to waist)
        c.line(crotch[0] * cm, (crotch[1] + 1.5) * cm,
               waist_l[0] * cm, waist_l[1] * cm)

        c.setFont("Tahoma-Bold", 11)
        c.drawString((x0 + 1) * cm, (y0 + leg_length + rise * 0.5) * cm,
                     f"Pants ({style}) - ตัด 2 ชิ้น mirrored")
        c.setFont("Tahoma", 7)
        c.drawString((x0 + 1) * cm, (y0 + leg_length + rise * 0.4) * cm,
                     f"Size {size_label}  |  Rise {rise:.1f}cm  |  "
                     f"Leg {leg_length:.1f}cm")
        c.drawString((x0 + 1) * cm, (y0 + leg_length + rise * 0.3) * cm,
                     "Elastic casing at waist: fold 2.5cm")

        draw_grain_line(c,
                        x0 + hip_half * 0.5, y0 + leg_length * 0.2,
                        x0 + hip_half * 0.5, y0 + leg_length * 0.8)

        # notches
        draw_notch(c, crotch[0], crotch[1] + 1.5, angle_deg=0)
        draw_notch(c, inseam_tip[0], inseam_tip[1], angle_deg=225)
        draw_notch(c, x0 + waist_half / 2, waist_r[1], angle_deg=270)

        c.setDash([4, 3], 0)
        c.setLineWidth(0.5)
        c.setStrokeColor(gray)
        c.rect((x0 - sa) * cm, (y0 - sa) * cm,
               (hip_half + sa * 2) * cm,
               (leg_length + rise + sa * 2) * cm)
        c.setDash([], 0)
        c.setStrokeColor(black)

    instructions = [
        f"กางเกง{'ขายาว' if style == 'long' else 'ขาสั้น'} - {size_label}",
        "",
        "วัสดุ:",
        "  - ผ้านิตหรือคอตตอนทอ 0.5 ม. กว้าง 115 ซม",
        "  - ด้ายสีเข้มกับผ้า",
        "  - ยางยืดกว้าง 2 ซม = รอบเอวเด็ก - 2 ซม",
        "",
        "ลำดับการเย็บ:",
        "  1. ตัดขา 2 ชิ้น (ซ้ายขวา)",
        "  2. เย็บตะเข็บเป้า ด้านในประกบใน (หน้ากับหลัง) ทั้งสองขา",
        "  3. หมุนขาข้างหนึ่งให้ด้านหน้าออก ใส่เข้าไปในขาอีกข้าง ด้านในประกบใน",
        "  4. เย็บตะเข็บด้านในต่อเนื่องจากข้อต่อขอ ผ่านเป้า",
        "  5. พับเอว 2.5 ซม เย็บปลอกร้อยยาง เว้นช่องว่าง 3 ซม",
        "  6. ใส่ยางยืด ทับซ้อน 1 ซม เย็บปิด",
        "  7. ปิดช่องว่างปลอกร้อยยาง เย็บตามขอบเอว",
        "  8. จบชายขา 1.5 ซม (หรือเพิ่มผ้าห่อข้อเท้า)",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} ซม",
        f"ลักษณะ: {style}",
    ]

    file_path = os.path.abspath(f"pants_pattern_{size_label}_{style}.pdf")
    total_pages = tile_and_save(file_path, f"กางเกงเด็ก ({style})", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Pants pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Style: {style}  |  "
            f"Pages: {total_pages} A4 sheets\n"
            f"Rise: {rise:.1f}cm  |  Leg length: {leg_length:.1f}cm")
