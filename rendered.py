"""
Stylised "finished garment" preview renderer (uses Pillow).

Different from preview.py — that one shows flat pattern piece outlines
(useful for engineers/sewers to verify shape before generating PDF).
This module draws what the garment looks like *when sewn together and worn*
— useful as a thumbnail for the catalog page.

Output PNG: rendered_<pattern_key>_<size>.png
"""
import os
import math
from PIL import Image, ImageDraw

from fonts import pil_font
from sizes import get_size


W, H = 480, 600
CENTER = W // 2

# Soft pastels matching the catalog's pink/purple theme
FABRIC_PINK = "#fce4ec"
FABRIC_PINK_DK = "#f8bbd0"
FABRIC_BLUE = "#e1f5fe"
FABRIC_BLUE_DK = "#b3e5fc"
FABRIC_MINT = "#e8f5e9"
FABRIC_LAVENDER = "#f3e5f5"
OUTLINE = "#37474f"
STITCH = "#90a4ae"
SHADOW = "#cfd8dc"


def _font(size=18, bold=False):
    return pil_font(size, bold=bold)


def _bezier(draw, p0, p1, p2, p3, fill, width=2, steps=40):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3 * p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3 * p3[1]
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i+1]], fill=fill, width=width)
    return pts


def _fill_polygon(draw, points, fabric, outline=OUTLINE, width=3):
    draw.polygon(points, fill=fabric, outline=outline)
    # redraw outline with thicker stroke
    if width > 1:
        for i in range(len(points)):
            draw.line([points[i], points[(i+1) % len(points)]],
                       fill=outline, width=width)


def _smooth_path(draw, points, fabric, outline=OUTLINE, width=3):
    """Fill a polygon and stroke its outline."""
    draw.polygon(points, fill=fabric, outline=None)
    for i in range(len(points)):
        draw.line([points[i], points[(i+1) % len(points)]],
                   fill=outline, width=width)


def _label(img, text, size=20):
    draw = ImageDraw.Draw(img)
    f = _font(size, bold=True)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 50), text, fill=OUTLINE, font=f)


def _new_canvas(bg="#ffffff"):
    img = Image.new("RGB", (W, H), bg)
    return img, ImageDraw.Draw(img)


