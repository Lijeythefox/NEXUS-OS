"""
NEXUS cyberdeck case + breadboard module  -  Fusion 360 script
==============================================================

HOW TO USE
  1. In Fusion 360 open  Utilities > Add-Ins > Scripts and Add-Ins.
  2. Add this folder (the one holding NexusCase.py and NexusCase.manifest).
  3. Select "NexusCase" and press Run. A new design is created with one
     component per printed part. Building the breadboard grid takes a minute.

TO CHANGE A SIZE
  Edit a number in the P = dict(...) block below, save, and run the script
  again. All sizes are in millimetres.

Every size marked MEASURE is a placeholder for a part that has not been
measured yet. Measure the real part and update it before printing.
"""

# ----------------------------------------------------------------------------
# SIZES (mm)
# ----------------------------------------------------------------------------
P = dict(
    # ---- breadboard module -------------------------------------------------
    mod_L=195.0,        # module length (fills both slots)
    mod_W=88.0,         # module depth
    mod_r=3.0,          # corner radius
    mod_wall=2.0,       # skirt wall thickness
    slab_t=8.5,         # thickness of the top slab that holds the clips
    skirt_h=8.9,        # room under the slab for the PCB (1.6) and its parts
    cover_t=2.6,        # bottom cover thickness
    pcb_t=1.6,
    pitch=2.54,         # hole spacing
    hole=1.25,          # MEASURE square hole size (test piece checks this)
    hole_lead=1.9,      # wider lead-in at the very top of each hole
    lead_d=0.4,
    skin=1.2,           # plastic left above the clips
    slot_w=2.1,         # MEASURE clip slot width (test piece has 2.0 / 2.1 / 2.2)
    slot_over=1.45,     # MEASURE how far a slot runs past the first/last hole
    bb_x0=9.0,          # x of terminal column 1
    bb_yc=31.5,         # y of the breadboard centre line
    cols=63,            # terminal columns (full-size breadboard)
    rail_groups=10,     # groups of 5 holes per power rail
    pin_cols=40,        # pin section: 40 pins, 4 holes each (female headers)
    pin_rows=4,
    pin_y0=66.5,        # front edge of the header window
    screw_pilot=2.1,    # pilot hole for M2.5 self-tapping screws
    screw_clear=2.9,
    magnet_d=6.2,       # 6 x 2 mm disc magnets
    magnet_h=2.1,
    pogo_w=16.0,        # MEASURE opening for the 4-pin magnetic pogo connector
    pogo_h=7.0,
    # ---- controller tray ---------------------------------------------------
    tray_L=97.2,
    pad_L=74.0,         # 8BitDo Zero 2 is 73 x 36.5 x 14.7
    pad_W=37.5,
    pad_depth=13.0,
    # ---- deck --------------------------------------------------------------
    deck_W=250.0,
    deck_D=208.0,
    base_h=30.6,        # base tub height (deck plate sits on top)
    plate_t=2.4,
    wall=3.0,
    floor=2.4,
    deck_r=5.0,
    bay_x0=8.0,         # module bay inner corner
    bay_y0=111.0,
    bay_clear=0.4,      # gap around the module
    bay_floor=3.0,
    kb_x0=10.2, kb_y0=12.0, kb_w=229.6, kb_d=96.25,   # MEASURE keyboard opening
    kb_post_top=19.0,   # MEASURE height of the keyboard support posts
    ball_x=228.0, ball_y=185.0, ball_d=30.0,          # MEASURE trackball opening
    lid_h=18.0,         # MEASURE lid thickness (depends on screen depth)
    scr_w=164.9, scr_h=124.27,                        # Waveshare 7" (H) outline
    scr_view_w=156.0, scr_view_h=88.0,                # MEASURE visible window
    scr_cx=125.0, scr_cy=108.0,
    hinge_y=213.5,      # hinge axis behind the back wall
    hinge_d=10.0,
    hinge_pin=3.3,      # M3 bolt
)

