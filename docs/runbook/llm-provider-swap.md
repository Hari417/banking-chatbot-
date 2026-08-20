# Runbook: LLM Provider Swap

**Version:** 1.0
**Status:** Current
**Last Verified:** 2026-08-20 against `src/banking_rag/llm.py`, `config.yaml`
**Sources:** `src/banking_rag/llm.py`, `config.yaml`, `docs/setup/configuration.md`
**Owner:** Scribe

---

## When to use this

- Switching from OpenAI to a local Ollama model (cost, latency, air-gap).
- Switching from Ollama back to OpenAI (quality, speed).
- Pointing at a custom OpenAI-compatible endpoint (vLLM, LM Studio, gateway).

**No re-index is required.** The LLM provider is independent of the embedding model and
FAISS index. Swapping providers only changes how responses are generated, not
retrieval. (If you also change the *embedding* model, see `embedding-model-change.md`.)

## Pre-flight checks

For the **target** provider:

| Target | Check |
|--------|-------|
| `openai` | `OPENAI_API_KEY` set; egress to `api.openai.com` |
| `openai_compatible` | base URL reachable; auth env var set if needed |
| `ollama` | `ollama serve` running; `ollama list` shows the model; `ollama show <model>` ok |

Confirm with a direct curl to the target `/chat/completions` (or `/models`).

## Procedure

1. **Back up config:**

   ```bash
   cp config.yaml config.yaml.bak
   ```

2. **Edit `llm:` in `config.yaml`.** Examples below.

3. **Restart the API / CLI.** v1 has no live reload; the workflow singleton is rebuilt
   only on process restart. Stop the API (Ctrl+C), then:

   ```bash
   BANKING_RAG_API_PORT=8000 python3 src/api.py &
   # or test via the CLI first:
   python3 src/cli.py query "What are your banking hours?"
   ```

4. **Verify** the response is a sensible banking answer (not a fallback/error). Tail
   logs (`BANKING_RAG_DEBUG=true`) for provider errors.

## Example: OpenAI → Ollama (llama3)

```yaml
llm:
  provider: "ollama"
  model: "llama3"                # LLMClient sends this as 'model' to Ollama
  temperature: 0.4
  max_tokens: 1000
  timeout: 60                    # local LLMs are slower; raise the timeout
  ollama_base_url: "http://localhost:11434"
```

> **Note:** `LLMClient` sends `llm.model` (not `ollama_model`) to Ollama. The
> `ollama_model` field is vestigial for the client path — set `llm.model` to the Ollama
> model id you pulled.

## Example: Ollama → OpenAI

```yaml
llm:
  provider: "openai"
  model: "gpt-4o-mini"
  api_base: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"
  temperature: 0.7
  max_tokens: 1000
  timeout: 30
```

```bash
export OPENAI_API_KEY="sk-..."
```

## Example: → a custom OpenAI-compatible endpoint

```yaml
llm:
  provider: "openai_compatible"
  model: "my-local-model"        # whatever id the endpoint expects
  api_base: "http://gateway.internal/v1"
  api_key_env: "GATEWAY_TOKEN"   # set the env var in your shell
  temperature: 0.5
  timeout: 45
```

```bash
export GATEWAY_TOKEN="..."
```

## Rollback

If the target provider produces poor scope control (refuses too much, or fails the
grounding validator), restore the backup and restart:

```bash
mv config.yaml.bak config.yaml
python3 src/api.py &
```

## v1-specific caveats

- The system prompt is fixed in `RAGWorkflow._load_system_prompt()`; there is no
  per-provider prompt tuning. Different models may interpret the scope/grounding rules
  differently — Ollama `llama3` may hedge more (triggering the abstention rewrite) or
  hallucinate differently.
- The grounding validator is a token-overlap heuristic; it does not adapt to the
  provider. Watch for a rise in `abstained: true` or `grounded: false` after a swap.
- Streaming is available at the LLM layer but not exposed through `/chat`. Non-streaming
  mode is the only v1 contract.
