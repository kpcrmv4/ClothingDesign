"""
Tiered-skirt baby dress — bodice plus 2-3 gathered tiers.

Covers the boutique looks where the skirt falls in ruffled layers, with
three neckline options:

  round   ชุดคอกลมธรรมดา ติดกุ๊นหรือลูกไม้รอบคอ
  halter  คอผูกหลัง มีโบว์ใหญ่ผูกด้านหลัง (ไม่มีตะเข็บไหล่)
  strap   สายไหล่เดี่ยว ผูกโบว์บนบ่า

Each tier is `tier_fullness` times wider than the seam it attaches to, so
tier 3 gets very long — over 60 cm it is split into equal strips that get
joined into a ring before gathering.
"""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray, red

import geometry
from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save,
                     THAI_FONT, THAI_FONT_BOLD)
from symbols import draw_gather_marks

_NECKLINE_TH = {
    "round": "คอกลม",
    "halter": "คอผูกหลัง (halter)",
    "strap": "สายไหล่ผูกโบว์",
}


def generate(size_label: str,
             seam_allowance: float = 1.0,
             tiers: int = 3,
             neckline: str = "round",
             tier_fullness: float = 1.5,
             lace_trim: bool = True,
             output_dir: str = ".") -> str:
    if neckline not in _NECKLINE_TH:
        return (f"Error: neckline ต้องเป็น 'round', 'halter' หรือ 'strap' "
                f"ไม่ใช่ '{neckline}'")
    if not 2 <= int(tiers) <= 3:
        return f"Error: tiers ต้องเป็น 2 หรือ 3 ไม่ใช่ {tiers}"
    if not 1.2 <= tier_fullness <= 2.5:
        return (f"Error: tier_fullness ต้องอยู่ระหว่าง 1.2-2.5 "
                f"ไม่ใช่ {tier_fullness}")

    spec = get_size(size_label)
    d = geometry.tiered_dress_dims(spec, tiers=tiers, neckline=neckline,
                                   tier_fullness=tier_fullness,
                                   lace_trim=lace_trim)

    sa = seam_allowance
    gap = 2.5

    # Expand each tier into printable strips.
    strips = []          # (tier_index, strip_index, n_strips, width, height)
    for i, full_w in enumerate(d["tier_widths"], start=1):
        n, each = geometry.split_strip(full_w)
        for s in range(n):
            strips.append((i, s + 1, n, each, d["tier_h"]))

    widest = max([d["bodice_w"]] + [s[3] for s in strips] +
                 [d["tie_l"], d["band_w"], d["strap_w"]])
    total_w = widest + sa * 2 + 3

    extras_h = 0.0
    if neckline == "halter":
        extras_h = d["band_h"] + d["tie_w"] + sa * 4 + gap * 2
    elif neckline == "strap":
        extras_h = d["strap_h"] + sa * 2 + gap

    total_h = (d["bodice_h"] + sum(s[4] for s in strips)
               + extras_h + sa * 2 * (1 + len(strips)) + gap * (1 + len(strips))
               + 4)

    def draw(c):
        y = 2.0

        # ---------- 1. Bodice ----------
        bx = 2.0
        _draw_bodice(c, bx, y, d, sa)
        c.setFont(THAI_FONT_BOLD, 10)
        c.drawString((bx + 0.4) * cm, (y + d["bodice_h"] * 0.55) * cm,
                     "1. ตัวเสื้อ — ตัด 2 ชิ้นบนรอยพับ (หน้า + หลัง)")
        c.setFont(THAI_FONT, 7)
        c.drawString((bx + 0.4) * cm, (y + d["bodice_h"] * 0.48) * cm,
                     f"ไซส์ {size_label} | คอแบบ {_NECKLINE_TH[neckline]}")
        c.drawString((bx + 0.4) * cm, (y + d["bodice_h"] * 0.42) * cm,
                     f"สำเร็จครึ่งตัว {d['bodice_w']:.1f} x "
                     f"{d['bodice_h']:.1f} ซม.")
        draw_fold_edge(c, bx, y, bx, y + d["bodice_h"])
        draw_grain_line(c, bx + d["bodice_w"] * 0.7, y + 1.5,
                        bx + d["bodice_w"] * 0.7, y + d["bodice_h"] - 1.5)
        draw_notch(c, bx + d["bodice_w"], y + d["bodice_h"] * 0.45,
                   angle_deg=180)
        y += d["bodice_h"] + sa * 2 + gap

        # ---------- 2..n. Tiers ----------
        n_piece = 2
        for tier_i, strip_i, n_strips, w, h in strips:
            c.setLineWidth(1.3)
            c.setStrokeColor(black)
            c.rect(bx * cm, y * cm, w * cm, h * cm)
            draw_sa_rect_envelope(c, bx, y, w, h, sa)

            if n_strips == 1:
                label = f"{n_piece}. ชั้นที่ {tier_i} — ตัด 1 ชิ้น"
            else:
                label = (f"{n_piece}. ชั้นที่ {tier_i} — ท่อน {strip_i}/"
                         f"{n_strips} (ตัด 1 ชิ้น ต่อกันเป็นวง)")
            c.setFont(THAI_FONT_BOLD, 9)
            c.drawString((bx + 0.3) * cm, (y + h - 0.8) * cm, label)
            c.setFont(THAI_FONT, 7)
            c.drawString((bx + 0.3) * cm, (y + h - 1.4) * cm,
                         f"{w:.1f} x {h:.1f} ซม. "
                         f"(กว้าง {tier_fullness}x ของขอบที่จะต่อ)")
            c.drawString((bx + 0.3) * cm, (y + 0.35) * cm,
                         "ขอบบน = รูดจีบ | ขอบล่าง = ต่อชั้นถัดไป"
                         if tier_i < d["tiers"] else
                         "ขอบบน = รูดจีบ | ขอบล่าง = ชายกระโปรง พับเย็บ 1 ซม.")

            draw_gather_marks(c, bx + 0.5, y + h, bx + w - 0.5, y + h,
                              n_ticks=max(6, int(w / 4)))
            draw_grain_line(c, bx + w / 2 - 2.5, y + h / 2,
                            bx + w / 2 + 2.5, y + h / 2)
            for frac in (0.25, 0.5, 0.75):
                draw_notch(c, bx + w * frac, y + h, angle_deg=270)

            if lace_trim and tier_i < d["tiers"]:
                c.setFillColor(gray)
                c.setFont(THAI_FONT, 6)
                c.drawString((bx + w - 6) * cm, (y + 0.35) * cm,
                             "เย็บลูกไม้ทับรอยต่อ")
                c.setFillColor(black)

            y += h + sa * 2 + gap
            n_piece += 1

        # ---------- Neckline hardware ----------
        if neckline == "halter":
            c.setLineWidth(1.3)
            c.rect(bx * cm, y * cm, d["band_w"] * cm, d["band_h"] * cm)
            draw_sa_rect_envelope(c, bx, y, d["band_w"], d["band_h"], sa)
            c.setFont(THAI_FONT_BOLD, 9)
            c.drawString((bx + 0.3) * cm, (y + d["band_h"] - 0.7) * cm,
                         f"{n_piece}. แถบคอ — ตัด 2 ชิ้น (ทบซ้อนกัน)")
            c.setFont(THAI_FONT, 7)
            c.drawString((bx + 0.3) * cm, (y + d["band_h"] - 1.3) * cm,
                         f"{d['band_w']:.1f} x {d['band_h']:.1f} ซม.")
            draw_grain_line(c, bx + d["band_w"] / 2 - 2, y + d["band_h"] / 2,
                            bx + d["band_w"] / 2 + 2, y + d["band_h"] / 2)
            y += d["band_h"] + sa * 2 + gap
            n_piece += 1

            c.setLineWidth(1.3)
            c.rect(bx * cm, y * cm, d["tie_l"] * cm, d["tie_w"] * cm)
            draw_sa_rect_envelope(c, bx, y, d["tie_l"], d["tie_w"], sa)
            c.setFont(THAI_FONT_BOLD, 9)
            c.drawString((bx + 0.3) * cm, (y + d["tie_w"] - 0.7) * cm,
                         f"{n_piece}. สายโบว์ผูกหลัง — ตัด 2 ชิ้น")
            c.setFont(THAI_FONT, 7)
            c.drawString((bx + 0.3) * cm, (y + d["tie_w"] - 1.3) * cm,
                         f"{d['tie_l']:.1f} x {d['tie_w']:.1f} ซม. "
                         f"(พับครึ่งตามยาว เย็บ แล้วกลับด้าน)")
            draw_grain_line(c, bx + 3, y + d["tie_w"] / 2,
                            bx + d["tie_l"] - 3, y + d["tie_w"] / 2)

        elif neckline == "strap":
            c.setLineWidth(1.3)
            c.rect(bx * cm, y * cm, d["strap_w"] * cm, d["strap_h"] * cm)
            draw_sa_rect_envelope(c, bx, y, d["strap_w"], d["strap_h"], sa)
            c.setFont(THAI_FONT_BOLD, 9)
            c.drawString((bx + 0.3) * cm, (y + d["strap_h"] - 0.7) * cm,
                         f"{n_piece}. สายไหล่ — ตัด 2 ชิ้น")
            c.setFont(THAI_FONT, 7)
            c.drawString((bx + 0.3) * cm, (y + d["strap_h"] - 1.3) * cm,
                         f"{d['strap_w']:.1f} x {d['strap_h']:.1f} ซม.")
            draw_grain_line(c, bx + d["strap_w"] / 2, y + 1,
                            bx + d["strap_w"] / 2, y + d["strap_h"] - 1)

    instructions = _instructions(size_label, d, seam_allowance, neckline,
                                 lace_trim, strips)

    file_path = os.path.abspath(os.path.join(
        output_dir, f"tiered_dress_pattern_{size_label}.pdf"))
    total_pages = tile_and_save(file_path, "เดรสกระโปรงชั้น", size_label,
                                total_w, total_h, draw, instructions)

    tier_desc = " + ".join(f"{w:.0f}" for w in d["tier_widths"])
    return (f"Tiered dress pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"คอ: {_NECKLINE_TH[neckline]}  |  {d['tiers']} ชั้น  |  "
            f"ตัวเสื้อ {d['bodice_w']:.1f}x{d['bodice_h']:.1f} ซม.\n"
            f"ความกว้างแต่ละชั้น: {tier_desc} ซม. "
            f"(ชายกระโปรงยาวรวม {d['skirt_total_h']:.1f} ซม.)")


