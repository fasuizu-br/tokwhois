"""Mutation tests proving that selftest fails when catalog or probes are corrupted."""

import copy
import pytest
from tokwhois.selftest import run_selftest
import tokwhois.catalog_data as catalog_module


def test_selftest_passes_on_valid_catalog():
    assert run_selftest(verbose=False) is True


def test_selftest_mutation_corrupted_vector():
    """Mutate a family vector to create a collision; selftest must fail."""
    real_catalog = catalog_module.load_catalog()
    corrupted_catalog = copy.deepcopy(real_catalog)

    # Force llama3 vector to match o200k_base (simulating collision)
    corrupted_catalog["families"]["llama3"]["vector"] = copy.deepcopy(
        corrupted_catalog["families"]["o200k_base"]["vector"]
    )

    assert run_selftest(custom_catalog=corrupted_catalog, verbose=False) is False


def test_selftest_mutation_corrupted_hash():
    """Mutate probe sha256 hash in catalog; selftest must fail."""
    real_catalog = catalog_module.load_catalog()
    corrupted_catalog = copy.deepcopy(real_catalog)

    # Change expected hash for cjk30
    corrupted_catalog["probes"]["cjk30"]["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"

    assert run_selftest(custom_catalog=corrupted_catalog, verbose=False) is False
