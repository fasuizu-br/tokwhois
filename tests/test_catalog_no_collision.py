"""Tests verifying zero pairwise collisions across all public catalog entries."""

import pytest
from tokwhois.catalog_data import load_catalog, get_families
from tokwhois.match import compute_l1_distance
from tokwhois.probes import PROBE_ORDER


def test_catalog_has_no_collisions():
    catalog = load_catalog()
    families = get_families(catalog)
    probe_order = catalog.get("probe_order", PROBE_ORDER)

    assert len(families) >= 15, "Catalog should contain at least 15 public families"

    fam_keys = list(families.keys())
    collisions = []
    min_dist = 999999
    closest = None

    for i in range(len(fam_keys)):
        for j in range(i + 1, len(fam_keys)):
            f1, f2 = fam_keys[i], fam_keys[j]
            v1, v2 = families[f1]["vector"], families[f2]["vector"]
            d = compute_l1_distance(v1, v2, probe_order)
            if d < min_dist:
                min_dist = d
                closest = (f1, f2, d)
            if d == 0:
                collisions.append((f1, f2))

    assert len(collisions) == 0, f"Collisions found: {collisions}"
    assert min_dist >= 4, f"Minimum distance should be >= 4, got {min_dist} between {closest}"


def test_all_probe_lengths_positive():
    catalog = load_catalog()
    families = get_families(catalog)
    probe_order = catalog.get("probe_order", PROBE_ORDER)

    for fam_id, info in families.items():
        vec = info["vector"]
        for p in probe_order:
            assert p in vec, f"Probe {p} missing in family {fam_id}"
            assert isinstance(vec[p], int)
            assert vec[p] >= 1, f"Token count for {p} in {fam_id} should be >= 1"
