"""
Cutting layout visualizer: shows how to place pattern pieces on
a bolt of fabric (90, 115, or 150 cm wide) for efficient cutting.

Uses simple shelf packing — not optimal bin packing, but readable.
"""
import os
from PIL import Image, ImageDraw, ImageFont

from sizes import get_size
from features import PATTERN_META, calculate_fabric


_PX_PER_CM = 5
_MARGIN_PX = 20


def _get_pieces_for_layout(pattern_key: str, size_label: str):
    """Return list of (name, width_cm, height_cm, count, rotatable)."""
    spec = get_size(size_label)

    if pattern_key == "dress":
        return [
            ("Bodice (fold)", spec["chest"] / 4 + 2.0, spec["length"], 2, False),
            ("Ruffle", (spec["chest"] / 4 + 2.0) * 2 * 1.5, spec["ruffle_h"], 2, True),
            ("Strap", 3.0, spec["strap_len"], 2, True),
        ]
    if pattern_key == "bib":
        body_w = spec["neck_circ"] * 0.9
        return [("Bib", body_w, body_w * 1.1, 2, True)]
    if pattern_key == "bloomers":
        return [("Bloomers (fold)",
                 spec["hip"] / 2 + 4.0,
                 (spec["rise_f"] + spec["rise_b"]) / 2 + 2 + 3, 2, False)]
    if pattern_key == "bonnet":
        fw = spec["head"] / 2 - 2.0
        return [
            ("Crown (fold)", fw, spec["head"] / 4 + 2.0, 2, False),
            ("Brim band", fw * 2 + 2.0, 5.0, 2, True),
            ("Tie", 25.0, 2.5, 2, True),
        ]
    if pattern_key == "kimono_top":
        return [
            ("Back (fold)", spec["chest"] / 4 + 2.0, spec["length"] * 0.9, 1, False),
            ("Front", spec["chest"] / 4 + 2.0, spec["length"] * 0.9, 2, True),
            ("Sleeve", spec["arm_len"] * 0.3 + spec["shoulder"],
             spec["arm_len"] * 0.5, 2, True),
        ]
    if pattern_key == "pants":
        return [("Leg", spec["hip"] / 4 + 3.0,
                 spec["length"] * 1.15 + (spec["rise_f"] + spec["rise_b"]) / 2 + 3,
                 2, False)]
    if pattern_key == "tshirt":
        return [
            ("Front (fold)", spec["chest"] / 4 + 2.5,
             spec["length"] * 0.85, 1, False),
            ("Back (fold)", spec["chest"] / 4 + 2.5,
             spec["length"] * 0.85, 1, False),
            ("Sleeve", spec["arm_len"] * 0.45 + 4.0,
             spec["arm_len"] * 0.35, 2, True),
            ("Neckband", 30, 5, 1, True),
        ]
    if pattern_key == "romper":
        return [
            ("Front (fold)", spec["chest"] / 4 + 2.0,
             spec["length"] * 0.55 + (spec["rise_f"] + spec["rise_b"]) / 2 + 4,
             1, False),
            ("Back (fold)", spec["chest"] / 4 + 2.0,
             spec["length"] * 0.55 + (spec["rise_f"] + spec["rise_b"]) / 2 + 4,
             1, False),
            ("Strap", spec["strap_len"] + 2, 3.0, 2, True),
        ]
    if pattern_key == "sleep_sack":
        h = spec["length"] + 20.0
        return [
            ("Back (fold)", spec["chest"] / 4 + 6.0, h, 1, False),
            ("Front (L)", spec["chest"] / 4 + 6.0, h, 1, False),
            ("Front (R)", spec["chest"] / 4 + 6.0, h, 1, False),
        ]
    return []


