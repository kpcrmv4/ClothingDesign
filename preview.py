"""
PNG thumbnail preview of patterns (uses Pillow).

Lightweight renderer that reproduces pattern outlines in simple form
for quick visual check before generating full PDF.
"""
import os
import math
from PIL import Image, ImageDraw

import geometry
from fonts import pil_font
from sizes import get_size


_PX_PER_CM = 10     # 10 pixels per cm = reasonable thumbnail
_PAD_CM = 2.0


def _mm_to_px(val_cm):
    return int(val_cm * _PX_PER_CM)


def _setup_canvas(width_cm, height_cm):
    """Create a white canvas and return (img, draw, transform_fn)."""
    w_px = _mm_to_px(width_cm + _PAD_CM * 2)
    h_px = _mm_to_px(height_cm + _PAD_CM * 2)
    img = Image.new("RGB", (w_px, h_px), "white")
    draw = ImageDraw.Draw(img)

    def tx(x_cm, y_cm):
        """cm coords -> PIL pixel coords (y flipped)."""
        px = _mm_to_px(x_cm + _PAD_CM)
        py = h_px - _mm_to_px(y_cm + _PAD_CM)
        return px, py

    return img, draw, tx


def _bezier_points(p0, p1, p2, p3, steps=30):
    """Sample points along a cubic bezier."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + \
            3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + \
            3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def _draw_bezier_pil(draw, tx, p0, p1, p2, p3, color="black", width=2):
    pts = _bezier_points(p0, p1, p2, p3)
    tx_pts = [tx(*p) for p in pts]
    for i in range(len(tx_pts) - 1):
        draw.line([tx_pts[i], tx_pts[i + 1]], fill=color, width=width)


def _draw_line_pil(draw, tx, x1, y1, x2, y2, color="black", width=2, dashed=False):
    if not dashed:
        draw.line([tx(x1, y1), tx(x2, y2)], fill=color, width=width)
        return
    # simple dash
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    segs = max(4, int(dist / 0.4))
    for i in range(0, segs, 2):
        t1 = i / segs
        t2 = min(1.0, (i + 1) / segs)
        draw.line(
            [tx(x1 + dx * t1, y1 + dy * t1),
             tx(x1 + dx * t2, y1 + dy * t2)],
            fill=color, width=width)


def _get_font(size=14):
    return pil_font(size)


# ============================================================
# PER-PATTERN PREVIEW RENDERERS
# ============================================================
def _preview_dress(spec):
    bw = spec["chest"] / 4 + 2.0
    bh = spec["length"]
    nw = spec["neck_circ"] / 6
    nd = 3.0
    ad = 5.5
    sw = spec["shoulder"]

    total_w = bw + 2
    total_h = bh + 2
    img, draw, tx = _setup_canvas(total_w, total_h)
    font = _get_font(14)
    label_font = _get_font(10)

    x, y = 1.0, 1.0
    # bodice outline (half piece, left edge = fold)
    _draw_line_pil(draw, tx, x, y, x + bw, y)              # hem
    _draw_line_pil(draw, tx, x + bw, y, x + bw, y + bh - ad)   # side
    _draw_bezier_pil(draw, tx,
                     (x + bw, y + bh - ad),
                     (x + bw - 1, y + bh - ad * 0.5),
                     (x + bw - 2, y + bh),
                     (x + nw + sw, y + bh))                # armhole
    _draw_line_pil(draw, tx, x + nw + sw, y + bh, x + nw, y + bh)  # shoulder
    _draw_bezier_pil(draw, tx,
                     (x + nw, y + bh),
                     (x + nw * 0.5, y + bh),
                     (x, y + bh - nd * 0.5),
                     (x, y + bh - nd))                     # neckline
    _draw_line_pil(draw, tx, x, y + bh - nd, x, y)         # fold edge
    # fold edge color blue
    _draw_line_pil(draw, tx, x - 0.05, y, x - 0.05, y + bh,
                   color="blue", width=1, dashed=True)
    draw.text(tx(x + 1, y + bh - 3), "ตัวเสื้อ", fill="black", font=label_font)
    draw.text((10, 10), f"พรีวิวเดรสเด็ก", fill="black", font=font)

    return img


def _preview_bib(spec):
    bw = spec["neck_circ"] * 0.9
    bh = bw * 1.1
    nr = spec["neck_circ"] / (2 * math.pi) + 0.5
    ow = nr * 0.8

    img, draw, tx = _setup_canvas(bw + 2, bh + 2)
    font = _get_font(14)

    cx = 1.0 + bw / 2
    bottom = 1.0
    top = bottom + bh
    lx = cx - bw / 2
    rx = cx + bw / 2

    _draw_bezier_pil(draw, tx,
                     (lx, bottom + bh * 0.3), (lx, bottom),
                     (rx, bottom), (rx, bottom + bh * 0.3))
    _draw_bezier_pil(draw, tx,
                     (lx, bottom + bh * 0.3), (lx - 0.5, bottom + bh * 0.6),
                     (lx + 1, top - 1.5), (cx - ow - 1.5, top - 1.0))
    _draw_bezier_pil(draw, tx,
                     (rx, bottom + bh * 0.3), (rx + 0.5, bottom + bh * 0.6),
                     (rx - 1, top - 1.5), (cx + ow + 1.5, top - 1.0))

    # neck hole (keyhole)
    _draw_bezier_pil(draw, tx,
                     (cx - ow - 1.5, top - 1.0), (cx - ow, top),
                     (cx - ow, top), (cx - ow, top - nr * 0.3))
    _draw_bezier_pil(draw, tx,
                     (cx - ow, top - nr * 0.3), (cx - ow * 0.6, top - nr * 1.4),
                     (cx - nr * 0.9, top - nr * 1.8), (cx, top - nr * 1.8))
    _draw_bezier_pil(draw, tx,
                     (cx, top - nr * 1.8), (cx + nr * 0.9, top - nr * 1.8),
                     (cx + ow * 0.6, top - nr * 1.4), (cx + ow, top - nr * 0.3))
    _draw_bezier_pil(draw, tx,
                     (cx + ow, top - nr * 0.3), (cx + ow, top),
                     (cx + ow, top), (cx + ow + 1.5, top - 1.0))

    draw.text((10, 10), "พรีวิวผ้ากันเปื้อน", fill="black", font=font)
    return img


def _preview_bloomers(spec):
    wh = spec["waist"] / 2 + 4.0
    hh = spec["hip"] / 2 + 4.0
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
    inseam = 3.0

    img, draw, tx = _setup_canvas(hh + 2, rise + inseam + 2)
    font = _get_font(14)

    x0, y0 = 1.0, 1.0 + inseam
    wl = (x0, y0 + rise)
    wr = (x0 + wh, y0 + rise)
    hr = (x0 + hh, y0 + rise * 0.3)
    crotch = (x0 + wh * 0.15, y0)
    li = (x0 + wh * 0.15, y0 - inseam)
    lo = (x0 + hh, y0 + rise * 0.15)

    _draw_line_pil(draw, tx, wl[0], wl[1], wr[0], wr[1])
    _draw_bezier_pil(draw, tx, wr,
                     (wr[0] + 0.3, wr[1] - rise * 0.3),
                     (hr[0], hr[1] + rise * 0.1), hr)
    _draw_line_pil(draw, tx, hr[0], hr[1], lo[0], lo[1])
    _draw_bezier_pil(draw, tx, lo,
                     (lo[0] - 3, lo[1] - 1.5),
                     (li[0] + 3, li[1] + 0.5), li)
    _draw_line_pil(draw, tx, li[0], li[1], crotch[0], crotch[1])
    _draw_bezier_pil(draw, tx, crotch,
                     (crotch[0] - 1, crotch[1] + 0.5),
                     (wl[0] + 0.5, wl[1] - rise * 0.6),
                     (wl[0], wl[1] - rise * 0.4))
    _draw_line_pil(draw, tx, wl[0], wl[1] - rise * 0.4, wl[0], wl[1],
                   color="blue", width=1, dashed=True)

    draw.text((10, 10), "พรีวิวกางเกง Bloomers", fill="black", font=font)
    return img


def _preview_bonnet(spec):
    fw = spec["head"] / 2 - 2.0
    ch = spec["head"] / 4 + 2.0
    bw = spec["head"] / 3

    img, draw, tx = _setup_canvas(fw * 2 + 2, ch + 2)
    font = _get_font(14)

    cx = 1.0 + fw
    cb = 1.0
    ct = cb + ch

    _draw_bezier_pil(draw, tx,
                     (cx - fw, cb), (cx - fw * 0.5, cb - 0.3),
                     (cx + fw * 0.5, cb - 0.3), (cx + fw, cb))
    _draw_bezier_pil(draw, tx,
                     (cx - fw, cb), (cx - fw - 1, cb + ch * 0.5),
                     (cx - bw / 2 - 0.5, ct - 0.3), (cx - bw / 2, ct))
    _draw_bezier_pil(draw, tx,
                     (cx + fw, cb), (cx + fw + 1, cb + ch * 0.5),
                     (cx + bw / 2 + 0.5, ct - 0.3), (cx + bw / 2, ct))
    _draw_line_pil(draw, tx, cx - bw / 2, ct, cx + bw / 2, ct,
                   color="blue", width=1, dashed=True)

    draw.text((10, 10), "พรีวิวหมวกเด็ก", fill="black", font=font)
    return img


def _preview_flutter_romper(spec):
    top_half = (spec["chest"] + 12) / 4
    chest_half = (spec["chest"] + 6) / 4
    hip_half = (spec["hip"] + 8) / 4
    crotch_half = 3.0
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
    body_torso = spec["length"] * 0.55
    shoulder_drop = 2.5
    total_h = shoulder_drop + body_torso + rise
    leg_drop = 8.0
    ruffle_h = 7.0

    img, draw, tx = _setup_canvas(hip_half + 2, total_h + ruffle_h + 2)
    font = _get_font(14)
    sfont = _get_font(9)

    x, y = 1.0, 1.0
    top_l = (x, y + total_h)
    top_r = (x + top_half, y + total_h)
    chest_r = (x + chest_half, y + total_h - shoulder_drop)
    hip_r = (x + hip_half, y + rise + leg_drop)
    crotch_r = (x + crotch_half, y)

    _draw_line_pil(draw, tx, top_l[0], top_l[1], top_r[0], top_r[1])
    _draw_bezier_pil(draw, tx, top_r,
                     (top_r[0] + 0.8, top_r[1] - shoulder_drop * 0.3),
                     (chest_r[0] - 0.3, chest_r[1] + shoulder_drop * 0.3),
                     chest_r)
    mid_y = (chest_r[1] + hip_r[1]) / 2
    _draw_bezier_pil(draw, tx, chest_r,
                     (chest_r[0] + 0.4, mid_y + 1),
                     (hip_r[0] + 0.2, mid_y - 1), hip_r)
    _draw_bezier_pil(draw, tx, hip_r,
                     (hip_r[0] - 2.5, hip_r[1] - leg_drop * 0.6),
                     (crotch_r[0] + 2.5, crotch_r[1] + 2), crotch_r)
    _draw_line_pil(draw, tx, crotch_r[0], crotch_r[1], x, y)
    _draw_line_pil(draw, tx, x, y, x, y + total_h,
                   color="blue", width=1, dashed=True)

    # ruffle strip sketch above body top edge
    ruffle_y = y + total_h + 0.5
    _draw_line_pil(draw, tx, x, ruffle_y, x + top_half, ruffle_y, color="gray")
    _draw_line_pil(draw, tx, x, ruffle_y + ruffle_h * 0.4,
                   x + top_half, ruffle_y + ruffle_h * 0.4, color="gray")

    draw.text((10, 10), "พรีวิวชุดหมีคอระบาย", fill="black", font=font)
    draw.text(tx(x + 0.3, y + total_h * 0.3),
              "ชิ้นตัว", fill="#555", font=sfont)
    draw.text(tx(x + 0.3, ruffle_y + 0.2),
              "ระบาย (ไม่ตามสเกล)", fill="#555", font=sfont)
    return img


def _preview_tiered_dress(spec, tiers=3, neckline="round",
                          tier_fullness=1.5, **_ignored):
    """Bodice outline plus a stacked sketch of each skirt tier."""
    d = geometry.tiered_dress_dims(spec, tiers=tiers, neckline=neckline,
                                   tier_fullness=tier_fullness)
    bw, bh = d["bodice_w"], d["bodice_h"]
    widest = max(d["tier_widths"]) / 2   # tiers drawn at half width, to scale

    total_w = max(bw, widest) + 2
    total_h = bh + d["skirt_total_h"] + 2
    img, draw, tx = _setup_canvas(total_w, total_h)
    font = _get_font(14)
    label_font = _get_font(10)

    x = 1.0
    y = 1.0 + d["skirt_total_h"]        # bodice sits above the tiers

    # --- bodice half piece, left edge = fold ---
    _draw_line_pil(draw, tx, x, y, x + bw, y)                 # hem
    if neckline == "halter":
        top_half = d["band_w"] / 2
        _draw_line_pil(draw, tx, x, y + bh, x + top_half, y + bh)
        _draw_bezier_pil(draw, tx,
                         (x + top_half, y + bh),
                         (x + top_half + 1.0, y + bh - 2.0),
                         (x + bw - 0.5, y + bh - d["armhole_drop"] * 0.5),
                         (x + bw, y + bh - d["armhole_drop"]))
    else:
        nw = d["neck_width"]
        sw = d["shoulder_w"] if neckline == "round" else d["strap_w"] * 0.9
        tip = min(x + nw + sw, x + bw - 0.5)
        _draw_line_pil(draw, tx, x + nw, y + bh, tip, y + bh)
        _draw_bezier_pil(draw, tx,
                         (x, y + bh - d["neck_drop"]),
                         (x + nw * 0.3, y + bh - d["neck_drop"]),
                         (x + nw, y + bh - d["neck_drop"] * 0.3),
                         (x + nw, y + bh))
        _draw_bezier_pil(draw, tx,
                         (tip, y + bh),
                         (tip + (x + bw - tip) * 0.2,
                          y + bh - d["armhole_drop"] * 0.4),
                         (x + bw - d["armhole_width"] * 0.5,
                          y + bh - d["armhole_drop"] * 0.7),
                         (x + bw, y + bh - d["armhole_drop"]))
    _draw_line_pil(draw, tx, x + bw, y + bh - d["armhole_drop"], x + bw, y)
    _draw_line_pil(draw, tx, x - 0.05, y, x - 0.05, y + bh,
                   color="blue", width=1, dashed=True)
    draw.text(tx(x + 0.4, y + bh * 0.45), "ตัวเสื้อ", fill="black",
              font=label_font)

    # --- tiers stacked below, each drawn at its own (half) width ---
    ty = y
    for i, full_w in enumerate(d["tier_widths"], start=1):
        half = full_w / 2
        th = d["tier_h"]
        ty -= th
        _draw_line_pil(draw, tx, x, ty, x + half, ty, color="#7a4fbf")
        _draw_line_pil(draw, tx, x + half, ty, x + half, ty + th,
                       color="#7a4fbf")
        _draw_line_pil(draw, tx, x, ty + th, x + half, ty + th,
                       color="#7a4fbf")
        _draw_line_pil(draw, tx, x - 0.05, ty, x - 0.05, ty + th,
                       color="blue", width=1, dashed=True)
        draw.text(tx(x + 0.4, ty + th * 0.4),
                  f"ชั้น {i} — กว้าง {full_w:.0f} ซม.",
                  fill="#7a4fbf", font=label_font)

    draw.text((10, 10), f"พรีวิวเดรสกระโปรงชั้น ({tiers} ชั้น)",
              fill="black", font=font)
    return img


def _preview_generic_rect(title, w, h):
    """Fallback for patterns without custom preview: labeled bounding box."""
    img, draw, tx = _setup_canvas(w + 2, h + 2)
    font = _get_font(14)
    small = _get_font(10)

    x, y = 1.0, 1.0
    _draw_line_pil(draw, tx, x, y, x + w, y)
    _draw_line_pil(draw, tx, x + w, y, x + w, y + h)
    _draw_line_pil(draw, tx, x + w, y + h, x, y + h)
    _draw_line_pil(draw, tx, x, y + h, x, y)

    draw.text((10, 10), title, fill="black", font=font)
    draw.text(tx(x + 0.3, y + h * 0.5),
              f"ขนาดประมาณ {w:.1f} x {h:.1f} ซม", fill="gray", font=small)
    return img


# ============================================================
# ENTRY POINT
# ============================================================
def generate_preview(pattern_key: str, size_label: str,
                     output_dir: str = ".", **params) -> str:
    spec = get_size(size_label)

    if pattern_key == "tiered_dress":
        img = _preview_tiered_dress(spec, **params)
    elif pattern_key == "dress":
        img = _preview_dress(spec)
    elif pattern_key == "bib":
        img = _preview_bib(spec)
    elif pattern_key == "bloomers":
        img = _preview_bloomers(spec)
    elif pattern_key == "bonnet":
        img = _preview_bonnet(spec)
    elif pattern_key == "kimono_top":
        w = spec["chest"] / 4 + 2.0
        h = spec["length"] * 0.9
        img = _preview_generic_rect("เสื้อป้ายผูกข้าง (หลัง)", w, h)
    elif pattern_key == "pants":
        w = spec["hip"] / 4 + 3.0
        h = spec["length"] * 1.15 + (spec["rise_f"] + spec["rise_b"]) / 2 + 3
        img = _preview_generic_rect("ขากางเกง", w, h)
    elif pattern_key == "tshirt":
        w = spec["chest"] / 4 + 2.5
        h = spec["length"] * 0.85
        img = _preview_generic_rect("เสื้อยืด (หน้า)", w, h)
    elif pattern_key == "romper":
        w = spec["chest"] / 4 + 2.0
        h = spec["length"] * 0.55 + (spec["rise_f"] + spec["rise_b"]) / 2 + 4
        img = _preview_generic_rect("ชุดหมี (หน้า)", w, h)
    elif pattern_key == "sleep_sack":
        w = spec["chest"] / 4 + 12.0
        h = spec["length"] + 20.0
        img = _preview_generic_rect("ถุงนอน (หลัง)", w, h)
    elif pattern_key == "flutter_romper":
        img = _preview_flutter_romper(spec)
    else:
        return f"Error: unknown pattern '{pattern_key}'"

    file_path = os.path.abspath(
        os.path.join(output_dir, f"preview_{pattern_key}_{size_label}.png"))
    img.save(file_path, "PNG")
    return file_path
