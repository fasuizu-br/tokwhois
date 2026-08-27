"""Unit tests for fertility vector matching and L1 distance calculation."""

import pytest
from tokwhois.catalog_data import load_catalog, get_families
from tokwhois.match import match_vector, compute_l1_distance, MatchResult


def test_exact_match_all_catalog_families():
    catalog = load_catalog()
    families = get_families(catalog)

    for fam_id, fam_info in families.items():
        vector = fam_info["vector"]
        res = match_vector(vector, catalog=catalog)

        assert res.top_match.family_id == fam_id
        assert res.top_match.l1_distance == 0
        assert res.confidence >= 0.90
        assert not res.is_ambiguous
        assert res.margin > 0


def test_ranking_monotonic():
    catalog = load_catalog()
    families = get_families(catalog)

    sample_vec = families["o200k_base"]["vector"]
    res = match_vector(sample_vec, catalog=catalog)

    distances = [m.l1_distance for m in res.ranked_matches]
    assert distances == sorted(distances)
    assert distances[0] == 0


def test_ambiguity_threshold():
    catalog = load_catalog()
    families = get_families(catalog)

    v_llama2 = families["llama2"]["vector"]
    v_phi3 = families["phi3"]["vector"]

    # Synthesize an intermediate equidistant vector
    synthetic_vec = {}
    for k in v_llama2:
        synthetic_vec[k] = (v_llama2[k] + v_phi3[k]) // 2

    res = match_vector(synthetic_vec, catalog=catalog, margin_threshold=5)
    # Equidistant or very close margin should flag ambiguous
    if res.margin < 5:
        assert res.is_ambiguous is True


def test_discriminating_probes_present():
    catalog = load_catalog()
    families = get_families(catalog)

    v_glm4 = families["glm4"]["vector"]
    res_glm4 = match_vector(v_glm4, catalog=catalog)

    assert len(res_glm4.discriminating_probes) > 0
    # In catalog v1.1, the runner-up for GLM-4 is GLM-5, differing specifically on emoji8 (21 vs 13)
    assert "emoji8" in res_glm4.discriminating_probes

    v_qwen = families["qwen2_5"]["vector"]
    res_qwen = match_vector(v_qwen, catalog=catalog)
    # Runner-up for Qwen 2.5 is Qwen 3.8, differing on cjk30, emoji8, byte_rare
    assert "cjk30" in res_qwen.discriminating_probes
    assert "emoji8" in res_qwen.discriminating_probes
    assert "byte_rare" in res_qwen.discriminating_probes


def test_to_dict_serialization():
    catalog = load_catalog()
    v_qwen = catalog["families"]["qwen2_5"]["vector"]
    res = match_vector(v_qwen, catalog=catalog, offset=5)

    data = res.to_dict()
    assert data["family"] == "qwen2_5"
    assert data["l1_distance"] == 0
    assert data["offset"] == 5
    assert len(data["rankings"]) == len(catalog["families"])
