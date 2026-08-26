"""Access functions for the pinned public tokenizer catalog."""

import importlib.resources
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_catalog(custom_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load catalog JSON data from file or embedded package data."""
    if custom_path is not None:
        with open(custom_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Try importlib.resources (Python 3.9+)
    try:
        if hasattr(importlib.resources, "files"):
            ref = importlib.resources.files("tokwhois.catalog").joinpath("v1.json")
            if ref.is_file():
                return json.loads(ref.read_text(encoding="utf-8"))
    except Exception:
        pass

    # Fallback to relative path lookup
    pkg_dir = Path(__file__).resolve().parent
    local_catalog = pkg_dir / "catalog" / "v1.json"
    if local_catalog.exists():
        with open(local_catalog, "r", encoding="utf-8") as f:
            return json.load(f)

    root_catalog = pkg_dir.parent.parent / "catalog" / "v1.json"
    if root_catalog.exists():
        with open(root_catalog, "r", encoding="utf-8") as f:
            return json.load(f)

    raise FileNotFoundError("Could not locate catalog/v1.json in package or repository.")


def get_families(catalog: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get all tokenizer families from the catalog."""
    if catalog is None:
        catalog = load_catalog()
    return catalog.get("families", {})


def get_probe_order(catalog: Optional[Dict[str, Any]] = None) -> List[str]:
    """Get probe sequence order."""
    if catalog is None:
        catalog = load_catalog()
    return catalog.get("probe_order", [])
