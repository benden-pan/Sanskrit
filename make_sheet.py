#!/usr/bin/env python3
"""Generate a writing practice sheet for one Devanagari character."""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path
import matplotlib.patheffects as pe
from PIL import Image, ImageDraw, ImageFont
import io, re

# ── character data ──────────────────────────────────────────────
CHAR  = 'क'
IAST  = 'ka'
TITLE_ZH = f"練習寫天城體字母 '{CHAR}' ({IAST})"
TITLE_EN = f"(Devanagari letter '{CHAR}' ({IAST}) - Writing Practice)"

# SVG paths in 100×100 viewBox, 3 strokes for क
STROKES = [
    {'d': 'M 42,28 C 30,34 19,52 26,68 C 30,78 42,80 52,74',
     'color': '#2ecc71', 'num': 1, 'label': '左弧'},
    {'d': 'M 56,28 Q 74,40 72,58 Q 69,72 58,76',
     'color': '#f1c40f', 'num': 2, 'label': '右鉤'},
    {'d': 'M 14,22 L 86,22',
     'color': '#e74c3c', 'num': 3, 'label': '頂橫線'},
]

# ── path parser ─────────────────────────────────────────────────
def parse_path(d):
    """Return list of (t, xy) arrays sampling the SVG path."""
    tokens = re.findall(r'[MLCQmlcq]|[-+]?\d*\.?\d+', d)
    pts = []
    i = 0
    cur = np.array([0., 0.])
    while i < len(tokens):
        cmd = tokens[i]; i += 1
        if cmd == 'M':
            cur = np.array([float(tokens[i]), float(tokens[i+1])]); i += 2
            pts.append(('M', cur.copy()))
        elif cmd == 'L':
            end = np.array([float(tokens[i]), float(tokens[i+1])]); i += 2
            pts.append(('L', cur.copy(), end.copy()))
            cur = end
        elif cmd == 'C':
            c1 = np.array([float(tokens[i]),   float(tokens[i+1])]); i += 2
            c2 = np.array([float(tokens[i]),   float(tokens[i+1])]); i += 2
            end= np.array([float(tokens[i]),   float(tokens[i+1])]); i += 2
            pts.append(('C', cur.copy(), c1, c2, end.copy()))
            cur = end
        elif cmd == 'Q':
            c  = np.array([float(tokens[i]),   float(tokens[i+1])]); i += 2
            end= np.array([float(tokens[i]),   float(tokens[i+1])]); i += 2
            pts.append(('Q', cur.copy(), c, end.copy()))
            cur = end
    return pts

def sample_path(segs, n=80):
    """Sample n points along path."""
    points = []
    for seg in segs:
        if seg[0] == 'M':
            points.append(seg[1])
        elif seg[0] == 'L':
            t = np.linspace(0, 1, 20)
            for ti in t:
                points.append((1-ti)*seg[1] + ti*seg[2])
        elif seg[0] == 'Q':
            p0,p1,p2 = seg[1],seg[2],seg[3]
            t = np.linspace(0, 1, 30)
            for ti in t:
                p = (1-ti)**2*p0 + 2*(1-ti)*ti*p1 + ti**2*p2
                points.append(p)
        elif seg[0] == 'C':
            p0,p1,p2,p3 = seg[1],seg[2],seg[3],seg[4]
            t = np.linspace(0, 1, 40)
            for ti in t:
                p = ((1-ti)**3*p0 + 3*(1-ti)**2*ti*p1
                     + 3*(1-ti)*ti**2*p2 + ti**3*p3)
                points.append(p)
    return np.array(points)

# ── drawing helpers ─────────────────────────────────────────────
def draw_grid(ax, xlim, ylim, step=10, color='#b0c4de', lw=0.5):
    for x in np.arange(xlim[0], xlim[1]+step, step):
        ax.plot([x,x], ylim, color=color, lw=lw, zorder=1)
    for y in np.arange(ylim[0], ylim[1]+step, step):
        ax.plot(xlim, [y,y], color=color, lw=lw, zorder=1)

def draw_stroke_dashed(ax, pts, color, scale, ox, oy, lw=3.5):
    xs = pts[:,0]*scale + ox
    ys = pts[:,1]*scale + oy
    ax.plot(xs, ys, color=color, lw=lw, linestyle='--',
            dashes=(6,4), alpha=0.85, zorder=3,
            solid_capstyle='round', dash_capstyle='round')

def draw_arrow(ax, pts, color, scale, ox, oy):
    """Draw arrow at ~85% along the sampled path."""
    n = len(pts)
    i1 = int(n*0.80); i2 = int(n*0.92)
    x1,y1 = pts[i1,0]*scale+ox, pts[i1,1]*scale+oy
    x2,y2 = pts[i2,0]*scale+ox, pts[i2,1]*scale+oy
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=2.2, mutation_scale=18), zorder=5)

def draw_number_badge(ax, x, y, num, color):
    ax.plot(x, y, 'o', ms=16, color=color, zorder=6, alpha=0.9)
    ax.text(x, y, str(num), ha='center', va='center',
            fontsize=9, fontweight='bold', color='white', zorder=7)

