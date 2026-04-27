"""Sleeveless baby dress with curved neckline/armhole, straps, and gathered ruffle."""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, tile_and_save)


def generate(size_label: str, seam_allowance: float = 1.0) -> str:
    spec = get_size(size_label)

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

        bx, by = 2.0, y_cursor
        _draw_dress_bodice(c, bx, by, bodice_w, bodice_h,
                           neck_width, neck_drop, shoulder_w,
                           armhole_width, armhole_drop, sa)
        c.setFont("Tahoma-Bold", 10)
        c.drawString((bx + 0.3) * cm, (by + bodice_h - 1) * cm,
                     "1. ตัวเสื้อ - ตัด 2 ชิ้นบนรอยพับ")
        c.setFont("Tahoma", 8)
        c.drawString((bx + 0.3) * cm, (by + bodice_h - 1.7) * cm,
                     f"สำเร็จ: {bodice_w:.1f} x {bodice_h:.1f} ซม")
        draw_grain_line(c, bx + bodice_w * 0.7, by + 2,
                        bx + bodice_w * 0.7, by + bodice_h - 2)
        draw_fold_edge(c, bx, by, bx, by + bodice_h)
        draw_notch(c, bx + bodice_w, by + bodice_h * 0.5, angle_deg=180)

        y_cursor = by + bodice_h + sa * 2 + gap

        sx, sy = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.rect(sx * cm, sy * cm, strap_w * cm, strap_h * cm)
        c.setDash([4, 3], 0)
        c.setLineWidth(0.5)
        c.rect((sx - sa) * cm, (sy - sa) * cm,
               (strap_w + sa * 2) * cm, (strap_h + sa * 2) * cm)
        c.setDash([], 0)
        c.setFont("Tahoma-Bold", 9)
        c.drawString((sx + 0.2) * cm, (sy + strap_h - 0.7) * cm,
                     "2. สายไหล่ - ตัด 2 ชิ้น")
        c.setFont("Tahoma", 7)
        c.drawString((sx + 0.2) * cm, (sy + strap_h - 1.3) * cm,
                     f"{strap_w:.1f} x {strap_h:.1f} ซม")
        draw_grain_line(c, sx + strap_w / 2, sy + 1,
                        sx + strap_w / 2, sy + strap_h - 1)

        y_cursor = sy + strap_h + sa * 2 + gap

        rx, ry = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.rect(rx * cm, ry * cm, ruffle_w * cm, ruffle_h * cm)
        c.setDash([4, 3], 0)
        c.setLineWidth(0.5)
        c.rect((rx - sa) * cm, (ry - sa) * cm,
               (ruffle_w + sa * 2) * cm, (ruffle_h + sa * 2) * cm)
        c.setDash([], 0)
        c.setFont("Tahoma-Bold", 9)
        c.drawString((rx + 0.2) * cm, (ry + ruffle_h - 0.7) * cm,
                     "3. ระบาย - ตัด 2 ชิ้น (รูดจีบขอบบน)")
        c.setFont("Tahoma", 7)
        c.drawString((rx + 0.2) * cm, (ry + ruffle_h - 1.3) * cm,
                     f"{ruffle_w:.1f} x {ruffle_h:.1f} ซม  (กว้าง 1.5 เท่าชายผ้า)")
        draw_grain_line(c, rx + ruffle_w / 2 - 2, ry + ruffle_h / 2,
                        rx + ruffle_w / 2 + 2, ry + ruffle_h / 2)
        for frac in (0.25, 0.5, 0.75):
            draw_notch(c, rx + ruffle_w * frac, ry + ruffle_h, angle_deg=270)

    instructions = [
        f"เดรสเด็ก - {size_label}",
        "",
        "วัสดุ:",
        "  - ผ้าคอตตอนหรือลินินไม่หนา ประมาณ 0.6-0.8 ม. ผ้ากว้าง 115 ซม",
        "  - ด้ายสีเข้มกับผ้า กระดุมหรือ snap ขนาดเล็ก 2-3 เม็ด (ทางเลือก)",
        "",
        "คำอธิบายสัญลักษณ์:",
        "  เส้นตัน      = เส้นตัด",
        "  เส้นประ      = ส่วนตะเข็บ (เพิ่มเมื่อตัด)",
        "  โซ่สีน้ำเงิน  = ตัดบนรอยพับ อย่าตัดขอบนี้",
        "  รอยหยักวี    = จับคู่ด้วยเครื่องหมายนี้",
        "  ลูกศรเมล็ด   = จัดให้ชิดไปตามเส้นเนื้อผ้า",
        "",
        "ลำดับการเย็บ:",
        "  1. ตัดตัวเสื้อ 2 ชิ้นบนรอยพับ (หน้า + หลัง)",
        "  2. ตัดสายไหล่ 2 ชิ้น",
        "  3. ตัดระบาย 2 ชิ้น",
        "  4. เย็บตะเข็บไหล่ตัวเสื้อ (หน้ากับหลังบริเวณสายไหล่)",
        "  5. พับสายไหล่ยาวตามปกติ เย็บ หมุนให้เรียบ",
        "  6. ติดสายไหล่ระหว่างหน้าและหลังที่ไหล่",
        "  7. เย็บตะเข็บด้านข้างตัวเสื้อ",
        "  8. รูดจีบขอบบนของระบายให้มีขนาดเท่าชายตัวเสื้อ",
        "  9. ติดระบายกับชายเสื้อแบบด้านในประกบใน",
        " 10. จบชายระบายด้วยความสวยงาม",
        " 11. จบคอเสื้อและวงแขนด้วยแถบผ้าเอียง",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {seam_allowance} ซม ทุกขอบ",
    ]

    file_path = os.path.abspath(f"dress_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "เดรสเด็ก", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Dress pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"ตัวเสื้อ: {bodice_w:.1f}x{bodice_h:.1f} cm  |  "
            f"Ruffle: {ruffle_w:.1f}x{ruffle_h:.1f} cm")


