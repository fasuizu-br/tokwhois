"""Terminal and JSON report rendering for tokwhois."""

import json
import os
import sys
from typing import Dict, List, Optional
from tokwhois.match import MatchResult

# Terminal styling ANSI codes
USE_COLOR = sys.stdout.isatty() and ("NO_COLOR" not in os.environ)

BOLD = "\033[1m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""
ITALIC = "\033[3m" if USE_COLOR else ""
RESET = "\033[0m" if USE_COLOR else ""

GREEN = "\033[38;5;48m" if USE_COLOR else ""
CYAN = "\033[38;5;45m" if USE_COLOR else ""
BLUE = "\033[38;5;75m" if USE_COLOR else ""
AMBER = "\033[38;5;214m" if USE_COLOR else ""
MAGENTA = "\033[38;5;201m" if USE_COLOR else ""
GRAY = "\033[38;5;244m" if USE_COLOR else ""
RED = "\033[38;5;196m" if USE_COLOR else ""


def format_cli_report(result: MatchResult, top_n_compare: int = 4) -> str:
    """Format a sleek, stunning ASCII/ANSI terminal comparison report."""
    lines: List[str] = []

    # 1. Header Banner
    lines.append("")
    lines.append(f"{BOLD}{CYAN}tokwhois{RESET} {DIM}v0.1.0 — Tokenizer Fertility Fingerprint{RESET}")
    lines.append(f"{GRAY}{'─' * 64}{RESET}")

    # 2. Main Verdict Block
    top = result.top_match
    conf_color = GREEN if result.confidence >= 0.9 else (AMBER if result.confidence >= 0.7 else RED)
    
    if result.is_ambiguous:
        lines.append(f"{BOLD}family{RESET}      {AMBER}{top.family_id}-class{RESET}  {RED}[AMBIGUOUS: margin < 2]{RESET}")
    else:
        lines.append(f"{BOLD}family{RESET}      {GREEN}{BOLD}{top.family_id}-class{RESET}     {DIM}confidence{RESET} {conf_color}{result.confidence:.2f}{RESET}  {DIM}(L1 distance: {top.l1_distance}){RESET}")

    if result.runner_up:
        lines.append(f"{BOLD}runner-up{RESET}   {BLUE}{result.runner_up.family_id}-class{RESET}    {DIM}margin{RESET} {result.margin} tokens (L1)")
    
    lines.append("")

    # 3. Comparative Probe Table
    # Select top families for columns
    compare_fams = result.ranked_matches[:top_n_compare]
    
    # Table header
    header_col = f"{'probe':<14} {'counted':>7}"
    for f in compare_fams:
        fam_short = f.family_id[:10]
        header_col += f" {fam_short:>10}"
    lines.append(f"{BOLD}{header_col}{RESET}")
    lines.append(f"{GRAY}{'─' * len(header_col)}{RESET}")

    # Table rows for each probe
    for p in result.probe_order:
        obs_val = result.observed_vector.get(p, 0)
        row = f"{CYAN}{p:<14}{RESET} {BOLD}{obs_val:>7}{RESET}"

        for f in compare_fams:
            exp_val = f.vector.get(p, 0)
            if exp_val == obs_val:
                cell = f"{GREEN}{exp_val:>10}{RESET}"
            else:
                cell = f"{GRAY}{exp_val:>10}{RESET}"
            row += f" {cell}"
        lines.append(row)

    lines.append(f"{GRAY}{'─' * len(header_col)}{RESET}")

    # 4. Offset & Calibration Info
    if result.offset > 0:
        lines.append(f"{DIM}offset (empty){RESET}  {BOLD}{result.offset:>5}{RESET}   {DIM}subtracted from every prompt count{RESET}")
    else:
        lines.append(f"{DIM}offset (empty){RESET}  {BOLD}    0{RESET}   {DIM}raw token counts (no template framing detected){RESET}")

    lines.append("")

    # 5. Metadata & Discriminators
    lines.append(f"{GRAY}n=1 probe / string   K=1   catalog={result.catalog_version}   {result.top_match.license}{RESET}")
    if result.discriminating_probes:
        disc_str = ", ".join(result.discriminating_probes[:6])
        if len(result.discriminating_probes) > 6:
            disc_str += f" (+{len(result.discriminating_probes) - 6} more)"
        lines.append(f"{DIM}discriminating probes vs runner-up:{RESET} {disc_str}")
    else:
        lines.append(f"{DIM}discriminating probes:{RESET} none")

    lines.append("")
    return "\n".join(lines)


def format_json_report(result: MatchResult) -> str:
    """Format report as a structured JSON string."""
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
