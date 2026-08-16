"""
Short pull-on top with flutter sleeves — the white blouse worn under a
pinafore or strap dress.

neck_finish:
  ruffle   คอระบายตั้งขึ้นรอบคอ (รูดจีบแถบผ้าแล้วเย็บติดขอบคอ)
  binding  คอเรียบ กุ๊นด้วยแถบผ้าเฉลียง

The flutter sleeve is a flared strip gathered into the armhole, so it falls
open over the shoulder instead of forming a closed tube — no underarm seam.
"""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray

import geometry
from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save,
                     THAI_FONT, THAI_FONT_BOLD)
from symbols import draw_gather_marks

_FINISH_TH = {"ruffle": "คอระบายตั้ง", "binding": "คอเรียบกุ๊น"}


def generate(size_label: str,
             seam_allowance: float = 1.0,
             sleeve_fullness: float = 1.8,
             neck_finish: str = "ruffle",
             output_dir: str = ".") -> str:
    if neck_finish not in _FINISH_TH:
        return (f"Error: neck_finish ต้องเป็น 'ruffle' หรือ 'binding' "
                f"ไม่ใช่ '{neck_finish}'")
    if not 1.2 <= sleeve_fullness <= 2.5:
        return (f"Error: sleeve_fullness ต้องอยู่ระหว่าง 1.2-2.5 "
                f"ไม่ใช่ {sleeve_fullness}")

    spec = get_size(size_label)
    d = geometry.flutter_top_dims(spec, sleeve_fullness=sleeve_fullness,
                                  neck_finish=neck_finish)

    sa = seam_allowance
    gap = 2.0

    total_w = max(d["chest_half"], d["sleeve_w"],
                  d["neck_strip_l"]) + sa * 2 + 2
    total_h = (d["length"] * 2 + d["sleeve_h"] + d["neck_strip_h"]
               + sa * 8 + gap * 3 + 4)

    def draw(c):
        y = 2.0

        # ---------- 1. Front ----------
        _draw_body(c, 2.0, y, d, d["neck_drop_front"], sa)
        c.setFont(THAI_FONT_BOLD, 10)
        c.drawString(2.4 * cm, (y + d["length"] * 0.55) * cm,
                     "1. ตัวหน้า - ตัด 1 ชิ้นบนรอยพับ")
        c.setFont(THAI_FONT, 7)
        c.drawString(2.4 * cm, (y + d["length"] * 0.49) * cm,
                     f"ไซส์ {size_label} | คอลึกกว่าด้านหลัง")
        c.drawString(2.4 * cm, (y + d["length"] * 0.43) * cm,
                     f"ครึ่งตัว {d['chest_half']:.1f} x {d['length']:.1f} ซม.")
        draw_fold_edge(c, 2.0, y, 2.0, y + d["length"])
        draw_grain_line(c, 2.0 + d["chest_half"] * 0.7, y + 1.5,
                        2.0 + d["chest_half"] * 0.7, y + d["length"] - 1.5)
        y += d["length"] + sa * 2 + gap

        # ---------- 2. Back ----------
        _draw_body(c, 2.0, y, d, d["neck_drop_back"], sa)
        c.setFont(THAI_FONT_BOLD, 10)
        c.drawString(2.4 * cm, (y + d["length"] * 0.55) * cm,
                     "2. ตัวหลัง - ตัด 1 ชิ้นบนรอยพับ")
        c.setFont(THAI_FONT, 7)
        c.drawString(2.4 * cm, (y + d["length"] * 0.49) * cm,
                     "คอตื้นกว่าด้านหน้า")
        draw_fold_edge(c, 2.0, y, 2.0, y + d["length"])
        draw_grain_line(c, 2.0 + d["chest_half"] * 0.7, y + 1.5,
                        2.0 + d["chest_half"] * 0.7, y + d["length"] - 1.5)
        y += d["length"] + sa * 2 + gap

        # ---------- 3. Flutter sleeve ----------
        sw, sh = d["sleeve_w"], d["sleeve_h"]
        _draw_flutter_sleeve(c, 2.0, y, sw, sh, sa)
        c.setFont(THAI_FONT_BOLD, 9)
        c.drawString(2.3 * cm, (y + sh - 0.7) * cm,
                     "3. แขนระบาย - ตัด 2 ชิ้น")
        c.setFont(THAI_FONT, 7)
        c.drawString(2.3 * cm, (y + sh - 1.3) * cm,
                     f"{sw:.1f} x {sh:.1f} ซม. "
                     f"(ขอบบนรูดจีบให้เหลือ {d['sleeve_cap']:.1f} ซม.)")
        draw_gather_marks(c, 2.5, y + sh, 2.0 + sw - 0.5, y + sh,
                          n_ticks=max(6, int(sw / 3)))
        for frac in (0.25, 0.5, 0.75):
            draw_notch(c, 2.0 + sw * frac, y + sh, angle_deg=270)
        draw_grain_line(c, 2.0 + sw / 2 - 2, y + sh / 2,
                        2.0 + sw / 2 + 2, y + sh / 2)
        y += sh + sa * 2 + gap

        # ---------- 4. Neck strip ----------
        nl, nh = d["neck_strip_l"], d["neck_strip_h"]
        c.setLineWidth(1.3)
        c.setStrokeColor(black)
        c.rect(2.0 * cm, y * cm, nl * cm, nh * cm)
        draw_sa_rect_envelope(c, 2.0, y, nl, nh, sa)
        c.setFont(THAI_FONT_BOLD, 9)
        if neck_finish == "ruffle":
            c.drawString(2.3 * cm, (y + nh - 0.7) * cm,
                         "4. แถบคอระบาย - ตัด 1 ชิ้น (รูดจีบ)")
            draw_gather_marks(c, 2.5, y, 2.0 + nl - 0.5, y,
                              n_ticks=max(6, int(nl / 3)))
        else:
            c.drawString(2.3 * cm, (y + nh - 0.7) * cm,
                         "4. แถบกุ๊นคอ - ตัด 1 ชิ้น (ตัดเฉลียง 45°)")
        c.setFont(THAI_FONT, 7)
        c.drawString(2.3 * cm, (y + nh - 1.3) * cm,
                     f"{nl:.1f} x {nh:.1f} ซม. (พับครึ่งตามยาว)")
        draw_grain_line(c, 2.0 + nl / 2 - 2, y + nh / 2,
                        2.0 + nl / 2 + 2, y + nh / 2)

    instructions = _instructions(size_label, d, seam_allowance, neck_finish)

    file_path = os.path.abspath(os.path.join(
        output_dir, f"flutter_top_pattern_{size_label}.pdf"))
    total_pages = tile_and_save(file_path, "เสื้อคอระบายแขนระบาย", size_label,
                                total_w, total_h, draw, instructions)

    return (f"Flutter top pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets  |  "
            f"{_FINISH_TH[neck_finish]}\n"
            f"ตัวเสื้อครึ่งตัว {d['chest_half']:.1f}x{d['length']:.1f} ซม.  |  "
            f"แขนระบาย {d['sleeve_w']:.1f}x{d['sleeve_h']:.1f} ซม.")


