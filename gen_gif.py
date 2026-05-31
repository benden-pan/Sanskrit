#!/usr/bin/env python3
"""Generate stroke-order GIF for one Devanagari character using cairosvg + Pillow."""

import io
import cairosvg
from PIL import Image

# Stroke data for क (ka) — from devanagari-varnamala.html
KA_STROKES = [
    {'d': 'M 42,28 C 30,34 19,52 26,68 C 30,78 42,80 52,74', 'label': '左弧形主體', 'color': '#e74c3c'},
    {'d': 'M 56,28 Q 74,40 72,58 Q 69,72 58,76',             'label': '右鉤形',     'color': '#2980b9'},
    {'d': 'M 14,22 L 86,22',                                  'label': '頂橫線',     'color': '#27ae60'},
]

CHAR = 'क'
IAST = 'ka'
COLORS = ['#e74c3c', '#2980b9', '#27ae60', '#8e44ad', '#e67e22']

W, H = 217, 181
SVG_W, SVG_H = 100, 100
# Scale factor: map 100x100 SVG to 160x160 area centred in 217x181
SCALE = 1.6
OFFSET_X = (W - SVG_W * SCALE) / 2
OFFSET_Y = (H - SVG_H * SCALE) / 2 + 5


def make_svg_frame(strokes_so_far, highlight_idx, all_strokes, char, iast):
    """Return SVG bytes for one frame."""
    path_els = []
    for i, s in enumerate(all_strokes):
        if i < strokes_so_far:
            color = COLORS[i % len(COLORS)]
            opacity = '1'
        elif i == strokes_so_far and i == highlight_idx:
            color = COLORS[i % len(COLORS)]
            opacity = '1'
        else:
            color = '#d4c5b0'
            opacity = '0.3'

        if i <= strokes_so_far:
            path_els.append(
                f'<path d="{s["d"]}" stroke="{color}" stroke-width="3.5" '
                f'fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}"/>'
            )
        else:
            path_els.append(
                f'<path d="{s["d"]}" stroke="#d4c5b0" stroke-width="2" '
                f'fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.25"/>'
            )

    paths_svg = '\n    '.join(path_els)

    # Stroke number label
    stroke_label = f'筆{strokes_so_far + 1}' if strokes_so_far < len(all_strokes) else '完成'
    label_color = COLORS[strokes_so_far % len(COLORS)] if strokes_so_far < len(all_strokes) else '#27ae60'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#fdf6e3"/>
  <!-- character label top-left -->
  <text x="12" y="22" font-size="18" fill="#8b3a00" font-family="serif">{char}</text>
  <text x="12" y="36" font-size="9" fill="#7a6050" font-family="sans-serif">{iast}</text>
  <!-- stroke counter top-right -->
  <text x="{W-12}" y="22" font-size="11" fill="{label_color}" font-family="sans-serif" text-anchor="end">{stroke_label}</text>
  <!-- main drawing group scaled+centred -->
  <g transform="translate({OFFSET_X:.1f},{OFFSET_Y:.1f}) scale({SCALE})">
    {paths_svg}
  </g>
