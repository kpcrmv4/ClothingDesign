"""
Thai-capable font lookup for the Pillow renderers (preview, rendered, layout).

The reportlab side has its own registration in drawing.py; this is the
equivalent for PNG output. Both fall back rather than raising, so a machine
with no Thai font produces a readable-but-Latin image instead of a crash.
"""
from PIL import ImageFont

_REGULAR = [
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\leelawad.ttf",
    "/usr/share/fonts/truetype/tlwg/Loma.ttf",
    "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Thonburi.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "DejaVuSans.ttf",
]

_BOLD = [
    r"C:\Windows\Fonts\tahomabd.ttf",
    r"C:\Windows\Fonts\leelawdb.ttf",
    "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf",
    "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf",
]

_cache = {}


def pil_font(size: int = 14, bold: bool = False):
    """Return a Pillow font at `size`, preferring one with Thai glyphs."""
    key = (size, bold)
    if key in _cache:
        return _cache[key]
    for path in (_BOLD if bold else _REGULAR):
        try:
            font = ImageFont.truetype(path, size)
            _cache[key] = font
            return font
        except Exception:
            continue
    font = ImageFont.load_default()
    _cache[key] = font
    return font