def _draw_dress_bodice(c, x, y, w, h, neck_w, neck_drop, shoulder_w,
                        arm_w, arm_drop, sa):
    neck_start = (x, y + h - neck_drop)
    neck_end = (x + neck_w, y + h)
    shoulder_tip = (min(x + neck_w + shoulder_w, x + w - 0.5), y + h)
    underarm = (x + w, y + h - arm_drop)

    c.setLineWidth(1.3)
    c.setStrokeColor(black)
    c.line((x + w) * cm, y * cm, underarm[0] * cm, underarm[1] * cm)
    c.line(x * cm, y * cm, (x + w) * cm, y * cm)
    c.line(neck_end[0] * cm, neck_end[1] * cm,
           shoulder_tip[0] * cm, shoulder_tip[1] * cm)

    draw_bezier_edge(c,
                     neck_start[0], neck_start[1],
                     neck_start[0] + neck_w * 0.3, neck_start[1],
                     neck_end[0], neck_end[1] - neck_drop * 0.3,
                     neck_end[0], neck_end[1])

    draw_bezier_edge(c,
                     shoulder_tip[0], shoulder_tip[1],
                     shoulder_tip[0] + (underarm[0] - shoulder_tip[0]) * 0.2,
                     shoulder_tip[1] - arm_drop * 0.4,
                     underarm[0] - arm_w * 0.5,
                     underarm[1] + arm_drop * 0.3,
                     underarm[0], underarm[1])

    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.line(x * cm, (y - sa) * cm, (x + w + sa) * cm, (y - sa) * cm)
    c.line((x + w + sa) * cm, (y - sa) * cm,
           (x + w + sa) * cm, (y + h + sa) * cm)
    c.line((x + w + sa) * cm, (y + h + sa) * cm, x * cm, (y + h + sa) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)
