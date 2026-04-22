"""Baby bib with keyhole neck opening and rounded body."""
import os
import math
from reportlab.lib.units import cm
from reportlab.lib.colors import black, red

from sizes import get_size
from drawing import draw_grain_line, draw_bezier_edge, tile_and_save


def generate(size_label: str, seam_allowance: float = 0.7) -> str:
    spec = get_size(size_label)

    body_w = spec["neck_circ"] * 0.9
    body_h = body_w * 1.1
    neck_r = spec["neck_circ"] / (2 * math.pi) + 0.5
    opening_w = neck_r * 0.8

    sa = seam_allowance
    total_w = body_w + sa * 2 + 2
    total_h = body_h + sa * 2 + 3

    def draw(c):
        cx = 1.0 + sa + body_w / 2
        bottom_y = 1.0 + sa
        top_y = bottom_y + body_h

        left_x = cx - body_w / 2
        right_x = cx + body_w / 2

        c.setStrokeColor(black)
        c.setLineWidth(1.3)

        draw_bezier_edge(c,
                         left_x, bottom_y + body_h * 0.3,
                         left_x, bottom_y,
                         right_x, bottom_y,
                         right_x, bottom_y + body_h * 0.3)

        draw_bezier_edge(c,
                         left_x, bottom_y + body_h * 0.3,
                         left_x - 0.5, bottom_y + body_h * 0.6,
                         left_x + 1.0, top_y - 1.5,
                         cx - opening_w - 1.5, top_y - 1.0)
        draw_bezier_edge(c,
                         right_x, bottom_y + body_h * 0.3,
                         right_x + 0.5, bottom_y + body_h * 0.6,
                         right_x - 1.0, top_y - 1.5,
                         cx + opening_w + 1.5, top_y - 1.0)

        draw_bezier_edge(c,
                         cx - opening_w - 1.5, top_y - 1.0,
                         cx - opening_w, top_y,
                         cx - opening_w, top_y,
                         cx - opening_w, top_y - neck_r * 0.3)
        draw_bezier_edge(c,
                         cx - opening_w, top_y - neck_r * 0.3,
                         cx - opening_w * 0.6, top_y - neck_r * 1.4,
                         cx - neck_r * 0.9, top_y - neck_r * 1.8,
                         cx, top_y - neck_r * 1.8)
        draw_bezier_edge(c,
                         cx, top_y - neck_r * 1.8,
                         cx + neck_r * 0.9, top_y - neck_r * 1.8,
                         cx + opening_w * 0.6, top_y - neck_r * 1.4,
                         cx + opening_w, top_y - neck_r * 0.3)
        draw_bezier_edge(c,
                         cx + opening_w, top_y - neck_r * 0.3,
                         cx + opening_w, top_y,
                         cx + opening_w, top_y,
                         cx + opening_w + 1.5, top_y - 1.0)

        c.setDash([3, 2], 0)
        c.line(cx * cm, (top_y - neck_r * 1.8) * cm,
               cx * cm, (top_y - neck_r * 1.8 - 2.0) * cm)
        c.setDash([], 0)

        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(cx * cm, (bottom_y + body_h * 0.55) * cm,
                            "Bib - Cut 2")
        c.setFont("Helvetica", 8)
        c.drawCentredString(cx * cm, (bottom_y + body_h * 0.48) * cm,
                            f"Size {size_label}")
        c.drawCentredString(cx * cm, (bottom_y + body_h * 0.42) * cm,
                            "1 main fabric + 1 absorbent backing (terry)")

        draw_grain_line(c, cx, bottom_y + body_h * 0.1,
                        cx, bottom_y + body_h * 0.25)

        c.setFillColor(red)
        c.circle(cx * cm, (top_y - neck_r * 1.8 - 2.2) * cm, 0.15 * cm, fill=1)
        c.setFont("Helvetica", 7)
        c.drawString((cx + 0.3) * cm, (top_y - neck_r * 1.8 - 2.3) * cm,
                     "snap")
        c.setFillColor(black)

    instructions = [
        f"BABY BIB - {size_label}",
        "",
        "Materials:",
        "  - 1 piece cotton or quilting fabric (front)",
        "  - 1 piece terry / bamboo / fleece (absorbent backing)",
        "  - 1 KAM snap set OR 20 cm velcro",
        "  - Approx. 25 x 25 cm of each fabric",
        "",
        "Sewing order:",
        "  1. Cut 1 front + 1 backing using the pattern",
        "  2. Place RST (right sides together)",
        "  3. Sew around all edges leaving a 5cm gap at bottom",
        "  4. Clip curves, turn right side out through gap",
        "  5. Press flat, topstitch 3mm from edge (closes gap)",
        "  6. Install snap at back neck slit",
        "",
        f"Seam allowance included: {seam_allowance} cm",
    ]

    file_path = os.path.abspath(f"bib_pattern_{size_label}.pdf")
    total_pages = tile_and_save(file_path, "Baby Bib", size_label,
                                 total_w, total_h, draw, instructions)

    return (f"Bib pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Body: {body_w:.1f} x {body_h:.1f} cm")
