#!/usr/bin/env python3
"""Build and validate the public tokenizer fertility catalog (v1.json).

This script:
1. Loads the 14 versioned probes from probes/v1/*.txt
2. Encodes them using standard public tokenizer backends (tiktoken, tokenizers)
3. Checks for zero-distance collisions across all pairs
4. Writes catalog/v1.json and src/tokwhois/catalog/v1.json
"""

import hashlib
import json
from pathlib import Path
import sys

# Probe definitions order
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

def load_probes(probes_dir: Path):
    probes = {}
    hashes = {}
    for p_id in PROBE_ORDER:
        p_file = probes_dir / f"{p_id}.txt"
        if not p_file.exists():
            raise FileNotFoundError(f"Missing probe file: {p_file}")
        content = p_file.read_text(encoding="utf-8")
        probes[p_id] = content
        hashes[p_id] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    empty_file = probes_dir / "empty.txt"
    empty_hash = hashlib.sha256(empty_file.read_text(encoding="utf-8").encode("utf-8")).hexdigest() if empty_file.exists() else hashlib.sha256(b"").hexdigest()
    return probes, hashes, empty_hash

def build_catalog():
    catalog_dir = Path(__file__).resolve().parent
    probes_dir = catalog_dir / "probes" / "v1"
    probes, probe_hashes, empty_hash = load_probes(probes_dir)

    print(f"Loaded {len(probes)} probes from {probes_dir}")

    try:
        import tiktoken
        from tokenizers import Tokenizer
    except ImportError as e:
        print(f"Error: Missing required build dependencies (tiktoken, tokenizers): {e}", file=sys.stderr)
        sys.exit(1)

    # Family registry
    families_config = {
        "o200k_base": {
            "display_name": "OpenAI o200k (GPT-4o / o1 / o3)",
            "backend": "tiktoken",
            "target": "o200k_base",
            "source_url": "https://github.com/openai/tiktoken",
            "license": "MIT",
            "vocab_size": 200019,
        },
        "cl100k_base": {
            "display_name": "OpenAI cl100k (GPT-4 / GPT-3.5-Turbo)",
            "backend": "tiktoken",
            "target": "cl100k_base",
            "source_url": "https://github.com/openai/tiktoken",
            "license": "MIT",
            "vocab_size": 100277,
        },
        "p50k_base": {
            "display_name": "OpenAI p50k (Codex / Davinci-002)",
            "backend": "tiktoken",
            "target": "p50k_base",
            "source_url": "https://github.com/openai/tiktoken",
            "license": "MIT",
            "vocab_size": 50281,
        },
        "r50k_base": {
            "display_name": "OpenAI r50k (GPT-2 / GPT-3 / Davinci-001)",
            "backend": "tiktoken",
            "target": "r50k_base",
            "source_url": "https://github.com/openai/tiktoken",
            "license": "MIT",
            "vocab_size": 50257,
        },
        "llama3": {
            "display_name": "Meta Llama 3 / 3.1 / 3.2 / 3.3 (128k)",
            "backend": "hf",
            "target": "unsloth/llama-3-8b",
            "source_url": "https://huggingface.co/meta-llama/Meta-Llama-3-8B",
            "license": "Llama 3 Community License",
            "vocab_size": 128256,
        },
        "llama2": {
            "display_name": "Meta Llama 2 / CodeLlama (32k)",
            "backend": "hf",
            "target": "huggyllama/llama-7b",
            "source_url": "https://huggingface.co/meta-llama/Llama-2-7b-hf",
            "license": "Llama 2 Community License",
            "vocab_size": 32000,
        },
        "qwen2_5": {
            "display_name": "Alibaba Qwen 2 / 2.5 (151k)",
            "backend": "hf",
            "target": "Qwen/Qwen2.5-7B",
            "source_url": "https://huggingface.co/Qwen/Qwen2.5-7B",
            "license": "Apache-2.0",
            "vocab_size": 151665,
        },
        "glm4": {
            "display_name": "Zhipu GLM-4 (151k)",
            "backend": "hf",
            "target": "THUDM/glm-4-9b-hf",
            "source_url": "https://huggingface.co/THUDM/glm-4-9b",
            "license": "Apache-2.0",
            "vocab_size": 151343,
        },
        "gemma": {
            "display_name": "Google Gemma 1 / Gemma 2 (256k)",
            "backend": "hf",
            "target": "unsloth/gemma-2-9b",
            "source_url": "https://huggingface.co/google/gemma-2-9b",
            "license": "Gemma Terms of Use",
            "vocab_size": 256000,
        },
        "deepseek_v2": {
            "display_name": "DeepSeek V2 (100k)",
            "backend": "hf",
            "target": "deepseek-ai/DeepSeek-V2-Lite",
            "source_url": "https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite",
            "license": "DeepSeek License",
            "vocab_size": 100002,
        },
        "deepseek_v3": {
            "display_name": "DeepSeek V3 / R1 (128k)",
            "backend": "hf",
            "target": "deepseek-ai/DeepSeek-V3",
            "source_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3",
            "license": "MIT",
            "vocab_size": 128815,
        },
        "mistral_v3": {
            "display_name": "Mistral v0.3 / Tekken (32k)",
            "backend": "hf",
            "target": "mistralai/Mistral-7B-v0.3",
            "source_url": "https://huggingface.co/mistralai/Mistral-7B-v0.3",
            "license": "Apache-2.0",
            "vocab_size": 32768,
        },
        "yi": {
            "display_name": "01-ai Yi 1.0 / 1.5 (64k)",
            "backend": "hf",
            "target": "01-ai/Yi-1.5-9B",
            "source_url": "https://huggingface.co/01-ai/Yi-1.5-9B",
            "license": "Apache-2.0",
            "vocab_size": 63992,
        },
        "phi3": {
            "display_name": "Microsoft Phi-3 / 3.5 (32k)",
            "backend": "hf",
            "target": "microsoft/Phi-3-mini-4k-instruct",
            "source_url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct",
            "license": "MIT",
            "vocab_size": 32011,
        },
        "internlm2": {
            "display_name": "Shanghai AI Lab InternLM 2 / 2.5 (92k)",
            "backend": "hf",
            "target": "internlm/internlm2_5-7b",
            "source_url": "https://huggingface.co/internlm/internlm2_5-7b",
            "license": "Apache-2.0",
            "vocab_size": 92544,
        },
        "starcoder2": {
            "display_name": "BigCode StarCoder 2 (49k)",
            "backend": "hf",
            "target": "bigcode/starcoder2-15b",
            "source_url": "https://huggingface.co/bigcode/starcoder2-15b",
            "license": "BigCode OpenRAIL-M",
            "vocab_size": 49152,
        },
    }

    families_data = {}

    for fam_id, cfg in families_config.items():
        print(f"Encoding family: {fam_id} ({cfg['display_name']})...")
        if cfg["backend"] == "tiktoken":
            enc = tiktoken.get_encoding(cfg["target"])
            def encode_fn(text):
                return enc.encode(text, allowed_special="all")
        elif cfg["backend"] == "hf":
            tok = Tokenizer.from_pretrained(cfg["target"])
            def encode_fn(text, tok=tok):
                return tok.encode(text, add_special_tokens=False).ids
        else:
            raise ValueError(f"Unknown backend: {cfg['backend']}")

        vector = {}
        for p_id in PROBE_ORDER:
            token_ids = encode_fn(probes[p_id])
            vector[p_id] = len(token_ids)

        families_data[fam_id] = {
            "display_name": cfg["display_name"],
            "backend": cfg["backend"],
            "target": cfg["target"],
            "source_url": cfg["source_url"],
            "license": cfg["license"],
            "vocab_size": cfg["vocab_size"],
            "vector": vector,
        }

    # Verify no collisions (pairwise L1 > 0)
    fam_names = list(families_data.keys())
    collisions = []
    min_l1 = float("inf")
    closest = None

    for i in range(len(fam_names)):
        for j in range(i + 1, len(fam_names)):
            f1, f2 = fam_names[i], fam_names[j]
            v1 = families_data[f1]["vector"]
            v2 = families_data[f2]["vector"]
            l1 = sum(abs(v1[p] - v2[p]) for p in PROBE_ORDER)
            if l1 < min_l1:
                min_l1 = l1
                closest = (f1, f2, l1)
            if l1 == 0:
                collisions.append((f1, f2))

    if collisions:
        print(f"ERROR: Collisions detected between families: {collisions}", file=sys.stderr)
        sys.exit(1)

    print(f"Validation passed! 0 collisions. Minimum pairwise L1 distance: {min_l1} between {closest[0]} and {closest[1]}")

    catalog = {
        "version": "v1",
        "generated_at": "2026-08-24",
        "probe_order": PROBE_ORDER,
        "probes": {
            p: {
                "length": len(probes[p]),
                "sha256": probe_hashes[p],
            }
            for p in PROBE_ORDER
        },
        "empty_probe_sha256": empty_hash,
        "families": families_data,
    }

    # Write output to catalog/v1.json
    out_json = catalog_dir / "v1.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_json}")

    # Copy to src/tokwhois/catalog/v1.json
    pkg_catalog_dir = catalog_dir.parent / "src" / "tokwhois" / "catalog"
    pkg_catalog_dir.mkdir(parents=True, exist_ok=True)
    pkg_out_json = pkg_catalog_dir / "v1.json"
    with open(pkg_out_json, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Wrote {pkg_out_json}")

if __name__ == "__main__":
    build_catalog()
