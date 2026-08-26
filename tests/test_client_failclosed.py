"""Tests verifying fail-closed behavior of ProbeClient under abnormal server responses."""

from http.server import HTTPServer
import socket
import sys
from pathlib import Path
import threading
import pytest

# Ensure example directory is in path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from example.mock_server import MockOpenAIHandler
from tokwhois.client import ProbeClient, ProbeClientError


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
def mock_server():
    port = find_free_port()
    MockOpenAIHandler.target_family = "glm4"
    MockOpenAIHandler.framing_offset = 7
    MockOpenAIHandler.server_mode = "normal"

    server = HTTPServer(("127.0.0.1", port), MockOpenAIHandler)
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    server.server_close()


def test_client_normal_successful_probe(mock_server):
    client = ProbeClient(base_url=mock_server, model="test-model")
    data = client.probe()

    assert "calibrated_vector" in data
    assert data["offset"] == 7
    assert len(data["calibrated_vector"]) == 14
    # GLM4 cjk30 is 22, gmask is 1
    assert data["calibrated_vector"]["cjk30"] == 22
    assert data["calibrated_vector"]["gmask"] == 1


def test_client_failclosed_missing_usage(mock_server):
    MockOpenAIHandler.server_mode = "no_usage"
    client = ProbeClient(base_url=mock_server, model="test-model")

    with pytest.raises(ProbeClientError, match="instrument: no usage field in response"):
        client.probe()


def test_client_failclosed_missing_prompt_tokens(mock_server):
    MockOpenAIHandler.server_mode = "no_prompt_tokens"
    client = ProbeClient(base_url=mock_server, model="test-model")

    with pytest.raises(ProbeClientError, match="instrument: no usage.prompt_tokens in response"):
        client.probe()


def test_client_failclosed_implausible_count(mock_server):
    MockOpenAIHandler.server_mode = "implausible"
    client = ProbeClient(base_url=mock_server, model="test-model")

    with pytest.raises(ProbeClientError, match="instrument: implausible count"):
        client.probe()


def test_client_failclosed_server_error_500(mock_server):
    MockOpenAIHandler.server_mode = "http_500"
    client = ProbeClient(base_url=mock_server, model="test-model")

    with pytest.raises(ProbeClientError, match="HTTP 500"):
        client.probe()


def test_client_failclosed_on_empty_disallowed(mock_server):
    MockOpenAIHandler.server_mode = "disallow_empty"
    client = ProbeClient(base_url=mock_server, model="test-model")

    with pytest.raises(ProbeClientError, match="empty probe failed"):
        client.probe()


def test_client_failclosed_calibrated_count_below_one(mock_server):
    MockOpenAIHandler.server_mode = "inflated_empty"
    client = ProbeClient(base_url=mock_server, model="test-model")

    with pytest.raises(ProbeClientError, match="calibrated count < 1"):
        client.probe()
