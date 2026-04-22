"""
Off-shoulder flutter romper — ruffle neckline, bubble body, snap crotch.
Matches the style in popular handmade baby boutiques: no shoulder seams,
elasticized neckline covered by a flounce that acts as flutter sleeves.
"""
import os
from reportlab.lib.units import cm
from reportlab.lib.colors import black, gray, red, blue

from sizes import get_size
from drawing import (draw_grain_line, draw_notch, draw_fold_edge,
                     draw_bezier_edge, draw_sa_rect_envelope, tile_and_save)


def generate(size_label: str,
             seam_allowance: float = 1.0,
             ruffle_height: float = 7.0,
             ruffle_fullness: float = 1.8,
             crotch_snaps: int = 3) -> str:
    """
    Pieces produced:
      1. Body  — cut 2 on fold (front + back, identical)
      2. Ruffle — cut 1 long strip (or cut 2 if too wide for A4)
      3. Crotch placket guide (printed annotation, no extra piece)
    """
    spec = get_size(size_label)

    # --- Body dimensions (all half-width, cut on fold) ---
    top_half = (spec["chest"] + 12) / 4         # gathered neckline
    chest_half = (spec["chest"] + 6) / 4        # below ruffle line
    hip_half = (spec["hip"] + 8) / 4            # at leg-level
    crotch_half = 3.0                           # 6cm crotch total

    shoulder_drop = 2.5
    rise = (spec["rise_f"] + spec["rise_b"]) / 2 + 2.0
    body_torso = spec["length"] * 0.55
    total_h = shoulder_drop + body_torso + rise
    leg_drop = 8.0

    # --- Ruffle dimensions ---
    # Neckline circumference (top edge of FULL body, front + back)
    neckline_circ = top_half * 2 * 2
    ruffle_length = neckline_circ * ruffle_fullness
    ruffle_h = ruffle_height

    # Decide if ruffle fits on one strip (within printable A4 width budget)
    # Max sensible strip width before tiling gets awkward = ~60cm
    max_ruffle_strip = 60.0
    if ruffle_length > max_ruffle_strip:
        ruffle_strips = 2
        ruffle_length_each = ruffle_length / 2
    else:
        ruffle_strips = 1
        ruffle_length_each = ruffle_length

    sa = seam_allowance
    gap = 2.5

    total_w = max(hip_half, ruffle_length_each) + sa * 2 + 3
    total_h_canvas = total_h + ruffle_h * ruffle_strips + sa * 6 + gap * 2 + 4

    def draw(c):
        y_cursor = 2.0

        # --- Body piece (cut 2 on fold) ---
        bx, by = 2.0, y_cursor
        _draw_flutter_body(c, bx, by, top_half, chest_half, hip_half,
                           crotch_half, shoulder_drop, leg_drop, rise,
                           body_torso, total_h, sa)

        c.setFont("Helvetica-Bold", 11)
        c.drawString((bx + 1) * cm, (by + total_h * 0.6) * cm,
                     "1. Body - Cut 2 on fold")
        c.setFont("Helvetica", 8)
        c.drawString((bx + 1) * cm, (by + total_h * 0.55) * cm,
                     f"Size {size_label}  |  "
                     f"Front + Back (identical)")
        c.setFont("Helvetica", 7)
        c.drawString((bx + 1) * cm, (by + total_h * 0.50) * cm,
                     f"Top {top_half * 2:.1f}cm | Hip {hip_half * 2:.1f}cm "
                     f"| Length {total_h:.1f}cm")
        c.drawString((bx + 1) * cm, (by + total_h * 0.46) * cm,
                     "Top edge = neckline (elastic casing here)")

        draw_fold_edge(c, bx, by, bx, by + total_h)
        draw_grain_line(c,
                        bx + chest_half * 0.65, by + rise * 0.3,
                        bx + chest_half * 0.65, by + total_h * 0.75)
        # notches
        # top-right corner marker (seam match for ruffle attachment)
        draw_notch(c, bx + top_half, by + total_h, angle_deg=270)
        # side match point
        draw_notch(c, bx + chest_half, by + total_h - shoulder_drop,
                   angle_deg=180)
        # leg corner
        draw_notch(c, bx + hip_half, by + rise + leg_drop, angle_deg=180)

        # crotch snap markers (printed on piece)
        c.setFillColor(red)
        snap_spacing = (crotch_half * 2 - 2) / max(crotch_snaps - 1, 1)
        snap_y = by + 0.5
        for i in range(crotch_snaps):
            snap_x = bx + 1 + i * snap_spacing
            c.circle(snap_x * cm, snap_y * cm, 0.2 * cm, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica", 6)
        c.setFillColor(red)
        c.drawString((bx + 0.3) * cm, (by + 1.1) * cm,
                     f"{crotch_snaps} snaps at crotch (back piece only)")
        c.setFillColor(black)

        # elastic casing annotation at top
        c.setFont("Helvetica-Oblique", 6)
        c.setFillColor(gray)
        c.drawString((bx + 0.3) * cm, (by + total_h - 0.35) * cm,
                     "fold 1.5cm for elastic casing")
        c.setFillColor(black)

        # leg elastic annotation
        c.drawString((bx + hip_half - 5) * cm, (by + rise + leg_drop * 0.5) * cm,
                     "leg elastic casing")

        y_cursor = by + total_h + sa * 2 + gap

        # --- Ruffle strip(s) ---
        for strip_i in range(ruffle_strips):
            rx, ry = 2.0, y_cursor
            c.setLineWidth(1.3)
            c.rect(rx * cm, ry * cm,
                   ruffle_length_each * cm, ruffle_h * cm)

            c.setFont("Helvetica-Bold", 10)
            if ruffle_strips == 1:
                label = "2. Ruffle - Cut 1 strip"
            else:
                label = f"2. Ruffle - Strip {strip_i + 1} of 2 (cut 1 each)"
            c.drawString((rx + 0.5) * cm,
                         (ry + ruffle_h - 0.7) * cm, label)
            c.setFont("Helvetica", 7)
            c.drawString((rx + 0.5) * cm, (ry + ruffle_h - 1.3) * cm,
                         f"{ruffle_length_each:.1f} x {ruffle_h:.1f} cm  "
                         f"(gather top, fullness {ruffle_fullness}x)")
            c.drawString((rx + 0.5) * cm, (ry + 0.3) * cm,
                         "Bottom edge: narrow rolled hem")

            # gather marks at top
            n_ticks = int(ruffle_length_each / 2)
            c.setLineWidth(0.4)
            c.setStrokeColor(gray)
            for i in range(1, n_ticks):
                tx = rx + i * (ruffle_length_each / n_ticks)
                c.line(tx * cm, (ry + ruffle_h) * cm,
                       tx * cm, (ry + ruffle_h - 0.3) * cm)
            c.setStrokeColor(black)

            # grain line (along length)
            draw_grain_line(c,
                            rx + 3, ry + ruffle_h / 2,
                            rx + ruffle_length_each - 3, ry + ruffle_h / 2)

            # notches at quarter points for alignment with body
            for frac in (0.25, 0.5, 0.75):
                draw_notch(c, rx + ruffle_length_each * frac,
                           ry + ruffle_h, angle_deg=270)

            draw_sa_rect_envelope(c, rx, ry, ruffle_length_each, ruffle_h, sa)

            y_cursor = ry + ruffle_h + sa * 2 + gap

    instructions = [
        f"OFF-SHOULDER FLUTTER ROMPER - {size_label}",
        "",
        "Materials:",
        "  - 0.6-0.9 m cotton lawn, poplin, or double gauze",
        "  - Matching thread",
        f"  - 5mm elastic: ~{top_half * 2 * 0.9:.0f} cm for neckline,",
        f"                  2 x ~{(spec['hip'] / 8 + 3) * 2:.0f} cm for leg openings",
        f"  - {crotch_snaps} KAM snap sets for crotch",
        "",
        "Construction overview:",
        "  This romper has NO shoulder seams - the ruffle wraps around",
        "  the neckline and cascades over the shoulders as flutter sleeves.",
        "  Neckline stretches on/off over baby's head (elasticized).",
        "",
        "Sewing order:",
        "  1. Cut 2 body pieces on fold (front + back)",
        "  2. Cut ruffle strip(s); join if 2 strips to make one continuous loop",
        "  3. Sew side seams RST (front to back)",
        "  4. Hem ruffle bottom with 6mm narrow rolled hem",
        "  5. Gather ruffle top edge to match neckline circumference",
        "  6. Pin ruffle to neckline (RIGHT side of ruffle to RIGHT side of body",
        "     top edge), distribute gathers evenly",
        "  7. Sew ruffle + body together along top edge",
        "  8. Fold top edge down 1.5cm to create elastic casing, leave 3cm gap",
        "  9. Thread neckline elastic, overlap 1cm, sew closed, close casing gap",
        " 10. Finish leg openings: fold 1cm casing, thread leg elastic",
        f" 11. Install {crotch_snaps} snaps at crotch edge",
        " 12. Final press",
        "",
        f"Seam allowance included: {seam_allowance} cm",
        f"Ruffle height: {ruffle_height} cm  |  Fullness: {ruffle_fullness}x",
    ]

    file_path = os.path.abspath(f"flutter_romper_pattern_{size_label}.pdf")
    total_pages = tile_and_save(
        file_path, "Off-Shoulder Flutter Romper", size_label,
        total_w, total_h_canvas, draw, instructions)

    return (f"Flutter romper pattern generated: {file_path}\n"
            f"Size: {size_label}  |  Pages: {total_pages} A4 sheets\n"
            f"Body {top_half * 2:.1f}x{total_h:.1f}cm | "
            f"Ruffle total {ruffle_length:.1f}x{ruffle_h:.1f}cm "
            f"({ruffle_strips} strip{'s' if ruffle_strips > 1 else ''})")


def _draw_flutter_body(c, x, y, top_half, chest_half, hip_half, crotch_half,
                       shoulder_drop, leg_drop, rise, body_torso, total_h, sa):
    """Draw one body piece (cut 2 on fold)."""
    top_l = (x, y + total_h)
    top_r = (x + top_half, y + total_h)
    chest_r = (x + chest_half, y + total_h - shoulder_drop)
    hip_r = (x + hip_half, y + rise + leg_drop)
    crotch_r = (x + crotch_half, y)

    c.setStrokeColor(black)
    c.setLineWidth(1.3)

    # top edge (gathered neckline)
    c.line(top_l[0] * cm, top_l[1] * cm,
           top_r[0] * cm, top_r[1] * cm)

    # gentle curve from neckline corner down/out to chest (off-shoulder drape)
    draw_bezier_edge(c,
                     top_r[0], top_r[1],
                     top_r[0] + 0.8, top_r[1] - shoulder_drop * 0.3,
                     chest_r[0] - 0.3, chest_r[1] + shoulder_drop * 0.3,
                     chest_r[0], chest_r[1])

    # side from chest down to hip (subtle bubble shape)
    mid_y = (chest_r[1] + hip_r[1]) / 2
    draw_bezier_edge(c,
                     chest_r[0], chest_r[1],
                     chest_r[0] + 0.4, mid_y + 1,
                     hip_r[0] + 0.2, mid_y - 1,
                     hip_r[0], hip_r[1])

    # leg opening curve (hip to crotch)
    draw_bezier_edge(c,
                     hip_r[0], hip_r[1],
                     hip_r[0] - 2.5, hip_r[1] - leg_drop * 0.6,
                     crotch_r[0] + 2.5, crotch_r[1] + 2,
                     crotch_r[0], crotch_r[1])

    # crotch bottom edge
    c.line(crotch_r[0] * cm, crotch_r[1] * cm,
           x * cm, y * cm)

    # center fold (bottom to top)
    c.line(x * cm, y * cm, x * cm, (y + total_h) * cm)

    # SA envelope
    c.setDash([4, 3], 0)
    c.setLineWidth(0.5)
    c.setStrokeColor(gray)
    c.rect((x - sa) * cm, (y - sa) * cm,
           (hip_half + sa * 2) * cm, (total_h + sa * 2) * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)
