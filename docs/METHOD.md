# Mathematical Method & Metrology of `tokwhois`

## 1. Overview

`tokwhois` identifies the tokenizer family of an unknown or stealth Large Language Model deployed behind an OpenAI-compatible API endpoint by measuring a 14-dimensional **fertility vector** through token billing counts.

Because tokenizers are frozen before pretraining and labs almost universally reuse open, well-established tokenizers, the fertility response over fixed pathological strings forms a unique, collision-free fingerprint.

---

## 2. Mathematical Formulation

Let $\Sigma$ denote the Unicode character set, and let $f: \Sigma^* \to \mathbb{N}$ be the unknown tokenization function mapping a character sequence $s \in \Sigma^*$ to its token sequence length $|f(s)|$.

### 2.1 Prompt Framing & Offset Calibration

When a user submits a prompt message $s_i$ to an OpenAI-compatible `/v1/chat/completions` endpoint, the server wraps $s_i$ in a chat template (BOS tokens, role markers, system headers, etc.):

$$\text{Prompt}_{\text{server}}(s_i) = \text{Template}(s_i)$$

The server reports billing via `usage.prompt_tokens`:

$$n_i = |f(\text{Template}(s_i))| = |f(s_i)| + n_\varnothing$$

where $n_\varnothing = |f(\text{Template}(\varepsilon))|$ is the constant chat-template framing overhead for an empty message $\varepsilon$.

`tokwhois` probes the empty prompt $\varepsilon$ (or minimal atomic prompt) to observe $n_\varnothing$. The calibrated fertility count for probe $s_i$ is then computed as:

$$\hat{n}_i = \max(1, n_i - n_\varnothing)$$

### 2.2 Fertility Vector

For a fixed, versioned battery of 14 probing strings $\mathcal{S} = (s_1, s_2, \ldots, s_{14})$, we construct the observed fertility vector:

$$\mathbf{v} = (\hat{n}_1, \hat{n}_2, \ldots, \hat{n}_{14}) \in \mathbb{N}^{14}$$

### 2.3 Catalog Matching via Manhattan ($L_1$) Distance

Let $\mathcal{C} = \{(\mathbf{v}^{(k)}, \text{meta}^{(k)})\}_{k=1}^K$ be the catalog of $K$ public tokenizers (e.g. `o200k_base`, `cl100k_base`, `llama3`, `qwen2_5`, `glm4`, etc.) evaluated offline against $\mathcal{S}$.

The candidate ranking is ordered by Manhattan ($L_1$) distance:

$$D_1(\mathbf{v}, \mathbf{v}^{(k)}) = \|\mathbf{v} - \mathbf{v}^{(k)}\|_1 = \sum_{i=1}^{14} |\hat{n}_i - v_i^{(k)}|$$

The top match $\hat{k}_1$ and runner-up $\hat{k}_2$ are:

$$\hat{k}_1 = \arg\min_{k} D_1(\mathbf{v}, \mathbf{v}^{(k)}), \quad \hat{k}_2 = \arg\min_{k \ne \hat{k}_1} D_1(\mathbf{v}, \mathbf{v}^{(k)})$$

The decision margin $\Delta$ is defined as:

$$\Delta = D_1(\mathbf{v}, \mathbf{v}^{(\hat{k}_2)}) - D_1(\mathbf{v}, \mathbf{v}^{(\hat{k}_1)})$$

---

## 3. Ambiguity & Fail-Closed Guardrails

### 3.1 Ambiguity Condition

A classification is declared **ambiguous** if:

1. $\Delta < \Delta_{\text{threshold}}$ (default $\Delta_{\text{threshold}} = 2$), OR
2. $D_1(\mathbf{v}, \mathbf{v}^{(\hat{k}_1)}) \ge 20$ (indicating an unfamiliar or novel tokenizer family not present in the catalog).

When ambiguous, `tokwhois` refuses to guess a single lab or family, outputting the tied candidates and the exact discriminating probes that separate them.

### 3.2 Fail-Closed Invariants

`tokwhois` enforces strict fail-closed invariants:
- If HTTP status $\ne 200$, abort immediately.
- If the `usage` object is missing from the API response, abort with `instrument: no usage field in response`.
- If `usage.prompt_tokens` is missing or not an integer, abort with `instrument: no usage.prompt_tokens in response`.
- If $n_i \le 0$ or $n_i > |s_i| + 1000$, abort with `instrument: implausible count`.

Zero silent fallbacks. Zero synthetic smoothing.

---

## 4. Probe Battery Rationale

| Probe ID | String Target | Primary Discrimination Vector |
|---|---|---|
| `cjk30` | 30 common CJK ideograms | Dedicated CJK vocabulary (GLM, Qwen) vs SentencePiece byte-level splits |
| `space40` | 40 ASCII spaces (`0x20`) | Whitespace compression / run-length encoding |
| `digit64` | 64 ASCII `'7'` digits | Digit grouping policy (single-digit vs 2-digit vs 3-digit BPE merges) |
| `ascii100` | 100 standard ASCII letters | Baseline Latin alphabet fertility |
| `emoji8` | 8 standard Unicode emojis | Direct emoji token entries vs multi-byte UTF-8 fallbacks |
| `hello_leadsp` | `' hello'` (leading space) | GPT-style `Ġhello` prefix handling vs standard BPE |
| `nl16` | 16 consecutive `\n` newlines | Multi-newline token merging |
| `tab16` | 16 consecutive `\t` tabs | Tab indentation tokenization |
| `cjk_en` | `'你好world'` × 4 | Script boundary merge behavior |
| `im_start` | `<\|im_start\|>` | ChatML special token vocabulary inclusion |
| `gmask` | `[gMASK]` | GLM-specific special token structure |
| `eot` | `<\|endoftext\|>` | OpenAI tiktoken token inclusion |
| `bot_llama` | `<\|begin_of_text\|>` | Meta Llama 3 special token structure |
| `byte_rare` | 8 rare Samaritan codepoints | UTF-8 byte-fallback behavior on rare unicode ranges |
| `empty` | `""` (0 length) | Chat template framing offset calibration ($n_\varnothing$) |
