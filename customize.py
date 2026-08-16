"""
Natural language / structured customization layer.

  suggest_pattern_from_description(text)  แปลงคำบรรยาย (หรือสรุปจากรูป) เป็น
                                          แพทเทิร์นที่ควรใช้ + พารามิเตอร์
  customize_pattern(key, size, changes)   แปลง changes dict เป็นคำสั่งเรียก tool

Matching scores by keyword length, so a specific phrase beats a generic one
that happens to be a substring of it — "กางเกงใน" (bloomers) must not also
match "กางเกง" (pants), and "ชุดหมีคอระบาย" must not also match "ชุดหมี".
"""
from features import PATTERN_META
from sizes import SIZE_CHART

# Keyword -> pattern. Longer, more specific phrases win (see _score_matches).
_KEYWORDS = {
    "flutter_romper": ["flutter", "off shoulder", "off-shoulder",
                       "ruffle neck", "ruffle romper", "peasant neckline",
                       "flounce", "คอระบาย", "ชุดหมีระบาย",
                       "ชุดหมีคอระบาย", "เปิดไหล่"],
    "tiered_dress": ["tiered", "tiered dress", "tiered skirt", "ruffle tiers",
                     "layered skirt", "layered dress", "halter dress",
                     "กระโปรงชั้น", "เดรสกระโปรงชั้น", "กระโปรงหลายชั้น",
                     "ชายระบายหลายชั้น", "เดรสชั้น", "ระบายเป็นชั้น",
                     "คอผูกหลัง", "ผูกโบว์หลัง"],
    "dress": ["dress", "sundress", "frock", "เดรส", "กระโปรง", "ชุดกระโปรง"],
    "bib": ["bib", "drool", "ผ้ากันเปื้อน", "กันเปื้อน"],
    "bloomers": ["bloomer", "bloomers", "diaper cover", "nappy cover",
                 "กางเกงใน", "กางเกงคลุมผ้าอ้อม"],
    "bonnet": ["bonnet", "sun hat", "baby hat", "cap", "หมวก", "หมวกคลุมผม"],
    "kimono_top": ["kimono", "wrap top", "wrap shirt", "เสื้อป้าย",
                   "เสื้อคิโมโน", "เสื้อผูกข้าง"],
    "pants": ["pants", "trousers", "legging", "shorts", "กางเกง",
              "กางเกงขายาว", "กางเกงขาสั้น"],
    "tshirt": ["t-shirt", "tshirt", "tee", "เสื้อยืด"],
    "romper": ["romper", "bodysuit", "onesie", "playsuit", "ชุดหมี",
               "ชุดบอดี้สูท"],
    "sleep_sack": ["sleep sack", "sleeping bag", "wearable blanket",
                   "ถุงนอน"],
}


def _score_matches(desc_lower: str) -> list:
    """Return [(pattern_key, best_keyword, score)] sorted best first.

    Score is the length of the longest matching keyword, so "กางเกงใน"
    (8 chars, bloomers) outranks "กางเกง" (6 chars, pants) on the same text.
    A pattern whose only hit is fully contained inside a longer hit from a
    different pattern is dropped as a false positive.
    """
    hits = []
    for key, keywords in _KEYWORDS.items():
        best = None
        for kw in keywords:
            if kw.lower() in desc_lower:
                if best is None or len(kw) > len(best):
                    best = kw
        if best:
            hits.append((key, best, len(best)))

    hits.sort(key=lambda h: -h[2])
    kept = []
    for key, kw, score in hits:
        shadowed = any(kw.lower() in other_kw.lower() and other_key != key
                       for other_key, other_kw, _ in kept)
        if not shadowed:
            kept.append((key, kw, score))
    return kept


