#!/usr/bin/env python3
"""Lightweight mock OpenAI-compatible server for testing and live demonstrations."""

import argparse
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
from typing import Dict, Optional
from tokwhois.catalog_data import load_catalog, get_families
from tokwhois.probes import EMBEDDED_PROBES


class MockOpenAIHandler(BaseHTTPRequestHandler):
    target_family: str = "glm4"
    framing_offset: int = 7
    server_mode: str = "normal"  # normal | no_usage | no_prompt_tokens | implausible | http_500 | disallow_empty | inflated_empty

    def log_message(self, format, *args):
        # Quiet standard logging
        pass

    def do_POST(self):
        if not (self.path.endswith("/chat/completions") or self.path.endswith("/completions")):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        # Handle mock server error modes
        if self.server_mode == "http_500":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Internal Server Error"}')
            return

        messages = req_data.get("messages", [])
        user_content = ""
        for m in messages:
            if m.get("role") == "user":
                user_content = m.get("content", "")
                break

        if self.server_mode == "disallow_empty" and user_content == "":
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Empty prompt content not allowed"}')
            return

        # Calculate simulated token count
        catalog = load_catalog()
        families = get_families(catalog)
        fam_info = families.get(self.target_family, list(families.values())[0])
        vector = fam_info["vector"]

        # Find matching probe
        matched_count = None
        for p_id, p_text in EMBEDDED_PROBES.items():
            if user_content == p_text:
                if p_id == "empty":
                    matched_count = 0
                else:
                    matched_count = vector.get(p_id, len(user_content))
                break

        if matched_count is None:
            if user_content == ".":
                matched_count = 1
            else:
                matched_count = max(1, len(user_content) // 4)

        # Add template framing overhead
        total_prompt_tokens = matched_count + self.framing_offset
        if self.server_mode == "inflated_empty" and user_content == "":
            total_prompt_tokens = 1000

        if self.server_mode == "implausible":
            total_prompt_tokens = 999999

        # Build response payload
        if self.server_mode == "no_usage":
            resp_body = {
                "id": "chatcmpl-mock-123",
                "object": "chat.completion",
                "created": 1724500000,
                "model": req_data.get("model", "mock-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
            }
        elif self.server_mode == "no_prompt_tokens":
            resp_body = {
                "id": "chatcmpl-mock-123",
                "object": "chat.completion",
                "created": 1724500000,
                "model": req_data.get("model", "mock-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 10},
            }
        else:
            resp_body = {
                "id": "chatcmpl-mock-123",
                "object": "chat.completion",
                "created": 1724500000,
                "model": req_data.get("model", "mock-model"),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": 1,
                    "total_tokens": total_prompt_tokens + 1,
                },
            }

        out_bytes = json.dumps(resp_body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out_bytes)))
        self.end_headers()
        self.wfile.write(out_bytes)


def run_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    family: str = "glm4",
    offset: int = 7,
    mode: str = "normal",
):
    MockOpenAIHandler.target_family = family
    MockOpenAIHandler.framing_offset = offset
    MockOpenAIHandler.server_mode = mode

    httpd = HTTPServer((host, port), MockOpenAIHandler)
    print(f"Mock OpenAI server running on http://{host}:{port}/v1 (family={family}, offset={offset}, mode={mode})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock server.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock OpenAI-compatible server for tokwhois.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--family", default="glm4")
    parser.add_argument("--offset", type=int, default=7)
    parser.add_argument("--mode", default="normal", choices=["normal", "no_usage", "no_prompt_tokens", "implausible", "http_500", "disallow_empty"])
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, family=args.family, offset=args.offset, mode=args.mode)
