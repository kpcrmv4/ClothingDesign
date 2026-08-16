"""
Feature tools: pattern metadata, fabric calculation, and shopping list.

PATTERN_META is the one registry of pattern identity — English title, Thai
title, emoji, difficulty, fabrics, notions and the cut list summary. The
gallery, the tool docstrings and the shopping list all read from here.

Fabric quantities come from geometry.estimate_fabric(), which packs the same
piece list that the cutting-layout PNG draws, so the two always agree.
"""
import geometry
from sizes import SIZE_CHART, get_size


# ============================================================
# PATTERN METADATA
# ============================================================
PATTERN_META = {
    "dress": {
        "title": "Baby Dress",
        "title_th": "เดรสเด็ก",
        "emoji": "👗",
        "difficulty": "Beginner",
        "time_hours": "2-3",
        "fabric_types": ["cotton lawn", "linen", "double gauze", "quilting cotton"],
        "notions": ["ด้ายสีเข้ากับผ้า", "ผ้ากุ๊น (bias tape) 1 ม.",
                    "กระดุมหรือ snap เล็ก 2-3 เม็ด (ทางเลือก)"],
        "pieces": [("ตัวเสื้อ", 2, "ตัดบนรอยพับ"),
                   ("สายไหล่", 2, ""),
                   ("ระบาย/กระโปรง", 2, "รูดจีบ")],
    },
    "tiered_dress": {
        "title": "Tiered Ruffle Dress",
        "title_th": "เดรสกระโปรงชั้น",
        "emoji": "🎀",
        "difficulty": "Intermediate",
        "time_hours": "3-5",
        "fabric_types": ["cotton gingham", "cotton lawn", "double gauze",
                         "seersucker", "ผ้าลายดอกเล็ก"],
        "notions": ["ด้ายสีเข้ากับผ้า", "ผ้ากุ๊น (bias tape) 1 ม.",
                    "ลูกไม้ลายฉลุ (ตกแต่งรอยต่อชั้น)",
                    "ซิปซ่อนหลัง 20 ซม. หรือ snap 3 เม็ด"],
        "pieces": [("ตัวเสื้อ", 2, "ตัดบนรอยพับ"),
                   ("ชั้นกระโปรง", 2, "ต่อชั้นละ 2-3 ชิ้น รูดจีบ"),
                   ("แถบคอ/สายไหล่", 2, "ตามแบบคอที่เลือก")],
    },
    "flutter_top": {
        "title": "Flutter-Sleeve Top",
        "title_th": "เสื้อคอระบายแขนระบาย",
        "emoji": "🤍",
        "difficulty": "Intermediate",
        "time_hours": "2-3",
        "fabric_types": ["cotton lawn สีขาว", "double gauze",
                         "ผ้าฝ้ายลายฉลุ (eyelet)", "voile"],
        "notions": ["ด้ายสีเข้ากับผ้า",
                    "snap หรือกระดุมเล็ก 2 เม็ด (เปิดหลังคอ)"],
        "pieces": [("ตัวหน้า", 1, "ตัดบนรอยพับ"),
                   ("ตัวหลัง", 1, "ตัดบนรอยพับ"),
                   ("แขนระบาย", 2, "รูดจีบขอบบน"),
                   ("แถบคอ", 1, "รูดจีบหรือกุ๊น")],
    },
    "bib": {
        "title": "Baby Bib",
        "title_th": "ผ้ากันเปื้อน",
        "emoji": "🧷",
        "difficulty": "Beginner",
        "time_hours": "1",
        "fabric_types": ["quilting cotton (ด้านหน้า)",
                         "terry / bamboo / fleece (ด้านหลังซับน้ำ)"],
        "notions": ["ด้ายสีเข้ากับผ้า", "KAM snap 1 ชุด หรือ velcro 20 ซม."],
        "pieces": [("ตัวผ้ากันเปื้อน", 2, "หน้า + ซับหลัง")],
    },
    "bloomers": {
        "title": "Baby Bloomers",
        "title_th": "กางเกงใน Bloomers",
        "emoji": "🩲",
        "difficulty": "Beginner",
        "time_hours": "1-2",
        "fabric_types": ["knit cotton", "woven cotton", "seersucker"],
        "notions": ["ด้ายสีเข้ากับผ้า",
                    "ยางยืด 1 ซม.: เอว 1 เส้น + ขา 2 เส้น"],
        "pieces": [("ตัวกางเกง", 2, "ตัดบนรอยพับ")],
    },
    "bonnet": {
        "title": "Baby Bonnet",
        "title_th": "หมวกเด็ก",
        "emoji": "👒",
        "difficulty": "Intermediate",
        "time_hours": "2-3",
        "fabric_types": ["quilting cotton", "linen", "double gauze"],
        "notions": ["ด้ายสีเข้ากับผ้า", "ผ้าซับใน 0.3 ม.",
                    "ผ้ากาว (interfacing) 20x10 ซม."],
        "pieces": [("ครอบหัว", 2, "นอก + ซับใน ตัดบนรอยพับ"),
                   ("แถบปีกหมวก", 2, "รีดผ้ากาว 1 ชิ้น"),
                   ("สายผูก", 2, "")],
    },
    "kimono_top": {
        "title": "Baby Kimono Wrap Top",
        "title_th": "เสื้อป้ายผูกข้าง",
        "emoji": "🥋",
        "difficulty": "Beginner",
        "time_hours": "2-3",
        "fabric_types": ["cotton lawn", "flannel", "double gauze", "jersey"],
        "notions": ["ด้ายสีเข้ากับผ้า", "ผ้ากุ๊น 1.5 ม.",
                    "snap เล็ก 2 เม็ด หรือ ริบบิ้นผูก 60 ซม."],
        "pieces": [("ตัวหลัง", 1, "ตัดบนรอยพับ"),
                   ("ตัวหน้า", 2, "ซ้าย + ขวา กลับด้าน"),
                   ("แขน", 2, "")],
    },
    "pants": {
        "title": "Baby Elastic-Waist Pants",
        "title_th": "กางเกงเอวยางยืด",
        "emoji": "👖",
        "difficulty": "Beginner",
        "time_hours": "1-2",
        "fabric_types": ["knit", "woven cotton", "french terry", "fleece"],
        "notions": ["ด้ายสีเข้ากับผ้า", "ยางยืดกว้าง 2 ซม. (ยาวเท่ารอบเอว)"],
        "pieces": [("ขากางเกง", 2, "ตัด 2 ชิ้นกลับด้าน")],
    },
    "tshirt": {
        "title": "Baby T-Shirt",
        "title_th": "เสื้อยืดเด็ก",
        "emoji": "👕",
        "difficulty": "Intermediate",
        "time_hours": "1-2",
        "fabric_types": ["cotton jersey", "interlock knit", "bamboo knit"],
        "notions": ["ด้ายสีเข้ากับผ้า",
                    "เข็มจักรปลายมน (ballpoint)",
                    "ผ้ายืดขอบคอ 30x5 ซม.",
                    "snap 3 เม็ด (เปิดไหล่)"],
        "pieces": [("ตัวหน้า", 1, "ตัดบนรอยพับ"),
                   ("ตัวหลัง", 1, "ตัดบนรอยพับ"),
                   ("แขน", 2, ""),
                   ("แถบคอ", 1, "ผ้ายืด")],
    },
    "romper": {
        "title": "Baby Romper",
        "title_th": "ชุดหมีเด็ก",
        "emoji": "👶",
        "difficulty": "Intermediate",
        "time_hours": "3-4",
        "fabric_types": ["cotton lawn", "double gauze", "light cotton"],
        "notions": ["ด้ายสีเข้ากับผ้า", "ผ้ากุ๊น 1 ม.",
                    "snap 3 เม็ด (เป้า)",
                    "ยางยืดเล็ก 20 ซม. (ขอบขา)"],
        "pieces": [("ตัวหน้า", 1, "ตัดบนรอยพับ"),
                   ("ตัวหลัง", 1, "ตัดบนรอยพับ"),
                   ("สายไหล่", 2, "")],
    },
    "sleep_sack": {
        "title": "Baby Sleep Sack",
        "title_th": "ถุงนอนเด็ก",
        "emoji": "😴",
        "difficulty": "Intermediate",
        "time_hours": "2-3",
        "fabric_types": ["cotton jersey", "flannel backed cotton", "muslin"],
        "notions": ["ด้ายสีเข้ากับผ้า",
                    "ซิปแยก 35-50 ซม. 1 เส้น",
                    "ผ้ากุ๊น 2 ม. (ขอบคอ + วงแขน)"],
        "pieces": [("ตัวหน้า", 2, "ซ้าย + ขวา สำหรับซิป"),
                   ("ตัวหลัง", 1, "ตัดบนรอยพับ")],
    },
    "flutter_romper": {
        "title": "Off-Shoulder Flutter Romper",
        "title_th": "ชุดหมีคอระบาย",
        "emoji": "🌸",
        "difficulty": "Intermediate",
        "time_hours": "3-4",
        "fabric_types": ["cotton lawn", "poplin", "double gauze",
                         "lightweight cotton"],
        "notions": ["ด้ายสีเข้ากับผ้า",
                    "ยางยืด 5 มม. (คอ + ขอบขา)",
                    "KAM snap 3 เม็ด (เป้า)"],
        "pieces": [("ตัวชุด", 2, "ตัดบนรอยพับ หน้า/หลังเหมือนกัน"),
                   ("แถบระบาย", 1, "แถบยาว รูดจีบ")],
    },
}