def _draw_body(c, x, y, d, neck_drop, sa):
    """Front or back body half-piece; left edge is the centre fold."""
    w, h = d["chest_half"], d["length"]
    neck_w = d["neck_width"]
    shoulder_tip = min(x + neck_w + d["shoulder_w"], x + w - 0.5)

    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    c.line(x * cm, y * cm, (x + w) * cm, y * cm)                      # hem
    c.line((x + neck_w) * cm, (y + h) * cm,
           shoulder_tip * cm, (y + h) * cm)                           # shoulder
    draw_bezier_edge(c,
                     x, y + h - neck_drop,
                     x + neck_w * 0.35, y + h - neck_drop,
                     x + neck_w, y + h - neck_drop * 0.3,
                     x + neck_w, y + h)                               # neckline
    draw_bezier_edge(c,
                     shoulder_tip, y + h,
                     shoulder_tip + (x + w - shoulder_tip) * 0.25,
                     y + h - d["armhole_drop"] * 0.35,
                     x + w - d["armhole_width"] * 0.5,
                     y + h - d["armhole_drop"] * 0.7,
                     x + w, y + h - d["armhole_drop"])                # armhole
    c.line((x + w) * cm, (y + h - d["armhole_drop"]) * cm,
           (x + w) * cm, y * cm)                                      # side
    draw_notch(c, x + w, y + h - d["armhole_drop"] - 1.0, angle_deg=180)
    draw_sa_rect_envelope(c, x, y, w, h, sa)


def _draw_flutter_sleeve(c, x, y, w, h, sa):
    """Flared strip: straight gathered top, gently curved falling hem."""
    c.setStrokeColor(black)
    c.setLineWidth(1.3)
    c.line(x * cm, (y + h) * cm, (x + w) * cm, (y + h) * cm)   # gathered edge
    c.line(x * cm, (y + h) * cm, x * cm, (y + h * 0.35) * cm)  # front edge
    c.line((x + w) * cm, (y + h) * cm,
           (x + w) * cm, (y + h * 0.35) * cm)                  # back edge
    draw_bezier_edge(c,
                     x, y + h * 0.35,
                     x + w * 0.2, y - h * 0.05,
                     x + w * 0.8, y - h * 0.05,
                     x + w, y + h * 0.35)                      # curved hem
    c.setFillColor(gray)
    c.setFont(THAI_FONT, 6)
    c.drawString((x + 0.3) * cm, (y + h * 0.15) * cm,
                 "ชายโค้ง: เย็บริมม้วนแคบ 6 มม.")
    c.setFillColor(black)
    draw_sa_rect_envelope(c, x, y, w, h, sa)


