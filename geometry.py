"""
Single source of truth for pattern piece geometry.

Every consumer of pattern dimensions reads from here:

  patterns/*.py      -> *_dims()   for drawing the PDF
  preview.py         -> *_dims()   for the flat outline PNG
  features.py        -> get_pieces() for fabric/shopping estimates
  cutting_layout.py  -> get_pieces() + pack_pieces() for the layout PNG

Before this module existed the same formulas were duplicated in all four
places and had drifted apart (pants leg length differed by ~2x between the
shopping list and the cutting layout). Add a new pattern by adding one
`<key>_dims()` function plus one branch in `get_pieces()`.

All dimensions are in cm. A piece's `w`/`h` is the bounding box of the
pattern piece exactly as drawn on the PDF, so a piece marked `on_fold`
carries its half-width, not the finished garment width.
"""
import math

from sizes import get_size

# Strips longer than this get split in two so a single piece never sprawls
# across an unreasonable number of A4 columns.
MAX_STRIP_LEN = 60.0


# ============================================================
# PER-PATTERN DIMENSION FORMULAS
# ============================================================
def dress_dims(spec, skirt_style: str = "gathered",
               ruffle_fullness: float = 1.5,
               front_placket: bool = False) -> dict:
    """Sleeveless dress: bodice + straps + gathered or bubble hem."""
    bodice_w = spec["chest"] / 4 + 2.0
    bodice_h = spec["length"]

    d = {
        "bodice_w": bodice_w,
        "bodice_h": bodice_h,
        "neck_drop": 3.0,
        "neck_width": spec["neck_circ"] / 6,
        "armhole_drop": 5.5,
        "armhole_width": 2.5,
        "shoulder_w": spec["shoulder"],
        "strap_w": 3.0,
        "strap_h": spec["strap_len"],
        "skirt_style": skirt_style,
        "front_placket": front_placket,
    }

    hem_circ = bodice_w * 2
    if skirt_style == "bubble":
        # A bubble hem is gathered at BOTH edges, so the piece is cut
        # taller than the finished drop and fuller than a flat ruffle.
        d["ruffle_w"] = hem_circ * max(ruffle_fullness, 1.8)
        d["ruffle_h"] = spec["ruffle_h"] * 1.9
        d["bubble_finished_h"] = spec["ruffle_h"] * 1.1
    else:
        d["ruffle_w"] = hem_circ * ruffle_fullness
        d["ruffle_h"] = spec["ruffle_h"]
        d["bubble_finished_h"] = None

    if front_placket:
        # Cut-on placket: a straight strip the length of the centre front.
        d["placket_w"] = 5.0
        d["placket_h"] = bodice_h + d["ruffle_h"]
        d["button_count"] = max(5, int((bodice_h + d["ruffle_h"]) / 5.0))
    else:
        d["placket_w"] = 0.0
        d["placket_h"] = 0.0
        d["button_count"] = 0

    return d