# Extra notions that only apply when a style option is switched on.
_OPTION_NOTIONS = {
    "lace_trim": "ลูกไม้ลายฉลุ (ตามความยาวที่ระบุด้านล่าง)",
    "front_placket": "กระดุมเล็ก {n} เม็ด + ผ้ากาวเส้นสาบ",
    "bubble": "ผ้าซับชายกระโปรง (ทรงบอลลูน) ~0.2 ม.",
    "halter": "ริบบิ้นหรือผ้าทำโบว์ผูกหลัง",
}


def list_all_patterns() -> str:
    """Format a table of all available patterns with metadata."""
    lines = [
        f"แพทเทิร์นทั้งหมด {len(PATTERN_META)} แบบ:",
        "",
        f"  {'key':<15} {'ระดับ':<14} {'เวลา':<8} ชื่อ",
        f"  {'-' * 15} {'-' * 14} {'-' * 8} {'-' * 30}",
    ]
    for key, meta in PATTERN_META.items():
        lines.append(
            f"  {key:<15} {meta['difficulty']:<14} "
            f"{meta['time_hours'] + 'h':<8} "
            f"{meta['emoji']} {meta['title_th']} ({meta['title']})"
        )
    lines.append("")
    lines.append("เรียก generate_<key>_pattern(size_label) เพื่อสร้าง PDF")
    lines.append("เรียก generate_shopping_list([keys], size) เพื่อดูรายการวัสดุ")
    return "\n".join(lines)