MAKE_HOLES = True       # set False for a quick build without the 830 holes

PIN_LABELS = ["GND", "GP0", "GP1", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GND",
              "GP8", "GP9", "GP10", "GP11", "GP12", "GP13", "GP14", "GP15", "GND",
              "GP16", "GP17", "GP18", "GP19", "GP20", "GP21", "GP22", "GND",
              "GP26", "GP27", "GP28", "GND", "RUN", "GND", "3V3", "3V3", "5V", "5V",
              "ADJA", "ADJB", "GND"]

MOD_SCREWS = [(5.0, 5.0), (190.0, 5.0), (5.0, 83.0), (190.0, 83.0), (97.5, 5.0), (97.5, 83.0)]
MOD_MAGNETS = [(30.0, 22.0), (165.0, 22.0), (30.0, 66.0), (165.0, 66.0)]
POGO_C = (150.0, 31.5)


# ----------------------------------------------------------------------------
# GEOMETRY PLAN (plain Python, no Fusion calls)
#   ("box", x0,y0,z0, x1,y1,z1, r)          first solid, vertical corners rounded
#   ("add_box"/"cut_box", x0,y0,z0, x1,y1,z1)
#   ("add_cyl"/"cut_cyl", cx,cy, z0,z1, d)  upright cylinder
#   ("cut_rects", z0,z1, [(x0,y0,x1,y1), ...])
#   ("cut_circles", z0,z1, [(cx,cy,d), ...])
#   ("add_cylx"/"cut_cylx", x0,x1, cy,cz, d) cylinder lying along X
# ----------------------------------------------------------------------------
def grid_points(p=P, x0=None, yc=None, cols=None, groups=None):
    """Hole centres: (terminal holes, rail holes)."""
    x0 = p["bb_x0"] if x0 is None else x0
    yc = p["bb_yc"] if yc is None else yc
    cols = p["cols"] if cols is None else cols
    groups = p["rail_groups"] if groups is None else groups
    pt = p["pitch"]
    term = []
    for i in range(cols):
        for k in range(5):
            off = 1.5 * pt + k * pt
            term.append((x0 + i * pt, yc + off))
            term.append((x0 + i * pt, yc - off))
    span_t = (cols - 1) * pt
    span_r = ((groups - 1) * 6 + 4) * pt
    xr0 = x0 + span_t / 2.0 - span_r / 2.0
    rail = []
    for g in range(groups):
        for i in range(5):
            x = xr0 + (g * 6 + i) * pt
            for off in (8.0 * pt, 9.0 * pt):
                rail.append((x, yc + off))
                rail.append((x, yc - off))
    return term, rail, xr0, span_r


def grid_ops(p, z_slab0, z_top, x0=None, yc=None, cols=None, groups=None, slot_w=None):
    """Clip slots (open underneath) and square holes through the top skin."""
    x0 = p["bb_x0"] if x0 is None else x0
    yc = p["bb_yc"] if yc is None else yc
    cols = p["cols"] if cols is None else cols
    slot_w = p["slot_w"] if slot_w is None else slot_w
    pt, so = p["pitch"], p["slot_over"]
    term, rail, xr0, span_r = grid_points(p, x0, yc, cols, groups)
    z_skin = z_top - p["skin"]
    slots = []
    for i in range(cols):
        x = x0 + i * pt
        slots.append((x - slot_w / 2, yc + 1.5 * pt - so, x + slot_w / 2, yc + 5.5 * pt + so))
        slots.append((x - slot_w / 2, yc - 5.5 * pt - so, x + slot_w / 2, yc - 1.5 * pt + so))
    if rail:
        for off in (8.0 * pt, 9.0 * pt):
            for s in (1, -1):
                y = yc + s * off
                slots.append((xr0 - so, y - slot_w / 2, xr0 + span_r + so, y + slot_w / 2))
    ops = [("cut_rects", z_slab0, z_skin, slots)]
    if MAKE_HOLES:
        h, hl = p["hole"] / 2, p["hole_lead"] / 2
        pts = term + rail
        ops.append(("cut_rects", z_skin, z_top, [(x - h, y - h, x + h, y + h) for x, y in pts]))
        ops.append(("cut_rects", z_top - p["lead_d"], z_top,
                    [(x - hl, y - hl, x + hl, y + hl) for x, y in pts]))
    return ops


