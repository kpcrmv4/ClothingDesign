"""
Sleeveless baby dress — curved neckline/armhole, shoulder straps, and a
gathered or bubble hem, with an optional front button placket.

skirt_style:
  gathered  ระบายชายกระโปรงแบบรูดจีบธรรมดา (ค่าเริ่มต้น)
  bubble    ชายบอลลูน — รูดจีบทั้งขอบบนและขอบล่าง แล้วเย็บกลับเข้าซับใน
"""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray, red

import geometry
from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save,
                     THAI_FONT, THAI_FONT_BOLD)
from symbols import draw_gather_marks, draw_button_placement, draw_buttonhole


def generate(size_label: str,
             seam_allowance: float = 1.0,
             skirt_style: str = "gathered",
             front_placket: bool = False,
             output_dir: str = ".") -> str:
    if skirt_style not in ("gathered", "bubble"):
        return (f"Error: skirt_style ต้องเป็น 'gathered' หรือ 'bubble' "
                f"ไม่ใช่ '{skirt_style}'")

    spec = get_size(size_label)
    d = geometry.dress_dims(spec, skirt_style=skirt_style,
                            front_placket=front_placket)

    bodice_w, bodice_h = d["bodice_w"], d["bodice_h"]
    ruffle_w, ruffle_h = d["ruffle_w"], d["ruffle_h"]
    strap_w, strap_h = d["strap_w"], d["strap_h"]
    is_bubble = skirt_style == "bubble"

    sa = seam_allowance
    gap = 2.0

    total_w = max(bodice_w, ruffle_w, strap_w, d["placket_w"]) + sa * 2 + 2
    total_h = (bodice_h + strap_h + ruffle_h + d["placket_h"]
               + sa * 8 + gap * 3 + 4)

    def draw(c):
        y_cursor = 2.0

        # ---------- 1. Bodice ----------
        bx, by = 2.0, y_cursor
        _draw_dress_bodice(c, bx, by, bodice_w, bodice_h,
                           d["neck_width"], d["neck_drop"], d["shoulder_w"],
                           d["armhole_width"], d["armhole_drop"], sa)
        c.setFont(THAI_FONT_BOLD, 10)
        c.drawString((bx + 0.3) * cm, (by + bodice_h - 1) * cm,
                     "1. ตัวเสื้อ - ตัด 2 ชิ้นบนรอยพับ")
        c.setFont(THAI_FONT, 8)
        c.drawString((bx + 0.3) * cm, (by + bodice_h - 1.7) * cm,
                     f"สำเร็จ: {bodice_w:.1f} x {bodice_h:.1f} ซม")
        draw_grain_line(c, bx + bodice_w * 0.7, by + 2,
                        bx + bodice_w * 0.7, by + bodice_h - 2)
        draw_fold_edge(c, bx, by, bx, by + bodice_h)
        draw_notch(c, bx + bodice_w, by + bodice_h * 0.5, angle_deg=180)

        if front_placket:
            # Button positions run down the centre front of the front piece.
            c.setFillColor(red)
            c.setStrokeColor(red)
            n = d["button_count"]
            span = bodice_h - 3.0
            for i in range(n):
                cy = by + 1.5 + span * i / max(n - 1, 1)
                draw_button_placement(c, bx + 0.8, cy, diameter=0.7)
            c.setFont(THAI_FONT, 6)
            c.drawString((bx + 1.5) * cm, (by + 0.6) * cm,
                         f"ตำแหน่งกระดุม {n} เม็ด (เฉพาะชิ้นหน้า)")
            c.setStrokeColor(black)
            c.setFillColor(black)

        y_cursor = by + bodice_h + sa * 2 + gap

        # ---------- 2. Straps ----------
        sx, sy = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.setStrokeColor(black)
        c.rect(sx * cm, sy * cm, strap_w * cm, strap_h * cm)
        draw_sa_rect_envelope(c, sx, sy, strap_w, strap_h, sa)
        c.setFont(THAI_FONT_BOLD, 9)
        c.drawString((sx + 0.2) * cm, (sy + strap_h - 0.7) * cm,
                     "2. สายไหล่ - ตัด 2 ชิ้น")
        c.setFont(THAI_FONT, 7)
        c.drawString((sx + 0.2) * cm, (sy + strap_h - 1.3) * cm,
                     f"{strap_w:.1f} x {strap_h:.1f} ซม")
        draw_grain_line(c, sx + strap_w / 2, sy + 1,
                        sx + strap_w / 2, sy + strap_h - 1)

        y_cursor = sy + strap_h + sa * 2 + gap

        # ---------- 3. Skirt / ruffle ----------
        rx, ry = 2.0, y_cursor
        c.setLineWidth(1.3)
        c.setStrokeColor(black)
        c.rect(rx * cm, ry * cm, ruffle_w * cm, ruffle_h * cm)
        draw_sa_rect_envelope(c, rx, ry, ruffle_w, ruffle_h, sa)

        c.setFont(THAI_FONT_BOLD, 9)
        if is_bubble:
            c.drawString((rx + 0.2) * cm, (ry + ruffle_h - 0.7) * cm,
                         "3. กระโปรงทรงบอลลูน - ตัด 2 ชิ้น (รูดจีบทั้งบนและล่าง)")
        else:
            c.drawString((rx + 0.2) * cm, (ry + ruffle_h - 0.7) * cm,
                         "3. ระบาย - ตัด 2 ชิ้น (รูดจีบขอบบน)")
        c.setFont(THAI_FONT, 7)
        c.drawString((rx + 0.2) * cm, (ry + ruffle_h - 1.3) * cm,
                     f"{ruffle_w:.1f} x {ruffle_h:.1f} ซม  "
                     f"(กว้าง {ruffle_w / (bodice_w * 2):.1f} เท่าชายเสื้อ)")

        draw_gather_marks(c, rx + 0.5, ry + ruffle_h, rx + ruffle_w - 0.5,
                          ry + ruffle_h, n_ticks=max(6, int(ruffle_w / 4)))
        for frac in (0.25, 0.5, 0.75):
            draw_notch(c, rx + ruffle_w * frac, ry + ruffle_h, angle_deg=270)

        if is_bubble:
            # The lower edge is gathered too, then turned up into the lining.
            draw_gather_marks(c, rx + 0.5, ry, rx + ruffle_w - 0.5, ry,
                              n_ticks=max(6, int(ruffle_w / 4)))
            c.setFillColor(gray)
            c.setFont(THAI_FONT, 6)
            c.drawString((rx + 0.2) * cm, (ry + 0.45) * cm,
                         f"ขอบล่าง: รูดจีบให้เหลือเท่าชายเสื้อ แล้วเย็บกลับเข้าซับใน "
                         f"(ชายสำเร็จ ~{d['bubble_finished_h']:.1f} ซม)")
            c.setFillColor(black)
        else:
            c.setFont(THAI_FONT, 7)
            c.drawString((rx + 0.2) * cm, (ry + 0.35) * cm,
                         "ขอบล่าง: พับเย็บชาย 1 ซม")
        draw_grain_line(c, rx + ruffle_w / 2 - 2, ry + ruffle_h / 2,
                        rx + ruffle_w / 2 + 2, ry + ruffle_h / 2)

        y_cursor = ry + ruffle_h + sa * 2 + gap

        # ---------- 4. Front placket ----------
        if front_placket:
            px, py = 2.0, y_cursor
            pw, ph = d["placket_w"], d["placket_h"]
            c.setLineWidth(1.3)
            c.setStrokeColor(black)
            c.rect(px * cm, py * cm, pw * cm, ph * cm)
            draw_sa_rect_envelope(c, px, py, pw, ph, sa)
            c.setFont(THAI_FONT_BOLD, 9)
            c.drawString((px + 0.2) * cm, (py + ph - 0.7) * cm,
                         "4. สาบกระดุมหน้า - ตัด 2 ชิ้น (รีดผ้ากาว 1 ชิ้น)")
            c.setFont(THAI_FONT, 7)
            c.drawString((px + 0.2) * cm, (py + ph - 1.3) * cm,
                         f"{pw:.1f} x {ph:.1f} ซม  (พับครึ่งตามยาว)")
            n = d["button_count"]
            span = ph - 3.0
            for i in range(n):
                cy = py + 1.5 + span * i / max(n - 1, 1)
                draw_buttonhole(c, px + pw / 2, cy, length=1.0,
                                horizontal=False)
            draw_grain_line(c, px + pw / 2, py + 1.5,
                            px + pw / 2, py + ph - 1.5)

    instructions = _instructions(size_label, d, seam_allowance,
                                 skirt_style, front_placket)

    file_path = os.path.abspath(os.path.join(
        output_dir, f"dress_pattern_{size_label}.pdf"))
    total_pages = tile_and_save(file_path, "เดรสเด็ก", size_label,
                                total_w, total_h, draw, instructions)

    style_th = "ชายบอลลูน" if is_bubble else "ชายระบายรูดจีบ"
    extra = " + สาบกระดุมหน้า" if front_placket else ""
    return (f"Dress pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets  |  "
            f"{style_th}{extra}\n"
            f"ตัวเสื้อ: {bodice_w:.1f}x{bodice_h:.1f} cm  |  "
            f"กระโปรง: {ruffle_w:.1f}x{ruffle_h:.1f} cm")


