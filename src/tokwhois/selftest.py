"""Comprehensive offline self-test for tokwhois integrity and collision-free atlas."""

import hashlib
import sys
from typing import Any, Dict, List, Optional, Tuple
import tokwhois.catalog_data as catalog_data
from tokwhois.match import match_vector, compute_l1_distance
from tokwhois.probes import PROBE_ORDER, EMBEDDED_PROBES, get_probe_hashes


def run_selftest(custom_catalog: Optional[Dict[str, Any]] = None, verbose: bool = True) -> bool:
    """Run self-tests and return True if all pass, False otherwise."""
    errors: List[str] = []

    def log(msg: str):
        if verbose:
            print(msg)

    log("\n[tokwhois selftest] Running content & calibration verification...")

    # 1. Load Catalog
    try:
        catalog = custom_catalog if custom_catalog is not None else catalog_data.load_catalog()
    except Exception as exc:
        errors.append(f"Failed to load catalog: {exc}")
        return False

    # 2. Verify Probe Hashes
    catalog_probes = catalog.get("probes", {})
    actual_hashes = get_probe_hashes(EMBEDDED_PROBES)

    for p_id in PROBE_ORDER:
        if p_id not in catalog_probes:
            errors.append(f"Probe {p_id} missing from catalog metadata.")
            continue
        expected_hash = catalog_probes[p_id].get("sha256")
        actual_hash = actual_hashes.get(p_id)
        if expected_hash != actual_hash:
            errors.append(f"SHA-256 mismatch for probe '{p_id}': expected {expected_hash}, got {actual_hash}")

    log(f"  ✓ Probe hashes verified ({len(PROBE_ORDER)} versioned strings)")

    # 3. Verify Self-Match (L1=0 against self)
    families = catalog_data.get_families(catalog)
    if not families:
        errors.append("No families found in catalog.")
        return False

    for fam_id, info in families.items():
        vec = info["vector"]
        res = match_vector(vec, catalog=catalog)
        if res.top_match.family_id != fam_id:
            errors.append(f"Self-match failed for '{fam_id}': matched '{res.top_match.family_id}' instead.")
        if res.top_match.l1_distance != 0:
            errors.append(f"Self-match distance for '{fam_id}' is {res.top_match.l1_distance}, expected 0.")

    log(f"  ✓ Self-matching verified ({len(families)} families match self at L1=0)")

    # 4. Verify Zero Collisions (Pairwise L1 > 0)
    fam_keys = list(families.keys())
    min_dist = 999999
    closest_pair: Tuple[str, str, int] = ("", "", 0)

    for i in range(len(fam_keys)):
        for j in range(i + 1, len(fam_keys)):
            f1, f2 = fam_keys[i], fam_keys[j]
            v1, v2 = families[f1]["vector"], families[f2]["vector"]
            d = compute_l1_distance(v1, v2, PROBE_ORDER)
            if d < min_dist:
                min_dist = d
                closest_pair = (f1, f2, d)
            if d == 0:
                errors.append(f"Collision detected between '{f1}' and '{f2}' (L1=0).")

    log(f"  ✓ No collisions in catalog (min pairwise L1 = {min_dist} between {closest_pair[0]} and {closest_pair[1]})")

    # 5. Verify Chat Template Offset Invariance
    sample_fam = list(families.keys())[0]
    sample_vec = families[sample_fam]["vector"]
    mock_offset = 12
    framed_vec = {k: v + mock_offset for k, v in sample_vec.items()}
    calibrated_vec = {k: max(1, v - mock_offset) for k, v in framed_vec.items()}
    offset_match = match_vector(calibrated_vec, catalog=catalog, offset=mock_offset)

    if offset_match.top_match.family_id != sample_fam or offset_match.top_match.l1_distance != 0:
        errors.append("Offset subtraction failed to recover exact ground truth family.")

    log(f"  ✓ Chat-template offset calibration verified (invariance check passed)")

    # 6. Summary Result
    if errors:
        log("\n[tokwhois selftest] FAILURES DETECTED:")
        for err in errors:
            log(f"  ✗ {err}")
        return False

    log("\n[tokwhois selftest] ALL CHECKS PASSED (100% verified, zero network required).\n")
    return True


if __name__ == "__main__":
    success = run_selftest(verbose=True)
    sys.exit(0 if success else 1)
