#!/usr/bin/env python3
"""Generate a PowerPoint deck that explains heat vs work as energy transfer
using Morph transitions (PowerPoint 2019 / Microsoft 365).

Every slide re-uses shapes with the same "!!name" so Morph animates the
piston, the gas particles and the energy bars from one slide to the next.

    pip install python-pptx
    python make_heat_work_morph.py
"""
import random
from copy import deepcopy
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

OUT = "heat_vs_work_morph.pptx"

# ---- scenes: (title, caption, piston_y, Q, W, show_heat, work_arrow) ------
# Energy in kJ.  First law (system view): dU = Q - W
BASE_PISTON = 3.8
SCENES = [
    dict(title="A gas in a piston-cylinder: our system",
         caption="Energy can cross the boundary in two ways: heat (Q) or work (W). "
                 "Nothing is crossing yet.",
         piston=BASE_PISTON, Q=0, W=0, heat=False, warrow=None),
    dict(title="1. Heat in, piston locked",
         caption="Q = +8 kJ, no movement so W = 0.  All the energy stays inside: "
                 "molecules speed up (hotter).",
         piston=BASE_PISTON, Q=8, W=0, heat=True, warrow=None),
    dict(title="Reset to the same starting state",
         caption="Same gas, same pressure, same temperature.",
         piston=BASE_PISTON, Q=0, W=0, heat=False, warrow=None),
    dict(title="2. Heat in, piston free to move",
         caption="Q = +8 kJ in, but the gas pushes the load up: W = +5 kJ out. "
                 "Only 3 kJ is left to raise the internal energy.",
         piston=3.0, Q=8, W=5, heat=True, warrow="up"),
    dict(title="Reset to the same starting state",
         caption="Same gas, same pressure, same temperature.",
         piston=BASE_PISTON, Q=0, W=0, heat=False, warrow=None),
    dict(title="3. Insulated, compress the gas",
         caption="No heat flows (Q = 0). The load pushes the piston down: work is done ON "
                 "the gas (W = -6 kJ), so the gas still gets hotter.",
         piston=4.6, Q=0, W=-6, heat=False, warrow="down"),
    dict(title="Heat and work are both energy in transit",
         caption="Neither is stored in the gas. What the gas stores is internal energy U.",
         piston=BASE_PISTON, Q=0, W=0, heat=False, warrow=None, summary=True),
]

# ---- geometry (inches) ----------------------------------------------------
CYL_L, CYL_R, CYL_TOP, CYL_BOT = 1.2, 4.8, 1.9, 6.3
WALL = 0.12
BASELINE, SCALE = 4.6, 0.22        # bar chart baseline y and inches per kJ
BAR_X = {"Q": 7.6, "W": 9.2, "dU": 10.8}
BAR_W = 1.0

NAVY = RGBColor(0x1F, 0x2A, 0x44)
GREY = RGBColor(0x8A, 0x93, 0xA3)
LIGHT = RGBColor(0xE8, 0xEC, 0xF2)
RED = RGBColor(0xD9, 0x48, 0x2B)
BLUE = RGBColor(0x2F, 0x6F, 0xBF)
GREEN = RGBColor(0x2E, 0x8B, 0x57)
PURPLE = RGBColor(0x7A, 0x4F, 0xB5)


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return RGBColor(*[int(a + (b - a) * t) for a, b in zip(c1, c2)])


def add(slide, shape, name, l, t, w, h, fill=None, line=None):
    s = slide.shapes.add_shape(shape, Inches(l), Inches(t), Inches(w), Inches(h))
    s.name = name
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.5)
    s.shadow.inherit = False
    return s


def text(slide, name, l, t, w, h, txt, size, color=NAVY, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = txt
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = "Calibri"
    return tb


def add_morph(slide):
    """Insert a Morph transition (falls back to fade in older PowerPoint)."""
    xml = (
        '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        '<mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" Requires="p159">'
        '<p:transition spd="slow" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" p14:dur="1800">'
        '<p159:morph option="byObject"/></p:transition></mc:Choice>'
        '<mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback>'
        '</mc:AlternateContent>'
    )
    el = etree.fromstring(xml)
    sld = slide._element
    clr = sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}clrMapOvr")
    if clr is not None:
        clr.addnext(el)
    else:
        sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}cSld").addnext(el)


