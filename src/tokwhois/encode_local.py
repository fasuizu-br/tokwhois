"""Local tokenizer encoding utilities for tokenizer.json files or local models."""

from pathlib import Path
from typing import Dict, Optional
from tokwhois.probes import PROBE_ORDER, load_probes


def encode_with_local_file(tokenizer_path: str | Path) -> Dict[str, int]:
    """Encode the 14 probes using a local HuggingFace tokenizer.json file."""
    try:
        from tokenizers import Tokenizer
    except ImportError:
        raise ImportError(
            "The 'tokenizers' library is required to encode local tokenizer.json files. "
            "Install with: pip install 'tokwhois[build-catalog]' or pip install tokenizers"
        )

    p = Path(tokenizer_path)
    if not p.exists():
        raise FileNotFoundError(f"Tokenizer file not found: {tokenizer_path}")

    tokenizer = Tokenizer.from_file(str(p))
    probes = load_probes()

    vector = {}
    for p_id in PROBE_ORDER:
        tokens = tokenizer.encode(probes[p_id], add_special_tokens=False)
        vector[p_id] = len(tokens.ids)

    return vector


def encode_with_hf_model(model_name_or_path: str) -> Dict[str, int]:
    """Encode the 14 probes using a HuggingFace tokenizer identifier."""
    try:
        from tokenizers import Tokenizer
    except ImportError:
        raise ImportError(
            "The 'tokenizers' library is required to load HF tokenizers. "
            "Install with: pip install 'tokwhois[build-catalog]' or pip install tokenizers"
        )

    tokenizer = Tokenizer.from_pretrained(model_name_or_path)
    probes = load_probes()

    vector = {}
    for p_id in PROBE_ORDER:
        tokens = tokenizer.encode(probes[p_id], add_special_tokens=False)
        vector[p_id] = len(tokens.ids)

    return vector


def encode_with_tiktoken(encoding_name: str) -> Dict[str, int]:
    """Encode the 14 probes using an OpenAI tiktoken encoding."""
    try:
        import tiktoken
    except ImportError:
        raise ImportError(
            "The 'tiktoken' library is required to encode with tiktoken. "
            "Install with: pip install 'tokwhois[build-catalog]' or pip install tiktoken"
        )

    enc = tiktoken.get_encoding(encoding_name)
    probes = load_probes()

    vector = {}
    for p_id in PROBE_ORDER:
        tokens = enc.encode(probes[p_id], allowed_special="all")
        vector[p_id] = len(tokens)

    return vector