def tiered_dress_dims(spec, tiers: int = 3,
                      neckline: str = "round",
                      tier_fullness: float = 1.5,
                      lace_trim: bool = True) -> dict:
    """Tiered-skirt dress. neckline: 'round' | 'halter' | 'strap'."""
    tiers = max(2, min(3, int(tiers)))
    bodice_w = spec["chest"] / 4 + 2.0          # half width, cut on fold
    bodice_h = spec["length"] * 0.42
    skirt_total_h = spec["length"] * 0.72       # tiers hang below the bodice

    # Each tier is `tier_fullness` times fuller than the seam it joins.
    tier_h = skirt_total_h / tiers
    widths = []
    prev_circ = bodice_w * 2                    # finished bodice hem circumference
    for _ in range(tiers):
        circ = prev_circ * tier_fullness
        widths.append(circ)
        prev_circ = circ

    d = {
        "tiers": tiers,
        "neckline": neckline,
        "tier_fullness": tier_fullness,
        "lace_trim": lace_trim,
        "bodice_w": bodice_w,
        "bodice_h": bodice_h,
        "skirt_total_h": skirt_total_h,
        "tier_h": tier_h,
        "tier_widths": widths,
        "neck_width": spec["neck_circ"] / 6,
        "armhole_drop": 5.5,
        "armhole_width": 2.5,
        "shoulder_w": spec["shoulder"],
    }

    if neckline == "halter":
        # One wide neck band that carries on into the back bow ties.
        d["neck_drop"] = 1.0
        d["band_w"] = spec["neck_circ"] / 3
        d["band_h"] = 4.0
        d["tie_w"] = 8.0
        d["tie_l"] = spec["strap_len"] + 14.0
        d["strap_w"] = 0.0
        d["strap_h"] = 0.0
    elif neckline == "strap":
        d["neck_drop"] = 2.5
        d["band_w"] = 0.0
        d["band_h"] = 0.0
        d["tie_w"] = 0.0
        d["tie_l"] = 0.0
        d["strap_w"] = 3.0
        d["strap_h"] = spec["strap_len"]
    else:  # round
        d["neck_drop"] = 3.0
        d["band_w"] = 0.0
        d["band_h"] = 0.0
        d["tie_w"] = 0.0
        d["tie_l"] = 0.0
        d["strap_w"] = 0.0
        d["strap_h"] = 0.0

    # Total trim length: neckline + armholes + one edge per tier seam.
    trim = spec["neck_circ"] + spec["arm_len"] * 2
    if lace_trim:
        trim += sum(widths)
    d["trim_len"] = trim
    return d


def flutter_top_dims(spec, sleeve_fullness: float = 1.8,
                     neck_finish: str = "ruffle") -> dict:
    """Short pull-on top with flutter sleeves — worn under a pinafore dress.

    neck_finish: 'ruffle' (gathered frill standing up round the neck) or
                 'binding' (flat bias-bound neckline).
    """
    chest_half = spec["chest"] / 4 + 2.5
    armhole_drop = spec["arm_len"] * 0.28 + 4.0
    # Flutter sleeves are flared strips gathered into the armhole; the cap
    # length is roughly the armhole arc for front + back.
    sleeve_cap = armhole_drop * 2.1
    neck_circ = spec["neck_circ"]
    return {
        "chest_half": chest_half,
        "length": spec["length"] * 0.55,
        "neck_width": neck_circ / 6 + 0.3,
        "neck_drop_front": 4.5,
        "neck_drop_back": 1.5,
        "shoulder_w": spec["shoulder"] - 0.5,
        "armhole_drop": armhole_drop,
        "armhole_width": 2.5,
        "sleeve_cap": sleeve_cap,
        "sleeve_w": sleeve_cap * sleeve_fullness,
        "sleeve_h": spec["arm_len"] * 0.3,
        "sleeve_fullness": sleeve_fullness,
        "neck_finish": neck_finish,
        "neck_strip_l": (neck_circ * 1.6 if neck_finish == "ruffle"
                         else neck_circ * 0.95),
        "neck_strip_h": 4.5 if neck_finish == "ruffle" else 3.5,
    }


def bib_dims(spec) -> dict:
    body_w = spec["neck_circ"] * 0.9
    return {
        "body_w": body_w,
        "body_h": body_w * 1.1,
        "neck_r": spec["neck_circ"] / (2 * math.pi) + 0.5,
        "opening_w": (spec["neck_circ"] / (2 * math.pi) + 0.5) * 0.8,
    }