# ============================================================
# FABRIC CALCULATOR
# ============================================================
def calculate_fabric(pattern_key: str, size_label: str, **params) -> dict:
    """Fabric length estimates for 90/115/150 cm bolts, plus the cut list."""
    try:
        pieces = geometry.get_pieces(pattern_key, size_label, **params)
    except ValueError as e:
        return {"error": str(e)}

    result = {"pieces": pieces}
    for width_cm in (90, 115, 150):
        result[f"est_{width_cm}cm"] = geometry.estimate_fabric(
            pattern_key, size_label, width_cm, **params)
    return result


def format_fabric_requirement(pattern_key: str, size_label: str,
                              **params) -> str:
    """Human-readable fabric estimate."""
    if size_label not in SIZE_CHART:
        return (f"Error: ไม่พบไซส์ '{size_label}' "
                f"ไซส์ที่มี: {', '.join(SIZE_CHART)}")

    data = calculate_fabric(pattern_key, size_label, **params)
    if "error" in data:
        return f"Error: {data['error']}"

    meta = PATTERN_META.get(pattern_key, {})
    title = meta.get("title_th", pattern_key)

    lines = [f"ประมาณการผ้า: {title} ไซส์ {size_label}", "", "ชิ้นที่ต้องตัด:"]
    for p in data["pieces"]:
        fold = " (ตัดบนรอยพับ)" if p["on_fold"] else ""
        lines.append(f"  {p['name_th']} x{p['count']}: "
                     f"{p['w']:.1f} x {p['h']:.1f} ซม.{fold}")
    lines.append("")
    lines.append("ความยาวผ้าที่ต้องใช้ (รวมเผื่อเสีย 10% แล้ว):")
    for w in (90, 115, 150):
        length = data[f"est_{w}cm"]
        lines.append(f"  ผ้าหน้ากว้าง {w} ซม. -> {length / 100:.2f} ม. "
                     f"({length:.0f} ซม.)")
    lines.append("")
    lines.append("คำนวณจากการวางผังจริง (พับผ้าเมื่อมีชิ้นตัดบนรอยพับ) "
                 "ตรงกับภาพผังตัดที่ generate_cutting_layout สร้าง")
    lines.append("ผ้าลายมีทิศทางหรือลายตารางที่ต้องต่อลาย ให้เผื่อเพิ่ม 15-20%")
    return "\n".join(lines)


