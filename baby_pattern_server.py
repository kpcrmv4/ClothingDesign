"""
Baby Fashion Engine - MCP Server for children's clothing patterns (0-24m).

Entry point: thin layer over the `patterns/` and `features` modules.
All tools return human-readable strings (with file paths for PDF/PNG output).

Run:
    pip install mcp reportlab Pillow
    cd <project_folder>
    python baby_pattern_server.py
"""
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from html import escape

# Force cwd to this script's folder so all generated PDF/PNG land here.
# Claude Desktop on Windows ignores the `cwd` config field and launches
# MCP servers from C:\Windows\System32, which would otherwise pollute that
# folder (and require admin rights). Pin output to the project folder.
_HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from mcp.server.fastmcp import FastMCP

from patterns import dress, bib, bloomers, bonnet
from patterns import kimono_top, pants, tshirt, romper, sleep_sack
from patterns import flutter_romper
import features
import preview
import cutting_layout
import customize

# ============================================================
# OUTPUT MANAGEMENT — per-call subfolders + auto index.html
# ============================================================
OUTPUTS_ROOT = os.path.join(_HERE, "outputs")
INDEX_HTML = os.path.join(_HERE, "index.html")

PATTERN_TITLES = {
    "dress": "เดรสเด็ก",
    "bib": "ผ้ากันเปื้อน",
    "bloomers": "กางเกงใน Bloomers",
    "bonnet": "หมวกเด็ก",
    "kimono_top": "เสื้อป้ายผูกข้าง",
    "pants": "กางเกงเอวยางยืด",
    "tshirt": "เสื้อยืดเด็ก",
    "romper": "ชุดหมีเด็ก",
    "sleep_sack": "ถุงนอนเด็ก",
    "flutter_romper": "ชุดหมีคอระบาย",
    "preview": "พรีวิว",
    "layout": "ผังตัด",
    "misc": "อื่น ๆ",
}

PATTERN_EMOJI = {
    "dress": "👗", "bib": "🧷", "bloomers": "🩲", "bonnet": "👒",
    "kimono_top": "🥋", "pants": "👖", "tshirt": "👕", "romper": "👶",
    "sleep_sack": "😴", "flutter_romper": "🌸", "misc": "🧵",
}


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(s))


