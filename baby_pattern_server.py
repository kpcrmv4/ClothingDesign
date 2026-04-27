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
import rendered
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
    rebuild the index, and (if AUTO_PUBLISH) push to GitHub. Returns the
    PDF generator's text result with status lines appended."""
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
        try:
            rpath = rendered.render_finished(pattern_key, size_label)
            if rpath and not rpath.startswith("Error"):
                preview_line += f"\nภาพชุดเสร็จ: {rpath}"
        except Exception as e:
            preview_line += f"\n(วาดชุดเสร็จไม่สำเร็จ: {e})"
    finally:
        os.chdir(prev)
    try:
        _rebuild_index()
    except Exception:
        pass
    gallery_line = f"\nแคตตาล็อก: file:///{INDEX_HTML.replace(os.sep, '/')}"

    # Auto-publish to GitHub Pages if enabled
    publish_line = ""
    if AUTO_PUBLISH:
        try:
            title = PATTERN_TITLES.get(pattern_key, pattern_key)
            tag = f"{title} {size_label}"
            if label_extra:
                tag += f" ({label_extra})"
            ts = datetime.now().strftime("%H:%M")
            commit_msg = f"เพิ่ม {tag} — {ts}"
            res = _publish(commit_msg)
            publish_line = f"\n\n{res['summary']}"
        except Exception as e:
            publish_line = f"\n\n⚠ auto-publish skipped: {e}"

    return f"{pdf_result}{preview_line}{gallery_line}{publish_line}"


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
        info["renders"] = [f for f in files if f.startswith("rendered_") and f.endswith(".png")]
        info["previews"] = [f for f in files if f.startswith("preview_") and f.endswith(".png")]
        info["layouts"] = [f for f in files if f.startswith("cutting_layout_") and f.endswith(".png")]
        info["other_pngs"] = [f for f in files
                               if f.endswith(".png")
                               and not f.startswith("preview_")
                               and not f.startswith("cutting_layout_")
                               and not f.startswith("rendered_")
                               and f != "index.html"]
        info["all_files"] = [f for f in files if f != "index.html"]
        runs.append(info)
    return runs


def _build_subfolder_index(folder: str, files: list) -> str:
    """Per-folder index.html so GitHub Pages doesn't 404 when user clicks
    the folder link."""
    items = []
    for f in sorted(files):
        if f == "index.html":
            continue
        ext = f.rsplit(".", 1)[-1].lower()
        if ext == "pdf":
            icon = "📄"
            preview_html = ""
        elif ext == "png":
            icon = "🖼"
            preview_html = f'<img src="{escape(f)}" class="w-full max-w-xl rounded-lg shadow border" alt="{escape(f)}">'
        else:
            icon = "📎"
            preview_html = ""
        items.append(f'''<li class="bg-white rounded-xl shadow-sm p-4 space-y-3">
  <a href="{escape(f)}" target="_blank" class="font-mono text-sm text-pink-600 hover:underline">{icon} {escape(f)}</a>
  {preview_html}
</li>''')
    items_html = "\n".join(items) if items else '<li class="text-gray-400">โฟลเดอร์ว่าง</li>'
    return f'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(folder)} — Baby Fashion Engine</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>body {{ font-family: 'Sarabun', system-ui, sans-serif; }}</style>
</head>
<body class="bg-gradient-to-br from-pink-50 to-purple-50 min-h-screen">
<div class="max-w-3xl mx-auto px-4 py-10">
  <a href="../../index.html" class="inline-block mb-4 text-sm text-pink-600 hover:underline">← กลับไปแคตตาล็อก</a>
  <h1 class="text-2xl font-bold text-gray-800 mb-2">📁 {escape(folder)}</h1>
  <p class="text-sm text-gray-500 mb-6">{len(items)} ไฟล์</p>
  <ul class="space-y-3">
    {items_html}
  </ul>
