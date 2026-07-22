# ckg-ai-platforms

AI developer platforms as traversable knowledge graphs — MCP-native.

**7 domains · 314 nodes · 445 edges · 11× fewer tokens than RAG**

| Domain | Nodes | Edges | Coverage |
|---|---|---|---|
| langchain | 48 | 71 | Chains, agents, LCEL, memory, retrievers, LangSmith |
| langgraph | 42 | 58 | Graph state, nodes, edges, cycles, persistence |
| openai-api | 43 | 59 | Chat completions, assistants, embeddings, DALL-E |
| anthropic-sdk | 44 | 62 | Messages API, tool use, prompt caching, computer use |
| huggingface | 46 | 65 | Hub, Transformers, Spaces, Datasets, Inference API |
| aws-bedrock | 46 | 67 | Converse API, Guardrails, Knowledge Bases, agents |
| vertex-ai | 45 | 63 | Model Garden, Gemini API, evaluation, fine-tuning |

## Install

```bash
pip install ckg-ai-platforms
uvx ckg-ai-platforms   # MCP server
```

## Use as MCP server

Add to your Claude Desktop or any MCP client:

```json
{
  "mcpServers": {
    "ai-platforms": {
      "command": "uvx",
      "args": ["ckg-ai-platforms"]
    }
  }
}
```

## Use as Python library

```python
from ckg_ai_platforms import ask_platform, list_domains

# Ask a question — auto-detects platform
result = ask_platform("How does LCEL RunnableSequence work?")
print(result)

# Explicit domain
result = ask_platform("explain tool use", domain="anthropic-sdk")
```

## Source provenance — verifiable to the byte

Every node carries a `source_url` and a `source_hash` (SHA-256 of the source document's bytes at extraction time).

```bash
curl -s https://python.langchain.com/docs/introduction/ | sha256sum
# expected: 75a86f60f9aa30d3f7f3e407827c17b9df90f17370237bc8a3c80b5c98b33ff5
```

Via MCP — `verify_source("LCEL", "langchain")`:
```
source_url:  https://python.langchain.com/docs/introduction/
source_hash: sha256:75a86f60f9aa30d3f7f3e407827c17b9df90f17370237bc8a3c80b5c98b33ff5
verify:      curl -s '<url>' | sha256sum
```

Reference implementation of `knowledge_source_ref` + `source_content_hash` from [GuardrailDecisionV1](https://github.com/crewAIInc/crewAI/issues/4877).

## Benchmark

| System | Macro F1 | Mean tokens | Cost / 1k queries |
|--------|----------|-------------|-------------------|
| **CKG** | **0.471** | **269** | **$7.81** |
| RAG | 0.123 | 2,982 | $76.23 |
| GraphRAG | 0.120 | ~3,000 | ~$76 |

[dataset](https://huggingface.co/datasets/danyarm/ckg-benchmark) · [full paper](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)

## Licensing

| Layer | License | Plain English |
|-------|---------|---------------|
| **Server code** — `server.py`, `graph.py`, `scripts/` | MIT ([LICENSE-CODE](LICENSE-CODE)) | Do anything. Fork it, embed it, sell products built on it. |
| **Graph data** — `domains/*.csv` + source hashes | Elastic License 2.0 ([LICENSE](LICENSE)) | Free for all internal and commercial use. Cannot offer this graph as a competing hosted service. |
| **Extraction pipeline** | Proprietary — Graphify.md | Not in this repo. |

## EVAL

```
benchmark: ckg-benchmark v0.6.2
dataset: huggingface.co/datasets/danyarm/ckg-benchmark
benchmarked: false
rag_baseline_f1: 0.123
graphrag_baseline_f1: 0.120
mean_tokens: 269
paper: github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf
```

---

Built by [Graphify.md](https://graphifymd.com) · [97 domains](https://graphifymd.com/pro/) · [PyPI](https://pypi.org/project/ckg-ai-platforms/) · patent pending

*Community-built. Not affiliated with LangChain, OpenAI, Anthropic, HuggingFace, AWS, or Google. All referenced trademarks belong to their respective owners.*