# ============================================================
# BODICE OUTLINE
# ============================================================
def _draw_bodice(c, x, y, d, sa):
    """Bodice half-piece; left edge is the centre fold."""
    w, h = d["bodice_w"], d["bodice_h"]
    neckline = d["neckline"]

    c.setStrokeColor(black)
    c.setLineWidth(1.3)

    # hem (bottom) — where tier 1 attaches
    c.line(x * cm, y * cm, (x + w) * cm, y * cm)

    if neckline == "halter":
        # Narrow gathered top edge, sides sweep out to the underarm.
        top_half = d["band_w"] / 2
        c.line(x * cm, (y + h) * cm, (x + top_half) * cm, (y + h) * cm)
        draw_bezier_edge(c,
                         x + top_half, y + h,
                         x + top_half + 1.0, y + h - 2.0,
                         x + w - 0.5, y + h - d["armhole_drop"] * 0.5,
                         x + w, y + h - d["armhole_drop"])
        c.line((x + w) * cm, (y + h - d["armhole_drop"]) * cm,
               (x + w) * cm, y * cm)
        c.setFillColor(gray)
        c.setFont(THAI_FONT, 6)
        c.drawString((x + 0.2) * cm, (y + h - 0.45) * cm,
                     "ขอบบน: รูดจีบแล้วเย็บติดแถบคอ")
        c.setFillColor(black)
    else:
        neck_w = d["neck_width"]
        neck_drop = d["neck_drop"]
        shoulder_w = (d["shoulder_w"] if neckline == "round"
                      else d["strap_w"] * 0.9)
        shoulder_tip_x = min(x + neck_w + shoulder_w, x + w - 0.5)

        # shoulder / strap seam
        c.line((x + neck_w) * cm, (y + h) * cm,
               shoulder_tip_x * cm, (y + h) * cm)
        # neckline scoop from the fold up to the shoulder
        draw_bezier_edge(c,
                         x, y + h - neck_drop,
                         x + neck_w * 0.3, y + h - neck_drop,
                         x + neck_w, y + h - neck_drop * 0.3,
                         x + neck_w, y + h)
        # armhole
        draw_bezier_edge(c,
                         shoulder_tip_x, y + h,
                         shoulder_tip_x + (x + w - shoulder_tip_x) * 0.2,
                         y + h - d["armhole_drop"] * 0.4,
                         x + w - d["armhole_width"] * 0.5,
                         y + h - d["armhole_drop"] * 0.7,
                         x + w, y + h - d["armhole_drop"])
        # side seam
        c.line((x + w) * cm, (y + h - d["armhole_drop"]) * cm,
               (x + w) * cm, y * cm)

    draw_sa_rect_envelope(c, x, y, w, h, sa)