# ============================================================
# SHOPPING LIST
# ============================================================
def generate_shopping_list(pattern_keys, size_label: str,
                           fabric_width_cm: int = 115) -> str:
    """Aggregate materials across one or more patterns for one size."""
    if isinstance(pattern_keys, str):
        pattern_keys = [pattern_keys]
    if size_label not in SIZE_CHART:
        return (f"Error: ไม่พบไซส์ '{size_label}' "
                f"ไซส์ที่มี: {', '.join(SIZE_CHART)}")

    invalid = [p for p in pattern_keys if p not in PATTERN_META]
    if invalid:
        return (f"Error: ไม่รู้จักแพทเทิร์น {invalid} "
                f"ที่มี: {', '.join(PATTERN_META)}")
    if not pattern_keys:
        return "Error: ต้องระบุแพทเทิร์นอย่างน้อย 1 แบบ"

    fabric_total = 0.0
    notion_count = {}

    lines = [f"รายการซื้อของ — ไซส์ {size_label} "
             f"(ผ้าหน้ากว้าง {fabric_width_cm} ซม.)",
             "=" * 55, ""]

    for key in pattern_keys:
        meta = PATTERN_META[key]
        est = geometry.estimate_fabric(key, size_label, fabric_width_cm)
        fabric_total += est / 100
        lines.append(f"{meta['emoji']} {meta['title_th']}  "
                     f"({meta['difficulty']}, {meta['time_hours']} ชม.)")
        lines.append(f"  ผ้าที่แนะนำ: {', '.join(meta['fabric_types'])}")
        lines.append(f"  ใช้ผ้า: ~{est / 100:.2f} ม.")
        lines.append("  วัสดุประกอบ:")
        for n in meta["notions"]:
            lines.append(f"    - {n}")
            notion_count[n] = notion_count.get(n, 0) + 1
        lines.append("")

    lines.append("=" * 55)
    lines.append("สรุป")
    lines.append("=" * 55)
    lines.append(f"ผ้ารวม (หน้ากว้าง {fabric_width_cm} ซม.): "
                 f"~{fabric_total:.2f} ม.")
    lines.append(f"แนะนำให้ซื้อ: {fabric_total * 1.1:.1f} ม. "
                 f"(เผื่อพลาดอีก 10%)")
    lines.append("")
    lines.append("วัสดุรวม (ตัวเลข = จำนวนแพทเทิร์นที่ใช้ของชิ้นนั้น):")
    for notion, count in sorted(notion_count.items(), key=lambda x: -x[1]):
        suffix = f"  x{count}" if count > 1 else ""
        lines.append(f"  - {notion}{suffix}")
    lines.append("")
    lines.append("หมายเหตุ: ถ้าแต่ละแบบใช้ผ้าคนละสี ให้ซื้อแยกตามที่ระบุ "
                 "ในแต่ละหัวข้อด้านบนแทนยอดรวม")
    return "\n".join(lines)


# ============================================================
# SIZE LIST
# ============================================================
def list_available_sizes() -> str:
    """Format the size chart as a table."""
    lines = ["ไซส์ทั้งหมด (หน่วย: เซนติเมตร):", ""]
    headers = ["ไซส์", "อก", "ยาว", "เอว", "สะโพก", "ศีรษะ",
               "ยาวแขน", "รอบคอ"]
    keys = ["chest", "length", "waist", "hip", "head", "arm_len", "neck_circ"]
    lines.append("  ".join(f"{h:>8}" for h in headers))
    lines.append("  ".join("-" * 8 for _ in headers))
    for size, spec in SIZE_CHART.items():
        row = [size] + [str(spec[k]) for k in keys]
        lines.append("  ".join(f"{v:>8}" for v in row))
    lines.append("")
    lines.append("ใช้ชื่อไซส์เหล่านี้กับ generate_*_pattern ทุกตัว")
    return "\n".join(lines)