def part_bb_body(p=P):
    L, W = p["mod_L"], p["mod_W"]
    z0 = p["skirt_h"]
    zt = z0 + p["slab_t"]
    w = p["mod_wall"]
    ops = [("box", 0, 0, 0, L, W, zt, p["mod_r"]),
           ("cut_box", w, w, 0, L - w, W - w, z0)]
    ops += grid_ops(p, z0, zt)
    # pin section: window for a 4 x 40 block of female headers soldered to the PCB
    pcx = p["bb_x0"] + (p["cols"] - 1) * p["pitch"] / 2
    hw = (p["pin_cols"] * p["pitch"] + 0.4) / 2
    py0, py1 = p["pin_y0"], p["pin_y0"] + p["pin_rows"] * p["pitch"] + 0.4
    ops.append(("cut_box", pcx - hw, py0, z0, pcx + hw, py1, zt))
    ops.append(("cut_box", pcx - hw - 0.5, 57.0, zt - 0.3, pcx + hw + 0.5, 65.2, zt))   # label strip
    # controls: thin skin over a pocket for the switches, thumbwheels and buttons
    ops.append(("cut_box", 171, 8, z0, 189, 80, zt - 1.6))
    ops.append(("cut_box", 172, 9, zt - 0.3, 188, 79, zt))                              # label area
    ops.append(("cut_rects", zt - 1.6, zt, [
        (175.0, 14.0, 185.0, 18.0),      # bottom rail switch (3.3V / ADJ / 5V)
        (174.5, 26.0, 185.5, 30.0),      # bottom rail knob (thumbwheel)
        (174.5, 58.0, 185.5, 62.0),      # top rail knob (thumbwheel)
        (175.0, 70.0, 185.0, 74.0),      # top rail switch
    ]))
    ops.append(("cut_circles", zt - 1.6, zt, [
        (176.5, 44.0, 3.6),              # BOOT button
        (183.5, 44.0, 3.6),              # RESET button
        (180.0, 37.0, 2.2),              # rails-on LED
    ]))
    ops.append(("cut_circles", z0, z0 + 6.0, [(x, y, p["screw_pilot"]) for x, y in MOD_SCREWS]))
    ops.append(("cut_box", L - 2.5, 4, z0 + 1.6, L, 24, z0 + 5.6))                      # finger groove
    return dict(name="bb_body", ops=ops,
                place=(p["bay_x0"] + p["bay_clear"], p["bay_y0"] + p["bay_clear"],
                       p["base_h"] + p["plate_t"] - p["skirt_h"] - p["slab_t"]),
                flip=True)


def part_bb_cover(p=P):
    L, W, t = p["mod_L"], p["mod_W"], p["cover_t"]
    post_top = t + p["skirt_h"] - p["pcb_t"]
    ops = [("box", 0, 0, 0, L, W, t, p["mod_r"])]
    for x, y in MOD_SCREWS:
        ops.append(("add_cyl", x, y, t, post_top, 5.0))
    ops.append(("cut_circles", 0, post_top, [(x, y, p["screw_clear"]) for x, y in MOD_SCREWS]))
    ops.append(("cut_circles", 0, 1.4, [(x, y, 5.4) for x, y in MOD_SCREWS]))
    ops.append(("cut_circles", 0, p["magnet_h"], [(x, y, p["magnet_d"]) for x, y in MOD_MAGNETS]))
    ops.append(("cut_box", POGO_C[0] - p["pogo_w"] / 2, POGO_C[1] - p["pogo_h"] / 2, 0,
                POGO_C[0] + p["pogo_w"] / 2, POGO_C[1] + p["pogo_h"] / 2, t))
    return dict(name="bb_cover", ops=ops,
                place=(p["bay_x0"] + p["bay_clear"], p["bay_y0"] + p["bay_clear"],
                       p["base_h"] + p["plate_t"] - p["skirt_h"] - p["slab_t"] - t),
                flip=False)


