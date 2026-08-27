#!/usr/bin/env python3
"""Generate high-quality animated demo.gif and demo.cast for tokwhois documentation."""

import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

docs_dir = Path(__file__).resolve().parent

# Window and layout dimensions
W, H = 840, 620
bg_color = (13, 17, 23)           # Dark slate background #0d1117
window_bg = (15, 23, 42)          # Card background #0f172a
header_bg = (30, 41, 59)          # Header bar #1e293b
border_color = (51, 65, 85)       # Border #334155

# Color Palette
text_white = (241, 245, 249)      # #f1f5f9
text_dim = (100, 116, 139)        # #64748b
text_mid = (148, 163, 184)        # #94a3b8
text_cyan = (56, 189, 248)        # #38bdf8
text_green = (52, 211, 153)       # #34d399
text_blue = (96, 165, 250)        # #60a5fa
text_purple = (168, 85, 247)      # #a855f7
divider_color = (51, 65, 85)      # #334155

# Fonts
font_path = "/System/Library/Fonts/Menlo.ttc"
try:
    font_reg = ImageFont.truetype(font_path, 13, index=0)
    font_bold = ImageFont.truetype(font_path, 13, index=1)
    font_small = ImageFont.truetype(font_path, 11, index=0)
    font_title = ImageFont.truetype(font_path, 11, index=0)
except Exception:
    font_reg = ImageFont.load_default()
    font_bold = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_title = ImageFont.load_default()

CHAR_W = 7.82  # Menlo 13 width per character
LINE_H = 19


