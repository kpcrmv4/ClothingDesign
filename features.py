"""
Feature tools: pattern metadata, shopping list, fabric calculation,
cutting layout, and customization helper.
"""
from sizes import SIZE_CHART, get_size


# ============================================================
# PATTERN METADATA
# ============================================================
PATTERN_META = {
    "dress": {
        "title": "Baby Dress",
        "difficulty": "Beginner",
        "time_hours": "2-3",
        "fabric_types": ["cotton lawn", "linen", "double gauze", "quilting cotton"],
        "notions": ["matching thread", "bias tape 1m", "snap or button (optional)"],
        "pieces": [("Bodice", 2, "cut on fold"),
                   ("Strap", 2, ""),
                   ("Ruffle", 2, "gather")],
    },
    "bib": {
        "title": "Baby Bib",
        "difficulty": "Beginner",
        "time_hours": "1",
        "fabric_types": ["quilting cotton (front)", "terry / bamboo / fleece (back)"],
        "notions": ["matching thread", "1 KAM snap OR 20cm velcro"],
        "pieces": [("Bib body", 2, "front + backing")],
    },
    "bloomers": {
        "title": "Baby Bloomers",
        "difficulty": "Beginner",
        "time_hours": "1-2",
        "fabric_types": ["knit cotton", "woven cotton", "seersucker"],
        "notions": ["matching thread",
                    "1 cm elastic: 1 waist piece + 2 leg pieces"],
        "pieces": [("Bloomer body", 2, "cut on fold")],
    },
    "bonnet": {
        "title": "Baby Bonnet",
        "difficulty": "Intermediate",
        "time_hours": "2-3",
        "fabric_types": ["quilting cotton", "linen", "double gauze"],
        "notions": ["matching thread",
                    "0.3m lining fabric",
                    "20x10cm fusible interfacing"],
        "pieces": [("Crown", 2, "outer + lining, on fold"),
                   ("Brim band", 2, "interline one"),
                   ("Tie", 2, "")],
    },
    "kimono_top": {
        "title": "Baby Kimono Wrap Top",
        "difficulty": "Beginner",
        "time_hours": "2-3",
        "fabric_types": ["cotton lawn", "flannel", "double gauze", "jersey"],
        "notions": ["matching thread", "bias tape 1.5m",
                    "2 small snaps OR ribbon ties 60cm"],
        "pieces": [("Back bodice", 1, "cut on fold"),
                   ("Front bodice", 2, "left + right mirror"),
                   ("Sleeve", 2, "")],
    },
    "pants": {
        "title": "Baby Elastic-Waist Pants",
        "difficulty": "Beginner",
        "time_hours": "1-2",
        "fabric_types": ["knit", "woven cotton", "french terry", "fleece"],
        "notions": ["matching thread", "2cm wide elastic (waist length)"],
        "pieces": [("Leg", 2, "cut 2, mirror")],
    },
    "tshirt": {
        "title": "Baby T-Shirt",
        "difficulty": "Intermediate",
        "time_hours": "1-2",
        "fabric_types": ["cotton jersey", "interlock knit", "bamboo knit"],
        "notions": ["matching thread",
                    "ballpoint sewing machine needle",
                    "neckband ribbing 30x5cm",
                    "3 snaps (shoulder opening)"],
        "pieces": [("Front", 1, "cut on fold"),
                   ("Back", 1, "cut on fold"),
                   ("Sleeve", 2, ""),
                   ("Neckband", 1, "ribbing")],
    },
    "romper": {
        "title": "Baby Romper",
        "difficulty": "Intermediate",
        "time_hours": "3-4",
        "fabric_types": ["cotton lawn", "double gauze", "light cotton"],
        "notions": ["matching thread", "bias tape 1m",
                    "3 snaps (crotch opening)",
                    "small elastic 20cm (leg openings)"],
        "pieces": [("Front", 1, "cut on fold"),
                   ("Back", 1, "cut on fold"),
                   ("Strap", 2, "")],
    },
    "sleep_sack": {
        "title": "Baby Sleep Sack",
        "difficulty": "Intermediate",
        "time_hours": "2-3",
        "fabric_types": ["cotton jersey", "flannel backed cotton", "muslin"],
        "notions": ["matching thread",
                    "1 separating zipper 35-50cm",
                    "bias tape 2m (armhole + neck binding)"],
        "pieces": [("Front", 2, "left + right for zipper"),
                   ("Back", 1, "cut on fold")],
    },
    "flutter_romper": {
        "title": "Off-Shoulder Flutter Romper",
        "difficulty": "Intermediate",
        "time_hours": "3-4",
        "fabric_types": ["cotton lawn", "poplin", "double gauze", "lightweight cotton"],
        "notions": ["matching thread",
                    "5mm elastic for neckline + leg openings",
                    "3 KAM snaps (crotch)"],
        "pieces": [("Body", 2, "cut on fold, front + back identical"),
                   ("Ruffle strip", 1, "long strip, gather")],
    },
}