def bloomers_dims(spec) -> dict:
    return {
        "waist_half": spec["waist"] / 2 + 4.0,
        "hip_half": spec["hip"] / 2 + 4.0,
        "rise": (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0,
        "inseam": 3.0,
    }


def bonnet_dims(spec) -> dict:
    face_w = spec["head"] / 2 - 2.0
    return {
        "face_w": face_w,
        "crown_h": spec["head"] / 4 + 2.0,
        "back_w": spec["head"] / 3,
        "band_l": face_w * 2 + 2.0,
        "band_h": 5.0,
        "tie_w": 2.5,
        "tie_l": 25.0,
    }


def kimono_top_dims(spec) -> dict:
    return {
        "chest_half": spec["chest"] / 4 + 2.0,
        "body_len": spec["length"] * 0.9,
        "neck_drop_back": 2.0,
        "neck_drop_front": 10.0,
        "neck_width": spec["neck_circ"] / 6,
        "shoulder_w": spec["shoulder"],
        "sleeve_cap_w": spec["arm_len"] * 0.3 + spec["shoulder"],
        "sleeve_len": spec["arm_len"] * 0.5,
        "sleeve_cuff": spec["arm_len"] * 0.25 + 3.0,
    }


def pants_dims(spec, style: str = "long") -> dict:
    if style == "long":
        leg_length = spec["length"] * 1.15
        leg_opening = spec["hip"] / 8 + 2.5
    else:
        leg_length = spec["length"] * 0.4
        leg_opening = spec["hip"] / 6 + 3.0
    return {
        "style": style,
        "hip_half": spec["hip"] / 4 + 3.0,
        "waist_half": spec["waist"] / 4 + 2.0,
        "rise": (spec["rise_f"] + spec["rise_b"]) / 2 + 3.0,
        "leg_length": leg_length,
        "leg_opening": leg_opening,
    }


def tshirt_dims(spec, sleeve: str = "short") -> dict:
    return {
        "sleeve": sleeve,
        "chest_half": spec["chest"] / 4 + 2.5,
        "length": spec["length"] * 0.85,
        "neck_drop_front": 4.0,
        "neck_drop_back": 1.5,
        "neck_width": spec["neck_circ"] / 6 + 0.3,
        "shoulder_w": spec["shoulder"] - 0.5,
        "armhole_drop": spec["arm_len"] * 0.3 + 4.0,
        "sleeve_cap_w": spec["arm_len"] * 0.45 + 4.0,
        "sleeve_len": (spec["arm_len"] * 0.35 if sleeve == "short"
                       else spec["arm_len"] * 0.9),
        "sleeve_cuff": spec["arm_len"] * 0.3 + 3.0,
        "neckband_l": spec["neck_circ"] * 0.9,
        "neckband_h": 5.0,
    }


def romper_dims(spec) -> dict:
    return {
        "chest_half": spec["chest"] / 4 + 2.0,
        "bodice_h": spec["length"] * 0.55,
        "rise": (spec["rise_f"] + spec["rise_b"]) / 2 + 4.0,
        "crotch_w": 6.0,
        "neck_drop": 4.0,
        "neck_w": spec["neck_circ"] / 6 + 0.3,
        "armhole_drop": 5.0,
        "armhole_w": 2.5,
        "shoulder": 2.5,
        "leg_opening": spec["hip"] / 8 + 3.0,
        "strap_w": 3.0,
        "strap_len": spec["strap_len"] + 2,
    }


def sleep_sack_dims(spec) -> dict:
    chest_half = spec["chest"] / 4 + 6.0
    return {
        "chest_half": chest_half,
        "hem_half": chest_half + 6.0,
        "total_len": spec["length"] + 20.0,
        "neck_drop_front": 5.0,
        "neck_drop_back": 2.0,
        "neck_w": spec["neck_circ"] / 6 + 0.5,
        "armhole_drop": spec["arm_len"] * 0.3 + 5.0,
        "armhole_w": 3.0,
        "shoulder": 3.0,
    }


def flutter_romper_dims(spec, ruffle_height: float = 7.0,
                        ruffle_fullness: float = 1.8) -> dict:
    top_half = (spec["chest"] + 12) / 4
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
    body_torso = spec["length"] * 0.55
    shoulder_drop = 2.5
    ruffle_length = top_half * 2 * 2 * ruffle_fullness
    strips, each = split_strip(ruffle_length)
    return {
        "top_half": top_half,
        "chest_half": (spec["chest"] + 6) / 4,
        "hip_half": (spec["hip"] + 8) / 4,
        "crotch_half": 3.0,
        "shoulder_drop": shoulder_drop,
        "rise": rise,
        "body_torso": body_torso,
        "total_h": shoulder_drop + body_torso + rise,
        "leg_drop": 8.0,
        "ruffle_h": ruffle_height,
        "ruffle_length": ruffle_length,
        "ruffle_strips": strips,
        "ruffle_length_each": each,
    }


def split_strip(length: float, max_len: float = MAX_STRIP_LEN):
    """Split an over-long strip into N equal pieces. Returns (count, each_len)."""
    if length <= max_len:
        return 1, length
    n = int(math.ceil(length / max_len))
    return n, length / n


# ============================================================
# CANONICAL PIECE LISTS
# ============================================================
def _piece(name, name_th, w, h, count=1, on_fold=False, rotatable=True):
    return {"name": name, "name_th": name_th, "w": w, "h": h,
            "count": count, "on_fold": on_fold, "rotatable": rotatable}


def get_pieces(pattern_key: str, size_label: str, **params) -> list:
    """Return the canonical cut list for a pattern.

    `params` accepts the same style options as the matching generator
    (style, sleeve, tiers, neckline, skirt_style, ...); unknown keys are
    ignored so callers can pass a whole options dict through.
    """
    spec = get_size(size_label)

    if pattern_key == "dress":
        d = dress_dims(spec,
                       skirt_style=params.get("skirt_style", "gathered"),
                       front_placket=params.get("front_placket", False))
        pieces = [
            _piece("Bodice (fold)", "ตัวเสื้อ (ทบ)",
                   d["bodice_w"], d["bodice_h"], 2, on_fold=True, rotatable=False),
            _piece("Skirt", "กระโปรง/ระบาย",
                   d["ruffle_w"], d["ruffle_h"], 2),
            _piece("Strap", "สายไหล่", d["strap_w"], d["strap_h"], 2),
        ]
        if d["front_placket"]:
            pieces.append(_piece("Placket", "สาบกระดุม",
                                 d["placket_w"], d["placket_h"], 2))
        return pieces

    if pattern_key == "tiered_dress":
        d = tiered_dress_dims(spec,
                              tiers=params.get("tiers", 3),
                              neckline=params.get("neckline", "round"),
                              tier_fullness=params.get("tier_fullness", 1.5))
        pieces = [
            _piece("Bodice (fold)", "ตัวเสื้อ (ทบ)",
                   d["bodice_w"], d["bodice_h"], 2, on_fold=True, rotatable=False),
        ]
        for i, w in enumerate(d["tier_widths"], start=1):
            n, each = split_strip(w)
            pieces.append(_piece(f"Tier {i}", f"ชั้นที่ {i}",
                                 each, d["tier_h"], n))
        if d["neckline"] == "halter":
            pieces.append(_piece("Neck band", "แถบคอ",
                                 d["band_w"], d["band_h"], 2))
            pieces.append(_piece("Bow tie", "โบว์ผูกหลัง",
                                 d["tie_l"], d["tie_w"], 2))
        elif d["neckline"] == "strap":
            pieces.append(_piece("Strap", "สายไหล่",
                                 d["strap_w"], d["strap_h"], 2))
        return pieces

    if pattern_key == "flutter_top":
        d = flutter_top_dims(
            spec,
            sleeve_fullness=params.get("sleeve_fullness", 1.8),
            neck_finish=params.get("neck_finish", "ruffle"))
        return [
            _piece("Front (fold)", "ตัวหน้า (ทบ)",
                   d["chest_half"], d["length"], 1, on_fold=True,
                   rotatable=False),
            _piece("Back (fold)", "ตัวหลัง (ทบ)",
                   d["chest_half"], d["length"], 1, on_fold=True,
                   rotatable=False),
            _piece("Flutter sleeve", "แขนระบาย",
                   d["sleeve_w"], d["sleeve_h"], 2),
            _piece("Neck strip", "แถบคอ",
                   d["neck_strip_l"], d["neck_strip_h"], 1),
        ]

    if pattern_key == "bib":
        d = bib_dims(spec)
        return [_piece("Bib", "ผ้ากันเปื้อน", d["body_w"], d["body_h"], 2)]

    if pattern_key == "bloomers":
        d = bloomers_dims(spec)
        return [_piece("Bloomers (fold)", "ตัวกางเกง (ทบ)",
                       d["hip_half"], d["rise"] + d["inseam"], 2,
                       on_fold=True, rotatable=False)]

    if pattern_key == "bonnet":
        d = bonnet_dims(spec)
        return [
            _piece("Crown (fold)", "ครอบหัว (ทบ)",
                   d["face_w"], d["crown_h"], 2, on_fold=True, rotatable=False),
            _piece("Brim band", "แถบปีก", d["band_l"], d["band_h"], 2),
            _piece("Tie", "สายผูก", d["tie_l"], d["tie_w"], 2),
        ]

    if pattern_key == "kimono_top":
        d = kimono_top_dims(spec)
        return [
            _piece("Back (fold)", "หลัง (ทบ)",
                   d["chest_half"], d["body_len"], 1, on_fold=True, rotatable=False),
            _piece("Front", "หน้า", d["chest_half"] + 3.0, d["body_len"], 2),
            _piece("Sleeve", "แขน", d["sleeve_cap_w"], d["sleeve_len"], 2),
        ]

    if pattern_key == "pants":
        d = pants_dims(spec, style=params.get("style", "long"))
        return [_piece("Leg", "ขากางเกง",
                       d["hip_half"], d["leg_length"] + d["rise"], 2,
                       rotatable=False)]

    if pattern_key == "tshirt":
        d = tshirt_dims(spec, sleeve=params.get("sleeve", "short"))
        return [
            _piece("Front (fold)", "หน้า (ทบ)",
                   d["chest_half"], d["length"], 1, on_fold=True, rotatable=False),
            _piece("Back (fold)", "หลัง (ทบ)",
                   d["chest_half"], d["length"], 1, on_fold=True, rotatable=False),
            _piece("Sleeve", "แขน", d["sleeve_cap_w"], d["sleeve_len"], 2),
            _piece("Neckband", "แถบคอ", d["neckband_l"], d["neckband_h"], 1),
        ]

    if pattern_key == "romper":
        d = romper_dims(spec)
        body_h = d["bodice_h"] + d["rise"]
        return [
            _piece("Front (fold)", "หน้า (ทบ)",
                   d["chest_half"], body_h, 1, on_fold=True, rotatable=False),
            _piece("Back (fold)", "หลัง (ทบ)",
                   d["chest_half"], body_h, 1, on_fold=True, rotatable=False),
            _piece("Strap", "สายไหล่", d["strap_len"], d["strap_w"], 2),
        ]

    if pattern_key == "sleep_sack":
        d = sleep_sack_dims(spec)
        return [
            _piece("Back (fold)", "หลัง (ทบ)",
                   d["hem_half"], d["total_len"], 1, on_fold=True, rotatable=False),
            _piece("Front L", "หน้าซ้าย", d["hem_half"], d["total_len"], 1,
                   rotatable=False),
            _piece("Front R", "หน้าขวา", d["hem_half"], d["total_len"], 1,
                   rotatable=False),
        ]

    if pattern_key == "flutter_romper":
        d = flutter_romper_dims(
            spec,
            ruffle_height=params.get("ruffle_height", 7.0),
            ruffle_fullness=params.get("ruffle_fullness", 1.8))
        return [
            _piece("Body (fold)", "ตัวชุด (ทบ)",
                   d["hip_half"], d["total_h"], 2, on_fold=True, rotatable=False),
            _piece("Ruffle", "ระบาย",
                   d["ruffle_length_each"], d["ruffle_h"], d["ruffle_strips"]),
        ]

    raise ValueError(f"unknown pattern '{pattern_key}'")


# ============================================================
# SHELF PACKING — shared by the fabric estimate and the layout PNG
# ============================================================
def pack_pieces(pieces, fabric_width_cm: float, padding_cm: float = 2.0):
    """Place pieces on a bolt of fabric. Returns (placements, total_length, info).

    When any piece is cut on the fold, the fabric is folded selvedge to
    selvedge: the usable width halves, and every non-fold piece is cut
    through both layers so its count halves too. That is how the fabric is
    actually laid out, and it makes the estimated length match the picture.

    `placements` items are (label, x, y, w, h) with the origin at the top
    left of the (possibly folded) fabric.
    """
    folded = any(p["on_fold"] for p in pieces)
    usable_w = fabric_width_cm / 2 if folded else fabric_width_cm

    items = []
    for p in pieces:
        if p["w"] <= 0 or p["h"] <= 0 or p["count"] <= 0:
            continue
        n = p["count"]
        if folded and not p["on_fold"]:
            n = int(math.ceil(n / 2))       # cut through both layers at once
        for i in range(n):
            label = p["name"] if n == 1 else f"{p['name']} #{i + 1}"
            items.append({"label": label, "w": p["w"], "h": p["h"],
                          "rotatable": p["rotatable"]})

    # Shelf packing is greedy, so a single fixed strategy can produce a
    # *worse* layout on a wider bolt (a long strip that no longer has to be
    # rotated stops sharing a shelf with the tall pieces). Try a handful of
    # deterministic strategies and keep the shortest result.
    best = None
    for strategy in ("tall_first", "wide_first", "narrow_side_up"):
        result = _pack_once(items, usable_w, padding_cm, strategy)
        if best is None or result[1] < best[1] - 1e-9:
            best = result

    placements, total_length, oversized = best
    info = {"folded": folded, "usable_width": usable_w,
            "oversized": oversized}
    return placements, total_length, info


def _pack_once(items, usable_w, padding_cm, strategy):
    """One greedy shelf pass. Returns (placements, total_length, oversized)."""
    if strategy == "wide_first":
        ordered = sorted(items, key=lambda it: -max(it["w"], it["h"]))
    else:
        ordered = sorted(items, key=lambda it: -it["h"])

    placements = []
    shelves = []
    cursor_y = 0.0
    oversized = []

    for it in ordered:
        w, h = it["w"], it["h"]
        if it["rotatable"]:
            if strategy == "narrow_side_up" and w > h and h + padding_cm <= usable_w:
                # Stand long strips on end so they can share a shelf with
                # the tall body pieces instead of claiming one of their own.
                w, h = h, w
            elif w + padding_cm > usable_w and h + padding_cm <= usable_w:
                w, h = h, w
        if w + padding_cm > usable_w:
            oversized.append(it["label"])

        placed = False
        for shelf in shelves:
            if shelf["used_x"] + w + padding_cm <= usable_w:
                placements.append((it["label"],
                                   shelf["used_x"] + padding_cm / 2,
                                   shelf["y"] + padding_cm / 2, w, h))
                shelf["used_x"] += w + padding_cm
                shelf["height"] = max(shelf["height"], h + padding_cm)
                placed = True
                break
        if not placed:
            shelves.append({"y": cursor_y, "used_x": w + padding_cm,
                            "height": h + padding_cm})
            placements.append((it["label"], padding_cm / 2,
                               cursor_y + padding_cm / 2, w, h))
            cursor_y += h + padding_cm

    return placements, sum(s["height"] for s in shelves), oversized


def estimate_fabric(pattern_key: str, size_label: str,
                    fabric_width_cm: float, waste_factor: float = 1.10,
                    **params) -> float:
    """Fabric length in cm for one pattern at one bolt width."""
    pieces = get_pieces(pattern_key, size_label, **params)
    _, length, _ = pack_pieces(pieces, fabric_width_cm)
    return length * waste_factor