def _instructions(size_label, d, sa, neck_finish):
    lines = [
        f"เสื้อคอระบาย แขนระบาย - ไซส์ {size_label}",
        f"แบบคอ: {_FINISH_TH[neck_finish]}  |  "
        f"ความฟูแขน {d['sleeve_fullness']}x",
        "",
        "ใส่คู่กับ: เดรสสายไหล่ (generate_full_dress_pattern) หรือ",
        "          เดรสกระโปรงชั้น (generate_tiered_dress_pattern)",
        "          เพื่อได้ลุคเอี๊ยมทับเสื้อคอระบาย",
        "",
        "วัสดุ:",
        "  - ผ้าคอตตอนบางสีขาว ~0.4-0.5 ม. (หน้ากว้าง 115 ซม.)",
        "    แนะนำ cotton lawn, double gauze หรือผ้าฝ้ายลายฉลุ",
        "  - ด้ายสีเข้ากับผ้า",
        "  - snap หรือกระดุมเล็ก 2 เม็ด (เปิดหลังคอ ถ้าคอค่อนข้างพอดี)",
        "",
        "คำอธิบายสัญลักษณ์:",
        "  เส้นตัน      = เส้นตัด",
        "  เส้นประเทา   = ส่วนตะเข็บ (เพิ่มเมื่อตัด)",
        "  โซ่สีน้ำเงิน  = ตัดบนรอยพับ อย่าตัดขอบนี้",
        "  เส้นประ+ขีด  = ขอบที่ต้องรูดจีบ",
        "  รอยหยักวี    = จุดจับคู่วงแขน",
        "",
        "ลำดับการเย็บ:",
        "  1. ตัดตัวหน้า 1 ชิ้นและตัวหลัง 1 ชิ้นบนรอยพับ (คอหน้าลึกกว่าคอหลัง)",
        "  2. ตัดแขนระบาย 2 ชิ้น และแถบคอ 1 ชิ้น",
        "  3. เย็บตะเข็บไหล่ทั้งสองข้าง (หน้าประกบหลัง)",
        "  4. เย็บริมม้วนแคบ 6 มม. ที่ชายโค้งของแขนระบายทั้ง 2 ชิ้น",
        f"  5. รูดจีบขอบบนแขนระบายให้เหลือ ~{d['sleeve_cap']:.1f} ซม. "
        f"เท่าความยาววงแขน",
        "  6. เย็บแขนระบายติดวงแขน (ให้ระบายตกลงคลุมไหล่ ไม่ต้องเย็บใต้วงแขน)",
        "  7. เย็บตะเข็บข้างลำตัวทั้งสองข้าง",
    ]
    if neck_finish == "ruffle":
        lines += [
            "  8. พับแถบคอครึ่งตามยาว รีด แล้วรูดจีบขอบล่างให้เท่ารอบคอ",
            "  9. เย็บแถบคอที่รูดจีบแล้วติดขอบคอ ให้ระบายตั้งขึ้น",
            " 10. จบขอบคอด้านในด้วยการพับเก็บริมแล้วสอยหรือเย็บทับ",
            " 11. พับชายเสื้อเข้า 1 ซม. เย็บให้เรียบร้อย",
            " 12. รีดทุกตะเข็บ ตรวจความเรียบร้อย",
        ]
    else:
        lines += [
            "  8. พับแถบกุ๊นครึ่งตามยาว รีดให้เรียบ",
            "  9. เย็บกุ๊นรอบขอบคอ ดึงให้ตึงพอดีไม่ย้วย",
            " 10. พลิกกุ๊นเก็บด้านใน เย็บทับให้เรียบ",
            " 11. พับชายเสื้อเข้า 1 ซม. เย็บให้เรียบร้อย",
            " 12. รีดทุกตะเข็บ ตรวจความเรียบร้อย",
        ]
    lines += [
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {sa} ซม. ทุกขอบ",
        "เคล็ดลับ: ถ้าคอสวมหัวไม่ผ่าน ให้ผ่าหลังคอลงมา 5 ซม. "
        "แล้วติด snap 1-2 เม็ด",
    ]
    return lines