def list_all_patterns() -> str:
    """Format a table of all available patterns with metadata."""
    lines = [
        "Available patterns:",
        "",
        f"  {'Key':<12} {'Difficulty':<14} {'Time':<8} Title",
        f"  {'-' * 12} {'-' * 14} {'-' * 8} {'-' * 30}",
    ]
    for key, meta in PATTERN_META.items():
        lines.append(
            f"  {key:<12} {meta['difficulty']:<14} "
            f"{meta['time_hours'] + 'h':<8} {meta['title']}"
        )
    lines.append("")
    lines.append("Call generate_<key>_pattern(size_label) to create a PDF.")
    lines.append("Call generate_shopping_list(pattern_keys, size) for materials.")
    return "\n".join(lines)


# ============================================================
# SHOPPING LIST
# ============================================================
def generate_shopping_list(pattern_keys: list, size_label: str) -> str:
    """Aggregate materials across multiple patterns for one size."""
    if size_label not in SIZE_CHART:
        return f"Error: size '{size_label}' not found. Available: {list(SIZE_CHART)}"

    invalid = [p for p in pattern_keys if p not in PATTERN_META]
    if invalid:
        return (f"Error: unknown pattern keys {invalid}. "
                f"Available: {list(PATTERN_META)}")

    fabric_meters = 0.0
    notion_set = {}

    lines = [f"Shopping list - Size {size_label}",
             "=" * 50, ""]

    for key in pattern_keys:
        meta = PATTERN_META[key]
        fabric_est = calculate_fabric(key, size_label)
        fabric_meters += fabric_est["est_115cm"] / 100
        lines.append(f"{meta['title']}  ({meta['difficulty']}, "
                     f"{meta['time_hours']}h)")
        lines.append(f"  Suggested fabrics: {', '.join(meta['fabric_types'])}")
        lines.append(f"  Fabric needed: ~{fabric_est['est_115cm'] / 100:.2f}m "
                     f"of 115cm wide")
        lines.append("  Notions:")
        for n in meta["notions"]:
            lines.append(f"    - {n}")
            notion_set[n] = notion_set.get(n, 0) + 1
        lines.append("")

    lines.append("=" * 50)
    lines.append("SUMMARY")
    lines.append("=" * 50)
    lines.append(f"Total fabric (115cm width): ~{fabric_meters:.2f} m "
                 f"(add 10% for error)")
    lines.append(f"Recommended purchase: {fabric_meters * 1.1:.1f} m")
    lines.append("")
    lines.append("Combined notions (quantities = # projects using each):")
    for notion, count in sorted(notion_set.items(), key=lambda x: -x[1]):
        suffix = f"  x{count}" if count > 1 else ""
        lines.append(f"  - {notion}{suffix}")

    return "\n".join(lines)


