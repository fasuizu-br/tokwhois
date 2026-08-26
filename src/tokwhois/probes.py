"""Versioned probe strings and metadata for tokenizer fertility fingerprinting."""

import hashlib
from pathlib import Path
from typing import Dict, Tuple

PROBE_ORDER = [
    "cjk30",
    "space40",
    "digit64",
    "ascii100",
    "emoji8",
    "hello_leadsp",
    "nl16",
    "tab16",
    "cjk_en",
    "im_start",
    "gmask",
    "eot",
    "bot_llama",
    "byte_rare",
]

# Canonical embedded probe strings for v1
EMBEDDED_PROBES: Dict[str, str] = {
    "cjk30": "的一是不了人我在有他这中大来上个国到说们为子和你地出品时要就",
    "space40": " " * 40,
    "digit64": "7" * 64,
    "ascii100": "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs! ABCDEFGHIJKLMN",
    "emoji8": "😀🎉🚀🔥💡🤖✨🌟",
    "hello_leadsp": " hello",
    "nl16": "\n" * 16,
    "tab16": "\t" * 16,
    "cjk_en": "你好world你好world你好world你好world",
    "im_start": "<|im_start|>",
    "gmask": "[gMASK]",
    "eot": "<|endoftext|>",
    "bot_llama": "<|begin_of_text|>",
    "byte_rare": "\u0800\u0801\u0802\u0803\u0804\u0805\u0806\u0807",
    "empty": "",
}

PROBE_DESCRIPTIONS: Dict[str, str] = {
    "cjk30": "30 CJK ideograms (dedicated CJK vocab vs SentencePiece)",
    "space40": "40 ASCII spaces (whitespace collapse / byte-fallback)",
    "digit64": "64 digits ('7' x 64, tests 1/2/3-digit grouping)",
    "ascii100": "100 ASCII characters (Latin fertility baseline)",
    "emoji8": "8 common emoji codepoints (direct tokens vs multi-byte fallback)",
    "hello_leadsp": "Leading space + 'hello' (GPT-style Ġ vs standard BPE)",
    "nl16": "16 consecutive newlines (newline merging rules)",
    "tab16": "16 consecutive tabs (tab indentation compression)",
    "cjk_en": "Mixed CJK and Latin script boundary ('你好world' x 4)",
    "im_start": "ChatML token '<|im_start|>' (special token vs split)",
    "gmask": "GLM special marker '[gMASK]' (GLM vocab signature)",
    "eot": "GPT end-of-text '<|endoftext|>' (tiktoken token signature)",
    "bot_llama": "Llama 3 begin-of-text '<|begin_of_text|>' (Llama 3 signature)",
    "byte_rare": "8 rare Samaritan Unicode codepoints (U+0800..U+0807)",
    "empty": "Empty prompt (measures chat template framing overhead)",
}


def load_probes(probes_dir: Path | None = None) -> Dict[str, str]:
    """Load probes from directory if provided, otherwise return embedded v1 probes."""
    if probes_dir is not None and probes_dir.exists():
        probes = {}
        for p_id in PROBE_ORDER:
            fpath = probes_dir / f"{p_id}.txt"
            if fpath.exists():
                probes[p_id] = fpath.read_text(encoding="utf-8")
            else:
                probes[p_id] = EMBEDDED_PROBES[p_id]
        empty_fpath = probes_dir / "empty.txt"
        probes["empty"] = empty_fpath.read_text(encoding="utf-8") if empty_fpath.exists() else ""
        return probes
    return dict(EMBEDDED_PROBES)


def get_probe_hashes(probes: Dict[str, str] | None = None) -> Dict[str, str]:
    """Compute SHA-256 digests for all probes."""
    if probes is None:
        probes = EMBEDDED_PROBES
    return {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in probes.items()}
