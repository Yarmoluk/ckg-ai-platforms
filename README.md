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

## Benchmark

Part of the [CKG benchmark](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf):
- F1: 0.471 vs RAG 0.123 (3.8×)
- Tokens/query: 269 vs 2,982 (11×)
- Cost/correct answer: $7.81 vs $76.23

## License

MIT · [graphifymd.com](https://graphifymd.com)