def draw_char_small(ax, cx, cy, scale, alpha=0.25):
    """Draw all strokes lightly for a practice cell."""
    for s in STROKES:
        segs = parse_path(s['d'])
        pts  = sample_path(segs)
        xs = pts[:,0]*scale + cx - 50*scale
        ys = pts[:,1]*scale + cy - 50*scale
        ax.plot(xs, ys, color='#5b9bd5', lw=1.5, linestyle='--',
                dashes=(4,3), alpha=alpha, zorder=2,
                solid_capstyle='round', dash_capstyle='round')

# ── main ────────────────────────────────────────────────────────
fig = plt.figure(figsize=(11, 14), dpi=120)
fig.patch.set_facecolor('white')

# Title
fig.text(0.5, 0.965, TITLE_ZH, ha='center', va='top',
         fontsize=22, fontweight='bold',
         fontproperties=matplotlib.font_manager.FontProperties(
             fname='/usr/share/fonts/truetype/freefont/FreeSerif.ttf', size=22))
fig.text(0.5, 0.940, TITLE_EN, ha='center', va='top',
         fontsize=13, color='#444',
         fontproperties=matplotlib.font_manager.FontProperties(
             fname='/usr/share/fonts/truetype/freefont/FreeSerif.ttf', size=13))

# ── large demo panel ────────────────────────────────────────────
ax_main = fig.add_axes([0.05, 0.52, 0.90, 0.40])
ax_main.set_xlim(0, 300)
ax_main.set_ylim(120, 0)   # y flipped (SVG-like)
ax_main.set_aspect('equal')
ax_main.axis('off')
ax_main.set_facecolor('#f0f6ff')
fig.patches.append(mpatches.FancyBboxPatch(
    (0.05, 0.52), 0.90, 0.40, transform=fig.transFigure,
    boxstyle='round,pad=0.005', facecolor='#f0f6ff',
    edgecolor='#90a0b0', linewidth=1.5, zorder=0))

draw_grid(ax_main, [0,300], [0,120], step=10)

# Draw strokes in the main panel (centred around x=150, y=60)
SCALE = 1.0   # 1px per SVG unit  → letter ~86 wide, fits well in 300×120
OX, OY = 100, 10   # offset so 100×100 SVG box lands centred

for s in STROKES:
    segs = parse_path(s['d'])
    pts  = sample_path(segs)
    draw_stroke_dashed(ax_main, pts, s['color'], SCALE, OX, OY, lw=4)
    draw_arrow(ax_main, pts, s['color'], SCALE, OX, OY)
    # badge at start
    sx = pts[0,0]*SCALE + OX
    sy = pts[0,1]*SCALE + OY
    draw_number_badge(ax_main, sx, sy, s['num'], s['color'])

# ── 3 practice rows ─────────────────────────────────────────────
ROWS = 3
COLS = 9
CELL_W, CELL_H = 0.90/COLS, 0.14

for row in range(ROWS):
    y0 = 0.50 - row*(CELL_H + 0.02) - CELL_H
    for col in range(COLS):
        x0 = 0.05 + col*(0.90/COLS)
        ax = fig.add_axes([x0, y0, 0.90/COLS, CELL_H])
        ax.set_xlim(0, 1); ax.set_ylim(1, 0)
        ax.set_aspect('equal')
        ax.set_facecolor('#f8fbff')
        for spine in ax.spines.values():
            spine.set_edgecolor('#90a0b0'); spine.set_linewidth(0.8)
        ax.set_xticks([]); ax.set_yticks([])

        # light grid
        for gx in np.arange(0, 1.01, 0.25):
            ax.plot([gx,gx],[0,1], color='#c8d8e8', lw=0.4)
        for gy in np.arange(0, 1.01, 0.25):
            ax.plot([0,1],[gy,gy], color='#c8d8e8', lw=0.4)

        # tiny stroke guide
        sc = 0.009   # scale to fit 100-unit SVG into 0..1 axes
        for s in STROKES:
            segs = parse_path(s['d'])
            pts  = sample_path(segs)
            xs = pts[:,0]*sc + 0.05
            ys = pts[:,1]*sc + 0.08
            ax.plot(xs, ys, color='#5b9bd5', lw=1.2, linestyle='--',
                    dashes=(4,3), alpha=0.35, zorder=2)

        # dot for stroke 1 start
        ax.plot(STROKES[0]['d'].split()[1].split(',')[0] + '?',  # skip — just colour dot
                0.07, '.', ms=5, color='#2ecc71', alpha=0.7, transform=ax.transData)

        # colour dots top-left cycling
        dot_colors = ['#2ecc71','#f1c40f','#e74c3c']
        dot_x = 0.08 + (col % 3)*0.0   # always same x
        ax.plot(dot_x, 0.12, 'o', ms=5,
                color=dot_colors[col % 3], alpha=0.9,
                transform=ax.transData, zorder=5, clip_on=False)

plt.savefig('/home/user/Sanskrit/test-sheet-ka.png',
            dpi=120, bbox_inches='tight',
            facecolor='white')
print('Saved test-sheet-ka.png')