# ============================================================
# FABRIC CALCULATOR
# ============================================================
def calculate_fabric(pattern_key: str, size_label: str) -> dict:
    """Return dict with fabric length estimates for 90/115/150 cm bolts."""
    spec = get_size(size_label)

    if pattern_key == "dress":
        bodice_w = spec["chest"] / 4 + 2.0
        bodice_h = spec["length"]
        ruffle_w = bodice_w * 2 * 1.5
        ruffle_h = spec["ruffle_h"]
        pieces = [
            ("Bodice (x2)", bodice_w * 2, bodice_h),
            ("Ruffle (x2)", ruffle_w, ruffle_h * 2),
        ]
        extra = 3.0 * spec["strap_len"] * 2
    elif pattern_key == "bib":
        body_w = spec["neck_circ"] * 0.9
        body_h = body_w * 1.1
        pieces = [("Front + back", body_w, body_h * 2)]
        extra = 0
    elif pattern_key == "bloomers":
        hip_half = spec["hip"] / 2 + 4.0
        rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
        pieces = [("Front + back (x2)", hip_half, rise * 2)]
        extra = 0
    elif pattern_key == "bonnet":
        face_w = spec["head"] / 2 - 2.0
        crown_h = spec["head"] / 4 + 2.0
        band_l = face_w * 2 + 2.0
        pieces = [
            ("Crown (x2)", face_w * 2, crown_h * 2),
            ("Brim (x2)", band_l, 10.0),
        ]
        extra = 2.5 * 25.0 * 2
    elif pattern_key == "kimono_top":
        back_w = spec["chest"] / 2 + 3.0
        length = spec["length"] * 0.9
        sleeve_w = spec["arm_len"] * 0.5 + 4.0
        pieces = [
            ("Back (x1) + Front (x2)", back_w * 1.5, length),
            ("Sleeve (x2)", sleeve_w * 2, sleeve_w),
        ]
        extra = 0
    elif pattern_key == "pants":
        hip_half = spec["hip"] / 2 + 3.0
        leg_len = spec["length"] * 0.75
        pieces = [("Legs (x2 mirrored)", hip_half * 2, leg_len)]
        extra = 0
    elif pattern_key == "tshirt":
        chest_half = spec["chest"] / 2 + 3.0
        length = spec["length"] * 0.8
        sleeve_w = spec["arm_len"] * 0.4 + 4.0
        pieces = [
            ("Front + Back (x2)", chest_half, length * 2),
            ("Sleeve (x2)", sleeve_w * 2, sleeve_w),
            ("Neckband", 30, 5),
        ]
        extra = 0
    elif pattern_key == "romper":
        chest_half = spec["chest"] / 2 + 3.0
        total_len = spec["length"] + (spec["rise_f"] + spec["rise_b"]) / 2 + 5
        pieces = [("Front + Back", chest_half * 2, total_len)]
        extra = 3 * spec["strap_len"] * 2
    elif pattern_key == "sleep_sack":
        chest_half = spec["chest"] / 2 + 6.0
        length = spec["length"] + 15
        pieces = [
            ("Back (x1)", chest_half, length),
            ("Front (x2 for zipper)", chest_half, length),
        ]
        extra = 0
    elif pattern_key == "flutter_romper":
        hip_half = (spec["hip"] + 8) / 4
        rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
        body_h = 2.5 + spec["length"] * 0.55 + rise
        top_half = (spec["chest"] + 12) / 4
        ruffle_len = top_half * 2 * 2 * 1.8
        pieces = [
            ("Body (x2 fold)", hip_half, body_h * 2),
            ("Ruffle strip", ruffle_len, 7.0),
        ]
        extra = 0
    else:
        return {"error": f"unknown pattern '{pattern_key}'"}

    sa_pad = 3.0
    result = {}
    for width_cm in (90, 115, 150):
        total_len = 0.0
        for _, pw, ph in pieces:
            effective_w = pw + sa_pad
            if effective_w > width_cm:
                total_len += (ph + sa_pad) * 2
            else:
                total_len += ph + sa_pad
        if extra:
            total_len += (extra / width_cm) + sa_pad
        result[f"est_{width_cm}cm"] = total_len * 1.10
    result["pieces"] = pieces
    return result


def format_fabric_requirement(pattern_key: str, size_label: str) -> str:
    """Return human-readable fabric estimate."""
    data = calculate_fabric(pattern_key, size_label)
    if "error" in data:
        return f"Error: {data['error']}"

    lines = [f"Fabric estimate: {pattern_key} size {size_label}", "", "Pieces:"]
    for name, pw, ph in data["pieces"]:
        lines.append(f"  {name}: {pw:.1f} x {ph:.1f} cm")
    lines.append("")
    lines.append("Required length by bolt width (10% wastage included):")
    for w in (90, 115, 150):
        length = data[f"est_{w}cm"]
        lines.append(f"  {w}cm wide -> {length / 100:.2f} m ({length:.0f} cm)")
    lines.append("")
    lines.append("Assumes single-layer layout. "
                 "Cut-on-fold pieces save ~40%, directional prints need more.")
    return "\n".join(lines)


# ============================================================
# SIZE LIST
# ============================================================
def list_available_sizes() -> str:
    """Format size chart as a table."""
    lines = ["Available sizes (all in cm):", ""]
    headers = ["size", "chest", "length", "waist", "hip", "head",
               "arm_len", "neck_circ"]
    lines.append("  ".join(f"{h:>9}" for h in headers))
    lines.append("  ".join("-" * 9 for _ in headers))
    for size, spec in SIZE_CHART.items():
        row = [size, str(spec["chest"]), str(spec["length"]),
               str(spec["waist"]), str(spec["hip"]), str(spec["head"]),
               str(spec["arm_len"]), str(spec["neck_circ"])]
        lines.append("  ".join(f"{v:>9}" for v in row))
    lines.append("")
    lines.append("Use these size labels with any generate_*_pattern tool.")
    return "\n".join(lines)
