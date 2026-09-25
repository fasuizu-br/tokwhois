#!/usr/bin/env python3
"""Build and validate the public tokenizer fertility catalog (v1.json).

This script:
1. Loads the 14 versioned probes from probes/v1/*.txt
2. Encodes them using standard public tokenizer backends (tiktoken, tokenizers)
3. Checks for zero-distance collisions across all pairs
4. Writes catalog/v1.json and src/tokwhois/catalog/v1.json
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

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

def get_default_families_config():
    return {
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
            "revision": "b0c09b815d8a74b70622c740f108c995c5041a14",
            "source_url": "https://huggingface.co/meta-llama/Meta-Llama-3-8B",
            "license": "Llama 3 Community License",
            "vocab_size": 128256,
        },
        "llama2": {
            "display_name": "Meta Llama 2 / CodeLlama (32k)",
            "backend": "hf",
            "target": "huggyllama/llama-7b",
            "revision": "4782ad278652c7c71b72204d462d6d01eaaf7549",
            "source_url": "https://huggingface.co/meta-llama/Llama-2-7b-hf",
            "license": "LLaMA license (huggyllama mirror of LLaMA 1, non-commercial); tokenizer identical to Llama 2",
            "vocab_size": 32000,
        },
        "qwen2_5": {
            "display_name": "Alibaba Qwen 2 / 2.5 (151k)",
            "backend": "hf",
            "target": "Qwen/Qwen2.5-7B",
            "revision": "d149729398750b98c0af14eb82c78cfe92750796",
            "source_url": "https://huggingface.co/Qwen/Qwen2.5-7B",
            "license": "Apache-2.0",
            "vocab_size": 151665,
        },
        "qwen3_8": {
            "display_name": "Alibaba Qwen 3.8 (248k)",
            "backend": "hf",
            "target": "Qwen/Qwen3.8-Flash-Next",
            "revision": "de4b8e4d43b917e7706784d8bb445c9af86a3540",
            "source_url": "https://huggingface.co/Qwen/Qwen3.8-Flash-Next",
            "license": "qwen-community-1.0",
            "vocab_size": 248320,
        },
        "glm4": {
            "display_name": "Zhipu GLM-4 (151k)",
            "backend": "hf",
            "target": "THUDM/glm-4-9b-hf",
            "revision": "b44e98fcc8df0faba03a48b405356af6b91821e7",
            "source_url": "https://huggingface.co/THUDM/glm-4-9b",
            "license": "glm-4 license (custom; see the model repository)",
            "vocab_size": 151343,
        },
        "glm5": {
            "display_name": "Zhipu GLM-5 / 5.3 (155k)",
            "backend": "hf",
            "target": "zai-org/GLM-5.3-Flash",
            "revision": "eb9eb208eb0d988989d07a6a12d0fdeb5f52574a",
            "source_url": "https://huggingface.co/zai-org/GLM-5.3-Flash",
            "license": "MIT",
            "vocab_size": 154880,
        },
        "gemma": {
            "display_name": "Google Gemma 1 / Gemma 2 (256k)",
            "backend": "hf",
            "target": "unsloth/gemma-2-9b",
            "revision": "9145841c83add11c48155cd7bb87d8656703f997",
            "source_url": "https://huggingface.co/google/gemma-2-9b",
            "license": "Gemma Terms of Use",
            "vocab_size": 256000,
        },
        "deepseek_v2": {
            "display_name": "DeepSeek V2 (100k)",
            "backend": "hf",
            "target": "deepseek-ai/DeepSeek-V2-Lite",
            "revision": "604d5664dddd88a0433dbae533b7fe9472482de0",
            "source_url": "https://huggingface.co/deepseek-ai/DeepSeek-V2-Lite",
            "license": "DeepSeek License",
            "vocab_size": 100002,
        },
        "deepseek_v3": {
            "display_name": "DeepSeek V3 / R1 (128k)",
            "backend": "hf",
            "target": "deepseek-ai/DeepSeek-V3",
            "revision": "e815299b0bcbac849fa540c768ef21845365c9eb",
            "source_url": "https://huggingface.co/deepseek-ai/DeepSeek-V3",
            "license": "DeepSeek Model License (code: MIT)",
            "vocab_size": 128815,
        },
        "mistral_v3": {
            "display_name": "Mistral v0.3 / Tekken (32k)",
            "backend": "hf",
            "target": "mistralai/Mistral-7B-v0.3",
            "revision": "caa1feb0e54d415e2df31207e5f4e273e33509b1",
            "source_url": "https://huggingface.co/mistralai/Mistral-7B-v0.3",
            "license": "Apache-2.0",
            "vocab_size": 32768,
        },
        "yi": {
            "display_name": "01-ai Yi 1.0 / 1.5 (64k)",
            "backend": "hf",
            "target": "01-ai/Yi-1.5-9B",
            "revision": "80d5471b1eae28beae33e06eadbd4b48e74d4ce1",
            "source_url": "https://huggingface.co/01-ai/Yi-1.5-9B",
            "license": "Apache-2.0",
            "vocab_size": 63992,
        },
        "phi3": {
            "display_name": "Microsoft Phi-3 / 3.5 (32k)",
            "backend": "hf",
            "target": "microsoft/Phi-3-mini-4k-instruct",
            "revision": "f39ac1d28e925b323eae81227eaba4464caced4e",
            "source_url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct",
            "license": "MIT",
            "vocab_size": 32011,
        },
        "internlm2": {
            "display_name": "Shanghai AI Lab InternLM 2 / 2.5 (92k)",
            "backend": "hf",
            "target": "internlm/internlm2_5-7b",
            "revision": "0481d88c24f938d97226eb8556cf1de89ba60772",
            "source_url": "https://huggingface.co/internlm/internlm2_5-7b",
            "license": "InternLM model terms (code: Apache-2.0; commercial use on application)",
            "vocab_size": 92544,
        },
        "starcoder2": {
            "display_name": "BigCode StarCoder 2 (49k)",
            "backend": "hf",
            "target": "bigcode/starcoder2-15b",
            "revision": "46d44742909c03ac8cee08eb03fdebce02e193ec",
            "source_url": "https://huggingface.co/bigcode/starcoder2-15b",
            "license": "BigCode OpenRAIL-M",
            "vocab_size": 49152,
        },
    }

def load_sources_toml(sources_file: Path):
    if not sources_file.exists() or tomllib is None:
        return None
    try:
        with open(sources_file, "rb" if hasattr(tomllib, "load") else "r", encoding=None if hasattr(tomllib, "load") else "utf-8") as f:
            data = tomllib.load(f)
            return data.get("families")
    except Exception as exc:
        print(f"Warning: could not parse {sources_file}: {exc}", file=sys.stderr)
        return None

def resolve_local_overrides(args_local: list[str] | None, local_dir: str | None, json_override: str | None) -> dict[str, Path]:
    local_map: dict[str, Path] = {}

    # 1. Environment variable TOKWHOIS_LOCAL_DIR
    env_dir = os.environ.get("TOKWHOIS_LOCAL_DIR")
    effective_dir = local_dir or env_dir
    if effective_dir:
        d = Path(effective_dir)
        if d.is_dir():
            for f in d.glob("*.tokenizer.json"):
                stem = f.name.replace(".tokenizer.json", "")
                local_map[stem.lower()] = f
                # Also handle variations like GLM-5.3-Flash -> glm5
                if "glm-5" in stem.lower() or "glm5" in stem.lower():
                    local_map["glm5"] = f
                if "qwen3.8" in stem.lower() or "qwen3_8" in stem.lower() or "qwen3" in stem.lower():
                    local_map["qwen3_8"] = f

    # 2. Environment variable TOKWHOIS_LOCAL_TOKENIZERS (JSON or key=val,key2=val)
    env_toks = os.environ.get("TOKWHOIS_LOCAL_TOKENIZERS")
    if env_toks:
        try:
            parsed = json.loads(env_toks)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    local_map[k] = Path(v)
        except Exception:
            for item in env_toks.split(","):
                if "=" in item:
                    k, v = item.split("=", 1)
                    local_map[k.strip()] = Path(v.strip())

    # 3. Specific environment variables TOKWHOIS_TOKENIZER_<FAM> or TOKWHOIS_LOCAL_<FAM>
    for env_k, env_v in os.environ.items():
        if env_k.startswith("TOKWHOIS_TOKENIZER_") or env_k.startswith("TOKWHOIS_LOCAL_"):
            fam_key = env_k.split("_", 2)[-1].lower()
            local_map[fam_key] = Path(env_v)

    # 4. JSON file or string override
    if json_override:
        p = Path(json_override)
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            data = json.loads(json_override)
        if isinstance(data, dict):
            for k, v in data.items():
                local_map[k] = Path(v)

    # 5. CLI --local arguments (format: fam=path)
    if args_local:
        for item in args_local:
            if "=" in item:
                k, v = item.split("=", 1)
                local_map[k.strip()] = Path(v.strip())

    return local_map

def build_catalog(
    local_overrides: dict[str, Path] | None = None,
    output_version: str = "v1.1",
    generated_date: str = "2026-08-27",
):
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

    # Load base family configurations
    sources_toml = catalog_dir / "sources.toml"
    toml_fams = load_sources_toml(sources_toml)
    families_config = toml_fams if toml_fams is not None else get_default_families_config()

    local_map = local_overrides or {}
    families_data = {}

    for fam_id, cfg in families_config.items():
        print(f"Encoding family: {fam_id} ({cfg['display_name']})...")
        encode_fn = None

        # Check local file override first
        local_path = local_map.get(fam_id)
        if local_path and Path(local_path).is_file():
            print(f"  -> Using local tokenizer file for {fam_id}: {local_path}")
            tok = Tokenizer.from_file(str(local_path))
            encode_fn = lambda text, tok=tok: tok.encode(text, add_special_tokens=False).ids
        elif cfg["backend"] == "tiktoken":
            enc = tiktoken.get_encoding(cfg["target"])
            encode_fn = lambda text, enc=enc: enc.encode(text, allowed_special="all")
        elif cfg["backend"] == "hf":
            revision = cfg.get("revision")
            try:
                kwargs = {}
                if revision:
                    kwargs["revision"] = revision
                tok = Tokenizer.from_pretrained(cfg["target"], **kwargs)
                encode_fn = lambda text, tok=tok: tok.encode(text, add_special_tokens=False).ids
            except Exception as hf_err:
                rev_info = f" (revision {revision})" if revision else ""
                raise RuntimeError(
                    f"Cannot encode family '{fam_id}': HF download failed for target '{cfg['target']}'{rev_info}: {hf_err}"
                ) from hf_err
        else:
            raise ValueError(f"Unknown backend: {cfg['backend']}")

        if encode_fn is not None:
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
        if "revision" in cfg:
            families_data[fam_id]["revision"] = cfg["revision"]

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

    print(f"Validation passed! 0 collisions across {len(fam_names)} families. Minimum pairwise L1 distance: {min_l1} between {closest[0]} and {closest[1]}")

    catalog = {
        "version": output_version,
        "generated_at": generated_date,
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

    return catalog

def main():
    parser = argparse.ArgumentParser(description="Build and validate public tokenizer catalog.")
    parser.add_argument(
        "--local",
        action="append",
        dest="local_overrides",
        help="Local tokenizer override in format: <family_id>=<path_to_tokenizer.json>",
    )
    parser.add_argument(
        "--local-dir",
        help="Directory containing local *.tokenizer.json files",
    )
    parser.add_argument(
        "--local-json",
        help="JSON file or string with {family_id: path_to_tokenizer.json} mapping",
    )
    parser.add_argument(
        "--version",
        default="v1.1",
        help="Catalog version string (default: v1.1)",
    )
    parser.add_argument(
        "--date",
        default="2026-08-27",
        help="Catalog generation date (default: 2026-08-27)",
    )
    args = parser.parse_args()

    local_overrides = resolve_local_overrides(args.local_overrides, args.local_dir, args.local_json)
    build_catalog(
        local_overrides=local_overrides,
        output_version=args.version,
        generated_date=args.date,
    )

if __name__ == "__main__":
    main()
