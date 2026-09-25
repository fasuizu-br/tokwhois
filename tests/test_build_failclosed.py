"""Tests for fail-closed behavior and revision pinning in catalog/build.py."""

from unittest.mock import MagicMock, patch
import pytest

from catalog.build import build_catalog


def test_build_hf_download_failure_raises_explicit_runtime_error():
    """Simulate a failure in Tokenizer.from_pretrained; build_catalog must raise RuntimeError with family and error."""
    simulated_error = ConnectionError("Could not resolve host: huggingface.co")
    with patch("tokenizers.Tokenizer.from_pretrained", side_effect=simulated_error):
        with pytest.raises(RuntimeError) as exc_info:
            build_catalog()

        msg = str(exc_info.value)
        # Must name the failing family and report the underlying error
        assert "llama3" in msg, f"Expected failing family 'llama3' in error message: {msg}"
        assert "Could not resolve host: huggingface.co" in msg, f"Expected root cause in error message: {msg}"


def test_build_hf_passes_pinned_revision():
    """Verify that build_catalog passes the 40-hex revision SHA to Tokenizer.from_pretrained."""
    recorded_calls = []

    def fake_from_pretrained(target, **kwargs):
        recorded_calls.append((target, kwargs))
        raise RuntimeError(f"Stop build after capturing call for {target}")

    with patch("tokenizers.Tokenizer.from_pretrained", side_effect=fake_from_pretrained):
        with pytest.raises(RuntimeError, match="Stop build after capturing"):
            build_catalog()

    assert len(recorded_calls) >= 1
    target, kwargs = recorded_calls[0]
    assert target == "unsloth/llama-3-8b"
    assert "revision" in kwargs
    assert kwargs["revision"] == "b0c09b815d8a74b70622c740f108c995c5041a14"