</svg>'''
    return svg.encode('utf-8')


def svg_to_pil(svg_bytes):
    png = cairosvg.svg2png(bytestring=svg_bytes)
    return Image.open(io.BytesIO(png)).convert('RGBA')


def rgba_to_p(img):
    """Convert RGBA to palette mode for GIF."""
    bg = Image.new('RGBA', img.size, (253, 246, 227, 255))
    composite = Image.alpha_composite(bg, img)
    return composite.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=128)


def build_frames(strokes):
    frames = []

    # Phase 1: show all strokes greyed out (2 frames)
    for _ in range(2):
        svg = make_svg_frame(-1, -1, strokes, CHAR, IAST)
        frames.append((rgba_to_p(svg_to_pil(svg)), 600))

    # Phase 2: draw each stroke progressively
    n = len(strokes)
    STEPS = 8  # sub-frames per stroke (animate dash)
    for si in range(n):
        for step in range(STEPS + 1):
            # Build partial path for the current stroke
            full_d = strokes[si]['d']
            # We just show the full stroke but vary opacity as a simple animation
            # (true dash animation needs a canvas; here we fade in)
            frac = step / STEPS
            partial_strokes = strokes[:si] + [{
                **strokes[si],
                '_opacity': frac
            }]

            # Build SVG with partial opacity for current stroke
            path_els = []
            for i, s in enumerate(strokes):
                if i < si:
                    color = COLORS[i % len(COLORS)]
                    path_els.append(
                        f'<path d="{s["d"]}" stroke="{color}" stroke-width="3.5" '
                        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                    )
                elif i == si:
                    color = COLORS[i % len(COLORS)]
                    path_els.append(
                        f'<path d="{s["d"]}" stroke="{color}" stroke-width="3.5" '
                        f'fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="{frac:.2f}"/>'
                    )
                else:
                    path_els.append(
                        f'<path d="{s["d"]}" stroke="#d4c5b0" stroke-width="2" '
                        f'fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.25"/>'
                    )

            stroke_label = f'筆{si + 1}'
            label_color = COLORS[si % len(COLORS)]
            paths_svg = '\n    '.join(path_els)
            svg_str = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#fdf6e3"/>
  <text x="12" y="22" font-size="18" fill="#8b3a00" font-family="serif">{CHAR}</text>
  <text x="12" y="36" font-size="9" fill="#7a6050" font-family="sans-serif">{IAST}</text>
  <text x="{W-12}" y="22" font-size="11" fill="{label_color}" font-family="sans-serif" text-anchor="end">{stroke_label}</text>
  <g transform="translate({OFFSET_X:.1f},{OFFSET_Y:.1f}) scale({SCALE})">
    {paths_svg}
  </g>
</svg>'''.encode('utf-8')
            frames.append((rgba_to_p(svg_to_pil(svg_str)), 60))

        # Hold completed stroke for a moment
        for _ in range(3):
            path_els = []
            for i, s in enumerate(strokes):
                if i <= si:
                    color = COLORS[i % len(COLORS)]
                    path_els.append(
                        f'<path d="{s["d"]}" stroke="{color}" stroke-width="3.5" '
                        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                    )
                else:
                    path_els.append(
                        f'<path d="{s["d"]}" stroke="#d4c5b0" stroke-width="2" '
                        f'fill="none" stroke-linecap="round" stroke-linejoin="round" opacity="0.25"/>'
                    )
            stroke_label = f'筆{si + 1}' if si < n - 1 else '完成'
            label_color = COLORS[si % len(COLORS)]
            paths_svg = '\n    '.join(path_els)
            svg_str = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#fdf6e3"/>
  <text x="12" y="22" font-size="18" fill="#8b3a00" font-family="serif">{CHAR}</text>
  <text x="12" y="36" font-size="9" fill="#7a6050" font-family="sans-serif">{IAST}</text>
  <text x="{W-12}" y="22" font-size="11" fill="{label_color}" font-family="sans-serif" text-anchor="end">{stroke_label}</text>
  <g transform="translate({OFFSET_X:.1f},{OFFSET_Y:.1f}) scale({SCALE})">
    {paths_svg}
  </g>
</svg>'''.encode('utf-8')
            frames.append((rgba_to_p(svg_to_pil(svg_str)), 200))

    # Final hold: complete character, 4 frames
    for _ in range(4):
        path_els = [
            f'<path d="{s["d"]}" stroke="{COLORS[i % len(COLORS)]}" stroke-width="3.5" '
            f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            for i, s in enumerate(strokes)
        ]
        paths_svg = '\n    '.join(path_els)
        svg_str = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#fdf6e3"/>
  <text x="12" y="22" font-size="18" fill="#8b3a00" font-family="serif">{CHAR}</text>
  <text x="12" y="36" font-size="9" fill="#7a6050" font-family="sans-serif">{IAST}</text>
  <text x="{W-12}" y="22" font-size="11" fill="#27ae60" font-family="sans-serif" text-anchor="end">完成</text>
  <g transform="translate({OFFSET_X:.1f},{OFFSET_Y:.1f}) scale({SCALE})">
    {paths_svg}
  </g>
</svg>'''.encode('utf-8')
        frames.append((rgba_to_p(svg_to_pil(svg_str)), 500))

    return frames


def save_gif(frames, path):
    images = [f[0] for f in frames]
    durations = [f[1] for f in frames]
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        loop=0,
        duration=durations,
        optimize=False,
    )
    print(f'Saved {len(frames)} frames → {path}')


if __name__ == '__main__':
    frames = build_frames(KA_STROKES)
    out = '/home/user/Sanskrit/test-क-order.gif'
    save_gif(frames, out)
    from PIL import Image as _I
    check = _I.open(out)
    print(f'Verified: {check.size}, {check.n_frames} frames')