def particle_positions(piston_y, seed_shift):
    """Fixed seed per particle, positions re-drawn inside the gas box so
    Morph makes them 'jiggle' between slides."""
    rng = random.Random(seed_shift)
    top = piston_y + 0.3
    bot = CYL_BOT - 0.25
    pts = []
    for _ in range(14):
        pts.append((rng.uniform(CYL_L + WALL + 0.1, CYL_R - WALL - 0.4),
                    rng.uniform(top, bot - 0.15)))
    return pts


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    for i, sc in enumerate(SCENES):
        s = prs.slides.add_slide(blank)
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        text(s, "!!title", 0.6, 0.3, 12.1, 0.7, sc["title"], 30, bold=True)
        text(s, "!!caption", 0.6, 1.0, 12.1, 0.8, sc["caption"], 16, color=GREY)

        dU = sc["Q"] - sc["W"]
        warmth = (dU + 0) / 8.0   # 0 (cold, blue) .. 1 (hot, red)
        gas_col = mix(RGBColor(0xDD, 0xEA, 0xF8), RGBColor(0xFB, 0xD9, 0xCF), warmth)
        p_col = mix(BLUE, RED, warmth)

        py = sc["piston"]
        # gas volume
        add(s, MSO_SHAPE.RECTANGLE, "!!gas", CYL_L + WALL, py + 0.2,
            CYL_R - CYL_L - 2 * WALL, CYL_BOT - py - 0.2 - WALL, fill=gas_col)
        # particles
        for k, (x, y) in enumerate(particle_positions(py, 100 + i * 7)):
            add(s, MSO_SHAPE.OVAL, f"!!p{k}", x, y, 0.22, 0.22, fill=p_col)
        # cylinder walls
        add(s, MSO_SHAPE.RECTANGLE, "!!wallL", CYL_L, CYL_TOP, WALL, CYL_BOT - CYL_TOP, fill=NAVY)
        add(s, MSO_SHAPE.RECTANGLE, "!!wallR", CYL_R - WALL, CYL_TOP, WALL, CYL_BOT - CYL_TOP, fill=NAVY)
        add(s, MSO_SHAPE.RECTANGLE, "!!base", CYL_L, CYL_BOT - WALL, CYL_R - CYL_L, WALL + 0.02, fill=NAVY)
        # piston, rod, load
        mid = (CYL_L + CYL_R) / 2
        add(s, MSO_SHAPE.RECTANGLE, "!!piston", CYL_L + WALL, py, CYL_R - CYL_L - 2 * WALL, 0.2, fill=GREY)
        add(s, MSO_SHAPE.RECTANGLE, "!!rod", mid - 0.06, py - 0.8, 0.12, 0.8, fill=GREY)
        load = add(s, MSO_SHAPE.RECTANGLE, "!!load", mid - 0.55, py - 1.3, 1.1, 0.5, fill=PURPLE)
        load.text_frame.text = "load"
        for r in load.text_frame.paragraphs[0].runs:
            r.font.size = Pt(14)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        # heat in (flame / arrow)
        if sc["heat"]:
            add(s, MSO_SHAPE.UP_ARROW, "!!heatArrow", mid - 0.45, CYL_BOT + 0.1, 0.9, 0.8, fill=RED)
            text(s, "!!heatLabel", mid + 0.6, CYL_BOT + 0.25, 1.6, 0.5, "Q in (heat)", 16,
                 color=RED, bold=True)
        # work arrow
        if sc["warrow"] == "up":
            add(s, MSO_SHAPE.UP_ARROW, "!!workArrow", CYL_R + 0.25, py - 1.0, 0.6, 0.9, fill=PURPLE)
            text(s, "!!workLabel", CYL_R + 0.9, py - 0.8, 2.0, 0.5, "W out", 15,
                 color=PURPLE, bold=True)
        elif sc["warrow"] == "down":
            add(s, MSO_SHAPE.DOWN_ARROW, "!!workArrow", CYL_R + 0.25, py - 1.0, 0.6, 0.9, fill=PURPLE)
            text(s, "!!workLabel", CYL_R + 0.9, py - 0.8, 2.0, 0.5, "W on gas", 15,
                 color=PURPLE, bold=True)

        # ---- energy bar chart ----
        add(s, MSO_SHAPE.RECTANGLE, "!!axis", 7.2, BASELINE - 0.01, 5.6, 0.03, fill=GREY)
        text(s, "!!barTitle", 7.2, 1.9, 5.6, 0.4, "Energy bookkeeping (kJ)", 16, bold=True)

        def bar(key, value, color, label):
            h = max(abs(value) * SCALE, 0.02)
            top = BASELINE - h if value >= 0 else BASELINE
            add(s, MSO_SHAPE.RECTANGLE, f"!!bar{key}", BAR_X[key], top, BAR_W, h, fill=color)
            sign = "+" if value > 0 else ""
            text(s, f"!!val{key}", BAR_X[key] - 0.3, 6.1, BAR_W + 0.6, 0.35,
                 f"{sign}{value}", 18, color=color, bold=True, align=PP_ALIGN.CENTER)
            text(s, f"!!lab{key}", BAR_X[key] - 0.3, 6.45, BAR_W + 0.6, 0.5,
                 label, 14, color=NAVY, align=PP_ALIGN.CENTER)

        bar("Q", sc["Q"], RED, "Q  heat in")
        bar("W", sc["W"], PURPLE, "W  work out")
        bar("dU", dU, GREEN, "ΔU  stored")

        # first-law equation
        eq = "ΔU  =  Q  −  W"
        text(s, "!!eq", 7.2, 2.3, 5.6, 0.6, eq, 28, bold=True)

        if sc.get("summary"):
            text(s, "!!sum", 7.2, 2.9, 5.6, 1.2,
                 "Heat: energy moved by a temperature difference.\n"
                 "Work: energy moved by a force through a distance.",
                 15, color=NAVY)

        add_morph(s) if i > 0 else None
    prs.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
