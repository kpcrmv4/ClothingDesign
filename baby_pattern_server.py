"""
Baby Fashion Engine - MCP Server for children's clothing patterns (0-24m).

Entry point: thin layer over the `patterns/` and `features` modules.
All tools return human-readable strings (with file paths for PDF/PNG output).

Run:
    pip install mcp reportlab Pillow
    cd <project_folder>
    python baby_pattern_server.py
"""
from mcp.server.fastmcp import FastMCP

from patterns import dress, bib, bloomers, bonnet
from patterns import kimono_top, pants, tshirt, romper, sleep_sack
import features
import preview
import cutting_layout

mcp = FastMCP("BabyFashionEngine_Complete")


# ============================================================
# PATTERN GENERATORS
# ============================================================
@mcp.tool()
def generate_full_dress_pattern(size_label: str,
                                 seam_allowance: float = 1.0) -> str:
    """Generate a sleeveless baby dress with gathered ruffle hem.

    size_label: one of '0-3m', '3-6m', '6-9m', '9-12m', '12-18m', '18-24m'.
    Difficulty: Beginner. Fabric: cotton lawn or double gauze.
    """
    return dress.generate(size_label, seam_allowance)


@mcp.tool()
def generate_bib_pattern(size_label: str,
                         seam_allowance: float = 0.7) -> str:
    """Generate a drool bib with keyhole neck (snap closure at back).

    Two-layer: fashion fabric + absorbent terry backing.
    Difficulty: Beginner, ideal first project.
    """
    return bib.generate(size_label, seam_allowance)


@mcp.tool()
def generate_bloomers_pattern(size_label: str,
                               seam_allowance: float = 1.0) -> str:
    """Generate elastic-waist bloomers / diaper cover with curved crotch.

    Elastic casings at waist + leg openings. Cut 2 on fold.
    """
    return bloomers.generate(size_label, seam_allowance)


@mcp.tool()
def generate_bonnet_pattern(size_label: str,
                             seam_allowance: float = 1.0) -> str:
    """Generate traditional baby bonnet: crown + brim band + ties.

    3 pieces. Uses curved edges. Needs 0.3m outer + 0.3m lining.
    """
    return bonnet.generate(size_label, seam_allowance)


@mcp.tool()
def generate_kimono_top_pattern(size_label: str,
                                 seam_allowance: float = 1.0) -> str:
    """Generate a baby kimono wrap top with side ties.

    No buttons, ideal for newborns. Sleeves included.
    Difficulty: Beginner. Fabric: cotton lawn, flannel, or jersey.
    """
    return kimono_top.generate(size_label, seam_allowance)


@mcp.tool()
def generate_pants_pattern(size_label: str,
                            seam_allowance: float = 1.0,
                            style: str = "long") -> str:
    """Generate elastic-waist baby pants.

    style: 'long' (full length) or 'short' (shorts length).
    Fabric: knit or light woven cotton.
    """
    return pants.generate(size_label, seam_allowance, style)


@mcp.tool()
def generate_tshirt_pattern(size_label: str,
                             seam_allowance: float = 1.0,
                             sleeve: str = "short") -> str:
    """Generate a basic baby t-shirt with crew neck.

    sleeve: 'short' or 'long'. Requires ribbing for neckband.
    Needs shoulder snaps for newborn sizes.
    Difficulty: Intermediate. Fabric: cotton jersey.
    """
    return tshirt.generate(size_label, seam_allowance, sleeve)


@mcp.tool()
def generate_romper_pattern(size_label: str,
                             seam_allowance: float = 1.0) -> str:
    """Generate a baby romper (one-piece bodysuit with straps and snaps).

    Includes crotch snap placket. Difficulty: Intermediate.
    """
    return romper.generate(size_label, seam_allowance)


@mcp.tool()
def generate_sleep_sack_pattern(size_label: str,
                                 seam_allowance: float = 1.0) -> str:
    """Generate a baby sleep sack (wearable blanket) with front zipper.

    Sleeveless design for safer sleep. Difficulty: Intermediate.
    Fabric: cotton jersey, flannel, or muslin.
    """
    return sleep_sack.generate(size_label, seam_allowance)


# ============================================================
# SUPPORT TOOLS
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
    path = preview.generate_preview(pattern_key, size_label)
    if path.startswith("Error"):
        return path
    return f"Preview saved: {path}"


@mcp.tool()
def generate_cutting_layout(pattern_key: str, size_label: str,
                             fabric_width_cm: int = 115) -> str:
    """Generate a PNG showing how to lay out pattern pieces on fabric.

    fabric_width_cm: 90, 115, or 150. Common bolt widths.
    Helps minimize fabric waste by showing a shelf-packed layout.
    Returns the absolute file path of the PNG.
    """
    path = cutting_layout.generate_layout(pattern_key, size_label, fabric_width_cm)
    if path.startswith("Error"):
        return path
    return f"Cutting layout saved: {path}"


if __name__ == "__main__":
    mcp.run()
