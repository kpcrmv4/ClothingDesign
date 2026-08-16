"""
Baby Fashion Engine — MCP server for children's clothing patterns (0-24m).

Entry point only: tool definitions plus the run/publish plumbing. The work
lives in the modules next to this file.

    geometry.py   ขนาดชิ้นทุกแพทเทิร์น (แหล่งความจริงเดียว)
    patterns/     วาดแพทเทิร์นลง PDF
    preview.py    PNG รูปทรงชิ้นแบน
    rendered.py   PNG ภาพชุดเมื่อเย็บเสร็จ
    cutting_layout.py  PNG ผังวางบนผ้า
    features.py   metadata + คำนวณผ้า + รายการซื้อของ
    customize.py  ตีความคำบรรยาย -> แพทเทิร์น + พารามิเตอร์
    gallery.py    จัดการโฟลเดอร์ outputs/ และสร้าง index.html

Run:
    pip install -r requirements.txt
    cd <project_folder>
    python baby_pattern_server.py
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime

# Claude Desktop on Windows ignores the `cwd` config field and launches MCP
# servers from C:\Windows\System32. Pin sys.path to this folder so the local
# modules import; generated files are addressed by explicit output_dir, never
# by the process cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:                        # MCP SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server
except ImportError:         # MCP SDK 2.x renamed FastMCP -> MCPServer
    from mcp.server import MCPServer as _Server

import cutting_layout
import customize
import drawing
import features
import gallery
import preview
import rendered
from patterns import (dress, tiered_dress, flutter_top, bib, bloomers,
                      bonnet, kimono_top, pants, tshirt, romper, sleep_sack,
                      flutter_romper)
from sizes import SIZE_CHART

CONFIG_PATH = os.path.join(_HERE, ".engine_config.json")
DEFAULT_CONFIG = {"auto_publish": True, "allow_publish_to_default_branch": False}
_PROTECTED_BRANCHES = {"main", "master"}


def _load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def _save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


# ============================================================
# RUN WRAPPERS
# ============================================================
def _size_error(size_label: str) -> str:
    return (f"❌ ไม่พบไซส์ '{size_label}'\n"
            f"ไซส์ที่ใช้ได้: {', '.join(SIZE_CHART)}\n"
            f"(เรียก list_available_sizes เพื่อดูสัดส่วนแต่ละไซส์)")


def _run_pattern(pattern_key: str, size_label: str, gen_fn,
                 label_extra: str = "", render_params: dict = None,
                 **kwargs) -> str:
    """Generate PDF + preview + finished-garment PNG into one fresh folder.

    Any failure becomes a readable message rather than a traceback, because
    the user only ever sees the returned string inside Claude.
    """
    if size_label not in SIZE_CHART:
        return _size_error(size_label)

    render_params = render_params or {}
    label = f"{pattern_key}_{size_label}"
    if label_extra:
        label += f"_{label_extra}"

    try:
        sub = gallery.make_run_dir(label)
    except OSError as e:
        return f"❌ สร้างโฟลเดอร์ผลลัพธ์ไม่สำเร็จ: {e}"

    try:
        pdf_result = gen_fn(size_label, output_dir=sub, **kwargs)
    except Exception as e:
        return (f"❌ สร้างแพทเทิร์น {pattern_key} ไม่สำเร็จ: "
                f"{type(e).__name__}: {e}\n"
                f"ลองตรวจไซส์และพารามิเตอร์ หรือเรียก list_all_patterns "
                f"เพื่อดูตัวเลือกที่ถูกต้อง")

    if isinstance(pdf_result, str) and pdf_result.startswith("Error"):
        return f"❌ {pdf_result}"

    extra_lines = []
    try:
        p = preview.generate_preview(pattern_key, size_label,
                                     output_dir=sub, **render_params)
        if p and not p.startswith("Error"):
            extra_lines.append(f"พรีวิว: {p}")
    except Exception as e:
        extra_lines.append(f"(สร้างพรีวิวไม่สำเร็จ: {e})")

    try:
        r = rendered.render_finished(pattern_key, size_label,
                                     output_dir=sub, **render_params)
        if r and not r.startswith("Error"):
            extra_lines.append(f"ภาพชุดเสร็จ: {r}")
    except Exception as e:
        extra_lines.append(f"(วาดชุดเสร็จไม่สำเร็จ: {e})")

    warn = drawing.font_warning()
    if warn:
        extra_lines.append(f"⚠ {warn}")

    try:
        gallery.rebuild_index()
        extra_lines.append(
            f"แคตตาล็อก: file:///{gallery.INDEX_HTML.replace(os.sep, '/')}")
    except Exception as e:
        extra_lines.append(f"(สร้างแคตตาล็อกไม่สำเร็จ: {e})")

    cfg = _load_config()
    if cfg["auto_publish"]:
        title = features.PATTERN_META.get(pattern_key, {}).get(
            "title_th", pattern_key)
        tag = f"{title} {size_label}"
        if label_extra:
            tag += f" ({label_extra})"
        res = _publish(f"เพิ่ม {tag} — {datetime.now().strftime('%H:%M')}")
        extra_lines.append("")
        extra_lines.append(res["summary"])

    return pdf_result + "\n" + "\n".join(extra_lines)


def _run_file_tool(label: str, fn, *args, **kwargs) -> str:
    """Run a single file-producing helper into its own folder."""
    try:
        sub = gallery.make_run_dir(label)
        path = fn(*args, output_dir=sub, **kwargs)
    except Exception as e:
        return f"❌ ทำงานไม่สำเร็จ: {type(e).__name__}: {e}"
    if isinstance(path, str) and path.startswith("Error"):
        return f"❌ {path}"
    try:
        gallery.rebuild_index()
    except Exception:
        pass
    return f"✓ บันทึกแล้ว: {path}"


# Startup housekeeping
gallery.migrate_loose_root_files()
try:
    gallery.rebuild_index()
except Exception:
    pass


mcp = _Server("BabyFashionEngine_Complete")


# ============================================================
# PATTERN GENERATORS
# ============================================================
@mcp.tool()
def generate_full_dress_pattern(size_label: str,
                                seam_allowance: float = 1.0,
                                skirt_style: str = "gathered",
                                front_placket: bool = False) -> str:
    """Generate a sleeveless baby dress with a gathered or bubble hem.

    Use for: simple sleeveless dresses and pinafores with ONE skirt piece.
    For a skirt made of 2-3 stacked ruffle layers use
    generate_tiered_dress_pattern instead.

    size_label: '0-3m', '3-6m', '6-9m', '9-12m', '12-18m', '18-24m'.
    skirt_style: 'gathered' (flat ruffle hem) or 'bubble' (balloon hem,
                 gathered at both edges and turned into a lining).
    front_placket: True adds a button placket down the centre front.
    Difficulty: Beginner. Fabric: cotton lawn, gingham, or double gauze.
    """
    return _run_pattern("dress", size_label, dress.generate,
                        label_extra=skirt_style,
                        render_params={},
                        seam_allowance=seam_allowance,
                        skirt_style=skirt_style,
                        front_placket=front_placket)


@mcp.tool()
def generate_tiered_dress_pattern(size_label: str,
                                  seam_allowance: float = 1.0,
                                  tiers: int = 3,
                                  neckline: str = "round",
                                  tier_fullness: float = 1.5,
                                  lace_trim: bool = True) -> str:
    """Generate a dress whose skirt is 2-3 stacked, gathered ruffle tiers.

    Use for: boutique-style layered dresses — gingham or floral, with lace
    between the tiers, and for halter dresses that tie in a bow at the back.

    tiers: 2 or 3 layers.
    neckline: 'round'  คอกลม ติดกุ๊น/ลูกไม้รอบคอ (มีตะเข็บไหล่)
              'halter' คอผูกหลัง มีโบว์ใหญ่ผูกด้านหลัง (ไม่มีตะเข็บไหล่)
              'strap'  สายไหล่เดี่ยว ผูกโบว์บนบ่า
    tier_fullness: how much wider each tier is than the seam above it
                   (1.5 = normal gather, 2.0 = very full). Range 1.2-2.5.
    lace_trim: True adds lace-over-seam notes and counts the lace yardage.
    Difficulty: Intermediate. Fabric: cotton gingham, lawn, or small florals.
    """
    return _run_pattern("tiered_dress", size_label, tiered_dress.generate,
                        label_extra=f"{tiers}tier_{neckline}",
                        render_params={"tiers": tiers, "neckline": neckline,
                                       "tier_fullness": tier_fullness,
                                       "lace_trim": lace_trim},
                        seam_allowance=seam_allowance,
                        tiers=tiers, neckline=neckline,
                        tier_fullness=tier_fullness, lace_trim=lace_trim)


@mcp.tool()
def generate_flutter_top_pattern(size_label: str,
                                 seam_allowance: float = 1.0,
                                 sleeve_fullness: float = 1.8,
                                 neck_finish: str = "ruffle") -> str:
    """Generate a short pull-on top with flutter sleeves.

    Use for: the white blouse worn UNDER a pinafore or strap dress. Pair it
    with generate_full_dress_pattern or generate_tiered_dress_pattern to get
    the layered look. Not a standalone dress.

    sleeve_fullness: how much wider the sleeve is than the armhole it
                     gathers into (1.8 = normal flutter). Range 1.2-2.5.
    neck_finish: 'ruffle'  คอระบายตั้งขึ้นรอบคอ
                 'binding' คอเรียบกุ๊นด้วยแถบผ้าเฉลียง
    Difficulty: Intermediate. Fabric: white cotton lawn, voile, or eyelet.
    """
    return _run_pattern("flutter_top", size_label, flutter_top.generate,
                        label_extra=neck_finish,
                        render_params={"sleeve_fullness": sleeve_fullness,
                                       "neck_finish": neck_finish},
                        seam_allowance=seam_allowance,
                        sleeve_fullness=sleeve_fullness,
                        neck_finish=neck_finish)


@mcp.tool()
def generate_bib_pattern(size_label: str, seam_allowance: float = 0.7) -> str:
    """Generate a drool bib with a keyhole neck (snap closure at back).

    Two layers: fashion fabric + absorbent terry backing.
    Difficulty: Beginner, ideal first project.
    """
    return _run_pattern("bib", size_label, bib.generate,
                        seam_allowance=seam_allowance)


@mcp.tool()
def generate_bloomers_pattern(size_label: str,
                              seam_allowance: float = 1.0) -> str:
    """Generate elastic-waist bloomers / diaper cover with a curved crotch.

    Elastic casings at the waist and both leg openings. Cut 2 on the fold.
    Pairs with any of the dress patterns.
    """
    return _run_pattern("bloomers", size_label, bloomers.generate,
                        seam_allowance=seam_allowance)


@mcp.tool()
def generate_bonnet_pattern(size_label: str,
                            seam_allowance: float = 1.0) -> str:
    """Generate a traditional baby bonnet: crown + brim band + ties.

    3 pieces with curved edges. Needs 0.3m outer + 0.3m lining fabric.
    """
    return _run_pattern("bonnet", size_label, bonnet.generate,
                        seam_allowance=seam_allowance)


@mcp.tool()
def generate_kimono_top_pattern(size_label: str,
                                seam_allowance: float = 1.0) -> str:
    """Generate a baby kimono wrap top with side ties.

    No buttons — ideal for newborns. Sleeves included.
    Difficulty: Beginner. Fabric: cotton lawn, flannel, or jersey.
    """
    return _run_pattern("kimono_top", size_label, kimono_top.generate,
                        seam_allowance=seam_allowance)


@mcp.tool()
def generate_pants_pattern(size_label: str,
                           seam_allowance: float = 1.0,
                           style: str = "long") -> str:
    """Generate elastic-waist baby pants.

    style: 'long' (full length) or 'short' (shorts).
    Fabric: knit or light woven cotton.
    """
    return _run_pattern("pants", size_label, pants.generate,
                        label_extra=style,
                        seam_allowance=seam_allowance, style=style)


@mcp.tool()
def generate_tshirt_pattern(size_label: str,
                            seam_allowance: float = 1.0,
                            sleeve: str = "short") -> str:
    """Generate a basic baby t-shirt with a crew neck.

    sleeve: 'short' or 'long'. Requires ribbing for the neckband and
    shoulder snaps for newborn sizes.
    Difficulty: Intermediate. Fabric: cotton jersey.
    """
    return _run_pattern("tshirt", size_label, tshirt.generate,
                        label_extra=sleeve,
                        seam_allowance=seam_allowance, sleeve=sleeve)


@mcp.tool()
def generate_romper_pattern(size_label: str,
                            seam_allowance: float = 1.0) -> str:
    """Generate a baby romper (one-piece bodysuit with straps and snaps).

    Includes a crotch snap placket. Difficulty: Intermediate.
    """
    return _run_pattern("romper", size_label, romper.generate,
                        seam_allowance=seam_allowance)


@mcp.tool()
def generate_sleep_sack_pattern(size_label: str,
                                seam_allowance: float = 1.0) -> str:
    """Generate a baby sleep sack (wearable blanket) with a front zipper.

    Sleeveless design for safer sleep. Difficulty: Intermediate.
    Fabric: cotton jersey, flannel, or muslin.
    """
    return _run_pattern("sleep_sack", size_label, sleep_sack.generate,
                        seam_allowance=seam_allowance)


@mcp.tool()
def generate_flutter_romper_pattern(size_label: str,
                                    seam_allowance: float = 1.0,
                                    ruffle_height: float = 7.0,
                                    ruffle_fullness: float = 1.8,
                                    crotch_snaps: int = 3) -> str:
    """Generate an off-shoulder flutter romper (elastic neck + cascading ruffle).

    No shoulder seams — the ruffle acts as flutter sleeves over a bubble
    body with a snap crotch. Best for girls 0-18 months.

    ruffle_height: depth of the flounce in cm (default 7, typical 5-9).
    ruffle_fullness: gather ratio vs the neckline (default 1.8, typical 1.5-2.2).
    crotch_snaps: number of snaps across the crotch (default 3).
    """
    return _run_pattern("flutter_romper", size_label, flutter_romper.generate,
                        render_params={"ruffle_height": ruffle_height,
                                       "ruffle_fullness": ruffle_fullness},
                        seam_allowance=seam_allowance,
                        ruffle_height=ruffle_height,
                        ruffle_fullness=ruffle_fullness,
                        crotch_snaps=crotch_snaps)


# ============================================================
# SUPPORT TOOLS (no file output)
# ============================================================
@mcp.tool()
def list_available_sizes() -> str:
    """Return the full size chart (0-3m through 18-24m) as a table."""
    return features.list_available_sizes()


@mcp.tool()
def list_all_patterns() -> str:
    """Return every available pattern with its difficulty and time estimate."""
    return features.list_all_patterns()


@mcp.tool()
def calculate_fabric_requirement(pattern_type: str, size_label: str) -> str:
    """Estimate fabric needed for a pattern across 90/115/150 cm bolt widths.

    pattern_type: any key from list_all_patterns, e.g. 'dress',
                  'tiered_dress', 'bib', 'pants', 'flutter_romper'.
    """
    return features.format_fabric_requirement(pattern_type, size_label)


@mcp.tool()
def generate_shopping_list(pattern_keys: list, size_label: str,
                           fabric_width_cm: int = 115) -> str:
    """Generate a consolidated shopping list for one or more patterns.

    pattern_keys: list of pattern names, e.g. ['tiered_dress', 'bloomers'].
    Returns fabric yardage plus notions (thread, elastic, snaps, lace...).
    """
    return features.generate_shopping_list(pattern_keys, size_label,
                                           fabric_width_cm)


@mcp.tool()
def suggest_pattern_from_description(description: str) -> str:
    """Analyse a text description and suggest which pattern tool(s) to use.

    Use this after viewing a reference photo and writing down what you see,
    or when the user describes what they want in free text. Returns ranked
    matches plus the suggested parameters for each.

    Does NOT generate files — follow up with a specific generate_*_pattern call.
    """
    return customize.suggest_pattern_from_description(description)


@mcp.tool()
def customize_pattern(pattern_key: str, size_label: str,
                      changes: dict) -> str:
    """Turn a structured 'changes' dict into a concrete tool call.

    Supported keys depend on the pattern — the reply lists them. Examples:
      dress:        seam_allowance, skirt_style, front_placket
      tiered_dress: seam_allowance, tiers, neckline, tier_fullness, lace_trim
      pants:        seam_allowance, style
      tshirt:       seam_allowance, sleeve

    Returns a recommended tool call. Does not produce files directly.
    """
    return customize.customize_pattern(pattern_key, size_label, changes)


# ============================================================
# FILE-PRODUCING HELPERS
# ============================================================
@mcp.tool()
def generate_pattern_preview(pattern_key: str, size_label: str) -> str:
    """Save a quick PNG of the flat pattern outline (faster than the PDF).

    Useful for checking overall shape and proportions before committing to
    a full tiled PDF. Returns the absolute file path of the PNG.
    """
    if size_label not in SIZE_CHART:
        return _size_error(size_label)
    return _run_file_tool(f"preview_{pattern_key}_{size_label}",
                          preview.generate_preview, pattern_key, size_label)


@mcp.tool()
def generate_cutting_layout(pattern_key: str, size_label: str,
                            fabric_width_cm: int = 115) -> str:
    """Generate a PNG showing how to lay the pieces out on fabric.

    fabric_width_cm: 90, 115, or 150. The fabric is folded automatically
    when the pattern has cut-on-fold pieces, and the length shown here is
    the same number calculate_fabric_requirement quotes.
    """
    if size_label not in SIZE_CHART:
        return _size_error(size_label)
    return _run_file_tool(
        f"layout_{pattern_key}_{size_label}_{fabric_width_cm}cm",
        cutting_layout.generate_layout, pattern_key, size_label,
        fabric_width_cm)


@mcp.tool()
def rebuild_gallery_index() -> str:
    """Force a rebuild of index.html from whatever exists in outputs/.

    Useful after manually moving files around.
    """
    try:
        path = gallery.rebuild_index()
    except Exception as e:
        return f"❌ สร้างแคตตาล็อกไม่สำเร็จ: {e}"
    runs = gallery.scan_runs()
    return (f"สร้าง index.html ใหม่: {path}\n"
            f"  รวม {len(runs)} รอบในแคตตาล็อก\n"
            f"เปิดในเบราว์เซอร์: file:///{path.replace(os.sep, '/')}")


# ============================================================
# GIT / GITHUB PAGES PUBLISHING
# ============================================================
def _git(*args):
    """Run git in the project folder. Returns (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"      # never block waiting for a password
    r = subprocess.run(["git", *args], cwd=_HERE, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _pages_url() -> str:
    rc, out, _ = _git("config", "--get", "remote.origin.url")
    if rc != 0 or not out:
        return ""
    m = re.match(r"(?:https://github\.com/|git@github\.com:)([^/]+)/([^/.]+)",
                 out)
    if not m:
        return ""
    return f"https://{m.group(1).lower()}.github.io/{m.group(2)}/"


def _publish(message: str = "") -> dict:
    """Stage + commit + push. Returns {ok, summary, detail}."""
    rc, _, err = _git("rev-parse", "--git-dir")
    if rc != 0:
        return {"ok": False, "summary": "⚠ ข้าม publish (ไม่ใช่ git repo)",
                "detail": f"❌ ไม่ใช่ git repo: {err}"}

    rc, branch, _ = _git("branch", "--show-current")
    branch = branch or "HEAD"
    cfg = _load_config()
    if (branch in _PROTECTED_BRANCHES
            and not cfg["allow_publish_to_default_branch"]):
        return {
            "ok": False,
            "summary": (f"⚠ ข้าม publish — อยู่บน branch '{branch}' "
                        f"ซึ่งป้องกันไว้"),
            "detail": (f"กำลังอยู่บน branch '{branch}' ระบบไม่ push ผลงาน "
                       f"ขึ้น branch หลักโดยอัตโนมัติ\n"
                       f"ทางเลือก: สลับไป branch ทำงานก่อน "
                       f"(git switch -c gallery) หรือเรียก "
                       f"set_auto_publish(enabled=True, "
                       f"allow_default_branch=True) ถ้าตั้งใจจริง")}

    rc, _, err = _git("add", "-A")
    if rc != 0:
        return {"ok": False, "summary": "⚠ git add ล้มเหลว",
                "detail": f"❌ git add: {err}"}

    rc, _, _ = _git("diff", "--cached", "--quiet")
    if rc == 0:
        return {"ok": True,
                "summary": "ℹ ไม่มีการเปลี่ยนแปลงใหม่ — ไม่ต้อง commit",
                "detail": "ℹ working tree สะอาด"}

    if not message:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"อัปเดตแคตตาล็อก ({len(gallery.scan_runs())} รอบ) — {ts}"

    rc, _, err = _git("commit", "-m", message)
    if rc != 0:
        if "Please tell me who you are" in err or "user.email" in err:
            return {"ok": False, "summary": "⚠ ยังไม่ได้ตั้ง git identity",
                    "detail": ("git ยังไม่รู้ว่าคุณเป็นใคร รันคำสั่งนี้ก่อน:\n"
                               '  git config --global user.email "you@example.com"\n'
                               '  git config --global user.name "Your Name"')}
        return {"ok": False, "summary": "⚠ git commit ล้มเหลว",
                "detail": f"❌ git commit: {err}"}

    rc, _, err = _git("push", "origin", branch)
    if rc != 0:
        if any(s in err for s in ("could not read Username",
                                  "Authentication failed",
                                  "terminal prompts disabled")):
            return {"ok": False,
                    "summary": "✓ commit แล้ว แต่ push ล้มเหลว (ยังไม่ได้ login)",
                    "detail": ("ยังไม่ได้ login GitHub บนเครื่องนี้ — "
                               "รันใน terminal ครั้งเดียว:\n"
                               f"  cd {_HERE}\n"
                               f"  git push origin {branch}\n"
                               "หลัง login แล้วระบบจะจำให้")}
        return {"ok": False, "summary": "✓ commit แล้ว แต่ push ล้มเหลว",
                "detail": (f"git push: {err}\n\npush เองด้วย:\n"
                           f"  cd {_HERE}\n  git push origin {branch}")}

    pages = _pages_url()
    summary = f"🚀 push ขึ้น GitHub แล้ว ({branch}) — Pages อัปเดตใน 1-2 นาที"
    if pages:
        summary += f"\n   {pages}"
    return {"ok": True, "summary": summary,
            "detail": f"✓ commit: {message}\n✓ push สำเร็จ → {branch}\n\n{pages}"}


@mcp.tool()
def publish_gallery(message: str = "") -> str:
    """Manually commit + push the catalog (index.html + outputs/) to GitHub.

    Use this when auto-publish is off, or to force a custom commit message.
    """
    result = _publish(message)
    return result["detail"] or result["summary"]


@mcp.tool()
def set_auto_publish(enabled: bool,
                     allow_default_branch: bool = False) -> str:
    """Enable/disable auto-publish to GitHub after each pattern generation.

    The setting is saved to .engine_config.json so it survives a restart.

    enabled: when True, every successful generate_*_pattern runs
             git add + commit + push.
    allow_default_branch: by default the server refuses to auto-push while
             on 'main'/'master' so generated output never lands on the main
             branch by accident. Set True only if that is what you want.
    """
    cfg = _load_config()
    cfg["auto_publish"] = bool(enabled)
    cfg["allow_publish_to_default_branch"] = bool(allow_default_branch)
    _save_config(cfg)
    state = "เปิด" if cfg["auto_publish"] else "ปิด"
    guard = ("อนุญาต" if cfg["allow_publish_to_default_branch"] else "ไม่อนุญาต")
    return (f"✓ auto-publish: {state}\n"
            f"✓ push ขึ้น branch หลัก (main/master): {guard}\n"
            f"บันทึกไว้ที่ {CONFIG_PATH}")


@mcp.tool()
def git_status_summary() -> str:
    """Show what is currently uncommitted (sanity check before publishing)."""
    rc, out, err = _git("status", "--short")
    if rc != 0:
        return f"❌ git status ล้มเหลว:\n{err}"
    if not out:
        return "✓ working tree สะอาด — ไม่มีอะไรต้อง commit"
    rc, branch, _ = _git("branch", "--show-current")
    lines = out.splitlines()
    return (f"branch ปัจจุบัน: {branch or 'HEAD'}\n"
            f"มีไฟล์เปลี่ยน {len(lines)} ไฟล์:\n\n{out}")


if __name__ == "__main__":
    mcp.run()