# ============================================================
# DRESS — sleeveless A-line with strap + ruffle hem
# ============================================================
def _render_dress(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    # body proportions
    bodice_w = 130
    bodice_h = 180
    ruffle_w = 220
    ruffle_h = 130
    strap_h = 60
    top_y = 70

    # straps
    sw = 14
    for sx in [cx - 40, cx + 40]:
        d.rectangle([sx - sw//2, top_y, sx + sw//2, top_y + strap_h],
                     fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)
        # bow on top
        bow_y = top_y - 6
        d.ellipse([sx - 18, bow_y - 10, sx - 2, bow_y + 6],
                   fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)
        d.ellipse([sx + 2, bow_y - 10, sx + 18, bow_y + 6],
                   fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)
        d.ellipse([sx - 4, bow_y - 4, sx + 4, bow_y + 4],
                   fill=OUTLINE, outline=None)

    # bodice
    by = top_y + strap_h
    bx_l = cx - bodice_w // 2
    bx_r = cx + bodice_w // 2
    bb_y = by + bodice_h
    # neckline scoop
    pts = []
    # left strap-bottom -> down side
    pts.append((bx_l, by + 5))
    pts.append((bx_l, bb_y))
    pts.append((bx_r, bb_y))
    pts.append((bx_r, by + 5))
    # neckline curve top
    _smooth_path(d, pts, FABRIC_PINK)
    # neckline curve (drawn on top)
    _bezier(d, (bx_l + 10, by + 5),
                (cx - 30, by + 35), (cx + 30, by + 35),
                (bx_r - 10, by + 5),
                fill=OUTLINE, width=3)
    # subtle shading on right side
    shade_pts = [(cx, by+5), (bx_r, by+5), (bx_r, bb_y), (cx, bb_y)]
    # apply lighter pink to right half via overlay
    for i in range(0, bodice_h, 4):
        d.line([(cx + 30, by + i), (bx_r - 5, by + i)],
                fill=FABRIC_PINK_DK if i % 8 == 0 else FABRIC_PINK,
                width=1)

    # ruffle hem - wider with gathered top
    rx_l = cx - ruffle_w // 2
    rx_r = cx + ruffle_w // 2
    rb_y = bb_y + ruffle_h
    ruffle_pts = [
        (bx_l, bb_y),
        (rx_l, bb_y + 12),
        (rx_l - 8, rb_y),
        (rx_r + 8, rb_y),
        (rx_r, bb_y + 12),
        (bx_r, bb_y),
    ]
    _smooth_path(d, ruffle_pts, FABRIC_PINK_DK)
    # vertical gather lines
    n_gathers = 9
    for i in range(1, n_gathers):
        gx = bx_l + (bx_r - bx_l) * i / n_gathers
        ratio = i / n_gathers
        bx = rx_l + (rx_r - rx_l) * ratio
        by_ruffle = bb_y + 12 + (rb_y - bb_y - 12) * 0.95
        _bezier(d, (gx, bb_y + 4),
                   (gx, bb_y + 30),
                   (bx, by_ruffle - 30),
                   (bx, by_ruffle),
                   fill=STITCH, width=1, steps=20)
    # scalloped hem
    for i in range(8):
        sx = rx_l - 8 + i * (ruffle_w + 16) / 7
        d.arc([sx - 8, rb_y - 8, sx + 8, rb_y + 8],
               start=0, end=180, fill=OUTLINE, width=2)

    # title
    _label(img, "เดรสเด็ก  •  ทรงสายไหล่ พร้อมระบาย", 18)
    return img


# ============================================================
# BLOOMERS — puffy diaper cover
# ============================================================
def _render_bloomers(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 180
    waist_w = 160
    hip_w = 220
    hem_w = 200
    bottom_y = 430

    # waist band (elastic)
    wb = 18
    d.rounded_rectangle([cx - waist_w//2, top_y, cx + waist_w//2, top_y + wb],
                         radius=8, fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)
    # gather lines on waistband
    for x in range(cx - waist_w//2 + 10, cx + waist_w//2 - 5, 8):
        d.line([(x, top_y + 3), (x, top_y + wb - 3)], fill=STITCH, width=1)

    # bubble body
    body_pts = []
    body_pts.append((cx - waist_w//2, top_y + wb))
    # left side bubble out
    _bz_pts = []
    bz = _bezier_pts(
        (cx - waist_w//2, top_y + wb),
        (cx - hip_w//2 - 20, top_y + wb + 50),
        (cx - hip_w//2 - 20, bottom_y - 50),
        (cx - hem_w//2, bottom_y - 30))
    body_pts.extend(bz)
    # bottom curve - leg openings
    body_pts.append((cx - 30, bottom_y))
    body_pts.append((cx, bottom_y - 25))
    body_pts.append((cx + 30, bottom_y))
    # right side
    bz = _bezier_pts(
        (cx + hem_w//2, bottom_y - 30),
        (cx + hip_w//2 + 20, bottom_y - 50),
        (cx + hip_w//2 + 20, top_y + wb + 50),
        (cx + waist_w//2, top_y + wb))
    body_pts.extend(bz)
    _smooth_path(d, body_pts, FABRIC_PINK)

    # leg ruffle openings
    for sign in [-1, 1]:
        cx_leg = cx + sign * 50
        d.arc([cx_leg - 35, bottom_y - 18, cx_leg + 35, bottom_y + 12],
               start=0, end=180, fill=OUTLINE, width=2)
        for i in range(8):
            x = cx_leg - 30 + i * 8
            d.line([(x, bottom_y), (x, bottom_y + 4)], fill=STITCH, width=1)

    # subtle texture
    for y in range(top_y + wb + 30, bottom_y - 50, 25):
        d.line([(cx - hip_w//2 + 30, y), (cx + hip_w//2 - 30, y)],
                fill=SHADOW, width=1)

    _label(img, "กางเกงใน Bloomers  •  เอวยางยืด เป้าโค้ง", 18)
    return img


def _bezier_pts(p0, p1, p2, p3, steps=20):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0]
        y = u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


# ============================================================
# BIB
# ============================================================
def _render_bib(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 130
    bw = 220
    bh = 280

    # body teardrop
    pts = []
    pts.extend(_bezier_pts(
        (cx - 25, top_y),
        (cx - 40, top_y + 30),
        (cx - bw//2, top_y + 60),
        (cx - bw//2 + 10, top_y + bh//2)))
    pts.extend(_bezier_pts(
        (cx - bw//2 + 10, top_y + bh//2),
        (cx - bw//2 + 5, top_y + bh - 30),
        (cx - 60, top_y + bh + 10),
        (cx, top_y + bh + 20)))
    pts.extend(_bezier_pts(
        (cx, top_y + bh + 20),
        (cx + 60, top_y + bh + 10),
        (cx + bw//2 - 5, top_y + bh - 30),
        (cx + bw//2 - 10, top_y + bh//2)))
    pts.extend(_bezier_pts(
        (cx + bw//2 - 10, top_y + bh//2),
        (cx + bw//2, top_y + 60),
        (cx + 40, top_y + 30),
        (cx + 25, top_y)))
    _smooth_path(d, pts, FABRIC_BLUE)

    # neck hole
    d.ellipse([cx - 30, top_y - 10, cx + 30, top_y + 40],
               fill="#fff5f7", outline=OUTLINE, width=2)
    # snap dots
    d.ellipse([cx - 25, top_y - 5, cx - 17, top_y + 3],
               fill=OUTLINE)
    d.ellipse([cx + 17, top_y - 5, cx + 25, top_y + 3],
               fill=OUTLINE)

    # decorative star
    d.text((cx - 12, top_y + bh//2 - 10), "✦", fill=FABRIC_BLUE_DK, font=_font(34, bold=True))

    _label(img, "ผ้ากันเปื้อน  •  คอ Keyhole + กระดุม snap", 18)
    return img


# ============================================================
# BONNET
# ============================================================
def _render_bonnet(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 150
    bw = 280
    bh = 200

    # crown — half circle
    d.pieslice([cx - bw//2, top_y - bh//2, cx + bw//2, top_y + bh + 20],
                start=180, end=360, fill=FABRIC_LAVENDER, outline=OUTLINE, width=3)
    # brim
    d.arc([cx - bw//2 - 8, top_y + bh - 30, cx + bw//2 + 8, top_y + bh + 50],
           start=0, end=180, fill=OUTLINE, width=3)
    d.pieslice([cx - bw//2 - 8, top_y + bh - 30, cx + bw//2 + 8, top_y + bh + 50],
                start=180, end=360, fill=FABRIC_LAVENDER)

    # ties
    for sign in [-1, 1]:
        x0 = cx + sign * (bw//2 - 5)
        y0 = top_y + bh + 5
        for k in range(0, 80, 4):
            offset = math.sin(k * 0.15) * 8 * sign
            d.line([(x0 + offset, y0 + k),
                    (x0 + offset, y0 + k + 3)],
                    fill=FABRIC_PINK_DK, width=4)

    # bow at top
    d.ellipse([cx - 30, top_y - 30, cx - 5, top_y - 10],
               fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)
    d.ellipse([cx + 5, top_y - 30, cx + 30, top_y - 10],
               fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)
    d.rectangle([cx - 5, top_y - 25, cx + 5, top_y - 15],
                 fill=OUTLINE)

    _label(img, "หมวกเด็ก  •  ครอบหัว 3 ชิ้น พร้อมสายผูก", 18)
    return img


# ============================================================
# KIMONO TOP
# ============================================================
def _render_kimono_top(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 100
    sw = 280  # shoulder
    bw = 240  # body
    sleeve_l = 80
    body_h = 280

    # back body (rectangle)
    pts = [
        (cx - sw//2, top_y),
        (cx + sw//2, top_y),
        (cx + sw//2 - 20, top_y + body_h),
        (cx - sw//2 + 20, top_y + body_h),
    ]
    _smooth_path(d, pts, FABRIC_MINT)

    # sleeves
    for sign in [-1, 1]:
        sx = cx + sign * (sw//2)
        sleeve_pts = [
            (sx, top_y),
            (sx + sign * sleeve_l, top_y + 10),
            (sx + sign * sleeve_l, top_y + 80),
            (sx, top_y + 90),
        ]
        _smooth_path(d, sleeve_pts, FABRIC_MINT)

    # wrap front (V neckline) — overlay
    overlap_pts = [
        (cx - 60, top_y),
        (cx + 60, top_y),
        (cx + 30, top_y + 60),
        (cx + 100, top_y + body_h),
        (cx + sw//2 - 25, top_y + body_h),
        (cx + sw//2 - 5, top_y + 80),
        (cx, top_y + 30),
    ]
    _smooth_path(d, overlap_pts, FABRIC_PINK_DK)

    # tie at side
    d.line([(cx + sw//2 - 15, top_y + 100),
            (cx + sw//2 + 50, top_y + 130)],
            fill=FABRIC_PINK_DK, width=4)
    d.ellipse([cx + sw//2 + 40, top_y + 120, cx + sw//2 + 65, top_y + 140],
               fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)

    _label(img, "เสื้อป้ายผูกข้าง  •  คิโมโนเด็กแรกเกิด", 18)
    return img


# ============================================================
# PANTS — elastic-waist
# ============================================================
def _render_pants(spec, style="long"):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 120
    waist_w = 180
    hip_w = 220
    bottom_y = 450 if style == "long" else 320
    leg_w = 80

    # waistband
    wb = 22
    d.rounded_rectangle([cx - waist_w//2, top_y, cx + waist_w//2, top_y + wb],
                         radius=8, fill=FABRIC_BLUE_DK, outline=OUTLINE, width=2)
    for x in range(cx - waist_w//2 + 8, cx + waist_w//2 - 5, 7):
        d.line([(x, top_y + 4), (x, top_y + wb - 4)], fill=STITCH, width=1)

    # hip flare to crotch
    crotch_y = top_y + wb + 110
    # left leg
    left_pts = [
        (cx - waist_w//2, top_y + wb),
        (cx - hip_w//2, top_y + wb + 50),
        (cx - leg_w//2 - 10, crotch_y),
        (cx - leg_w//2 - 5, bottom_y),
        (cx - leg_w//2 + leg_w + 5, bottom_y),
        (cx - 5, crotch_y + 5),
    ]
    _smooth_path(d, left_pts, FABRIC_BLUE)
    right_pts = [
        (cx + 5, crotch_y + 5),
        (cx + leg_w//2 - leg_w - 5, bottom_y),
        (cx + leg_w//2 + 5, bottom_y),
        (cx + leg_w//2 + 10, crotch_y),
        (cx + hip_w//2, top_y + wb + 50),
        (cx + waist_w//2, top_y + wb),
    ]
    _smooth_path(d, right_pts, FABRIC_BLUE)

    # cuff hem
    for sign in [-1, 1]:
        cx_leg = cx + sign * 40
        d.line([(cx_leg - leg_w//2 - 5, bottom_y),
                (cx_leg + leg_w//2 - 5, bottom_y)],
                fill=OUTLINE, width=3)

    label_th = "กางเกงเด็ก  •  ขายาว เอวยางยืด" if style == "long" else "กางเกงเด็ก  •  ขาสั้น เอวยางยืด"
    _label(img, label_th, 18)
    return img


# ============================================================
# T-SHIRT
# ============================================================
def _render_tshirt(spec, sleeve="short"):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 130
    sw = 320  # shoulder
    bw = 240  # body bottom
    sleeve_l = 60 if sleeve == "short" else 130
    body_h = 240

    # body trapezoid
    pts = [
        (cx - sw//2 + 30, top_y + 20),
        (cx - bw//2, top_y + body_h),
        (cx + bw//2, top_y + body_h),
        (cx + sw//2 - 30, top_y + 20),
    ]
    _smooth_path(d, pts, FABRIC_MINT)

    # sleeves
    for sign in [-1, 1]:
        sx = cx + sign * (sw//2 - 30)
        sleeve_pts = [
            (sx, top_y + 20),
            (sx + sign * sleeve_l, top_y + 30),
            (sx + sign * sleeve_l, top_y + 30 + (60 if sleeve == "short" else 35)),
            (sx + sign * 5, top_y + 90),
        ]
        _smooth_path(d, sleeve_pts, FABRIC_MINT)
        # cuff
        d.line([(sx + sign * sleeve_l, top_y + 30),
                (sx + sign * sleeve_l, top_y + 30 + (60 if sleeve == "short" else 35))],
                fill=OUTLINE, width=3)

    # neckband (crew)
    d.ellipse([cx - 38, top_y, cx + 38, top_y + 40],
               outline=OUTLINE, width=3, fill="#fff5f7")
    d.arc([cx - 35, top_y + 5, cx + 35, top_y + 35],
           start=0, end=180, fill=OUTLINE, width=2)

    label = f"เสื้อยืดเด็ก  •  คอกลม แขน{sleeve_th(sleeve)}"
    _label(img, label, 18)
    return img


def sleeve_th(s):
    return "สั้น" if s == "short" else "ยาว"


# ============================================================
# ROMPER — strap bodysuit
# ============================================================
def _render_romper(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 100
    body_w = 220
    body_h = 200
    leg_drop = 200
    leg_w = 70

    # straps
    sw = 16
    for sx in [cx - 50, cx + 50]:
        d.rectangle([sx - sw//2, top_y, sx + sw//2, top_y + 40],
                     fill=FABRIC_LAVENDER, outline=OUTLINE, width=2)

    # bodice
    bx_l = cx - body_w//2
    bx_r = cx + body_w//2
    bb_y = top_y + 40 + body_h
    pts = [
        (bx_l, top_y + 40),
        (bx_l - 10, top_y + 80),
        (bx_l - 10, bb_y - 30),
        (bx_l + 5, bb_y),
    ]
    # Build full perimeter
    perim = [
        (bx_l + 30, top_y + 40),
        (bx_l, top_y + 70),
        (bx_l, bb_y - 30),
        (bx_l + 5, bb_y),
        # crotch left leg outer
        (cx - leg_w - 10, bb_y + leg_drop - 30),
        (cx - leg_w - 5, bb_y + leg_drop),
        (cx - 15, bb_y + leg_drop),
        # inner left leg up
        (cx - 15, bb_y + leg_drop - 80),
        (cx, bb_y + 30),
        (cx + 15, bb_y + leg_drop - 80),
        # right leg
        (cx + 15, bb_y + leg_drop),
        (cx + leg_w + 5, bb_y + leg_drop),
        (cx + leg_w + 10, bb_y + leg_drop - 30),
        (bx_r - 5, bb_y),
        (bx_r, bb_y - 30),
        (bx_r, top_y + 70),
        (bx_r - 30, top_y + 40),
    ]
    _smooth_path(d, perim, FABRIC_LAVENDER)

    # snap dots at crotch
    for x in [cx - 20, cx, cx + 20]:
        d.ellipse([x - 3, bb_y + 28, x + 3, bb_y + 34], fill=OUTLINE)

    _label(img, "ชุดหมีเด็ก  •  สายไหล่ + กระดุม snap เป้า", 18)
    return img


# ============================================================
# SLEEP SACK
# ============================================================
def _render_sleep_sack(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 110
    sw = 280
    bw = 320
    bh = 380

    # main body — rounded rectangle
    pts = [
        (cx - sw//2 + 30, top_y),
        (cx + sw//2 - 30, top_y),
        (cx + sw//2 - 5, top_y + 60),
        (cx + bw//2, top_y + 100),
        (cx + bw//2, top_y + bh - 20),
        (cx + bw//2 - 25, top_y + bh),
        (cx - bw//2 + 25, top_y + bh),
        (cx - bw//2, top_y + bh - 20),
        (cx - bw//2, top_y + 100),
        (cx - sw//2 + 5, top_y + 60),
    ]
    _smooth_path(d, pts, FABRIC_BLUE)

    # neckline
    d.arc([cx - 35, top_y - 10, cx + 35, top_y + 30],
           start=0, end=180, fill=OUTLINE, width=3)
    # armholes
    d.arc([cx - sw//2 + 25, top_y + 40, cx - sw//2 + 65, top_y + 90],
           start=270, end=90, fill=OUTLINE, width=2)
    d.arc([cx + sw//2 - 65, top_y + 40, cx + sw//2 - 25, top_y + 90],
           start=90, end=270, fill=OUTLINE, width=2)

    # zipper down center
    d.line([(cx, top_y + 30), (cx, top_y + bh - 30)],
            fill=OUTLINE, width=3)
    for y in range(top_y + 35, top_y + bh - 30, 8):
        d.line([(cx - 4, y), (cx + 4, y)], fill=STITCH, width=1)
    # zipper pull
    d.rectangle([cx - 6, top_y + 20, cx + 6, top_y + 35],
                 fill=OUTLINE)

    # stars decorative
    for x, y in [(cx - 60, top_y + 150), (cx + 50, top_y + 200), (cx - 80, top_y + 250), (cx + 70, top_y + 300)]:
        d.text((x, y), "✦", fill=FABRIC_BLUE_DK, font=_font(20, bold=True))

    _label(img, "ถุงนอนเด็ก  •  ซิปกลาง ไม่มีแขน", 18)
    return img


# ============================================================
# FLUTTER ROMPER — off-shoulder ruffle
# ============================================================
def _render_flutter_romper(spec):
    img, d = _new_canvas("#fff5f7")
    cx = CENTER
    top_y = 120
    body_w = 240
    chest_y = top_y + 80
    waist_y = chest_y + 110
    leg_drop = waist_y + 130
    leg_w = 70

    # bubble bottom + body
    perim = [
        (cx - body_w//2 + 20, chest_y),
        (cx - body_w//2 - 10, chest_y + 50),
        (cx - body_w//2 - 5, waist_y),
        (cx - leg_w - 10, leg_drop - 30),
        (cx - leg_w - 5, leg_drop),
        (cx - 15, leg_drop),
        (cx - 15, leg_drop - 80),
        (cx, waist_y + 30),
        (cx + 15, leg_drop - 80),
        (cx + 15, leg_drop),
        (cx + leg_w + 5, leg_drop),
        (cx + leg_w + 10, leg_drop - 30),
        (cx + body_w//2 + 5, waist_y),
        (cx + body_w//2 + 10, chest_y + 50),
        (cx + body_w//2 - 20, chest_y),
    ]
    _smooth_path(d, perim, FABRIC_PINK)

    # ruffle (off-shoulder flounce) at top — wider than body
    rh = 70
    rx_l = cx - body_w//2 - 30
    rx_r = cx + body_w//2 + 30
    # ruffle wave bottom
    wave = []
    for i in range(40):
        t = i / 39
        x = rx_l + (rx_r - rx_l) * t
        y = chest_y + 4 + math.sin(t * math.pi * 8) * 4
        wave.append((x, y))
    # full ruffle perimeter
    ruffle_pts = [(rx_l, chest_y - rh + 10)]
    ruffle_pts.append((cx - body_w//2 + 30, chest_y - rh))
    ruffle_pts.append((cx + body_w//2 - 30, chest_y - rh))
    ruffle_pts.append((rx_r, chest_y - rh + 10))
    ruffle_pts.append((rx_r + 5, chest_y))
    ruffle_pts.extend(reversed(wave))
    ruffle_pts.append((rx_l - 5, chest_y))
    _smooth_path(d, ruffle_pts, FABRIC_PINK_DK)

    # gather lines
    for i in range(1, 12):
        gx = rx_l + (rx_r - rx_l) * i / 12
        d.line([(gx, chest_y - rh + 5), (gx, chest_y - 4)],
                fill=STITCH, width=1)

    # snap dots
    for x in [cx - 20, cx, cx + 20]:
        d.ellipse([x - 3, leg_drop - 5, x + 3, leg_drop + 1], fill=OUTLINE)

    _label(img, "ชุดหมีคอระบาย  •  คอ off-shoulder + flutter sleeves", 16)
    return img


# ============================================================
# FLUTTER TOP — short blouse with flutter sleeves
# ============================================================
def _render_flutter_top(spec, neck_finish="ruffle", **_ignored):
    img, d = _new_canvas("#f7fbfd")
    cx = CENTER
    top_y = 150
    body_w = 190
    body_h = 250
    bx_l, bx_r = cx - body_w // 2, cx + body_w // 2
    bb_y = top_y + body_h

    # flutter sleeves fall open over each shoulder
    for side in (-1, 1):
        sx = cx + side * (body_w // 2)
        pts = [(sx - side * 26, top_y + 12),
               (sx + side * 74, top_y + 40),
               (sx + side * 58, top_y + 130),
               (sx - side * 6, top_y + 96)]
        _smooth_path(d, pts, FABRIC_BLUE)
        for k in range(1, 5):
            t = k / 5
            _bezier(d,
                    (sx - side * 26 + side * 100 * t, top_y + 14 + 6 * k),
                    (sx + side * (30 + 8 * k), top_y + 50 + 8 * k),
                    (sx + side * (44 + 6 * k), top_y + 80 + 6 * k),
                    (sx + side * (30 + 4 * k), top_y + 110 + 4 * k),
                    fill=STITCH, width=1, steps=14)

    # body
    _smooth_path(d, [(bx_l, top_y), (bx_l, bb_y),
                     (bx_r, bb_y), (bx_r, top_y)], "#ffffff")

    # neckline
    if neck_finish == "ruffle":
        # standing frill: a scalloped band round the neck opening
        _bezier(d, (cx - 52, top_y + 4), (cx - 24, top_y + 44),
                (cx + 24, top_y + 44), (cx + 52, top_y + 4),
                fill=OUTLINE, width=3)
        for k in range(9):
            t = k / 8
            px = cx - 58 + 116 * t
            py = top_y - 6 + 30 * (0.5 - abs(t - 0.5)) * 2
            d.arc([px - 9, py - 12, px + 9, py + 8],
                  start=180, end=360, fill=OUTLINE, width=2)
    else:
        _bezier(d, (cx - 52, top_y + 4), (cx - 24, top_y + 44),
                (cx + 24, top_y + 44), (cx + 52, top_y + 4),
                fill=OUTLINE, width=4)

    # subtle eyelet texture
    for gy in range(top_y + 70, bb_y - 20, 34):
        for gx in range(bx_l + 22, bx_r - 14, 34):
            d.ellipse([gx, gy, gx + 7, gy + 7], outline=SHADOW, width=2)

    # hem
    d.line([(bx_l, bb_y), (bx_r, bb_y)], fill=OUTLINE, width=3)
    d.line([(bx_l, bb_y - 9), (bx_r, bb_y - 9)], fill=STITCH, width=1)

    finish_th = "คอระบายตั้ง" if neck_finish == "ruffle" else "คอเรียบกุ๊น"
    _label(img, f"เสื้อคอระบาย แขนระบาย  •  {finish_th}", 18)
    return img


# ============================================================
# TIERED DRESS — bodice over 2-3 ruffled layers
# ============================================================
def _render_tiered_dress(spec, tiers=3, neckline="round", lace_trim=True,
                         **_ignored):
    img, d = _new_canvas("#fdf4f8")
    cx = CENTER
    tiers = max(2, min(3, int(tiers)))

    top_y = 90
    bodice_w = 132
    bodice_h = 150
    bx_l, bx_r = cx - bodice_w // 2, cx + bodice_w // 2
    bb_y = top_y + bodice_h

    # --- neckline hardware ---
    if neckline == "halter":
        # big bow above a narrow gathered neckline
        neck_half = 34
        for side in (-1, 1):
            d.polygon([(cx, top_y - 26),
                       (cx + side * 62, top_y - 54),
                       (cx + side * 62, top_y - 2)],
                      fill=FABRIC_PINK_DK, outline=OUTLINE)
        d.ellipse([cx - 11, top_y - 37, cx + 11, top_y - 15],
                  fill=FABRIC_PINK, outline=OUTLINE, width=2)
        for side in (-1, 1):
            d.line([(cx + side * 20, top_y - 14),
                    (cx + side * neck_half, top_y + 4)],
                   fill=OUTLINE, width=3)
    elif neckline == "strap":
        for sx in (cx - 42, cx + 42):
            d.rectangle([sx - 7, top_y - 44, sx + 7, top_y + 4],
                        fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)
            # shoulder bow: two loops meeting at a knot on top of the strap
            ky = top_y - 44
            for side in (-1, 1):
                d.polygon([(sx, ky), (sx + side * 24, ky - 16),
                           (sx + side * 24, ky + 10)],
                          fill=FABRIC_PINK, outline=OUTLINE)
            d.ellipse([sx - 6, ky - 6, sx + 6, ky + 6],
                      fill=FABRIC_PINK_DK, outline=OUTLINE, width=2)

    # --- bodice ---
    _smooth_path(d, [(bx_l, top_y + 6), (bx_l, bb_y),
                     (bx_r, bb_y), (bx_r, top_y + 6)], FABRIC_PINK)
    if neckline == "round":
        _bezier(d, (bx_l + 12, top_y + 6), (cx - 32, top_y + 40),
                (cx + 32, top_y + 40), (bx_r - 12, top_y + 6),
                fill=OUTLINE, width=3)
        if lace_trim:
            _bezier(d, (bx_l + 12, top_y + 13), (cx - 32, top_y + 47),
                    (cx + 32, top_y + 47), (bx_r - 12, top_y + 13),
                    fill="#ffffff", width=6)
            _bezier(d, (bx_l + 12, top_y + 13), (cx - 32, top_y + 47),
                    (cx + 32, top_y + 47), (bx_r - 12, top_y + 13),
                    fill=STITCH, width=1)
    else:
        d.line([(bx_l + 4, top_y + 6), (bx_r - 4, top_y + 6)],
               fill=OUTLINE, width=3)

    # gingham-ish texture on the bodice
    for gx in range(bx_l + 8, bx_r - 4, 14):
        d.line([(gx, top_y + 10), (gx, bb_y - 3)], fill=FABRIC_PINK_DK, width=2)
    for gy in range(top_y + 16, bb_y - 3, 14):
        d.line([(bx_l + 3, gy), (bx_r - 3, gy)], fill=FABRIC_PINK_DK, width=2)

    # --- tiers ---
    avail_h = H - 120 - bb_y
    tier_h = avail_h / tiers
    widths = [bodice_w * (1.45 ** (i + 1)) for i in range(tiers)]
    widths = [min(w, W - 60) for w in widths]

    y = bb_y
    prev_half = bodice_w / 2
    for i in range(tiers):
        half = widths[i] / 2
        y2 = y + tier_h
        shade = FABRIC_PINK if i % 2 == 0 else FABRIC_PINK_DK
        _smooth_path(d, [(cx - prev_half, y), (cx - half, y2),
                         (cx + half, y2), (cx + prev_half, y)], shade)
        # gather ripples along the seam
        n = 11
        for k in range(1, n):
            t = k / n
            sx = cx - prev_half + prev_half * 2 * t
            ex = cx - half + half * 2 * t
            _bezier(d, (sx, y + 3), (sx, y + tier_h * 0.35),
                    (ex, y2 - tier_h * 0.35), (ex, y2 - 3),
                    fill=STITCH, width=1, steps=16)
        if lace_trim and i < tiers - 1:
            d.line([(cx - half - 2, y2), (cx + half + 2, y2)],
                   fill="#ffffff", width=7)
            d.line([(cx - half - 2, y2), (cx + half + 2, y2)],
                   fill=STITCH, width=1)
        prev_half = half
        y = y2

    # scalloped hem on the last tier
    n_scallops = 9
    step = (prev_half * 2) / n_scallops
    for k in range(n_scallops):
        sx = cx - prev_half + k * step
        d.arc([sx, y - 9, sx + step, y + 9], start=0, end=180,
              fill=OUTLINE, width=2)

    neck_th = {"round": "คอกลม", "halter": "คอผูกหลัง",
               "strap": "สายไหล่"}[neckline]
    _label(img, f"เดรสกระโปรงชั้น  •  {tiers} ชั้น  •  {neck_th}", 18)
    return img


# ============================================================
# ENTRY POINT
# ============================================================
def render_finished(pattern_key: str, size_label: str,
                    output_dir: str = ".", **params) -> str:
    """Render a stylised 'finished garment' preview and save as PNG.
    Returns the absolute file path."""
    spec = get_size(size_label)

    if pattern_key == "tiered_dress":
        img = _render_tiered_dress(spec, **params)
    elif pattern_key == "flutter_top":
        img = _render_flutter_top(spec, **params)
    elif pattern_key == "dress":
        img = _render_dress(spec)
    elif pattern_key == "bib":
        img = _render_bib(spec)
    elif pattern_key == "bloomers":
        img = _render_bloomers(spec)
    elif pattern_key == "bonnet":
        img = _render_bonnet(spec)
    elif pattern_key == "kimono_top":
        img = _render_kimono_top(spec)
    elif pattern_key == "pants":
        img = _render_pants(spec)
    elif pattern_key == "tshirt":
        img = _render_tshirt(spec)
    elif pattern_key == "romper":
        img = _render_romper(spec)
    elif pattern_key == "sleep_sack":
        img = _render_sleep_sack(spec)
    elif pattern_key == "flutter_romper":
        img = _render_flutter_romper(spec)
    else:
        return f"Error: unknown pattern '{pattern_key}'"

    file_path = os.path.abspath(
        os.path.join(output_dir, f"rendered_{pattern_key}_{size_label}.png"))
    img.save(file_path, "PNG")
    return file_path