def part_clip_test(p=P):
    """Small test piece: 3 terminal columns at each slot width, plus short rail slots."""
    L, W, t = 38.0, 27.0, p["slab_t"]
    pt, so = p["pitch"], p["slot_over"]
    ops = [("box", 0, 0, 0, L, W, t, 1.5)]
    slots, holes, leads = [], [], []
    h, hl = p["hole"] / 2, p["hole_lead"] / 2
    for g, sw in enumerate((2.0, 2.1, 2.2)):
        for i in range(3):
            x = 6.0 + g * 4 * pt + i * pt
            slots.append((x - sw / 2, 11.0 - so, x + sw / 2, 11.0 + 4 * pt + so))
            for k in range(5):
                holes.append((x, 11.0 + k * pt))
        for n in range(g + 1):                           # 1, 2 or 3 notches mark the width
            ops.append(("cut_box", 5.0 + g * 4 * pt + n * 2.0, W - 1.0, 0,
                        6.0 + g * 4 * pt + n * 2.0, W, t))
    for g, sw in enumerate((2.0, 2.2)):
        xa = 6.0 + g * 16.0
        slots.append((xa - so, 4.5 - sw / 2, xa + 4 * pt + so, 4.5 + sw / 2))
        for i in range(5):
            holes.append((xa + i * pt, 4.5))
    ops.append(("cut_rects", 0, t - p["skin"], slots))
    ops.append(("cut_rects", t - p["skin"], t, [(x - h, y - h, x + h, y + h) for x, y in holes]))
    ops.append(("cut_rects", t - p["lead_d"], t, [(x - hl, y - hl, x + hl, y + hl) for x, y in holes]))
    return dict(name="clip_test", ops=ops, place=(270, 20, 0), flip=True)


def part_tray(p=P, name="controller_tray", place=(270, 111.4, 0)):
    L, W, H = p["tray_L"], p["mod_W"], p["skirt_h"] + p["slab_t"] + p["cover_t"]
    cx, cy = L / 2, 60.0
    ops = [("box", 0, 0, 0, L, W, H, p["mod_r"]),
           ("cut_box", cx - p["pad_L"] / 2, cy - p["pad_W"] / 2, H - p["pad_depth"],
            cx + p["pad_L"] / 2, cy + p["pad_W"] / 2, H),
           ("cut_circles", H - p["pad_depth"], H, [(cx - p["pad_L"] / 2, cy, 16.0),
                                                   (cx + p["pad_L"] / 2, cy, 16.0)]),
           ("cut_box", 6, 6, 3.0, L - 6, 36, H),                     # jumper wire bin
           ("cut_circles", 0, p["magnet_h"], [(30.0, 66.0, p["magnet_d"]),
                                              (165.0 - (p["mod_L"] - L), 66.0, p["magnet_d"])]),
           ("cut_box", L - 2.5, 4, 10.5, L, 24, 14.5)]               # finger groove
    return dict(name=name, ops=ops, place=place, flip=False)


def _knuckle(p, x0, x1, z0, z1, lid):
    hy, r = p["hinge_y"], p["hinge_d"] / 2
    D = p["deck_D"]
    top = p["base_h"] + p["plate_t"]
    ops = []
    if lid:
        ops.append(("add_box", x0, D, z0, x1, hy + r, z1))
    else:
        ops.append(("add_box", x0, D, z0, x1, hy + r, p["base_h"]))
        ops.append(("add_box", x0, D + 0.4, p["base_h"], x1, hy + r, top))
    ops.append(("add_cylx", x0, x1, hy, top, p["hinge_d"]))
    ops.append(("cut_cylx", x0 - 0.1, x1 + 0.1, hy, top, p["hinge_pin"]))
    return ops


