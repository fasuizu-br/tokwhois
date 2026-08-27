"""Tests verifying zero pairwise collisions across all public catalog entries."""

import pytest
from tokwhois.catalog_data import load_catalog, get_families
from tokwhois.match import compute_l1_distance
from tokwhois.probes import PROBE_ORDER


def test_catalog_has_no_collisions():
    catalog = load_catalog()
    families = get_families(catalog)
    probe_order = catalog.get("probe_order", PROBE_ORDER)

    assert len(families) >= 18, f"Catalog v1.1 should contain at least 18 public families, got {len(families)}"
    assert "glm5" in families, "Family glm5 must be present in catalog"
    assert "qwen3_8" in families, "Family qwen3_8 must be present in catalog"

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
    assert min_dist == 6, f"Documented minimum distance in catalog v1.1 is 6, got {min_dist} between {closest}"


def test_v11_families_measured_margins():
    """Verify exact documented L1 distances for v1.1 additions: glm5 (L1=8 from glm4) and qwen3_8 (L1=22 from qwen2_5)."""
    catalog = load_catalog()
    families = get_families(catalog)
    probe_order = catalog.get("probe_order", PROBE_ORDER)

    v_glm4 = families["glm4"]["vector"]
    v_glm5 = families["glm5"]["vector"]
    d_glm = compute_l1_distance(v_glm4, v_glm5, probe_order)
    assert d_glm == 8, f"Expected L1 distance of 8 between glm4 and glm5, got {d_glm}"

    # GLM-4 vs GLM-5 is isolated to emoji8: 21 vs 13
    assert abs(v_glm4["emoji8"] - v_glm5["emoji8"]) == 8
    for p in probe_order:
        if p != "emoji8":
            assert v_glm4[p] == v_glm5[p], f"Probe {p} should be identical between glm4 and glm5"

    v_qwen25 = families["qwen2_5"]["vector"]
    v_qwen38 = families["qwen3_8"]["vector"]
    d_qwen = compute_l1_distance(v_qwen25, v_qwen38, probe_order)
    assert d_qwen == 22, f"Expected L1 distance of 22 between qwen2_5 and qwen3_8, got {d_qwen}"

    # Qwen 2.5 vs Qwen 3.8 differs on cjk30 (26 vs 22), emoji8 (8 vs 19), byte_rare (16 vs 23)
    assert abs(v_qwen25["cjk30"] - v_qwen38["cjk30"]) == 4
    assert abs(v_qwen25["emoji8"] - v_qwen38["emoji8"]) == 11
    assert abs(v_qwen25["byte_rare"] - v_qwen38["byte_rare"]) == 7


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
