"""
Natural language / structured customization layer.

Two entry points:
  - suggest_pattern_from_description(description): Claude analyses the text
    (possibly after viewing a photo) and gets a recommendation of which
    pattern to use plus suggested parameters.
  - customize_pattern(pattern_key, size, changes): applies simple named
    adjustments (longer, shorter, add sleeves, etc.) and dispatches to
    the underlying generator.

Since Claude reads the results of these tools and can make follow-up
tool calls, the logic stays simple: map structured change requests to
known pattern tool parameters.
"""
from sizes import SIZE_CHART
from features import PATTERN_META


# ============================================================
# Description keyword -> pattern key mapping
# ============================================================
_KEYWORDS = {
    # flutter_romper MUST be checked before generic romper so it wins
    # when both sets of keywords appear
    "flutter_romper": ["flutter", "off shoulder", "off-shoulder",
                       "ruffle neck", "ruffle romper", "peasant neckline",
                       "flounce", "คอระบาย", "ชุดหมีระบาย",
                       "ชุดหมีคอระบาย", "เปิดไหล่"],
    "dress": ["dress", "sundress", "frock", "เดรส", "กระโปรง"],
    "bib": ["bib", "drool", "ผ้ากันเปื้อน", "กันเปื้อน"],
    "bloomers": ["bloomer", "diaper cover", "nappy cover", "กางเกงใน"],
    "bonnet": ["bonnet", "hat", "cap", "หมวก"],
    "kimono_top": ["kimono", "wrap top", "wrap shirt", "เสื้อป้าย", "เสื้อคิโมโน"],
    "pants": ["pants", "trousers", "legging", "กางเกง"],
    "tshirt": ["t-shirt", "tshirt", "tee", "เสื้อยืด"],
    "romper": ["romper", "bodysuit", "onesie", "playsuit", "ชุดหมี"],
    "sleep_sack": ["sleep sack", "sleeping bag", "wearable blanket",
                   "ถุงนอน"],
}


def suggest_pattern_from_description(description: str) -> str:
    """
    Analyse a description and suggest which pattern tool to use.

    Returns a report string containing:
      - matched pattern keys (ranked)
      - suggested parameters (sleeve length, pants length, etc.)
      - next-step tool call syntax

    Works for: text descriptions, summaries extracted from photos by Claude,
    or multi-item requests ("I want a dress and a hat").
    """
    desc_lower = description.lower()

    matches = []
    for key, keywords in _KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in desc_lower:
                matches.append(key)
                break

    if not matches:
        return (
            "No matching pattern found in description. Available patterns: "
            + ", ".join(PATTERN_META.keys()) + "\n"
            "Try keywords like 'dress', 'bib', 'bonnet', 'kimono', 'pants', "
            "'romper', 'sleep sack', 'bloomers', 't-shirt'."
        )

    lines = [f"Found {len(matches)} pattern match(es) in the description:",
             ""]

    for key in matches:
        meta = PATTERN_META[key]
        lines.append(f"== {meta['title']} ({key}) ==")
        lines.append(f"  Difficulty: {meta['difficulty']}, "
                     f"Time: {meta['time_hours']}h")
        lines.append(f"  Fabric types: {', '.join(meta['fabric_types'])}")

        params = _infer_params(key, desc_lower)
        if params:
            call_args = ", ".join(f"{k}='{v}'" if isinstance(v, str)
                                   else f"{k}={v}" for k, v in params.items())
            lines.append(f"  Suggested call: generate_{key}_pattern("
                         f"size_label='<SIZE>', {call_args})")
        else:
            lines.append(f"  Suggested call: generate_{key}_pattern("
                         f"size_label='<SIZE>')")
        lines.append("")

    lines.append("Next steps:")
    lines.append("  1. Ask user for baby's age/size if not yet specified")
    lines.append("  2. Optional: generate_pattern_preview(key, size) "
                 "to verify shape")
    lines.append("  3. Call the generate_*_pattern tool to produce PDF")
    lines.append("  4. Call generate_shopping_list([keys], size) for materials")

    return "\n".join(lines)


def _infer_params(pattern_key: str, desc: str) -> dict:
    """Extract reasonable params from free-text description."""
    params = {}

    if pattern_key == "pants":
        if any(w in desc for w in ["short", "summer", "hot",
                                     "ขาสั้น", "กางเกงขาสั้น"]):
            params["style"] = "short"
        elif any(w in desc for w in ["long", "winter", "cold",
                                       "ขายาว", "กางเกงขายาว"]):
            params["style"] = "long"

    elif pattern_key == "tshirt":
        if any(w in desc for w in ["long sleeve", "long-sleeve",
                                     "แขนยาว"]):
            params["sleeve"] = "long"
        elif any(w in desc for w in ["short sleeve", "short-sleeve",
                                       "tee", "แขนสั้น"]):
            params["sleeve"] = "short"

    if any(w in desc for w in ["thin seam", "narrow seam", "small seam"]):
        params["seam_allowance"] = 0.7
    elif any(w in desc for w in ["wide seam", "generous seam",
                                   "large seam allowance"]):
        params["seam_allowance"] = 1.5

    return params


# ============================================================
# Structured customization
# ============================================================
_ALLOWED_CHANGES = {
    "seam_allowance": float,
    "style": str,
    "sleeve": str,
}


def customize_pattern(pattern_key: str, size_label: str,
                       changes: dict) -> str:
    """
    Apply named adjustments and return a recommendation of which tool to call.

    This is a planner — it does NOT generate a PDF itself. Claude takes
    the recommendation and calls the actual generate_*_pattern tool.

    changes can contain:
      - seam_allowance: float (override SA)
      - style: 'long' or 'short' (pants)
      - sleeve: 'long' or 'short' (tshirt)
      - notes: free-text description for future context

    Returns a string with the dispatch recommendation.
    """
    if pattern_key not in PATTERN_META:
        return (f"Error: unknown pattern '{pattern_key}'. "
                f"Available: {list(PATTERN_META)}")
    if size_label not in SIZE_CHART:
        return f"Error: size '{size_label}' not found."

    valid_params = {}
    notes = []
    for k, v in changes.items():
        if k == "notes":
            notes.append(str(v))
            continue
        if k not in _ALLOWED_CHANGES:
            notes.append(f"(ignored unknown change '{k}'={v})")
            continue
        try:
            valid_params[k] = _ALLOWED_CHANGES[k](v)
        except (TypeError, ValueError):
            notes.append(f"(ignored invalid {k}={v})")

    if pattern_key != "pants" and "style" in valid_params:
        notes.append("'style' is only supported for pants; ignored")
        del valid_params["style"]
    if pattern_key != "tshirt" and "sleeve" in valid_params:
        notes.append("'sleeve' is only supported for tshirt; ignored")
        del valid_params["sleeve"]

    arg_str = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}"
                         for k, v in valid_params.items())
    call = (f"generate_{pattern_key}_pattern(size_label='{size_label}'"
            + (", " + arg_str if arg_str else "") + ")")

    lines = [f"Customization plan for {PATTERN_META[pattern_key]['title']}:",
             f"  Size: {size_label}",
             f"  Applied params: {valid_params or '(defaults)'}",
             f"  Suggested tool call:",
             f"    {call}",
             ""]
    if notes:
        lines.append("Notes:")
        for n in notes:
            lines.append(f"  - {n}")
    return "\n".join(lines)