def _make_run_dir(label: str) -> str:
    """Create outputs/<label>_<timestamp>/ and return its absolute path."""
    os.makedirs(OUTPUTS_ROOT, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(OUTPUTS_ROOT, f"{_safe(label)}_{ts}")
    sub = base
    n = 1
    while os.path.exists(sub):
        n += 1
        sub = f"{base}_{n}"
    os.makedirs(sub)
    return sub


def _run_in_subdir(label: str, fn, *args, **kwargs):
    """Run a file-producing function with cwd pinned to a fresh subfolder.
    Then rebuild the gallery index.html so the new run shows up."""
    sub = _make_run_dir(label)
    prev = os.getcwd()
    try:
        os.chdir(sub)
        result = fn(*args, **kwargs)
    finally:
        os.chdir(prev)
    try:
        _rebuild_index()
    except Exception:
        pass  # never let an index error mask a successful generation
    return result


def _run_pattern(pattern_key: str, size_label: str, gen_fn, *args,
                  label_extra: str = "", **kwargs):
    """Generate a pattern PDF + preview PNG into the same fresh subfolder,
    then rebuild the index. Returns the PDF generator's text result with
    the preview path appended."""
    label = f"{pattern_key}_{size_label}"
    if label_extra:
        label += f"_{label_extra}"
    sub = _make_run_dir(label)
    prev = os.getcwd()
    pdf_result = ""
    preview_line = ""
    try:
        os.chdir(sub)
        pdf_result = gen_fn(*args, **kwargs)
        try:
            ppath = preview.generate_preview(pattern_key, size_label)
            if ppath and not ppath.startswith("Error"):
                preview_line = f"\nพรีวิว: {ppath}"
        except Exception as e:
            preview_line = f"\n(สร้างพรีวิวไม่สำเร็จ: {e})"
    finally:
        os.chdir(prev)
    try:
        _rebuild_index()
    except Exception:
        pass
    gallery_line = f"\nแคตตาล็อก: file:///{INDEX_HTML.replace(os.sep, '/')}"
    return f"{pdf_result}{preview_line}{gallery_line}"


def _migrate_loose_root_files():
    """Move any pattern-shaped files in the project root into
    outputs/legacy_<key>_<size>/ so the gallery can pick them up.
    Runs once at startup; safe to re-run."""
    if not os.path.isdir(_HERE):
        return []
    moved = []
    for fn in list(os.listdir(_HERE)):
        full = os.path.join(_HERE, fn)
        if not os.path.isfile(full):
            continue
        if not (fn.endswith(".pdf") or fn.endswith(".png")):
            continue
        m1 = re.match(r"^([a-z_]+?)_pattern_(\d+-\d+m)", fn)
        m2 = re.match(r"^preview_([a-z_]+?)_(\d+-\d+m)", fn)
        m3 = re.match(r"^cutting_layout_([a-z_]+?)_(\d+-\d+m)_", fn)
        key = size = None
        for m in (m1, m2, m3):
            if m:
                key, size = m.group(1), m.group(2)
                break
        if not key:
            continue
        sub = os.path.join(OUTPUTS_ROOT, f"legacy_{_safe(key)}_{_safe(size)}")
        os.makedirs(sub, exist_ok=True)
        try:
            shutil.move(full, os.path.join(sub, fn))
            moved.append(fn)
        except Exception:
            pass
    return moved


def _parse_run_folder(name: str) -> dict:
    """Parse 'dress_3-6m_20260427-120530' or 'legacy_dress_3-6m' into parts."""
    is_legacy = name.startswith("legacy_")
    rest = name[len("legacy_"):] if is_legacy else name
    m = re.match(r"^(.+?)_(\d+-\d+m)(?:_(\d{8}-\d{6})(?:_(\d+))?)?$", rest)
    if m:
        key = m.group(1)
        size = m.group(2)
        ts = m.group(3)
    else:
        key, size, ts = rest, "?", None
    return {"key": key, "size": size, "ts": ts, "legacy": is_legacy}


def _format_ts(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.strptime(ts, "%Y%m%d-%H%M%S")
        return dt.strftime("%d %b %Y · %H:%M:%S")
    except Exception:
        return ts


def _scan_runs():
    runs = []
    if not os.path.isdir(OUTPUTS_ROOT):
        return runs
    for entry in sorted(os.listdir(OUTPUTS_ROOT), reverse=True):
        sub = os.path.join(OUTPUTS_ROOT, entry)
        if not os.path.isdir(sub):
            continue
        files = sorted(os.listdir(sub))
        info = _parse_run_folder(entry)
        info["folder"] = entry
        info["pdfs"] = [f for f in files if f.endswith(".pdf")]
        info["previews"] = [f for f in files if f.startswith("preview_") and f.endswith(".png")]
        info["layouts"] = [f for f in files if f.startswith("cutting_layout_") and f.endswith(".png")]
        info["other_pngs"] = [f for f in files
                               if f.endswith(".png")
                               and not f.startswith("preview_")
                               and not f.startswith("cutting_layout_")]
        info["all_files"] = files
        runs.append(info)
    return runs


def _build_index_html(runs) -> str:
    cards_html = "\n".join(_card_html(r) for r in runs) if runs else _empty_state_html()
    total = len(runs)
    pattern_counts = {}
    for r in runs:
        k = r["key"]
        pattern_counts[k] = pattern_counts.get(k, 0) + 1
    chips = " ".join(
        f'<span class="px-3 py-1 bg-pink-100 text-pink-700 text-xs rounded-full font-medium">'
        f'{PATTERN_EMOJI.get(k, "🧵")} {escape(PATTERN_TITLES.get(k, k))} · {n}</span>'
        for k, n in sorted(pattern_counts.items())
    )
    now = datetime.now().strftime("%d/%m/%Y · %H:%M")
    run_word = "รอบ" if total != 1 else "รอบ"
    return f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Baby Fashion Engine — แคตตาล็อกแพทเทิร์น</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  body {{ font-family: 'Sarabun', 'Noto Sans Thai', system-ui, sans-serif; }}
  .grain {{ background-image: radial-gradient(circle at 1px 1px, rgba(0,0,0,0.04) 1px, transparent 0); background-size: 16px 16px; }}
</style>
</head>
<body class="bg-gradient-to-br from-pink-50 via-white to-purple-50 min-h-screen grain">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
  <header class="mb-10">
    <div class="flex items-baseline justify-between flex-wrap gap-2">
      <h1 class="text-4xl font-bold tracking-tight text-gray-800">
        <span class="text-pink-500">🌸</span> Baby Fashion Engine
      </h1>
      <span class="text-sm text-gray-400">อัปเดตล่าสุด {escape(now)}</span>
    </div>
    <p class="mt-2 text-gray-500">แคตตาล็อกแพทเทิร์นเสื้อผ้าเด็ก · อัปเดตอัตโนมัติทุกครั้งที่สั่งสร้าง · คลิกการ์ดเพื่อเปิดไฟล์</p>
    <div class="mt-4 flex flex-wrap gap-2">
      <span class="px-3 py-1 bg-gray-900 text-white text-xs rounded-full font-medium">{total} {run_word}</span>
      {chips}
    </div>
    <button onclick="location.reload()" class="mt-4 inline-flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-200 hover:border-pink-300 hover:bg-pink-50 text-xs text-gray-600 rounded-full transition">
      🔄 รีเฟรชหน้านี้
    </button>
  </header>
  <main class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
    {cards_html}
  </main>
  <footer class="mt-16 text-center text-xs text-gray-400">
    สร้างโดย <code class="font-mono text-gray-500">baby_pattern_server.py</code> ·
    ไฟล์ทั้งหมดอยู่ใน <code class="font-mono text-gray-500">outputs/</code>
  </footer>
</div>
</body>
</html>
"""


def _card_html(r: dict) -> str:
    folder = r["folder"]
    key = r["key"]
    size = r["size"]
    title = PATTERN_TITLES.get(key, key.replace("_", " ").title())
    emoji = PATTERN_EMOJI.get(key, "🧵")
    ts_str = _format_ts(r["ts"]) if r["ts"] else ("ของเดิม" if r["legacy"] else "")
    legacy_badge = ('<span class="px-2 py-0.5 bg-amber-100 text-amber-700 text-[10px] rounded">ของเดิม</span>'
                    if r["legacy"] else "")
    preview_src = f"outputs/{escape(folder)}/{escape(r['previews'][0])}" if r["previews"] else ""
    if preview_src:
        thumb = f'<img src="{preview_src}" alt="preview" class="w-full h-56 object-contain bg-pink-50/60 p-4">'
    else:
        thumb = (f'<div class="w-full h-56 bg-pink-50/60 flex items-center justify-center text-5xl">'
                  f'{emoji}</div>')

    btns = []
    for f in r["pdfs"]:
        btns.append(
            f'<a href="outputs/{escape(folder)}/{escape(f)}" target="_blank" '
            f'class="px-3 py-1.5 bg-pink-500 hover:bg-pink-600 text-white text-xs rounded-full '
            f'font-medium transition shadow-sm">📄 PDF</a>')
    for f in r["layouts"]:
        btns.append(
            f'<a href="outputs/{escape(folder)}/{escape(f)}" target="_blank" '
            f'class="px-3 py-1.5 bg-purple-100 hover:bg-purple-200 text-purple-800 text-xs '
            f'rounded-full font-medium transition">📐 ผังตัด</a>')
    for f in r["previews"]:
        btns.append(
            f'<a href="outputs/{escape(folder)}/{escape(f)}" target="_blank" '
            f'class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs '
            f'rounded-full font-medium transition">🖼 พรีวิว</a>')
    for f in r["other_pngs"]:
        btns.append(
            f'<a href="outputs/{escape(folder)}/{escape(f)}" target="_blank" '
            f'class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs '
            f'rounded-full font-medium transition">🖼 {escape(f)}</a>')
    btns_html = "\n      ".join(btns) if btns else '<span class="text-xs text-gray-400">ไม่มีไฟล์</span>'

    file_count = len(r["all_files"])
    return f"""<article class="bg-white rounded-2xl shadow-sm hover:shadow-xl transition overflow-hidden border border-gray-100">
  <a href="outputs/{escape(folder)}/" target="_blank" class="block">
    {thumb}
  </a>
  <div class="p-5 space-y-3">
    <div class="flex items-baseline justify-between gap-2">
      <h3 class="font-semibold text-gray-800 truncate">{emoji} {escape(title)}</h3>
      <span class="text-xs font-mono text-pink-600 bg-pink-50 px-2 py-0.5 rounded">{escape(size)}</span>
    </div>
    <div class="flex items-center gap-2 text-xs text-gray-400">
      <span>{escape(ts_str)}</span>
      {legacy_badge}
      <span class="ml-auto">{file_count} ไฟล์</span>
    </div>
    <div class="pt-1 flex flex-wrap gap-2">
      {btns_html}
    </div>
    <details class="text-xs text-gray-500">
      <summary class="cursor-pointer hover:text-gray-700">📁 {escape(folder)}</summary>
      <ul class="mt-2 pl-3 space-y-0.5 font-mono text-[11px]">
        {''.join(f'<li>· {escape(f)}</li>' for f in r['all_files'])}
      </ul>
    </details>
  </div>
</article>"""


def _empty_state_html() -> str:
    return """<div class="col-span-full bg-white rounded-2xl shadow-sm border border-dashed border-gray-200 p-12 text-center">
  <div class="text-6xl mb-4">🌸</div>
  <h2 class="text-xl font-semibold text-gray-700">ยังไม่มีแพทเทิร์นในแคตตาล็อก</h2>
  <p class="mt-2 text-sm text-gray-500">ลองสั่ง Claude ว่า <code class="px-2 py-1 bg-gray-100 rounded font-mono text-pink-600">สร้างแพทเทิร์นเดรสไซส์ 3-6 เดือน</code></p>
</div>"""


def _rebuild_index() -> str:
    runs = _scan_runs()
    html = _build_index_html(runs)
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    return INDEX_HTML


# Run startup tasks
_migrate_loose_root_files()
try:
    _rebuild_index()
except Exception:
    pass


# ============================================================
# MCP server
# ============================================================
mcp = FastMCP("BabyFashionEngine_Complete")


# ============================================================
# PATTERN GENERATORS (file-producing — wrapped in subfolders)
# ============================================================
@mcp.tool()
def generate_full_dress_pattern(size_label: str,
                                 seam_allowance: float = 1.0) -> str:
    """Generate a sleeveless baby dress with gathered ruffle hem.

    size_label: one of '0-3m', '3-6m', '6-9m', '9-12m', '12-18m', '18-24m'.
    Difficulty: Beginner. Fabric: cotton lawn or double gauze.
    """
    return _run_pattern("dress", size_label,
                         dress.generate, size_label, seam_allowance)


@mcp.tool()
def generate_bib_pattern(size_label: str,
                         seam_allowance: float = 0.7) -> str:
    """Generate a drool bib with keyhole neck (snap closure at back).

    Two-layer: fashion fabric + absorbent terry backing.
    Difficulty: Beginner, ideal first project.
    """
    return _run_pattern("bib", size_label,
                         bib.generate, size_label, seam_allowance)


@mcp.tool()
def generate_bloomers_pattern(size_label: str,
                               seam_allowance: float = 1.0) -> str:
    """Generate elastic-waist bloomers / diaper cover with curved crotch.

    Elastic casings at waist + leg openings. Cut 2 on fold.
    """
    return _run_pattern("bloomers", size_label,
                         bloomers.generate, size_label, seam_allowance)


@mcp.tool()
def generate_bonnet_pattern(size_label: str,
                             seam_allowance: float = 1.0) -> str:
    """Generate traditional baby bonnet: crown + brim band + ties.

    3 pieces. Uses curved edges. Needs 0.3m outer + 0.3m lining.
    """
    return _run_pattern("bonnet", size_label,
                         bonnet.generate, size_label, seam_allowance)


@mcp.tool()
def generate_kimono_top_pattern(size_label: str,
                                 seam_allowance: float = 1.0) -> str:
    """Generate a baby kimono wrap top with side ties.

    No buttons, ideal for newborns. Sleeves included.
    Difficulty: Beginner. Fabric: cotton lawn, flannel, or jersey.
    """
    return _run_pattern("kimono_top", size_label,
                         kimono_top.generate, size_label, seam_allowance)


@mcp.tool()
def generate_pants_pattern(size_label: str,
                            seam_allowance: float = 1.0,
                            style: str = "long") -> str:
    """Generate elastic-waist baby pants.

    style: 'long' (full length) or 'short' (shorts length).
    Fabric: knit or light woven cotton.
    """
    return _run_pattern("pants", size_label,
                         pants.generate, size_label, seam_allowance, style,
                         label_extra=style)


@mcp.tool()
def generate_tshirt_pattern(size_label: str,
                             seam_allowance: float = 1.0,
                             sleeve: str = "short") -> str:
    """Generate a basic baby t-shirt with crew neck.

    sleeve: 'short' or 'long'. Requires ribbing for neckband.
    Needs shoulder snaps for newborn sizes.
    Difficulty: Intermediate. Fabric: cotton jersey.
    """
    return _run_pattern("tshirt", size_label,
                         tshirt.generate, size_label, seam_allowance, sleeve,
                         label_extra=sleeve)


@mcp.tool()
def generate_romper_pattern(size_label: str,
                             seam_allowance: float = 1.0) -> str:
    """Generate a baby romper (one-piece bodysuit with straps and snaps).

    Includes crotch snap placket. Difficulty: Intermediate.
    """
    return _run_pattern("romper", size_label,
                         romper.generate, size_label, seam_allowance)


@mcp.tool()
def generate_sleep_sack_pattern(size_label: str,
                                 seam_allowance: float = 1.0) -> str:
    """Generate a baby sleep sack (wearable blanket) with front zipper.

    Sleeveless design for safer sleep. Difficulty: Intermediate.
    Fabric: cotton jersey, flannel, or muslin.
    """
    return _run_pattern("sleep_sack", size_label,
                         sleep_sack.generate, size_label, seam_allowance)


@mcp.tool()
def generate_flutter_romper_pattern(size_label: str,
                                     seam_allowance: float = 1.0,
                                     ruffle_height: float = 7.0,
                                     ruffle_fullness: float = 1.8,
                                     crotch_snaps: int = 3) -> str:
    """Generate off-shoulder flutter romper (elastic neckline + cascading ruffle).

    Matches the popular handmade boutique style: no shoulder seams,
    ruffle acts as flutter sleeves, bubble body, snap crotch.
    Best for girls 0-18 months.

    ruffle_height: depth of the flounce in cm (default 7). Typical 5-9.
    ruffle_fullness: gather ratio vs neckline (default 1.8x). Typical 1.5-2.2.
    crotch_snaps: number of snaps across crotch (default 3).
    """
    return _run_pattern("flutter_romper", size_label,
                         flutter_romper.generate, size_label, seam_allowance,
                         ruffle_height, ruffle_fullness, crotch_snaps)


# ============================================================
# SUPPORT TOOLS (info-only — no file output, no wrapping)
# ============================================================
@mcp.tool()
def list_available_sizes() -> str:
    """Return the full size chart (0-3m through 18-24m) as a table."""
    return features.list_available_sizes()


@mcp.tool()
def list_all_patterns() -> str:
    """Return a table of all 9 available patterns with difficulty and time estimates."""
    return features.list_all_patterns()


@mcp.tool()
def calculate_fabric_requirement(pattern_type: str, size_label: str) -> str:
    """Estimate fabric needed for a pattern across 90/115/150 cm bolt widths.

    pattern_type: one of 'dress', 'bib', 'bloomers', 'bonnet',
                  'kimono_top', 'pants', 'tshirt', 'romper', 'sleep_sack'.
    """
    return features.format_fabric_requirement(pattern_type, size_label)


@mcp.tool()
def generate_shopping_list(pattern_keys: list, size_label: str) -> str:
    """Generate a consolidated shopping list for one or more patterns.

    pattern_keys: list of pattern names, e.g. ['dress', 'bib'].
    size_label: e.g. '6-9m'.
    Returns fabric yardage + notions (thread, elastic, snaps, etc.).
    """
    return features.generate_shopping_list(pattern_keys, size_label)


@mcp.tool()
def generate_pattern_preview(pattern_key: str, size_label: str) -> str:
    """Save a quick PNG thumbnail of a pattern outline (faster than PDF).

    Useful for verifying overall shape and proportions before generating
    the full tiled PDF. Returns the absolute file path of the PNG.

    pattern_key: one of 'dress', 'bib', 'bloomers', 'bonnet', 'kimono_top',
                 'pants', 'tshirt', 'romper', 'sleep_sack'.
    """
    def _do():
        path = preview.generate_preview(pattern_key, size_label)
        if path.startswith("Error"):
            return path
        return f"Preview saved: {path}"
    return _run_in_subdir(f"preview_{pattern_key}_{size_label}", _do)


@mcp.tool()
def generate_cutting_layout(pattern_key: str, size_label: str,
                             fabric_width_cm: int = 115) -> str:
    """Generate a PNG showing how to lay out pattern pieces on fabric.

    fabric_width_cm: 90, 115, or 150. Common bolt widths.
    Helps minimize fabric waste by showing a shelf-packed layout.
    Returns the absolute file path of the PNG.
    """
    def _do():
        path = cutting_layout.generate_layout(pattern_key, size_label, fabric_width_cm)
        if path.startswith("Error"):
            return path
        return f"Cutting layout saved: {path}"
    return _run_in_subdir(f"layout_{pattern_key}_{size_label}_{fabric_width_cm}cm", _do)


@mcp.tool()
def suggest_pattern_from_description(description: str) -> str:
    """Analyse a text description and suggest which pattern tool(s) to use.

    Use this after viewing a reference image and writing a summary, or when
    the user describes what they want in free text. Returns ranked pattern
    matches plus suggested parameters.

    Does NOT generate files; follow up with a specific generate_*_pattern call.
    """
    return customize.suggest_pattern_from_description(description)


@mcp.tool()
def customize_pattern(pattern_key: str, size_label: str, changes: dict) -> str:
    """Plan a customized pattern call from a structured 'changes' dict.

    Supported keys in changes:
      - seam_allowance: float (cm)
      - style: 'long' or 'short' (pants only)
      - sleeve: 'long' or 'short' (tshirt only)
      - notes: free-text (stored for future context)

    Returns a recommended tool call. Does not produce files directly.
    """
    return customize.customize_pattern(pattern_key, size_label, changes)


@mcp.tool()
def rebuild_gallery_index() -> str:
    """Force a rebuild of index.html from whatever exists in outputs/.

    Useful after manually moving files around. Returns the path to index.html.
    """
    path = _rebuild_index()
    runs = _scan_runs()
    return (f"สร้าง index.html ใหม่: {path}\n"
            f"  รวม {len(runs)} รอบในแคตตาล็อก\n"
            f"เปิดในเบราว์เซอร์: file:///{path.replace(os.sep, '/')}")


# ============================================================
# GIT / GITHUB PAGES PUBLISHING
# ============================================================
def _git(*args):
    """Run git in the project folder. Returns (returncode, stdout, stderr)."""
    r = subprocess.run(
        ["git", *args],
        cwd=_HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _pages_url() -> str:
    rc, out, _ = _git("config", "--get", "remote.origin.url")
    if rc != 0 or not out:
        return ""
    m = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/([^/.]+)", out)
    if not m:
        return ""
    user, repo = m.group(1), m.group(2)
    return f"https://{user.lower()}.github.io/{repo}/"


@mcp.tool()
def publish_gallery(message: str = "") -> str:
    """Commit + push the catalog (index.html + outputs/) to GitHub.

    GitHub Pages will auto-rebuild within ~1 minute and the new patterns
    will appear at https://<user>.github.io/<repo>/.

    Use this after generating one or more patterns to publish them publicly.
    Requires:
      - the project folder is a git repo with an 'origin' remote on GitHub
      - git credentials are configured (git config user.email/name)
      - your machine is authenticated to push (token / Credential Manager)

    message: optional commit message. If empty, an auto message is used.
    """
    # 1. Verify git repo
    rc, _, err = _git("rev-parse", "--git-dir")
    if rc != 0:
        return f"❌ ไม่ใช่ git repo: {err}\nรัน 'git init' ก่อน หรือ clone repo ใหม่"

    # 2. Stage everything
    rc, _, err = _git("add", "-A")
    if rc != 0:
        return f"❌ git add ล้มเหลว:\n{err}"

    # 3. Anything to commit?
    rc, _, _ = _git("diff", "--cached", "--quiet")
    if rc == 0:
        return "ℹ️ ไม่มีการเปลี่ยนแปลงใหม่ที่จะ publish (working tree สะอาด)"

    # 4. Commit
    if not message:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        runs = _scan_runs()
        message = f"อัปเดตแคตตาล็อก ({len(runs)} รอบ) — {ts}"

    rc, _, err = _git("commit", "-m", message)
    if rc != 0:
        if "Please tell me who you are" in err or "user.email" in err:
            return ("❌ git ยังไม่รู้ identity\n"
                     "รันคำสั่งนี้ก่อน:\n"
                     "  git config --global user.email \"your@email.com\"\n"
                     "  git config --global user.name \"Your Name\"")
        return f"❌ git commit ล้มเหลว:\n{err}"

    # 5. Get branch
    rc, branch, _ = _git("branch", "--show-current")
    branch = branch or "HEAD"

    # 6. Push
    rc, _, err = _git("push", "origin", branch)
    if rc != 0:
        # commit succeeded — give them recovery info
        return (f"✓ Commit สำเร็จ: {message}\n"
                 f"❌ git push ล้มเหลว:\n{err}\n\n"
                 f"แก้ไขแล้ว push เองด้วย:\n"
                 f"  cd {_HERE}\n"
                 f"  git push origin {branch}")

    # 7. Success — point to Pages URL
    pages = _pages_url()
    lines = [
        f"✓ Commit: {message}",
        f"✓ Push สำเร็จ → branch '{branch}'",
    ]
    if pages:
        lines.append("")
        lines.append("⏳ GitHub Pages จะอัปเดตภายใน 1-2 นาที:")
        lines.append(f"   {pages}")
        lines.append("")
        lines.append("ครั้งแรก: เปิด Settings > Pages เลือก source = branch ปัจจุบัน")
    return "\n".join(lines)


@mcp.tool()
def git_status_summary() -> str:
    """Show what's currently uncommitted in the project (for sanity-check
    before publish_gallery)."""
    rc, out, err = _git("status", "--short")
    if rc != 0:
        return f"❌ git status ล้มเหลว:\n{err}"
    if not out:
        return "✓ Working tree สะอาด — ไม่มีอะไรต้อง commit"
    lines = out.splitlines()
    return f"มีไฟล์เปลี่ยน {len(lines)} ไฟล์:\n\n" + out


if __name__ == "__main__":
    mcp.run()