def suggest_pattern_from_description(description: str) -> str:
    """Analyse a description and suggest which pattern tool(s) to use."""
    if not description or not description.strip():
        return "Error: ต้องใส่คำบรรยายชุดที่ต้องการ"

    desc_lower = description.lower()
    matches = _score_matches(desc_lower)

    if not matches:
        return (
            "ไม่พบแพทเทิร์นที่ตรงกับคำบรรยายนี้\n"
            "แพทเทิร์นที่มี: "
            + ", ".join(f"{k} ({m['title_th']})"
                        for k, m in PATTERN_META.items())
            + "\n\nลองใช้คำอย่าง: เดรส, เดรสกระโปรงชั้น, ผ้ากันเปื้อน, หมวก, "
              "เสื้อป้าย, กางเกง, กางเกงใน, เสื้อยืด, ชุดหมี, ชุดหมีคอระบาย, ถุงนอน"
        )

    lines = [f"พบแพทเทิร์นที่ตรงกับคำบรรยาย {len(matches)} แบบ:", ""]

    for key, matched_kw, _ in matches:
        meta = PATTERN_META[key]
        lines.append(f"== {meta['emoji']} {meta['title_th']} ({key}) ==")
        lines.append(f"  ตรงกับคำว่า: \"{matched_kw}\"")
        lines.append(f"  ระดับ: {meta['difficulty']} | "
                     f"เวลา: {meta['time_hours']} ชม.")
        lines.append(f"  ผ้าที่แนะนำ: {', '.join(meta['fabric_types'])}")

        params = _infer_params(key, desc_lower)
        if params:
            call_args = ", ".join(
                f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}"
                for k, v in params.items())
            lines.append(f"  แนะนำให้เรียก: generate_{key}_pattern("
                         f"size_label='<SIZE>', {call_args})")
        else:
            lines.append(f"  แนะนำให้เรียก: generate_{key}_pattern("
                         f"size_label='<SIZE>')")
        lines.append("")

    lines.append("ขั้นตอนถัดไป:")
    lines.append("  1. ถามอายุ/ไซส์ของเด็กถ้ายังไม่ได้ระบุ "
                 f"(ไซส์ที่มี: {', '.join(SIZE_CHART)})")
    lines.append("  2. (ทางเลือก) generate_pattern_preview(key, size) "
                 "เพื่อดูรูปทรงก่อน")
    lines.append("  3. เรียก generate_*_pattern เพื่อสร้าง PDF จริง")
    lines.append("  4. generate_shopping_list([keys], size) เพื่อดูรายการวัสดุ")
    lines.append("")
    lines.append("หมายเหตุ: ลูกไม้ โบว์ ริบบิ้น และลายผ้าเป็นของตกแต่ง "
                 "ไม่ต้องมีชิ้นแพทเทิร์นแยก — เลือกผ้าและวัสดุตามรูปได้เลย")

    return "\n".join(lines)


def _infer_params(pattern_key: str, desc: str) -> dict:
    """Extract reasonable params for a pattern from free text."""
    params = {}

    if pattern_key == "pants":
        if any(w in desc for w in ["short", "summer", "hot",
                                   "ขาสั้น", "กางเกงขาสั้น"]):
            params["style"] = "short"
        elif any(w in desc for w in ["long", "winter", "cold",
                                     "ขายาว", "กางเกงขายาว"]):
            params["style"] = "long"

    elif pattern_key == "tshirt":
        if any(w in desc for w in ["long sleeve", "long-sleeve", "แขนยาว"]):
            params["sleeve"] = "long"
        elif any(w in desc for w in ["short sleeve", "short-sleeve",
                                     "tee", "แขนสั้น"]):
            params["sleeve"] = "short"

    elif pattern_key == "dress":
        if any(w in desc for w in ["bubble", "balloon", "puff hem",
                                   "บอลลูน", "ชายพอง", "ทรงบอลลูน"]):
            params["skirt_style"] = "bubble"
        if any(w in desc for w in ["button", "placket", "buttons down",
                                   "กระดุมหน้า", "สาบกระดุม", "ติดกระดุม"]):
            params["front_placket"] = True

    elif pattern_key == "tiered_dress":
        if any(w in desc for w in ["2 tier", "two tier", "สองชั้น", "2 ชั้น"]):
            params["tiers"] = 2
        elif any(w in desc for w in ["3 tier", "three tier",
                                     "สามชั้น", "3 ชั้น"]):
            params["tiers"] = 3
        if any(w in desc for w in ["halter", "neck tie", "bow at back",
                                   "คอผูกหลัง", "ผูกโบว์หลัง", "โบว์หลัง"]):
            params["neckline"] = "halter"
        elif any(w in desc for w in ["strap", "spaghetti", "tie shoulder",
                                     "สายไหล่", "สายผูกไหล่", "สายเดี่ยว"]):
            params["neckline"] = "strap"
        elif any(w in desc for w in ["round neck", "crew neck", "คอกลม"]):
            params["neckline"] = "round"
        if any(w in desc for w in ["no lace", "without lace", "ไม่มีลูกไม้"]):
            params["lace_trim"] = False

    if any(w in desc for w in ["thin seam", "narrow seam", "small seam",
                               "ตะเข็บแคบ"]):
        params["seam_allowance"] = 0.7
    elif any(w in desc for w in ["wide seam", "generous seam",
                                 "large seam allowance", "ตะเข็บกว้าง"]):
        params["seam_allowance"] = 1.5

    return params