# ============================================================
# SEWING INSTRUCTIONS
# ============================================================
def _instructions(size_label, d, sa, neckline, lace_trim, strips):
    tier_join = []
    for i, w in enumerate(d["tier_widths"], start=1):
        n, each = geometry.split_strip(w)
        if n == 1:
            tier_join.append(f"     ชั้น {i}: 1 ชิ้น กว้าง {each:.0f} ซม.")
        else:
            tier_join.append(f"     ชั้น {i}: {n} ท่อน ท่อนละ {each:.0f} ซม. "
                             f"(ต่อเป็นวงกว้าง {w:.0f} ซม.)")

    lines = [
        f"เดรสกระโปรงชั้น — ไซส์ {size_label}",
        f"คอแบบ: {_NECKLINE_TH[neckline]}  |  {d['tiers']} ชั้น  |  "
        f"ความฟู {d['tier_fullness']}x",
        "",
        "วัสดุ:",
        "  - ผ้าคอตตอนลายตารางหรือลายดอกเล็ก ~0.7-1.0 ม. (หน้ากว้าง 115 ซม.)",
        "  - ด้ายสีเข้ากับผ้า",
        "  - ผ้ากุ๊นสำเร็จ 1 ม. (ขอบคอและวงแขน)",
    ]
    if lace_trim:
        lines.append(f"  - ลูกไม้ลายฉลุ ~{d['trim_len'] / 100:.1f} ม. "
                     f"(ตกแต่งคอ วงแขน และรอยต่อชั้น)")
    if neckline == "halter":
        lines.append("  - ไม่ต้องใช้กระดุม (ผูกโบว์ด้านหลัง)")
    else:
        lines.append("  - ซิปซ่อนหลัง 20 ซม. หรือ snap 3 เม็ด")

    lines += [
        "",
        "คำอธิบายสัญลักษณ์:",
        "  เส้นตัน      = เส้นตัด",
        "  เส้นประเทา   = ส่วนตะเข็บ (เพิ่มเมื่อตัด)",
        "  โซ่สีน้ำเงิน  = ตัดบนรอยพับ อย่าตัดขอบนี้",
        "  รอยหยักวี    = จับคู่ด้วยเครื่องหมายนี้",
        "  เส้นประ+ขีด  = ขอบที่ต้องรูดจีบ",
        "",
        "ขนาดชั้นกระโปรง:",
    ] + tier_join + [
        "",
        "ประหยัดกระดาษ: ชั้นกระโปรงทุกชั้นเป็นสี่เหลี่ยมผืนผ้าธรรมดา",
        "  วัดและตัดด้วยไม้บรรทัดตามขนาดด้านบนได้เลย ไม่ต้องพิมพ์หน้าที่เป็นชั้น",
        "  พิมพ์เฉพาะหน้าที่มีชิ้นตัวเสื้อก็พอ (ดูช่องตารางมุมขวาบนของแต่ละหน้า)",
        "",
        "ลำดับการเย็บ:",
        "  1. ตัดตัวเสื้อ 2 ชิ้นบนรอยพับ (หน้า + หลัง)",
        "  2. ตัดชั้นกระโปรงตามขนาดด้านบน ถ้ามีหลายท่อนให้ต่อเป็นวงก่อน",
    ]

    step = 3
    if neckline == "halter":
        lines += [
            f"  {step}. เย็บตะเข็บข้างตัวเสื้อทั้งสองด้าน (หน้าประกบหลัง)",
            f"  {step + 1}. รูดจีบขอบบนตัวเสื้อให้เท่าความยาวแถบคอ",
            f"  {step + 2}. พับสายโบว์ตามยาว เย็บ กลับด้าน รีดให้เรียบ",
            f"  {step + 3}. ประกบแถบคอ 2 ชิ้น สอดสายโบว์ไว้ปลายทั้งสองข้าง เย็บ",
            f"  {step + 4}. เย็บแถบคอครอบขอบบนตัวเสื้อที่รูดจีบไว้",
        ]
        step += 5
    elif neckline == "strap":
        lines += [
            f"  {step}. พับสายไหล่ตามยาว เย็บ กลับด้าน รีดให้เรียบ",
            f"  {step + 1}. ติดสายไหล่ระหว่างตัวหน้าและตัวหลังที่ตำแหน่งไหล่",
            f"  {step + 2}. เย็บตะเข็บข้างตัวเสื้อทั้งสองด้าน",
            f"  {step + 3}. จบขอบคอและวงแขนด้วยผ้ากุ๊น",
        ]
        step += 4
    else:
        lines += [
            f"  {step}. เย็บตะเข็บไหล่ (หน้าประกบหลัง)",
            f"  {step + 1}. เย็บตะเข็บข้างตัวเสื้อทั้งสองด้าน",
            f"  {step + 2}. จบขอบคอและวงแขนด้วยผ้ากุ๊น",
        ]
        step += 3

    prev = "ชายตัวเสื้อ"
    for i in range(1, d["tiers"] + 1):
        lines.append(f"  {step}. รูดจีบขอบบนชั้นที่ {i} ให้เท่ากับ{prev} "
                     f"แล้วเย็บติดกัน")
        step += 1
        if lace_trim and i < d["tiers"]:
            lines.append(f"  {step}. เย็บลูกไม้ทับรอยต่อชั้นที่ {i}")
            step += 1
        prev = f"ชายชั้นที่ {i}"

    lines += [
        f"  {step}. พับชายกระโปรงชั้นล่างสุดเข้า 1 ซม. เย็บให้เรียบร้อย",
        f"  {step + 1}. รีดทุกตะเข็บ ตรวจความเรียบร้อย",
        "",
        f"ส่วนตะเข็บรวมอยู่แล้ว: {sa} ซม. ทุกขอบ",
        "เคล็ดลับ: รูดจีบให้สวย ให้เย็บด้ายเส้นยาวสองแถวขนานกัน "
        "แล้วดึงด้ายล่างพร้อมกันทั้งสองเส้น",
    ]
    return lines
