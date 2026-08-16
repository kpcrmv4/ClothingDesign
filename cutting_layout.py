"""
Cutting layout visualizer: shows how to place pattern pieces on a bolt of
fabric (90, 115, or 150 cm wide).

Piece sizes and the packing itself come from geometry.py, which is also what
the fabric estimate in features.py uses — so the metres quoted in the
shopping list are the metres drawn in this picture.
"""
import os
from PIL import Image, ImageDraw

import geometry
from features import PATTERN_META
from fonts import pil_font

_PX_PER_CM = 5
_MARGIN_PX = 20

_COLORS = ["#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF",
           "#A0C4FF", "#BDB2FF", "#FFC6FF", "#FFADAD"]


def generate_layout(pattern_key: str, size_label: str,
                    fabric_width_cm: int = 115,
                    output_dir: str = ".", **params) -> str:
    """Generate a PNG showing the suggested cut layout. Returns the path."""
    if pattern_key not in PATTERN_META:
        return (f"Error: unknown pattern '{pattern_key}'. "
                f"Available: {list(PATTERN_META)}")
    if fabric_width_cm not in (90, 115, 150):
        return "Error: fabric_width_cm must be 90, 115, or 150"

    pieces = geometry.get_pieces(pattern_key, size_label, **params)
    if not pieces:
        return f"Error: no layout data for '{pattern_key}'"

    placements, total_length, info = geometry.pack_pieces(
        pieces, fabric_width_cm)

    usable_w = info["usable_width"]
    folded = info["folded"]

    pad = _MARGIN_PX * 2
    img_w = int(usable_w * _PX_PER_CM) + pad + 220
    img_h = int(total_length * _PX_PER_CM) + pad + 110

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)

    title_font = pil_font(16, bold=True)
    label_font = pil_font(11)
    small_font = pil_font(9)

    meta = PATTERN_META[pattern_key]
    draw.text((_MARGIN_PX, 10),
              f"{meta['title_th']} — ไซส์ {size_label} — ผ้ากว้าง {fabric_width_cm} ซม.",
              fill="black", font=title_font)
    draw.text((_MARGIN_PX, 32),
              f"ใช้ผ้ายาว ~{total_length:.0f} ซม. ({total_length / 100:.2f} ม.) "
              f"— เผื่อไว้อีก 10% เวลาซื้อ",
              fill="#555", font=label_font)

    if folded:
        fold_note = (f"พับผ้าครึ่งตามยาว → ใช้งานกว้าง {usable_w:.0f} ซม. "
                     f"(ชิ้น 'ทบ' วางชิดรอยพับ, ชิ้นอื่นตัดทีเดียวได้ 2 ชิ้น)")
    else:
        fold_note = f"วางผ้าชั้นเดียว ใช้งานกว้าง {usable_w:.0f} ซม."
    draw.text((_MARGIN_PX, 50), fold_note, fill="#7a4fbf", font=small_font)

    ox, oy = _MARGIN_PX, 72
    fabric_px_w = int(usable_w * _PX_PER_CM)
    fabric_px_h = int(total_length * _PX_PER_CM)
    draw.rectangle([ox, oy, ox + fabric_px_w, oy + fabric_px_h],
                   outline="blue", width=2)

    if folded:
        # The fold runs down the left edge; mark it so pieces read correctly.
        draw.line([ox, oy, ox, oy + fabric_px_h], fill="#7a4fbf", width=4)

    for i, (name, x, y, w, h) in enumerate(placements):
        color = _COLORS[i % len(_COLORS)]
        x1 = ox + int(x * _PX_PER_CM)
        y1 = oy + int(y * _PX_PER_CM)
        x2 = x1 + int(w * _PX_PER_CM)
        y2 = y1 + int(h * _PX_PER_CM)
        draw.rectangle([x1, y1, x2, y2], fill=color, outline="black", width=1)
        draw.text((x1 + 3, y1 + 3), name, fill="black", font=small_font)
        draw.text((x1 + 3, y1 + 15), f"{w:.0f}x{h:.0f}", fill="#555",
                  font=small_font)

    draw.text((ox, oy + fabric_px_h + 6),
              f"<-- {usable_w:.0f} ซม. -->", fill="blue", font=small_font)
    draw.text((ox + fabric_px_w + 8, oy + fabric_px_h // 2 - 8),
              f"{total_length:.0f} ซม.\n(ความยาวผ้า)", fill="blue",
              font=small_font)

    note_y = oy + fabric_px_h + 24
    if folded:
        draw.text((_MARGIN_PX, note_y),
                  "เส้นม่วงซ้าย = รอยพับผ้า ห้ามตัด",
                  fill="#7a4fbf", font=small_font)
        note_y += 14
    if info["oversized"]:
        draw.text((_MARGIN_PX, note_y),
                  "⚠ ชิ้นที่กว้างเกินหน้าผ้า: " + ", ".join(info["oversized"]) +
                  " — ให้ต่อผ้าหรือเลือกผ้าหน้ากว้างขึ้น",
                  fill="#c0392b", font=small_font)

    file_path = os.path.abspath(os.path.join(
        output_dir,
        f"cutting_layout_{pattern_key}_{size_label}_{fabric_width_cm}cm.png"))
    img.save(file_path, "PNG")
    return file_path