# ============================================================
# Structured customization
# ============================================================
_ALLOWED_CHANGES = {
    "seam_allowance": float,
    "style": str,
    "sleeve": str,
    "skirt_style": str,
    "front_placket": bool,
    "tiers": int,
    "neckline": str,
    "tier_fullness": float,
    "lace_trim": bool,
    "ruffle_height": float,
    "ruffle_fullness": float,
    "crotch_snaps": int,
}

# Which optional params each pattern actually accepts.
_PATTERN_PARAMS = {
    "dress": {"seam_allowance", "skirt_style", "front_placket"},
    "tiered_dress": {"seam_allowance", "tiers", "neckline",
                     "tier_fullness", "lace_trim"},
    "pants": {"seam_allowance", "style"},
    "tshirt": {"seam_allowance", "sleeve"},
    "flutter_romper": {"seam_allowance", "ruffle_height",
                       "ruffle_fullness", "crotch_snaps"},
}

_ENUMS = {
    "style": ("long", "short"),
    "sleeve": ("short", "long"),
    "skirt_style": ("gathered", "bubble"),
    "neckline": ("round", "halter", "strap"),
}


def customize_pattern(pattern_key: str, size_label: str,
                      changes: dict) -> str:
    """Turn a changes dict into a concrete tool call recommendation.

    This is a planner — it does NOT generate a PDF. Claude reads the
    recommendation and calls the real generate_*_pattern tool.
    """
    if pattern_key not in PATTERN_META:
        return (f"Error: ไม่รู้จักแพทเทิร์น '{pattern_key}' "
                f"ที่มี: {', '.join(PATTERN_META)}")
    if size_label not in SIZE_CHART:
        return (f"Error: ไม่พบไซส์ '{size_label}' "
                f"ไซส์ที่มี: {', '.join(SIZE_CHART)}")
    if not isinstance(changes, dict):
        return "Error: changes ต้องเป็น dict เช่น {'neckline': 'halter'}"

    allowed = _PATTERN_PARAMS.get(pattern_key, {"seam_allowance"})
    valid_params = {}
    notes = []

    for k, v in changes.items():
        if k == "notes":
            notes.append(str(v))
            continue
        if k not in _ALLOWED_CHANGES:
            notes.append(f"ข้ามค่าที่ไม่รู้จัก '{k}'={v}")
            continue
        if k not in allowed:
            meta = PATTERN_META[pattern_key]
            notes.append(f"'{k}' ใช้กับ {meta['title_th']} ไม่ได้ — ข้าม")
            continue
        try:
            cast = _ALLOWED_CHANGES[k](v)
        except (TypeError, ValueError):
            notes.append(f"ค่า {k}={v} ไม่ถูกต้อง — ข้าม")
            continue
        if k in _ENUMS and cast not in _ENUMS[k]:
            notes.append(f"{k} ต้องเป็นหนึ่งใน {_ENUMS[k]} — ข้าม '{cast}'")
            continue
        valid_params[k] = cast

    arg_str = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}"
                        for k, v in valid_params.items())
    call = (f"generate_{pattern_key}_pattern(size_label='{size_label}'"
            + (", " + arg_str if arg_str else "") + ")")

    meta = PATTERN_META[pattern_key]
    lines = [f"แผนปรับแต่ง: {meta['emoji']} {meta['title_th']}",
             f"  ไซส์: {size_label}",
             f"  พารามิเตอร์ที่ใช้ได้: {valid_params or '(ค่าเริ่มต้นทั้งหมด)'}",
             f"  คำสั่งที่ควรเรียก:",
             f"    {call}",
             ""]
    if allowed - {"seam_allowance"}:
        lines.append(f"  ตัวเลือกทั้งหมดของแบบนี้: "
                     f"{', '.join(sorted(allowed))}")
        lines.append("")
    if notes:
        lines.append("หมายเหตุ:")
        for n in notes:
            lines.append(f"  - {n}")
    return "\n".join(lines)
