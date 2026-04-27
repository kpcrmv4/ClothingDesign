"""
Professional pattern symbols: dart, pleat, gather, buttonhole, button placement,
pocket placement, and hem fold line markers.

All functions take reportlab Canvas + cm coordinates.
"""
import math
from reportlab.lib.units import cm
from reportlab.lib.colors import black, red, gray


def draw_dart(c, tip_x, tip_y, base_left_x, base_left_y,
              base_right_x, base_right_y, label=None):
    """Dart marker: triangle with dotted center line from tip to base midpoint."""
    c.setStrokeColor(black)
    c.setLineWidth(1.0)
    # triangle
    c.line(tip_x * cm, tip_y * cm, base_left_x * cm, base_left_y * cm)
    c.line(tip_x * cm, tip_y * cm, base_right_x * cm, base_right_y * cm)
    # dotted center (fold line)
    mx = (base_left_x + base_right_x) / 2
    my = (base_left_y + base_right_y) / 2
    c.setDash([2, 2], 0)
    c.setLineWidth(0.5)
    c.line(tip_x * cm, tip_y * cm, mx * cm, my * cm)
    c.setDash([], 0)
    if label:
        c.setFont("Helvetica", 6)
        c.drawString((tip_x + 0.2) * cm, tip_y * cm, label)


def draw_pleat(c, x1, y1, x2, y2, direction="right", label=None):
    """Pleat marker: two parallel lines + direction arrow indicating fold."""
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    c.line(x1 * cm, y1 * cm, x2 * cm, y2 * cm)
    # perpendicular arrow (short) at midpoint
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    angle = math.atan2(y2 - y1, x2 - x1)
    perp = angle + math.pi / 2
    arrow_len = 0.6
    dx = 0.3 if direction == "right" else -0.3

    # arrow shaft perpendicular
    ex = mx + arrow_len * math.cos(perp) + dx
    ey = my + arrow_len * math.sin(perp)
    c.line(mx * cm, my * cm, ex * cm, ey * cm)

    if label:
        c.setFont("Helvetica", 6)
        c.drawString((mx + 0.3) * cm, (my + 0.3) * cm, label)


def draw_gather_marks(c, x1, y1, x2, y2, n_ticks=8):
    """Gather/ease line: dotted with short perpendicular ticks."""
    c.setStrokeColor(black)
    c.setLineWidth(0.6)
    c.setDash([2, 2], 0)
    c.line(x1 * cm, y1 * cm, x2 * cm, y2 * cm)
    c.setDash([], 0)

    angle = math.atan2(y2 - y1, x2 - x1)
    perp = angle + math.pi / 2
    for i in range(n_ticks):
        t = (i + 1) / (n_ticks + 1)
        tx = x1 + (x2 - x1) * t
        ty = y1 + (y2 - y1) * t
        ex = tx + 0.2 * math.cos(perp)
        ey = ty + 0.2 * math.sin(perp)
        c.line(tx * cm, ty * cm, ex * cm, ey * cm)


def draw_buttonhole(c, cx, cy, length=1.0, horizontal=True):
    """Horizontal or vertical buttonhole marker: rectangle + I-bar ends."""
    c.setStrokeColor(black)
    c.setLineWidth(0.8)
    if horizontal:
        x1, x2 = cx - length / 2, cx + length / 2
        c.rect((x1) * cm, (cy - 0.1) * cm, length * cm, 0.2 * cm)
        c.line(x1 * cm, (cy - 0.25) * cm, x1 * cm, (cy + 0.25) * cm)
        c.line(x2 * cm, (cy - 0.25) * cm, x2 * cm, (cy + 0.25) * cm)
    else:
        y1, y2 = cy - length / 2, cy + length / 2
        c.rect((cx - 0.1) * cm, y1 * cm, 0.2 * cm, length * cm)
        c.line((cx - 0.25) * cm, y1 * cm, (cx + 0.25) * cm, y1 * cm)
        c.line((cx - 0.25) * cm, y2 * cm, (cx + 0.25) * cm, y2 * cm)


def draw_button_placement(c, cx, cy, diameter=1.0):
    """Button position: circle with X through it."""
    c.setStrokeColor(black)
    c.setLineWidth(0.6)
    r = diameter / 2
    c.circle(cx * cm, cy * cm, r * cm)
    c.line((cx - r) * cm, (cy - r) * cm,
           (cx + r) * cm, (cy + r) * cm)
    c.line((cx - r) * cm, (cy + r) * cm,
           (cx + r) * cm, (cy - r) * cm)


def draw_pocket_placement(c, x, y, w, h, label="POCKET"):
    """Pocket location: dashed rectangle with label."""
    c.setStrokeColor(gray)
    c.setLineWidth(0.6)
    c.setDash([4, 2], 0)
    c.rect(x * cm, y * cm, w * cm, h * cm)
    c.setDash([], 0)
    c.setFont("Helvetica-Oblique", 6)
    c.setFillColor(gray)
    c.drawCentredString((x + w / 2) * cm, (y + h / 2) * cm, label)
    c.setFillColor(black)
    c.setStrokeColor(black)


def draw_hem_line(c, x1, y1, x2, y2, fold_depth=2.5, label=None):
    """Hem fold indicator: dashed line showing fold position with arrow."""
    c.setStrokeColor(gray)
    c.setLineWidth(0.5)
    c.setDash([3, 2], 0)
    c.line(x1 * cm, y1 * cm, x2 * cm, y2 * cm)
    c.setDash([], 0)

    # arrow indicating fold direction
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    c.setFont("Helvetica", 5)
    c.setFillColor(gray)
    c.drawCentredString(mx * cm, (my - 0.15) * cm,
                        label or f"HEM FOLD - {fold_depth}cm")
    c.setFillColor(black)
    c.setStrokeColor(black)


def draw_center_line(c, x1, y1, x2, y2, label="CF"):
    """Center front / back indicator: thin dashed line + text."""
    c.setStrokeColor(gray)
    c.setLineWidth(0.3)
    c.setDash([6, 2, 1, 2], 0)
    c.line(x1 * cm, y1 * cm, x2 * cm, y2 * cm)
    c.setDash([], 0)
    c.setStrokeColor(black)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    c.setFont("Helvetica-Oblique", 6)
    c.setFillColor(gray)
    c.drawString((mx + 0.2) * cm, my * cm, label)
    c.setFillColor(black)
