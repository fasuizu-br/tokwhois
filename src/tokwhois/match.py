"""Fertility vector matching algorithms, L1 distances, and ambiguity heuristics."""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple
from tokwhois.catalog_data import load_catalog, get_families, get_probe_order
from tokwhois.probes import PROBE_ORDER


@dataclass
class FamilyMatch:
    family_id: str
    display_name: str
    l1_distance: int
    vector: Dict[str, int]
    source_url: str
    license: str
    vocab_size: int


@dataclass
class MatchResult:
    observed_vector: Dict[str, int]
    top_match: FamilyMatch
    runner_up: Optional[FamilyMatch]
    margin: int
    confidence: float
    is_ambiguous: bool
    ranked_matches: List[FamilyMatch]
    discriminating_probes: List[str]
    probe_order: List[str]
    offset: int = 0
    catalog_version: str = "v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.top_match.family_id,
            "display_name": self.top_match.display_name,
            "l1_distance": self.top_match.l1_distance,
            "confidence": round(self.confidence, 4),
            "is_ambiguous": self.is_ambiguous,
            "margin": self.margin,
            "runner_up": (
                {
                    "family": self.runner_up.family_id,
                    "display_name": self.runner_up.display_name,
                    "l1_distance": self.runner_up.l1_distance,
                }
                if self.runner_up
                else None
            ),
            "discriminating_probes": self.discriminating_probes,
            "offset": self.offset,
            "catalog_version": self.catalog_version,
            "observed_vector": self.observed_vector,
            "rankings": [
                {
                    "rank": idx + 1,
                    "family": m.family_id,
                    "display_name": m.display_name,
                    "l1_distance": m.l1_distance,
                }
                for idx, m in enumerate(self.ranked_matches)
            ],
        }


def compute_l1_distance(
    v1: Dict[str, int],
    v2: Dict[str, int],
    probes: Optional[List[str]] = None,
) -> int:
    """Compute L1 Manhattan distance between two probe vectors."""
    if probes is None:
        probes = PROBE_ORDER
    return sum(abs(v1.get(p, 0) - v2.get(p, 0)) for p in probes)


def match_vector(
    observed_vector: Dict[str, int],
    catalog: Optional[Dict[str, Any]] = None,
    margin_threshold: int = 2,
    offset: int = 0,
) -> MatchResult:
    """Match an observed 14-integer fertility vector against the public catalog."""
    if catalog is None:
        catalog = load_catalog()

    families = get_families(catalog)
    probe_order = get_probe_order(catalog) or PROBE_ORDER
    catalog_version = catalog.get("version", "v1")

    ranked: List[FamilyMatch] = []
    for fam_id, info in families.items():
        fam_vec = info["vector"]
        dist = compute_l1_distance(observed_vector, fam_vec, probe_order)
        ranked.append(
            FamilyMatch(
                family_id=fam_id,
                display_name=info.get("display_name", fam_id),
                l1_distance=dist,
                vector=fam_vec,
                source_url=info.get("source_url", ""),
                license=info.get("license", "unknown"),
                vocab_size=info.get("vocab_size", 0),
            )
        )

    ranked.sort(key=lambda x: x.l1_distance)

    top = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    if runner_up is not None:
        margin = runner_up.l1_distance - top.l1_distance
    else:
        margin = 999

    # Confidence calculation:
    # If exact match L1=0:
    if top.l1_distance == 0:
        if margin >= 4:
            confidence = 1.00
        elif margin >= 2:
            confidence = 0.95
        else:
            confidence = 0.85
    else:
        # Distance penalty + margin bonus
        dist_factor = max(0.0, 1.0 - (top.l1_distance / 25.0))
        margin_factor = min(1.0, max(0.1, margin / 5.0))
        confidence = round(dist_factor * margin_factor, 2)

    # Ambiguity check
    # Top match is ambiguous if margin < margin_threshold or total distance is excessively large
    is_ambiguous = (margin < margin_threshold) or (top.l1_distance >= 20)

    # Find discriminating probes between winner and runner-up
    discriminating: List[str] = []
    if runner_up is not None:
        for p in probe_order:
            top_val = top.vector.get(p, 0)
            run_val = runner_up.vector.get(p, 0)
            if top_val != run_val:
                discriminating.append(p)

    return MatchResult(
        observed_vector=observed_vector,
        top_match=top,
        runner_up=runner_up,
        margin=margin,
        confidence=confidence,
        is_ambiguous=is_ambiguous,
        ranked_matches=ranked,
        discriminating_probes=discriminating,
        probe_order=probe_order,
        offset=offset,
        catalog_version=catalog_version,
    )
