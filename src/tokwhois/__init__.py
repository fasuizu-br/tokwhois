"""tokwhois: Whois for stealth LLMs.

Identifies tokenizer families behind OpenAI-compatible APIs via prompt token fertility vectors.
"""

__version__ = "0.1.0"
__author__ = "Fabio Suizu / Brainiall"
__license__ = "Apache-2.0"

from tokwhois.probes import PROBE_ORDER, load_probes, get_probe_hashes
from tokwhois.catalog_data import load_catalog, get_families, get_probe_order
from tokwhois.match import match_vector, MatchResult
from tokwhois.client import ProbeClient, ProbeClientError
from tokwhois.selftest import run_selftest

__all__ = [
    "__version__",
    "PROBE_ORDER",
    "load_probes",
    "get_probe_hashes",
    "load_catalog",
    "get_families",
    "get_probe_order",
    "match_vector",
    "MatchResult",
    "ProbeClient",
    "ProbeClientError",
    "run_selftest",
]
