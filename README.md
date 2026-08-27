# tokwhois

**Whois for stealth LLMs.**

Labs can hide the weights, the logits, and the architecture.  
They cannot hide the tokenizer they bill you with.

```bash
git clone https://github.com/fasuizu-br/tokwhois
cd tokwhois
pip install -e .
python3 -m tokwhois demo
```

Zero-install, from the git URL (the package is not on PyPI):

```bash
uvx --from git+https://github.com/fasuizu-br/tokwhois tokwhois demo
uvx --from git+https://github.com/fasuizu-br/tokwhois tokwhois https://api.example.com/v1 --model gpt-4o-mini
```

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

![demo](docs/demo.gif)

---

## What you get in 12 seconds

A 14-integer **fertility vector**. Each probe is a fixed, versioned string. The
server returns `usage.prompt_tokens` for a 1-token completion. That
integer is compared to a catalog of **public** tokenizers
(tiktoken encodings + Hugging Face `tokenizer.json`, licenses
permissive, pinned by commit/version). Catalog v1 is **16 families**;
Qwen 2/2.5 is not Qwen3.

```
$ python3 -m tokwhois demo

family      glm4-class     confidence (heuristic) 1.00  (L1 distance: 0)
runner-up   cl100k_base    margin 35 tokens (L1)

probe          counted       glm4 cl100k_bas  internlm2 o200k_base
cjk30               22         22         30         23         28
space40              1          1          1          1          1
digit64             43         43         22         32         22
ascii100            26         26         26         27         26
emoji8              21         21         21         29         13
hello_leadsp         1          1          1          1          1
nl16                 1          1          1          1          1
tab16                1          1          1          1          1
cjk_en               8          8         12          8          8
im_start             6          6          6          1          6
gmask                1          1          3          3          3
eot                  1          1          1          7          1
bot_llama            7          7          7          7          7
byte_rare           22         22         22         24         23
──────────────────────────────────────────────────────────────────
offset (empty)      7   subtracted from every prompt count

n=1 probe / string   K=1   catalog=v1   2026-08-24
discriminating probes vs runner-up: cjk30, digit64, cjk_en, gmask
```

It reports a **tokenizer family**, not a checkpoint, not a lab, not
a parameter count. If the top two families land inside the margin,
it prints `ambiguous` and stops. It does not guess. `confidence` in
the output is a **heuristic** score of L1 distance and margin, not a
probability.

---

## Tokenizer Fertility Atlas (v1)

![fingerprint](docs/fingerprint.svg)

---

## Install

The package is not on PyPI. Install from the repository:

```bash
git clone https://github.com/fasuizu-br/tokwhois
cd tokwhois
pip install -e .

# or, zero install:
uvx --from git+https://github.com/fasuizu-br/tokwhois tokwhois demo
```

Python 3.10+. The demo and selftest run **offline** (stdlib + the embedded catalog).
Live mode requires `httpx`. `tiktoken` and `tokenizers` are optional
and only used to rebuild the catalog or encode local files.

---

## 5-Minute Path

### 1. Offline (no API key, no network)

```bash
python3 -m tokwhois demo
```

This encodes the v1 probes against the embedded catalog, prints the vectors, and asserts
that each family matches itself at $L_1 = 0$ and the others at $L_1 > 0$.
If that assertion ever fails, the instrument is hollow — the
selftest is written to fail on purpose when the catalog collides.

### 2. Live (any OpenAI-compatible endpoint)

```bash
export OPENAI_API_KEY=...
python3 -m tokwhois "$OPENAI_BASE_URL" --model "$MODEL"
```

Fourteen `max_tokens=1` calls. Fail-closed if `usage.prompt_tokens`
is missing. Chat-template framing overhead is subtracted via an empty probe
so the live vector can be compared to the local catalog. That comparison
is a working hypothesis (BPE is not addition; see [METHOD.md](docs/METHOD.md)).
If the empty probe fails, or a calibrated count is less than 1, the
client aborts. There is no silent fallback.

### 3. Local file (you already have `tokenizer.json`)

```bash
python3 -m tokwhois --local path/to/tokenizer.json
```

### 4. Machine-readable JSON output

```bash
python3 -m tokwhois demo --json
python3 -m tokwhois "$OPENAI_BASE_URL" --model "$MODEL" --json
```

---

## Why this works

Tokenizers are frozen at training. Stealth deployments almost
always reuse a public tokenizer because training a new one is a
research project, not a wrap. Billing requires `usage`. The
combination is a fingerprint the server computes for you.

This is not a watermark, not a logit attack, and not stylometry.
The empty-prompt offset is a first-order correction, not an identity.
BPE is not addition; a chat template is not concatenation. See
[METHOD.md](docs/METHOD.md).

---

## What this is not

- **Not** a statement about model quality.
- **Not** an identification of a lab, a checkpoint, or a size.
- **Not** a benchmark. There is no leaderboard in this repository.
- **Not** a request that anyone violate a provider's terms. You run
  it against endpoints **you** are authorized to call.

---

## Method in one paragraph

Let $f$ be the unknown tokenizer. For a fixed probe set
$s_1,\ldots,s_{14}$ we observe $n_i = |f(\mathrm{Template}(s_i))|$ via the
billing field, minus the chat-template offset $n_\varnothing$.
That difference is a **working hypothesis** for $|f(s_i)|$, not an
identity: BPE merges can cross the template boundary, and the catalog
is built with `encode(s)` (no template). The catalog stores
$n_i^{(k)}$ for each public tokenizer $k$.
The report is $\arg\min_k \sum_i |n_i - n_i^{(k)}|$, with
`ambiguous` if the runner-up is within `margin` (default 2).
Every number in the report is an integer count with $n=1, K=1$.
See [METHOD.md](docs/METHOD.md) for the full formulation.

---

## License

Copyright 2026 Fabio Suizu / Brainiall.

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