</div>
</body>
</html>
'''


def _write_subfolder_indexes():
    """Write index.html in every outputs/<run>/ subfolder."""
    if not os.path.isdir(OUTPUTS_ROOT):
        return
    for entry in os.listdir(OUTPUTS_ROOT):
        sub = os.path.join(OUTPUTS_ROOT, entry)
        if not os.path.isdir(sub):
            continue
        files = [f for f in sorted(os.listdir(sub)) if f != "index.html"]
        html = _build_subfolder_index(entry, files)
        with open(os.path.join(sub, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)


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
    # Prefer rendered (finished-garment illustration) over flat preview
    thumb_src = ""
    if r.get("renders"):
        thumb_src = f"outputs/{escape(folder)}/{escape(r['renders'][0])}"
    elif r["previews"]:
        thumb_src = f"outputs/{escape(folder)}/{escape(r['previews'][0])}"
    # Pick what to open when clicking the thumbnail — prefer PDF, else folder index
    click_target = (f"outputs/{escape(folder)}/{escape(r['pdfs'][0])}"
                     if r["pdfs"]
                     else f"outputs/{escape(folder)}/index.html")
    if thumb_src:
        thumb = f'<img src="{thumb_src}" alt="preview" class="w-full h-56 object-cover bg-pink-50/60">'
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
  <a href="{click_target}" target="_blank" class="block">
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
    try:
        _write_subfolder_indexes()
    except Exception:
        pass
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
# Set to False to disable auto-publish after every pattern generation
AUTO_PUBLISH = True


def _git(*args):
    """Run git in the project folder. Returns (returncode, stdout, stderr).
    GIT_TERMINAL_PROMPT=0 ensures git never blocks waiting for credentials —
    if creds aren't cached, push fails fast with a clear error."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    r = subprocess.run(
        ["git", *args],
        cwd=_HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
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


def _publish(message: str = "") -> dict:
    """Internal: stage + commit + push. Returns dict with status info.

    Result dict keys: ok (bool), summary (str — short status line for the
    pattern tool to append), detail (str — full multi-line message).
    """
    # 1. Repo present?
    rc, _, err = _git("rev-parse", "--git-dir")
    if rc != 0:
        return {"ok": False,
                "summary": "⚠ publish ข้าม (ไม่ใช่ git repo)",
                "detail": f"❌ ไม่ใช่ git repo: {err}"}

    # 2. Stage
    rc, _, err = _git("add", "-A")
    if rc != 0:
        return {"ok": False,
                "summary": "⚠ git add ล้มเหลว",
                "detail": f"❌ git add: {err}"}

    # 3. Anything to commit?
    rc, _, _ = _git("diff", "--cached", "--quiet")
    if rc == 0:
        return {"ok": True,
                "summary": "ℹ Working tree สะอาด — ไม่มีอะไรต้อง commit",
                "detail": "ℹ ไม่มีการเปลี่ยนแปลงใหม่"}

    # 4. Commit
    if not message:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        runs = _scan_runs()
        message = f"อัปเดตแคตตาล็อก ({len(runs)} รอบ) — {ts}"

    rc, _, err = _git("commit", "-m", message)
    if rc != 0:
        if "Please tell me who you are" in err or "user.email" in err:
            hint = ("git ยังไม่รู้ identity — รันคำสั่งนี้ก่อน:\n"
                    "  git config --global user.email \"your@email.com\"\n"
                    "  git config --global user.name \"Your Name\"")
            return {"ok": False, "summary": "⚠ ยังไม่ได้ตั้ง git identity",
                    "detail": hint}
        return {"ok": False, "summary": "⚠ git commit ล้มเหลว",
                "detail": f"❌ git commit: {err}"}

    rc, branch, _ = _git("branch", "--show-current")
    branch = branch or "HEAD"

    # 5. Push
    rc, _, err = _git("push", "origin", branch)
    if rc != 0:
        if "could not read Username" in err or "Authentication failed" in err or "terminal prompts disabled" in err:
            hint = ("ยังไม่ได้ login GitHub บนเครื่องนี้ — รันใน PowerShell ครั้งเดียว:\n"
                    f"  cd {_HERE}\n"
                    f"  git push origin {branch}\n"
                    "Git Credential Manager จะเด้งหน้าต่าง login มา หลังจากนั้นจะจำให้")
            return {"ok": False,
                    "summary": "✓ commit แล้ว แต่ push ล้มเหลว (auth)",
                    "detail": hint}
        return {"ok": False,
                "summary": "✓ commit แล้ว แต่ push ล้มเหลว",
                "detail": f"git push: {err}\n\npush เองด้วย:\n  cd {_HERE}\n  git push origin {branch}"}

    pages = _pages_url()
    summary = f"🚀 Push ขึ้น GitHub แล้ว ({branch}) — Pages อัปเดตใน 1-2 นาที"
    if pages:
        summary += f"\n   {pages}"
    return {"ok": True, "summary": summary,
            "detail": f"✓ Commit: {message}\n✓ Push สำเร็จ → {branch}\n\n{pages}"}


@mcp.tool()
def publish_gallery(message: str = "") -> str:
    """Manually commit + push the catalog (index.html + outputs/) to GitHub.

    Use this if AUTO_PUBLISH is disabled, or to force a custom commit message.
    By default, every generate_*_pattern call already auto-publishes.

    message: optional commit message.
    """
    result = _publish(message)
    return result["detail"] or result["summary"]


@mcp.tool()
def set_auto_publish(enabled: bool) -> str:
    """Enable/disable auto-publish to GitHub after each pattern generation.

    When enabled (default): every successful generate_*_pattern automatically
    runs git add + commit + push. The catalog on GitHub Pages stays in sync.

    When disabled: patterns are only saved locally. Use publish_gallery
    manually when you want to publish a batch.
    """
    global AUTO_PUBLISH
    AUTO_PUBLISH = bool(enabled)
    state = "เปิด" if AUTO_PUBLISH else "ปิด"
    return f"✓ Auto-publish: {state}"


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
