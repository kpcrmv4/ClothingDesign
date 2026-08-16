"""
Output management + the HTML catalogue.

Every file-producing tool writes into its own `outputs/<label>_<timestamp>/`
folder; this module scans those folders and rebuilds `index.html` (plus one
small index per subfolder so GitHub Pages does not 404 on a folder link).

Titles and emoji come from features.PATTERN_META so there is one registry of
pattern identity rather than a second copy living in the server module.
"""
import os
import re
import shutil
from datetime import datetime
from html import escape

from features import PATTERN_META

_HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_ROOT = os.path.join(_HERE, "outputs")
INDEX_HTML = os.path.join(_HERE, "index.html")

_EXTRA_TITLES = {"preview": "พรีวิว", "layout": "ผังตัด", "misc": "อื่น ๆ"}


def title_for(key: str) -> str:
    if key in PATTERN_META:
        return PATTERN_META[key]["title_th"]
    return _EXTRA_TITLES.get(key, key.replace("_", " ").title())


def emoji_for(key: str) -> str:
    if key in PATTERN_META:
        return PATTERN_META[key]["emoji"]
    return {"preview": "🖼", "layout": "📐"}.get(key, "🧵")


def safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(s))


# ============================================================
# RUN FOLDERS
# ============================================================
def make_run_dir(label: str) -> str:
    """Create outputs/<label>_<timestamp>/ and return its absolute path."""
    os.makedirs(OUTPUTS_ROOT, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(OUTPUTS_ROOT, f"{safe(label)}_{ts}")
    sub, n = base, 1
    while os.path.exists(sub):
        n += 1
        sub = f"{base}_{n}"
    os.makedirs(sub)
    return sub


def migrate_loose_root_files():
    """Move stray pattern files from the project root into outputs/.

    Older versions wrote into the process cwd. Runs once at startup; safe to
    re-run.
    """
    moved = []
    if not os.path.isdir(_HERE):
        return moved
    for fn in list(os.listdir(_HERE)):
        full = os.path.join(_HERE, fn)
        if not os.path.isfile(full) or not fn.endswith((".pdf", ".png")):
            continue
        key = size = None
        for pat in (r"^([a-z_]+?)_pattern_(\d+-\d+m)",
                    r"^preview_([a-z_]+?)_(\d+-\d+m)",
                    r"^rendered_([a-z_]+?)_(\d+-\d+m)",
                    r"^cutting_layout_([a-z_]+?)_(\d+-\d+m)_"):
            m = re.match(pat, fn)
            if m:
                key, size = m.group(1), m.group(2)
                break
        if not key:
            continue
        sub = os.path.join(OUTPUTS_ROOT, f"legacy_{safe(key)}_{safe(size)}")
        os.makedirs(sub, exist_ok=True)
        try:
            shutil.move(full, os.path.join(sub, fn))
            moved.append(fn)
        except OSError:
            pass
    return moved


def _parse_run_folder(name: str) -> dict:
    """Parse 'dress_3-6m_20260427-120530' or 'legacy_dress_3-6m'."""
    is_legacy = name.startswith("legacy_")
    rest = name[len("legacy_"):] if is_legacy else name
    m = re.match(r"^(.+?)_(\d+-\d+m)(?:_(\d{8}-\d{6})(?:_(\d+))?)?$", rest)
    if m:
        key, size, ts = m.group(1), m.group(2), m.group(3)
    else:
        key, size, ts = rest, "?", None
    return {"key": key, "size": size, "ts": ts, "legacy": is_legacy}


def _format_ts(ts: str) -> str:
    if not ts:
        return ""
    try:
        return datetime.strptime(ts, "%Y%m%d-%H%M%S").strftime(
            "%d %b %Y · %H:%M:%S")
    except ValueError:
        return ts


def scan_runs() -> list:
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
        info["renders"] = [f for f in files
                           if f.startswith("rendered_") and f.endswith(".png")]
        info["previews"] = [f for f in files
                            if f.startswith("preview_") and f.endswith(".png")]
        info["layouts"] = [f for f in files
                           if f.startswith("cutting_layout_")
                           and f.endswith(".png")]
        info["other_pngs"] = [
            f for f in files
            if f.endswith(".png")
            and not f.startswith(("preview_", "cutting_layout_", "rendered_"))
        ]
        info["all_files"] = [f for f in files if f != "index.html"]
        runs.append(info)
    return runs


# ============================================================
# HTML
# ============================================================
_HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>body {{ font-family: 'Sarabun', 'Noto Sans Thai', system-ui, sans-serif; }}</style>"""


def _subfolder_index(folder: str, files: list) -> str:
    items = []
    for f in sorted(files):
        if f == "index.html":
            continue
        ext = f.rsplit(".", 1)[-1].lower()
        if ext == "png":
            icon, prev = "🖼", (f'<img src="{escape(f)}" class="w-full '
                                f'max-w-xl rounded-lg shadow border" '
                                f'alt="{escape(f)}">')
        elif ext == "pdf":
            icon, prev = "📄", ""
        else:
            icon, prev = "📎", ""
        items.append(
            f'<li class="bg-white rounded-xl shadow-sm p-4 space-y-3">'
            f'<a href="{escape(f)}" target="_blank" class="font-mono text-sm '
            f'text-pink-600 hover:underline">{icon} {escape(f)}</a>{prev}</li>')
    items_html = "\n".join(items) or '<li class="text-gray-400">โฟลเดอร์ว่าง</li>'
    return f"""<!doctype html>
<html lang="th">
<head>
{_HEAD.format()}
<title>{escape(folder)} — Baby Fashion Engine</title>
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
"""


def _card_html(r: dict) -> str:
    folder, key, size = r["folder"], r["key"], r["size"]
    title, emoji = title_for(key), emoji_for(key)
    ts_str = _format_ts(r["ts"]) if r["ts"] else ("ของเดิม" if r["legacy"] else "")
    legacy_badge = ('<span class="px-2 py-0.5 bg-amber-100 text-amber-700 '
                    'text-[10px] rounded">ของเดิม</span>'
                    if r["legacy"] else "")

    if r["renders"]:
        thumb_src = f"outputs/{escape(folder)}/{escape(r['renders'][0])}"
    elif r["previews"]:
        thumb_src = f"outputs/{escape(folder)}/{escape(r['previews'][0])}"
    else:
        thumb_src = ""

    click_target = (f"outputs/{escape(folder)}/{escape(r['pdfs'][0])}"
                    if r["pdfs"]
                    else f"outputs/{escape(folder)}/index.html")
    if thumb_src:
        thumb = (f'<img src="{thumb_src}" alt="preview" '
                 f'class="w-full h-56 object-cover bg-pink-50/60">')
    else:
        thumb = (f'<div class="w-full h-56 bg-pink-50/60 flex items-center '
                 f'justify-center text-5xl">{emoji}</div>')

    btns = []
    for f in r["pdfs"]:
        btns.append(f'<a href="outputs/{escape(folder)}/{escape(f)}" '
                    f'target="_blank" class="px-3 py-1.5 bg-pink-500 '
                    f'hover:bg-pink-600 text-white text-xs rounded-full '
                    f'font-medium transition shadow-sm">📄 PDF</a>')
    for f in r["layouts"]:
        btns.append(f'<a href="outputs/{escape(folder)}/{escape(f)}" '
                    f'target="_blank" class="px-3 py-1.5 bg-purple-100 '
                    f'hover:bg-purple-200 text-purple-800 text-xs rounded-full '
                    f'font-medium transition">📐 ผังตัด</a>')
    for f in r["previews"]:
        btns.append(f'<a href="outputs/{escape(folder)}/{escape(f)}" '
                    f'target="_blank" class="px-3 py-1.5 bg-gray-100 '
                    f'hover:bg-gray-200 text-gray-700 text-xs rounded-full '
                    f'font-medium transition">🖼 พรีวิว</a>')
    for f in r["other_pngs"]:
        btns.append(f'<a href="outputs/{escape(folder)}/{escape(f)}" '
                    f'target="_blank" class="px-3 py-1.5 bg-gray-100 '
                    f'hover:bg-gray-200 text-gray-700 text-xs rounded-full '
                    f'font-medium transition">🖼 {escape(f)}</a>')
    btns_html = ("\n      ".join(btns)
                 or '<span class="text-xs text-gray-400">ไม่มีไฟล์</span>')

    file_list = "".join(f"<li>· {escape(f)}</li>" for f in r["all_files"])
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
      <span class="ml-auto">{len(r['all_files'])} ไฟล์</span>
    </div>
    <div class="pt-1 flex flex-wrap gap-2">
      {btns_html}
    </div>
    <details class="text-xs text-gray-500">
      <summary class="cursor-pointer hover:text-gray-700">📁 {escape(folder)}</summary>
      <ul class="mt-2 pl-3 space-y-0.5 font-mono text-[11px]">
        {file_list}
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


def _index_html(runs) -> str:
    cards = "\n".join(_card_html(r) for r in runs) if runs else _empty_state_html()
    counts = {}
    for r in runs:
        counts[r["key"]] = counts.get(r["key"], 0) + 1
    chips = " ".join(
        f'<span class="px-3 py-1 bg-pink-100 text-pink-700 text-xs '
        f'rounded-full font-medium">{emoji_for(k)} '
        f'{escape(title_for(k))} · {n}</span>'
        for k, n in sorted(counts.items()))
    now = datetime.now().strftime("%d/%m/%Y · %H:%M")
    return f"""<!doctype html>
<html lang="th">
<head>
{_HEAD.format()}
<title>Baby Fashion Engine — แคตตาล็อกแพทเทิร์น</title>
<style>
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
      <span class="px-3 py-1 bg-gray-900 text-white text-xs rounded-full font-medium">{len(runs)} รอบ</span>
      {chips}
    </div>
  </header>
  <main class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
    {cards}
  </main>
  <footer class="mt-16 text-center text-xs text-gray-400">
    สร้างโดย <code class="font-mono text-gray-500">baby_pattern_server.py</code> ·
    ไฟล์ทั้งหมดอยู่ใน <code class="font-mono text-gray-500">outputs/</code>
  </footer>
</div>
</body>
</html>
"""


def rebuild_index() -> str:
    """Rewrite index.html plus every subfolder index. Returns the main path."""
    runs = scan_runs()
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(_index_html(runs))

    if os.path.isdir(OUTPUTS_ROOT):
        for entry in os.listdir(OUTPUTS_ROOT):
            sub = os.path.join(OUTPUTS_ROOT, entry)
            if not os.path.isdir(sub):
                continue
            files = [f for f in sorted(os.listdir(sub)) if f != "index.html"]
            with open(os.path.join(sub, "index.html"), "w",
                      encoding="utf-8") as f:
                f.write(_subfolder_index(entry, files))
    return INDEX_HTML