def _pack_shelf(pieces, fabric_width_cm, padding_cm=2.0):
    """Place rectangles on horizontal shelves. Returns (placements, total_length)."""
    placements = []
    shelves = []  # list of dicts: {y: float, used_x: float, height: float}
    current_max_y = 0.0

    # expand counts into individual items, sort by height desc
    items = []
    for name, w, h, count, rotatable in pieces:
        for i in range(count):
            items.append((f"{name} #{i + 1}" if count > 1 else name,
                          w, h, rotatable))
    items.sort(key=lambda x: -x[2])

    for name, w, h, rotatable in items:
        # try to rotate if doesn't fit width and rotatable
        if w + padding_cm > fabric_width_cm and rotatable and h + padding_cm <= fabric_width_cm:
            w, h = h, w

        if w + padding_cm > fabric_width_cm:
            # piece too wide, will overlap but we still place it
            pass

        placed = False
        for shelf in shelves:
            if shelf["used_x"] + w + padding_cm <= fabric_width_cm:
                placements.append((name, shelf["used_x"] + padding_cm / 2,
                                   shelf["y"] + padding_cm / 2, w, h))
                shelf["used_x"] += w + padding_cm
                if h + padding_cm > shelf["height"]:
                    shelf["height"] = h + padding_cm
                placed = True
                break
        if not placed:
            new_y = current_max_y
            shelves.append({"y": new_y, "used_x": 0, "height": h + padding_cm})
            placements.append((name, padding_cm / 2,
                               new_y + padding_cm / 2, w, h))
            shelves[-1]["used_x"] = w + padding_cm
            current_max_y = new_y + h + padding_cm

    total_length = sum(s["height"] for s in shelves)
    return placements, total_length


def _get_font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def generate_layout(pattern_key: str, size_label: str,
                     fabric_width_cm: int = 115) -> str:
    """Generate PNG showing suggested cut layout on a bolt of given width."""
    if pattern_key not in PATTERN_META:
        return (f"Error: unknown pattern '{pattern_key}'. "
                f"Available: {list(PATTERN_META)}")
    if fabric_width_cm not in (90, 115, 150):
        return "Error: fabric_width_cm must be 90, 115, or 150"

    pieces = _get_pieces_for_layout(pattern_key, size_label)
    if not pieces:
        return f"Error: no layout data for '{pattern_key}'"

    placements, total_length = _pack_shelf(pieces, fabric_width_cm)

    # render
    pad = _MARGIN_PX * 2
    img_w = int(fabric_width_cm * _PX_PER_CM) + pad + 200   # legend space
    img_h = int(total_length * _PX_PER_CM) + pad + 80       # header space

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)

    title_font = _get_font(16)
    label_font = _get_font(11)
    small_font = _get_font(9)

    # header
    meta = PATTERN_META[pattern_key]
    draw.text((_MARGIN_PX, 10),
              f"{meta['title']} - Size {size_label} - Fabric width {fabric_width_cm}cm",
              fill="black", font=title_font)
    draw.text((_MARGIN_PX, 30),
              f"Required length: {total_length:.0f} cm "
              f"(~{total_length / 100:.2f} m, add 10% margin)",
              fill="gray", font=label_font)

    # fabric outline
    ox = _MARGIN_PX
    oy = 60
    fabric_px_w = int(fabric_width_cm * _PX_PER_CM)
    fabric_px_h = int(total_length * _PX_PER_CM)
    draw.rectangle(
        [ox, oy, ox + fabric_px_w, oy + fabric_px_h],
        outline="blue", width=2)

    # selvedge labels
    draw.text((ox, oy + fabric_px_h + 5),
              f"<- {fabric_width_cm} cm fabric width ->",
              fill="blue", font=small_font)
    draw.text((ox + fabric_px_w + 5, oy + fabric_px_h // 2 - 8),
              f"{total_length:.0f} cm\nlength",
              fill="blue", font=small_font)

    # pieces (note: layout uses x=0 at left of fabric, y=0 at top)
    colors = ["#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF",
              "#A0C4FF", "#BDB2FF", "#FFC6FF", "#FFADAD"]
    for i, (name, x, y, w, h) in enumerate(placements):
        color = colors[i % len(colors)]
        x1 = ox + int(x * _PX_PER_CM)
        y1 = oy + int(y * _PX_PER_CM)
        x2 = x1 + int(w * _PX_PER_CM)
        y2 = y1 + int(h * _PX_PER_CM)
        draw.rectangle([x1, y1, x2, y2], fill=color, outline="black", width=1)
        draw.text((x1 + 3, y1 + 3), name, fill="black", font=small_font)
        draw.text((x1 + 3, y1 + 16),
                  f"{w:.0f}x{h:.0f}", fill="#555", font=small_font)

    # note about folds
    note_y = oy + fabric_px_h + 25
    draw.text((_MARGIN_PX, note_y),
              "Note: '(fold)' pieces are cut on the fabric fold "
              "(fold fabric in half first), so only half the piece is shown.",
              fill="gray", font=small_font)

    file_path = os.path.abspath(
        f"cutting_layout_{pattern_key}_{size_label}_{fabric_width_cm}cm.png")
    img.save(file_path, "PNG")
    return file_path
