#!/usr/bin/env python3
"""Programmatic usage example for tokwhois."""

import json
from tokwhois import match_vector, ProbeClient, load_catalog

def main():
    print("=== tokwhois Programmatic Quickstart ===\n")

    # 1. Matching a fertility vector directly
    print("1. Matching a 14-integer fertility vector against public catalog:")
    
    # Example vector matching OpenAI o200k (GPT-4o)
    sample_o200k_vector = {
        "cjk30": 28,
        "space40": 1,
        "digit64": 22,
        "ascii100": 26,
        "emoji8": 13,
        "hello_leadsp": 1,
        "nl16": 1,
        "tab16": 1,
        "cjk_en": 8,
        "im_start": 6,
        "gmask": 3,
        "eot": 1,
        "bot_llama": 7,
        "byte_rare": 23,
    }

    result = match_vector(sample_o200k_vector)
    print(f"  Top Match:    {result.top_match.display_name} (L1 distance: {result.top_match.l1_distance})")
    print(f"  Confidence:   {result.confidence:.2f}")
    print(f"  Runner-up:    {result.runner_up.display_name} (margin: {result.margin} tokens)")
    print(f"  Is Ambiguous: {result.is_ambiguous}")

    # 2. Inspecting Catalog metadata
    catalog = load_catalog()
    print(f"\n2. Loaded catalog v{catalog.get('version')} with {len(catalog.get('families', {}))} public tokenizer families.")

    # 3. Example Live Probe Client instantiation (dry run)
    print("\n3. Live client setup (usage against any OpenAI-compatible API):")
    client = ProbeClient(
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        api_key="sk-example-key",
    )
    print(f"  Target Endpoint: {client.endpoint_url}")
    print(f"  Model:           {client.model}")
    print("  (Run 'tokwhois <url> --model <model>' in terminal for live probing)\n")

if __name__ == "__main__":
    main()
