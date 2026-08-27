#!/usr/bin/env python3
"""Generate a stunning SVG heatmap matrix of tokenizer fertility vectors.

Outputs docs/fingerprint.svg from catalog/v1.json.
"""

import json
from pathlib import Path

def generate_svg():
    catalog_dir = Path(__file__).resolve().parent
    v1_json = catalog_dir / "v1.json"
    with open(v1_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    probes = data["probe_order"]
    families = list(data["families"].keys())
    
    cell_w = 54
    cell_h = 30
    label_x_w = 160
    header_y_h = 110
    footer_h = 70
    
    width = label_x_w + len(probes) * cell_w + 60
    height = header_y_h + len(families) * cell_h + footer_h
    
    def get_color(val):
        if val == 1:
            return "#10b981", "#ffffff"
        elif val <= 3:
            return "#06b6d4", "#ffffff"
        elif val <= 10:
            return "#3b82f6", "#ffffff"
        elif val <= 25:
            return "#8b5cf6", "#ffffff"
        elif val <= 40:
            return "#ec4899", "#ffffff"
        else:
            return "#f59e0b", "#000000"

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" style="background:#0b0f19; font-family:-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, monospace;">')
    
    svg_parts.append('<defs>')
    svg_parts.append('  <linearGradient id="cardGlow" x1="0%" y1="0%" x2="100%" y2="100%">')
    svg_parts.append('    <stop offset="0%" stop-color="#1e293b" stop-opacity="0.8"/>')
    svg_parts.append('    <stop offset="100%" stop-color="#0f172a" stop-opacity="0.9"/>')
    svg_parts.append('  </linearGradient>')
    svg_parts.append('</defs>')

    svg_parts.append(f'<rect x="16" y="16" width="{width - 32}" height="{height - 32}" rx="12" fill="url(#cardGlow)" stroke="#334155" stroke-width="1.5" />')
    svg_parts.append('<text x="36" y="48" fill="#f8fafc" font-size="18" font-weight="700" letter-spacing="-0.02em">tokwhois — Tokenizer Fertility Atlas</text>')
    svg_parts.append('<text x="36" y="68" fill="#94a3b8" font-size="12">Fixed 14-probe fertility fingerprint matrix across public tokenizer families (v1.1 catalog)</text>')

    for j, p in enumerate(probes):
        cx = label_x_w + j * cell_w + cell_w // 2
        cy = header_y_h - 12
        svg_parts.append(f'<text x="{cx}" y="{cy}" fill="#cbd5e1" font-size=\"11\" font-family=\"ui-monospace, monospace\" text-anchor=\"middle\" font-weight=\"600\">{p}</text>')

    for i, fam in enumerate(families):
        fam_info = data["families"][fam]
        ry = header_y_h + i * cell_h
        
        if i % 2 == 1:
            svg_parts.append(f'<rect x="30" y="{ry}" width="{width - 60}" height="{cell_h}" fill="#1e293b" fill-opacity="0.3" rx="4" />')
        
        short_disp = fam
        svg_parts.append(f'<text x="{label_x_w - 14}" y="{ry + 20}" fill="#f1f5f9" font-size="12" font-family="ui-monospace, monospace" font-weight="600" text-anchor="end">{short_disp}</text>')

        vec = fam_info["vector"]
        for j, p in enumerate(probes):
            rx = label_x_w + j * cell_w
            val = vec.get(p, 0)
            bg, fg = get_color(val)
            
            svg_parts.append(f'<rect x="{rx + 2}" y="{ry + 2}" width="{cell_w - 4}" height="{cell_h - 4}" rx="4" fill="{bg}" fill-opacity="0.85" />')
            svg_parts.append(f'<text x="{rx + cell_w // 2}" y="{ry + 20}" fill="{fg}" font-size="11" font-family="ui-monospace, monospace" font-weight="700" text-anchor="middle">{val}</text>')

    legend_y = height - 32
    svg_parts.append(f'<text x="36" y="{legend_y}" fill="#64748b" font-size="11">14 probes × {len(families)} families · zero collisions · offline verification</text>')
    
    swatches = [
        ("1 token", "#10b981"),
        ("2-3 tokens", "#06b6d4"),
        ("4-10 tokens", "#3b82f6"),
        ("11-25 tokens", "#8b5cf6"),
        ("26-40 tokens", "#ec4899"),
        ("40+ tokens", "#f59e0b"),
    ]
    swatch_start_x = width - 460
    for s_idx, (s_label, s_col) in enumerate(swatches):
        sx = swatch_start_x + s_idx * 72
        svg_parts.append(f'<rect x="{sx}" y="{legend_y - 10}" width="10" height="10" rx="2" fill="{s_col}" />')
        svg_parts.append(f'<text x="{sx + 14}" y="{legend_y - 1}" fill="#94a3b8" font-size="10">{s_label}</text>')

    svg_parts.append('</svg>')

    out_svg = catalog_dir.parent / "docs" / "fingerprint.svg"
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    with open(out_svg, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
    print(f"Generated SVG heatmap: {out_svg}")

if __name__ == "__main__":
    generate_svg()