def _bay(p):
    c = p["bay_clear"]
    bx0, by0 = p["bay_x0"], p["bay_y0"]
    bx1, by1 = bx0 + p["mod_L"] + 2 * c, by0 + p["mod_W"] + 2 * c
    top = p["base_h"] + p["plate_t"]
    mod_h = p["skirt_h"] + p["slab_t"] + p["cover_t"]
    zf = top - mod_h - 0.2            # top of the bay floor
    return bx0, by0, bx1, by1, zf, zf - p["bay_floor"]


PLATE_SCREWS = [(7.0, 7.0), (243.0, 7.0), (125.0, 7.0), (243.0, 201.0)]
BAY_SCREWS_LOCAL = [(60.0, 44.0), (135.0, 44.0)]


def _to_bay(p, pts):
    ox, oy = p["bay_x0"] + p["bay_clear"], p["bay_y0"] + p["bay_clear"]
    return [(x + ox, y + oy) for x, y in pts]


def part_base(p=P):
    Wd, D, H = p["deck_W"], p["deck_D"], p["base_h"]
    w, f = p["wall"], p["floor"]
    bx0, by0, bx1, by1, zf, zu = _bay(p)
    ops = [("box", 0, 0, 0, Wd, D, H, p["deck_r"]),
           ("cut_box", w, w, f, Wd - w, D - w, H)]
    for x, y in PLATE_SCREWS:
        ops.append(("add_cyl", x, y, f, H, 9.0))
    for x, y in _to_bay(p, BAY_SCREWS_LOCAL):
        ops.append(("add_cyl", x, y, f, zu, 8.0))
    kb = [(16.0, 18.0), (234.0, 18.0), (16.0, 102.0), (234.0, 102.0)]
    for x, y in kb:
        ops.append(("add_cyl", x, y, f, p["kb_post_top"], 7.0))
    ops += _knuckle(p, 30.0, 42.0, 0, H, lid=False)
    ops += _knuckle(p, 208.0, 220.0, 0, H, lid=False)
    ops.append(("cut_circles", H - 10.0, H, [(x, y, 2.5) for x, y in PLATE_SCREWS]))
    ops.append(("cut_circles", f + 1.0, zu, [(x, y, 2.5) for x, y in _to_bay(p, BAY_SCREWS_LOCAL)]))
    ops.append(("cut_circles", p["kb_post_top"] - 8.0, p["kb_post_top"], [(x, y, 2.5) for x, y in kb]))
    # MEASURE: port openings in the left wall (USB-C power, 2 x USB-A, micro SD)
    ops.append(("cut_box", 0, 25.3, 10.2, w, 34.7, 13.8))
    ops.append(("cut_box", 0, 43.2, 9.0, w, 56.8, 15.0))
    ops.append(("cut_box", 0, 63.2, 9.0, w, 76.8, 15.0))
    ops.append(("cut_box", 0, 83.7, 10.9, w, 96.3, 13.1))
    ops.append(("cut_cylx", Wd - w - 0.1, Wd, 60.0, 16.0, 12.0))     # power button, right wall
    return dict(name="deck_base", ops=ops, place=(0, 0, 0), flip=False)


def part_plate(p=P):
    Wd, D, H, t = p["deck_W"], p["deck_D"], p["base_h"], p["plate_t"]
    top = H + t
    bx0, by0, bx1, by1, zf, zu = _bay(p)
    ops = [("box", 0, 0, H, Wd, D, top, p["deck_r"]),
           ("cut_box", bx0, by0, H, bx1, by1, top),                          # module bay opening
           ("cut_cyl", bx1 + 2, 125, H, top, 22.0),                          # finger scoop
           ("cut_box", p["kb_x0"], p["kb_y0"], H, p["kb_x0"] + p["kb_w"], p["kb_y0"] + p["kb_d"], top),
           ("cut_cyl", p["ball_x"], p["ball_y"], H, top, p["ball_d"]),
           ("cut_rects", H, top, [(212, 146, 224, 164), (230, 146, 242, 164)]),   # mouse buttons
           ("cut_circles", H, top, [(x, y, 3.4) for x, y in PLATE_SCREWS]),
           ("cut_circles", top - 1.2, top, [(x, y, 6.4) for x, y in PLATE_SCREWS])]
    return dict(name="deck_plate", ops=ops, place=(0, 0, 0), flip=False)