def create_base_canvas(title="tokwhois demo (offline · embedded catalog v1.1)"):
    img = Image.new("RGB", (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Terminal card
    draw.rounded_rectangle(
        [16, 16, W - 16, H - 16],
        radius=10,
        fill=window_bg,
        outline=border_color,
        width=1,
    )
    # Header bar
    draw.rounded_rectangle([16, 16, W - 16, 50], radius=10, fill=header_bg)
    draw.rectangle([16, 36, W - 16, 50], fill=header_bg)
    draw.line([16, 50, W - 16, 50], fill=border_color, width=1)

    # macOS window buttons
    draw.ellipse([32, 27, 44, 39], fill=(255, 95, 86))
    draw.ellipse([52, 27, 64, 39], fill=(255, 189, 46))
    draw.ellipse([72, 27, 84, 39], fill=(39, 201, 63))

    # Title centered
    draw.text((104, 26), title, fill=text_mid, font=font_title)
    return img, draw


# Real probe table lines from tokwhois output (v1.1)
TABLE_ROWS = [
    ("cjk30", "22", "22", "22", "22", "30"),
    ("space40", "1", "1", "1", "1", "1"),
    ("digit64", "43", "43", "43", "64", "22"),
    ("ascii100", "26", "26", "26", "26", "26"),
    ("emoji8", "21", "21", "13", "19", "21"),
    ("hello_leadsp", "1", "1", "1", "1", "1"),
    ("nl16", "1", "1", "1", "1", "1"),
    ("tab16", "1", "1", "1", "1", "1"),
    ("cjk_en", "8", "8", "8", "8", "12"),
    ("im_start", "6", "6", "6", "1", "6"),
    ("gmask", "1", "1", "1", "3", "3"),
    ("eot", "1", "1", "1", "1", "1"),
    ("bot_llama", "7", "7", "7", "7", "7"),
    ("byte_rare", "22", "22", "22", "23", "22"),
]


def render_scene(
    typed_command: str = "",
    show_cursor: bool = True,
    show_banner: bool = False,
    show_verdict: bool = False,
    num_table_rows: int = 0,
    show_footer: bool = False,
    show_final_prompt: bool = False,
    final_cursor: bool = True,
) -> Image.Image:
    img, draw = create_base_canvas()
    x_left = 36
    y = 66

    # Prompt line
    draw.text((x_left, y), "$ ", fill=text_purple, font=font_bold)
    cmd_x = x_left + 18
    draw.text((cmd_x, y), typed_command, fill=text_white, font=font_bold)
    if show_cursor:
        cur_x = cmd_x + int(len(typed_command) * CHAR_W) + 2
        draw.text((cur_x, y), "█", fill=text_cyan, font=font_reg)
    y += LINE_H + 4

    if show_banner:
        draw.text((x_left, y), "tokwhois demo", fill=text_cyan, font=font_bold)
        banner_w = int(draw.textlength("tokwhois demo ", font=font_bold))
        draw.text(
            (x_left + banner_w, y),
            "— running offline against embedded v1.1 catalog (zero network)",
            fill=text_dim,
            font=font_reg,
        )
        y += LINE_H
        draw.text(
            (x_left, y),
            "Simulating live endpoint response for public tokenizer...",
            fill=text_mid,
            font=font_reg,
        )
        y += LINE_H + 6

    if show_verdict:
        draw.text((x_left, y), "tokwhois v0.1.0 — Tokenizer Fertility Fingerprint", fill=text_cyan, font=font_bold)
        y += LINE_H
        draw.line([x_left, y - 4, x_left + int(66 * CHAR_W), y - 4], fill=divider_color, width=1)
        
        # Verdict: Family
        draw.text((x_left, y), "family      ", fill=text_white, font=font_bold)
        draw.text((x_left + int(12 * CHAR_W), y), "glm4-class     ", fill=text_green, font=font_bold)
        draw.text((x_left + int(27 * CHAR_W), y), "confidence ", fill=text_dim, font=font_reg)
        draw.text((x_left + int(38 * CHAR_W), y), "1.00", fill=text_green, font=font_bold)
        draw.text((x_left + int(43 * CHAR_W), y), "  (L1 distance: 0)", fill=text_dim, font=font_reg)
        y += LINE_H

        # Verdict: Runner-up
        draw.text((x_left, y), "runner-up   ", fill=text_white, font=font_bold)
        draw.text((x_left + int(12 * CHAR_W), y), "glm5-class           ", fill=text_blue, font=font_reg)
        draw.text((x_left + int(33 * CHAR_W), y), "margin ", fill=text_dim, font=font_reg)
        draw.text((x_left + int(40 * CHAR_W), y), "8 tokens (L1)", fill=text_white, font=font_reg)
        y += LINE_H + 6

    if num_table_rows > 0:
        # Table Header
        draw.text((x_left, y), "probe          counted       glm4       glm5    qwen3_8 cl100k_bas", fill=text_white, font=font_bold)
        y += LINE_H - 2
        draw.line([x_left, y - 2, x_left + int(66 * CHAR_W), y - 2], fill=divider_color, width=1)

        for i in range(min(num_table_rows, len(TABLE_ROWS))):
            probe_name, counted, c_glm4, c_glm5, c_qwen38, c_cl100k = TABLE_ROWS[i]
            # Probe name (col width 15)
            draw.text((x_left, y), f"{probe_name:<15}", fill=text_cyan, font=font_reg)
            # Counted (col width 8)
            draw.text((x_left + int(15 * CHAR_W), y), f"{counted:>7} ", fill=text_white, font=font_bold)
            # Match column: glm4 (col width 11)
            draw.text((x_left + int(24 * CHAR_W), y), f"{c_glm4:>10} ", fill=text_green, font=font_bold)
            # glm5 (col width 11)
            draw.text((x_left + int(35 * CHAR_W), y), f"{c_glm5:>10} ", fill=text_dim, font=font_reg)
            # qwen3_8 (col width 11)
            draw.text((x_left + int(46 * CHAR_W), y), f"{c_qwen38:>10} ", fill=text_dim, font=font_reg)
            # cl100k_bas (col width 11)
            draw.text((x_left + int(57 * CHAR_W), y), f"{c_cl100k:>10}", fill=text_dim, font=font_reg)
            y += LINE_H

    if show_footer:
        draw.line([x_left, y + 2, x_left + int(66 * CHAR_W), y + 2], fill=divider_color, width=1)
        y += 8
        draw.text((x_left, y), "offset (empty)      7   subtracted from every prompt count", fill=text_mid, font=font_reg)
        y += LINE_H + 4
        draw.text((x_left, y), "n=1 probe / string   K=1   catalog=v1.1   Apache-2.0", fill=text_dim, font=font_reg)
        y += LINE_H
        draw.text((x_left, y), "discriminating probes vs runner-up: ", fill=text_dim, font=font_reg)
        disc_w = int(draw.textlength("discriminating probes vs runner-up: ", font=font_reg))
        draw.text((x_left + disc_w, y), "emoji8", fill=text_cyan, font=font_reg)
        y += LINE_H + 8

    if show_final_prompt:
        draw.text((x_left, y), "$ ", fill=text_purple, font=font_bold)
        if final_cursor:
            draw.text((x_left + 18, y), "█", fill=text_cyan, font=font_reg)

    return img


def build_demo_gif():
    frames = []
    durations = []  # milliseconds per frame

    full_cmd = "tokwhois demo"

    # 1. Initial idle cursor (0.4s)
    frames.append(render_scene(typed_command="", show_cursor=True))
    durations.append(250)
    frames.append(render_scene(typed_command="", show_cursor=False))
    durations.append(150)

    # 2. Typing command smoothly
    for i in range(1, len(full_cmd) + 1):
        typed = full_cmd[:i]
        frames.append(render_scene(typed_command=typed, show_cursor=True))
        durations.append(60 if typed[-1] == " " else 45)

    # Short pause after command typed (0.3s)
    frames.append(render_scene(typed_command=full_cmd, show_cursor=True))
    durations.append(200)
    frames.append(render_scene(typed_command=full_cmd, show_cursor=False))
    durations.append(100)

    # 3. Enter pressed -> banner appears
    frames.append(render_scene(typed_command=full_cmd, show_cursor=False, show_banner=True))
    durations.append(400)

    # 4. Verdict header appears
    frames.append(
        render_scene(
            typed_command=full_cmd,
            show_cursor=False,
            show_banner=True,
            show_verdict=True,
        )
    )
    durations.append(250)

    # 5. Table rows render progressively in 4 batches
    for num_rows in [3, 7, 11, 14]:
        frames.append(
            render_scene(
                typed_command=full_cmd,
                show_cursor=False,
                show_banner=True,
                show_verdict=True,
                num_table_rows=num_rows,
            )
        )
        durations.append(90)

    # 6. Full output with footer
    frames.append(
        render_scene(
            typed_command=full_cmd,
            show_cursor=False,
            show_banner=True,
            show_verdict=True,
            num_table_rows=14,
            show_footer=True,
            show_final_prompt=True,
            final_cursor=True,
        )
    )
    durations.append(400)

    # 7. Holding final state with pulsing cursor (~3.5s)
    for _ in range(5):
        frames.append(
            render_scene(
                typed_command=full_cmd,
                show_cursor=False,
                show_banner=True,
                show_verdict=True,
                num_table_rows=14,
                show_footer=True,
                show_final_prompt=True,
                final_cursor=False,
            )
        )
        durations.append(350)
        frames.append(
            render_scene(
                typed_command=full_cmd,
                show_cursor=False,
                show_banner=True,
                show_verdict=True,
                num_table_rows=14,
                show_footer=True,
                show_final_prompt=True,
                final_cursor=True,
            )
        )
        durations.append(350)

    gif_path = docs_dir / "demo.gif"
    
    # Save using PIL with optimization
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size_bytes = gif_path.stat().st_size
    print(f"Generated {gif_path} ({size_bytes} bytes, {size_bytes / 1024:.1f} KB)")


if __name__ == "__main__":
    build_demo_gif()