def _instructions(size_label, d, sa, skirt_style, front_placket):
    is_bubble = skirt_style == "bubble"
    lines = [
        f"เดรสเด็ก - {size_label}",
        f"ทรงชาย: {'บอลลูน (bubble hem)' if is_bubble else 'ระบายรูดจีบ'}"
        + ("  |  มีสาบกระดุมหน้า" if front_placket else ""),
        "",
        "วัสดุ:",
        "  - ผ้าคอตตอนหรือลินินไม่หนา ประมาณ 0.6-0.8 ม. ผ้ากว้าง 115 ซม",
        "  - ด้ายสีเข้ากับผ้า",
        "  - ผ้ากุ๊นสำเร็จ 1 ม. (ขอบคอและวงแขน)",
    ]
    if front_placket:
        lines.append(f"  - กระดุมเล็ก {d['button_count']} เม็ด "
                     f"+ ผ้ากาวเส้นสาบ")
    if is_bubble:
        lines.append("  - ผ้าซับชายกระโปรง ~0.2 ม. (สีเดียวกันหรือสีขาว)")

    lines += [
        "",
        "คำอธิบายสัญลักษณ์:",
        "  เส้นตัน      = เส้นตัด",
        "  เส้นประเทา   = ส่วนตะเข็บ (เพิ่มเมื่อตัด)",
        "  โซ่สีน้ำเงิน  = ตัดบนรอยพับ อย่าตัดขอบนี้",
        "  รอยหยักวี    = จับคู่ด้วยเครื่องหมายนี้",
        "  เส้นประ+ขีด  = ขอบที่ต้องรูดจีบ",
        "  ลูกศรเมล็ด   = จัดให้ชิดไปตามเส้นเนื้อผ้า",
        "",
        "ลำดับการเย็บ:",
        "  1. ตัดตัวเสื้อ 2 ชิ้นบนรอยพับ (หน้า + หลัง)",
        "  2. ตัดสายไหล่ 2 ชิ้น และกระโปรง 2 ชิ้น",
    ]
    step = 3
    if front_placket:
        lines += [
            f"  {step}. รีดผ้ากาวลงสาบ 1 ชิ้น พับครึ่งตามยาว รีดให้เรียบ",
            f"  {step + 1}. เย็บสาบติดริมกลางหน้าทั้งสองข้าง เจาะรังดุมตามตำแหน่ง",
        ]
        step += 2
    lines += [
        f"  {step}. พับสายไหล่ตามยาว เย็บ กลับด้าน รีดให้เรียบ",
        f"  {step + 1}. ติดสายไหล่ระหว่างตัวหน้าและตัวหลังที่ตำแหน่งไหล่",
        f"  {step + 2}. เย็บตะเข็บด้านข้างตัวเสื้อทั้งสองด้าน",
    ]
    step += 3
    if is_bubble:
        lines += [
            f"  {step}. เย็บตะเข็บข้างกระโปรงให้เป็นวง",
            f"  {step + 1}. รูดจีบขอบล่างกระโปรงให้เหลือเท่าชายตัวเสื้อ "
            f"แล้วเย็บติดผ้าซับชาย",
            f"  {step + 2}. พลิกผ้าซับขึ้นด้านใน ทำให้ชายพองเป็นทรงบอลลูน "
            f"(ชายสำเร็จ ~{d['bubble_finished_h']:.1f} ซม)",
            f"  {step + 3}. รูดจีบขอบบนกระโปรงให้เท่าชายตัวเสื้อ แล้วเย็บติดกัน",
        ]
        step += 4
    else:
        lines += [
            f"  {step}. เย็บตะเข็บข้างกระโปรงให้เป็นวง",
            f"  {step + 1}. รูดจีบขอบบนกระโปรงให้เท่าชายตัวเสื้อ แล้วเย็บติดกัน "
            f"(ด้านในประกบด้านใน)",
            f"  {step + 2}. พับชายกระโปรงเข้า 1 ซม. เย็บให้เรียบร้อย",
        ]
        step += 3
    lines += [
        f"  {step}. จบขอบคอและวงแขนด้วยผ้ากุ๊น",
        f"  {step + 1}. รีดทุกตะเข็บ ตรวจความเรียบร้อย",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {sa} ซม ทุกขอบ",
    ]
    return lines


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