def part_bay(p=P):
    """Tub that the module or the trays drop into. Sits on the base posts, under the plate."""
    H = p["base_h"]
    bx0, by0, bx1, by1, zf, zu = _bay(p)
    ops = [("box", bx0 - 2, by0 - 2, zu, bx1 + 2, by1 + 2, H, 0),
           ("add_box", bx1, 113, zu, bx1 + 14.2, 137, H),                    # finger scoop cup
           ("cut_box", bx0, by0, zf, bx1, by1, H),
           ("cut_cyl", bx1 + 2, 125, 20, H, 22.0),
           ("cut_circles", zu, zf, [(x, y, 3.4) for x, y in _to_bay(p, BAY_SCREWS_LOCAL)]),
           ("cut_circles", zf - 1.8, zf, [(x, y, 6.4) for x, y in _to_bay(p, BAY_SCREWS_LOCAL)]),
           ("cut_circles", zf - p["magnet_h"], zf, [(x, y, p["magnet_d"]) for x, y in _to_bay(p, MOD_MAGNETS)])]
    px, py = _to_bay(p, [POGO_C])[0]
    ops.append(("cut_box", px - p["pogo_w"] / 2, py - p["pogo_h"] / 2, zu,
                px + p["pogo_w"] / 2, py + p["pogo_h"] / 2, zf))
    return dict(name="module_bay", ops=ops, place=(0, 0, 0), flip=False)


LID_SCREWS = [(7.0, 7.0), (243.0, 7.0), (7.0, 201.0), (243.0, 201.0), (125.0, 7.0), (125.0, 201.0)]


def part_lid_bezel(p=P):
    Wd, D = p["deck_W"], p["deck_D"]
    z0 = p["base_h"] + p["plate_t"]
    z1 = z0 + 2.4
    cx, cy = p["scr_cx"], p["scr_cy"]
    vw, vh = p["scr_view_w"] / 2, p["scr_view_h"] / 2
    sw, sh = p["scr_w"] / 2 + 0.3, p["scr_h"] / 2 + 0.3
    fr = 1.6
    ops = [("box", 0, 0, z0, Wd, D, z1, p["deck_r"]),
           ("cut_box", cx - vw, cy - vh, z0, cx + vw, cy + vh, z1),
           # frame that locates the screen behind the window
           ("add_box", cx - sw - fr, cy - sh - fr, z1, cx + sw + fr, cy - sh, z1 + 4.0),
           ("add_box", cx - sw - fr, cy + sh, z1, cx + sw + fr, cy + sh + fr, z1 + 4.0),
           ("add_box", cx - sw - fr, cy - sh, z1, cx - sw, cy + sh, z1 + 4.0),
           ("add_box", cx + sw, cy - sh, z1, cx + sw + fr, cy + sh, z1 + 4.0)]
    slots = []
    for i in range(5):
        for xc in (14.0 + i * 4.0, Wd - 14.0 - i * 4.0):
            slots.append((xc - 0.8, cy - 11, xc + 0.8, cy + 11))            # speaker grilles
    ops.append(("cut_rects", z0, z1, slots))
    ops.append(("cut_circles", z0, z1, [(x, y, 3.4) for x, y in LID_SCREWS]))
    ops.append(("cut_circles", z0, z0 + 1.2, [(x, y, 6.4) for x, y in LID_SCREWS]))
    return dict(name="lid_bezel", ops=ops, place=(0, 0, 60), flip=False)


