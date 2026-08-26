"""Fail-closed client for probing OpenAI-compatible endpoints."""

import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import httpx
from tokwhois.probes import PROBE_ORDER, load_probes


class ProbeClientError(Exception):
    """Raised when an API endpoint cannot be probed or fails validation."""
    pass


class ProbeClient:
    """Probes an OpenAI-compatible API to construct a tokenizer fertility vector."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 20.0,
    ):
        self.base_url = base_url.rstrip("/")
        if not (self.base_url.endswith("/chat/completions") or self.base_url.endswith("/completions")):
            if self.base_url.endswith("/v1"):
                self.endpoint_url = f"{self.base_url}/chat/completions"
            else:
                self.endpoint_url = f"{self.base_url}/v1/chat/completions"
        else:
            self.endpoint_url = self.base_url

        self.model = model
        self.api_key = api_key
        self.custom_headers = headers or {}
        self.timeout = timeout

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "tokwhois/0.1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        headers.update(self.custom_headers)
        return headers

    def _probe_single(
        self,
        client: httpx.Client,
        content: str,
        probe_id: str,
    ) -> Tuple[int, float]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 1,
            "temperature": 0.0,
        }

        start_t = time.perf_counter()
        try:
            resp = client.post(
                self.endpoint_url,
                json=payload,
                headers=self._build_headers(),
                timeout=self.timeout,
            )
        except httpx.RequestError as exc:
            raise ProbeClientError(f"Connection error to {self.endpoint_url}: {exc}") from exc

        latency = time.perf_counter() - start_t

        if resp.status_code != 200:
            raise ProbeClientError(
                f"HTTP {resp.status_code} from {self.endpoint_url}: {resp.text[:300]}"
            )

        try:
            data = resp.json()
        except Exception as exc:
            raise ProbeClientError(f"Invalid JSON response: {resp.text[:300]}") from exc

        if not isinstance(data, dict):
            raise ProbeClientError("Invalid response: expected JSON object")

        if "usage" not in data or data["usage"] is None:
            raise ProbeClientError("instrument: no usage field in response")

        usage = data["usage"]
        if not isinstance(usage, dict) or "prompt_tokens" not in usage:
            raise ProbeClientError("instrument: no usage.prompt_tokens in response")

        prompt_tokens = usage["prompt_tokens"]
        if not isinstance(prompt_tokens, int):
            raise ProbeClientError(f"instrument: usage.prompt_tokens is not an integer ({type(prompt_tokens)})")

        if prompt_tokens < 0 or prompt_tokens > (len(content) + 1000):
            raise ProbeClientError(
                f"instrument: implausible count (prompt_tokens={prompt_tokens} for content len={len(content)})"
            )

        return prompt_tokens, latency

    def probe(
        self,
        progress_callback: Optional[Callable[[str, int, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Probe all 14 probes + empty probe, calibrate offsets, and return results.

        Returns dictionary with:
          - calibrated_vector: Dict[str, int]
          - raw_vector: Dict[str, int]
          - offset: int (chat template overhead)
          - latencies: Dict[str, float]
        """
        probes = load_probes()
        raw_counts: Dict[str, int] = {}
        latencies: Dict[str, float] = {}

        with httpx.Client() as client:
            # 1. Probe empty prompt to measure template overhead
            try:
                empty_count, empty_lat = self._probe_single(client, "", "empty")
            except ProbeClientError:
                # Some servers disallow empty string, fallback to single dot "."
                dot_count, empty_lat = self._probe_single(client, ".", "empty_dot")
                empty_count = max(0, dot_count - 1)

            offset = empty_count
            latencies["empty"] = empty_lat

            # 2. Probe all 14 discriminating strings
            calibrated_vector: Dict[str, int] = {}
            for idx, p_id in enumerate(PROBE_ORDER):
                p_text = probes[p_id]
                raw_cnt, lat = self._probe_single(client, p_text, p_id)
                raw_counts[p_id] = raw_cnt
                latencies[p_id] = lat

                # Subtract chat template overhead
                calibrated_cnt = max(1, raw_cnt - offset)
                calibrated_vector[p_id] = calibrated_cnt

                if progress_callback is not None:
                    progress_callback(p_id, idx + 1, len(PROBE_ORDER), calibrated_cnt)

        return {
            "calibrated_vector": calibrated_vector,
            "raw_vector": raw_counts,
            "offset": offset,
            "latencies": latencies,
            "endpoint_url": self.endpoint_url,
            "model": self.model,
        }
