"""Command line interface for tokwhois."""

import argparse
import os
import sys
import time
from typing import List, Optional

from tokwhois import __version__
from tokwhois.catalog_data import load_catalog, get_families
from tokwhois.client import ProbeClient, ProbeClientError
from tokwhois.encode_local import encode_with_local_file
from tokwhois.match import match_vector
from tokwhois.report import format_cli_report, format_json_report
from tokwhois.selftest import run_selftest


def run_demo(json_output: bool = False) -> int:
    """Run an offline interactive demonstration using the embedded public catalog."""
    catalog = load_catalog()
    families = get_families(catalog)

    # Demo against GLM-4 and Llama-3 and OpenAI o200k public vectors
    demo_fam = "glm4" if "glm4" in families else list(families.keys())[0]
    sample_vec = dict(families[demo_fam]["vector"])

    if not json_output:
        print("\n\033[1m\033[38;5;45mtokwhois demo\033[0m — \033[2mrunning offline against embedded v1 catalog (zero network)\033[0m")
        print("\033[38;5;244mSimulating live endpoint response for public tokenizer...\033[0m")
        time.sleep(0.3)

    # Add a mock offset of 7 tokens as shown in README to demonstrate calibration
    mock_offset = 7
    framed_vector = {k: v + mock_offset for k, v in sample_vec.items()}
    
    # Live calibration: subtract offset
    calibrated_vector = {k: max(1, v - mock_offset) for k, v in framed_vector.items()}
    result = match_vector(calibrated_vector, catalog=catalog, offset=mock_offset)

    if json_output:
        print(format_json_report(result))
    else:
        print(format_cli_report(result, top_n_compare=4))

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="tokwhois",
        description="Whois for stealth LLMs: fingerprint tokenizer families via prompt token fertility vectors.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  tokwhois demo
  tokwhois https://api.openai.com/v1 --model gpt-4o-mini
  tokwhois https://api.together.xyz/v1 --model meta-llama/Llama-3-8b-chat-hf
  tokwhois --local path/to/tokenizer.json
  tokwhois --selftest
""",
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Target OpenAI-compatible base URL (e.g. https://api.openai.com/v1) or 'demo'",
    )
    parser.add_argument(
        "-m", "--model",
        help="Target model identifier (required for live URL mode)",
    )
    parser.add_argument(
        "-k", "--api-key",
        default=os.environ.get("OPENAI_API_KEY"),
        help="API key for authentication (defaults to OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--header",
        action="append",
        dest="headers",
        help="Custom HTTP header in 'Name: Value' format (can be specified multiple times)",
    )
    parser.add_argument(
        "--local",
        help="Path to local HuggingFace tokenizer.json file",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run offline self-test and verify catalog integrity",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=25.0,
        help="HTTP request timeout in seconds (default: 25.0)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"tokwhois {__version__}",
    )

    args = parser.parse_args(argv)

    # 1. Selftest Mode
    if args.selftest:
        success = run_selftest(verbose=not args.json)
        if args.json:
            print(json.dumps({"selftest_passed": success}))
        return 0 if success else 1

    # 2. Demo Mode
    if args.target == "demo" or (args.target is None and not args.local and not args.selftest):
        return run_demo(json_output=args.json)

    # 3. Local Tokenizer File Mode
    if args.local:
        try:
            vector = encode_with_local_file(args.local)
        except Exception as exc:
            print(f"Error reading local tokenizer: {exc}", file=sys.stderr)
            return 1

        result = match_vector(vector)
        if args.json:
            print(format_json_report(result))
        else:
            print(format_cli_report(result))
        return 0

    # 4. Live API Mode
    if args.target:
        if not args.model:
            print("Error: --model (-m) is required when specifying a live URL endpoint.", file=sys.stderr)
            return 1

        # Parse custom headers
        custom_headers = {}
        if args.headers:
            for h in args.headers:
                if ":" in h:
                    k, v = h.split(":", 1)
                    custom_headers[k.strip()] = v.strip()

        client = ProbeClient(
            base_url=args.target,
            model=args.model,
            api_key=args.api_key,
            headers=custom_headers,
            timeout=args.timeout,
        )

        if not args.json:
            print(f"\n\033[1mProbing endpoint:\033[0m {client.endpoint_url} (\033[38;5;75mmodel={args.model}\033[0m)")

        def progress(p_id: str, current: int, total: int, count: int):
            if not args.json and sys.stdout.isatty():
                sys.stdout.write(f"\r\033[K  \033[38;5;244m[{current:2d}/{total:2d}]\033[0m probe \033[38;5;45m{p_id:<14}\033[0m → \033[1m{count} tokens\033[0m")
                sys.stdout.flush()

        try:
            probe_data = client.probe(progress_callback=progress)
        except ProbeClientError as exc:
            if not args.json and sys.stdout.isatty():
                sys.stdout.write("\n")
            print(f"\n\033[38;5;196mError probing endpoint:\033[0m {exc}", file=sys.stderr)
            return 2
        except Exception as exc:
            if not args.json and sys.stdout.isatty():
                sys.stdout.write("\n")
            print(f"\n\033[38;5;196mUnexpected error:\033[0m {exc}", file=sys.stderr)
            return 3

        if not args.json and sys.stdout.isatty():
            sys.stdout.write("\n")

        result = match_vector(
            observed_vector=probe_data["calibrated_vector"],
            offset=probe_data["offset"],
        )

        if args.json:
            full_data = result.to_dict()
            full_data["endpoint"] = probe_data["endpoint_url"]
            full_data["model"] = probe_data["model"]
            full_data["latencies"] = probe_data["latencies"]
            print(json.dumps(full_data, indent=2, ensure_ascii=False))
        else:
            print(format_cli_report(result))

        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