def part_lid_back(p=P):
    Wd, D, w = p["deck_W"], p["deck_D"], p["wall"]
    zc = p["base_h"] + p["plate_t"]
    z0 = zc + 2.4
    z1 = zc + p["lid_h"]
    ops = [("box", 0, 0, z0, Wd, D, z1, p["deck_r"]),
           ("cut_box", w, w, z0, Wd - w, D - w, z1 - 2.4)]
    for x, y in LID_SCREWS:
        ops.append(("add_cyl", x, y, z0, z1 - 2.4, 9.0))
    ops += _knuckle(p, 42.4, 54.0, z0, z1, lid=True)
    ops += _knuckle(p, 196.0, 207.6, z0, z1, lid=True)
    ops.append(("cut_circles", z0, z0 + 9.0, [(x, y, 2.5) for x, y in LID_SCREWS]))
    return dict(name="lid_back", ops=ops, place=(0, 0, 60), flip=True)


def build_parts(p=P):
    return [part_base(p), part_bay(p), part_plate(p), part_bb_cover(p), part_bb_body(p),
            part_lid_bezel(p), part_lid_back(p),
            part_tray(p, "controller_tray_1", (270, 111.4, 0)),
            part_tray(p, "controller_tray_2", (380, 111.4, 0)),
            part_clip_test(p)]


# ----------------------------------------------------------------------------
# FUSION 360 BUILDER
# ----------------------------------------------------------------------------
try:
    import adsk.core
    import adsk.fusion
    import traceback
    _IN_FUSION = True
except ImportError:
    _IN_FUSION = False

CM = 0.1   # Fusion's API works in centimetres


def _vi(mm):
    return adsk.core.ValueInput.createByReal(mm * CM)


def _plane(comp, base, offset_mm):
    planes = comp.constructionPlanes
    inp = planes.createInput()
    inp.setByOffset(base, _vi(offset_mm))
    pl = planes.add(inp)
    pl.isLightBulbOn = False
    return pl


def _pt(sk, x, y, z):
    return sk.modelToSketchSpace(adsk.core.Point3D.create(x * CM, y * CM, z * CM))


def _extrude(comp, sk, length_mm, cut, first):
    profs = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        profs.add(sk.profiles.item(i))
    feats = comp.features.extrudeFeatures
    if first:
        op = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    elif cut:
        op = adsk.fusion.FeatureOperations.CutFeatureOperation
    else:
        op = adsk.fusion.FeatureOperations.JoinFeatureOperation
    inp = feats.createInput(profs, op)
    inp.setSymmetricExtent(_vi(length_mm), True)
    if not first and comp.bRepBodies.count > 0:
        try:
            inp.participantBodies = [comp.bRepBodies.item(0)]
        except Exception:
            pass
    feat = feats.add(inp)
    sk.isLightBulbOn = False
    return feat


def _rects(comp, z0, z1, rects, cut, first=False):
    zm = (z0 + z1) / 2.0
    sk = comp.sketches.add(_plane(comp, comp.xYConstructionPlane, zm))
    sk.isComputeDeferred = True
    lines = sk.sketchCurves.sketchLines
    for (x0, y0, x1, y1) in rects:
        lines.addTwoPointRectangle(_pt(sk, x0, y0, zm), _pt(sk, x1, y1, zm))
    sk.isComputeDeferred = False
    return _extrude(comp, sk, z1 - z0, cut, first)


def _circles(comp, z0, z1, circles, cut):
    zm = (z0 + z1) / 2.0
    sk = comp.sketches.add(_plane(comp, comp.xYConstructionPlane, zm))
    sk.isComputeDeferred = True
    cs = sk.sketchCurves.sketchCircles
    for (cx, cy, d) in circles:
        cs.addByCenterRadius(_pt(sk, cx, cy, zm), d / 2.0 * CM)
    sk.isComputeDeferred = False
    return _extrude(comp, sk, z1 - z0, cut, False)


def _cylx(comp, x0, x1, cy, cz, d, cut):
    xm = (x0 + x1) / 2.0
    sk = comp.sketches.add(_plane(comp, comp.yZConstructionPlane, xm))
    sk.sketchCurves.sketchCircles.addByCenterRadius(_pt(sk, xm, cy, cz), d / 2.0 * CM)
    return _extrude(comp, sk, x1 - x0, cut, False)


def _round_corners(comp, r_mm):
    body = comp.bRepBodies.item(0)
    edges = adsk.core.ObjectCollection.create()
    for e in body.edges:
        if e.geometry.curveType != adsk.core.Curve3DTypes.Line3DCurveType:
            continue
        a, b = e.startVertex.geometry, e.endVertex.geometry
        if abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) < 1e-6:
            edges.add(e)
    fil = comp.features.filletFeatures
    inp = fil.createInput()
    try:
        inp.edgeSetInputs.addConstantRadiusEdgeSet(edges, _vi(r_mm), False)
    except Exception:
        inp.addConstantRadiusEdgeSet(edges, _vi(r_mm), False)
    fil.add(inp)


def _do_op(comp, op):
    k = op[0]
    if k == "box":
        _, x0, y0, z0, x1, y1, z1, r = op
        _rects(comp, z0, z1, [(x0, y0, x1, y1)], cut=False, first=True)
        if r > 0:
            try:
                _round_corners(comp, r)
            except Exception:
                pass                      # square corners are fine if the fillet fails
    elif k in ("add_box", "cut_box"):
        _, x0, y0, z0, x1, y1, z1 = op
        _rects(comp, z0, z1, [(x0, y0, x1, y1)], cut=(k == "cut_box"))
    elif k in ("add_cyl", "cut_cyl"):
        _, cx, cy, z0, z1, d = op
        _circles(comp, z0, z1, [(cx, cy, d)], cut=(k == "cut_cyl"))
    elif k == "cut_rects":
        _, z0, z1, rects = op
        _rects(comp, z0, z1, rects, cut=True)
    elif k == "cut_circles":
        _, z0, z1, circles = op
        _circles(comp, z0, z1, circles, cut=True)
    elif k in ("add_cylx", "cut_cylx"):
        _, x0, x1, cy, cz, d = op
        _cylx(comp, x0, x1, cy, cz, d, cut=(k == "cut_cylx"))
    else:
        raise ValueError("unknown op " + str(k))


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        parts = build_parts(P)
        total = sum(len(pt["ops"]) for pt in parts)
        prog = ui.createProgressDialog()
        prog.isBackgroundTranslucent = False
        prog.show("NEXUS case", "Building %v of %m steps", 0, total)
        done, problems = 0, []

        for part in parts:
            m = adsk.core.Matrix3D.create()
            dx, dy, dz = part["place"]
            m.translation = adsk.core.Vector3D.create(dx * CM, dy * CM, dz * CM)
            occ = root.occurrences.addNewComponent(m)
            comp = occ.component
            comp.name = part["name"]
            for i, op in enumerate(part["ops"]):
                try:
                    _do_op(comp, op)
                except Exception:
                    problems.append("%s step %d (%s): %s" % (
                        part["name"], i + 1, op[0], traceback.format_exc().splitlines()[-1]))
                done += 1
                prog.progressValue = done
                adsk.doEvents()
                if prog.wasCancelled:
                    break
            if comp.bRepBodies.count > 0:
                comp.bRepBodies.item(0).name = part["name"]
            if prog.wasCancelled:
                break

        prog.hide()
        app.activeViewport.fit()
        if problems:
            ui.messageBox("Finished with %d problem(s). Copy this text and send it to Claude:\n\n%s"
                          % (len(problems), "\n".join(problems[:25])))
        else:
            ui.messageBox("NEXUS case built: %d parts.\n\nThe lid is shown lifted 60 mm above the "
                          "deck. Sizes marked MEASURE in the script are placeholders." % len(parts))
    except Exception:
        if ui:
            ui.messageBox("NEXUS case script failed. Copy this text and send it to Claude:\n\n"
                          + traceback.format_exc())
