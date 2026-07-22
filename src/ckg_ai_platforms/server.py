"""
ckg-ai-platforms — AI developer platforms as traversable knowledge graphs.

7 domains · 314 nodes · MCP-native · 11x fewer tokens than RAG

Domains: LangChain · LangGraph · OpenAI API · Anthropic SDK · HuggingFace ·
         AWS Bedrock · Vertex AI

Edge types: REQUIRES · ENABLES · RELATES_TO · IMPLEMENTS

Usage:
    uvx ckg-ai-platforms                 # run as MCP server
    python -m ckg_ai_platforms           # same

Claude Desktop config:
    {
      "mcpServers": {
        "ai-platforms": {
          "command": "uvx",
          "args": ["ckg-ai-platforms"]
        }
      }
    }
"""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from .graph import available_domains, load_graph, load_domain_meta, find_concept, bfs_subgraph, prerequisite_chain

_DOMAIN_HINTS: dict[str, list[str]] = {
    "langchain":     ["langchain", "lcel", "chain", "langsmith", "runnable", "agent executor"],
    "langgraph":     ["langgraph", "graph state", "state machine", "state graph", "cycl"],
    "openai-api":    ["openai", "gpt", "chat completion", "embeddings", "assistants", "dall-e", "whisper"],
    "anthropic-sdk": ["anthropic", "claude", "messages api", "tool use", "prompt caching", "computer use"],
    "huggingface":   ["huggingface", "hugging face", "transformers", "hub", "spaces", "datasets", "inference api"],
    "aws-bedrock":   ["bedrock", "aws bedrock", "amazon bedrock", "converse api", "guardrails", "knowledge base"],
    "vertex-ai":     ["vertex", "google cloud", "vertex ai", "model garden", "gemini", "palm"],
}


def _detect_domain(question: str) -> str | None:
    q = question.lower()
    best, top = None, 0
    for domain, hints in _DOMAIN_HINTS.items():
        score = sum(1 for h in hints if h in q)
        if score > top:
            top, best = score, domain
    return best


mcp = FastMCP(
    "ckg-ai-platforms",
    instructions=(
        "CKG server for AI developer platforms (LangChain, LangGraph, OpenAI, Anthropic, "
        "HuggingFace, AWS Bedrock, Vertex AI). "
        "Call list_domains first, then query_ckg or get_prerequisites. "
        "Edges are typed: REQUIRES / ENABLES / RELATES_TO / IMPLEMENTS."
    ),
)


@mcp.tool()
def ask_platform(question: str, domain: str = "") -> str:
    """Answer a question about an AI platform by traversing the relevant CKG.

    Auto-detects the platform from the question if domain is not specified.

    Args:
        question: Your question about an AI platform concept or workflow.
        domain: Optional — one of: langchain, langgraph, openai-api, anthropic-sdk,
                huggingface, aws-bedrock, vertex-ai
    """
    domains = available_domains()
    if not domain:
        domain = _detect_domain(question)
    if not domain or domain not in domains:
        return (
            f"Could not detect platform. Available: {', '.join(domains)}.\n"
            "Re-call with domain= set explicitly."
        )

    id_to_label, label_to_id, prerequisites, dependents, taxonomy, _ = load_graph(domain)
    meta = load_domain_meta(domain)

    cid = find_concept(label_to_id, question)
    if cid is None:
        for word in sorted(question.lower().split(), key=len, reverse=True):
            if len(word) > 3:
                cid = find_concept(label_to_id, word)
                if cid:
                    break
    if cid is None:
        top = list(label_to_id.keys())[:8]
        return (
            f"No concept matched '{question}' in {domain}.\n"
            f"Sample concepts: {', '.join(t.title() for t in top)}"
        )

    concept_label = id_to_label[cid]
    chain = prerequisite_chain(cid, prerequisites, id_to_label)
    subgraph = bfs_subgraph(cid, prerequisites, id_to_label, max_depth=3)

    lines = [
        f"# CKG: {domain} — {concept_label}",
        f"Taxonomy: {taxonomy.get(cid, 'unknown')}",
        "",
        "## Prerequisite chain (upstream dependencies)",
    ]
    for label in chain[1:]:
        lines.append(f"  ← {label}")

    lines += ["", "## What this concept enables / depends on"]
    for entry in subgraph:
        if entry["concept"] != concept_label and entry["depth"] == 1:
            lines.append(f"  {entry['edge_type']}: {entry['concept']}")

    if meta:
        lines += ["", f"Domain: {meta.get('description', '')}"]
    lines.append("\nSource: ckg-ai-platforms v0.1.0 · graphifymd.com")
    return "\n".join(lines)


@mcp.tool()
def list_domains() -> str:
    """List all available AI platform domains in this package."""
    domains = available_domains()
    lines = [f"Available domains ({len(domains)}):"]
    for d in sorted(domains):
        lines.append(f"  - {d}")
    lines.append("\nUse query_ckg(concept, domain) or ask_platform(question).")
    return "\n".join(lines)


@mcp.tool()
def search_concepts(query: str, domain: str) -> str:
    """Find concepts in a domain by partial name match.

    Args:
        query: Substring to search for (case-insensitive).
        domain: One of the available domains.
    """
    _, label_to_id, _, _, taxonomy, _ = load_graph(domain)
    q = query.lower()
    matches = [(label, cid) for label, cid in label_to_id.items() if q in label][:20]
    if not matches:
        return f"No concepts matching '{query}' in {domain}."
    return "\n".join(
        f"  - {label.title()} [{taxonomy.get(cid, '')}]"
        for label, cid in matches
    )


@mcp.tool()
def query_ckg(concept: str, domain: str, depth: int = 3) -> str:
    """Return the dependency subgraph around a concept.

    Args:
        concept: Concept name (partial match supported).
        domain: Domain to search in.
        depth: Upstream hops to include (1-5, default 3).
    """
    id_to_label, label_to_id, prerequisites, dependents, taxonomy, _ = load_graph(domain)
    cid = find_concept(label_to_id, concept)
    if cid is None:
        return f"Concept '{concept}' not found in {domain}."

    concept_label = id_to_label[cid]
    chain = prerequisite_chain(cid, prerequisites, id_to_label)
    subgraph = bfs_subgraph(cid, dependents, id_to_label, max_depth=min(depth, 5))

    lines = [
        f"## {concept_label} [{taxonomy.get(cid, '')}] — {domain}",
        "",
        "### Prerequisites (what you need to know first)",
    ]
    for label in chain[1:]:
        lines.append(f"  ← {label}")

    lines += ["", "### Builds toward (concepts that depend on this)"]
    for entry in subgraph:
        if entry["concept"] != concept_label:
            lines.append(f"  → {entry['concept']} [{entry['edge_type']}]")
    return "\n".join(lines)


@mcp.tool()
def get_prerequisites(concept: str, domain: str) -> str:
    """Return the full upstream prerequisite chain for a concept.

    Args:
        concept: Concept to trace (partial match supported).
        domain: Domain to search in.
    """
    id_to_label, label_to_id, prerequisites, _, _, _ = load_graph(domain)
    cid = find_concept(label_to_id, concept)
    if cid is None:
        return f"Concept '{concept}' not found in {domain}."

    chain = prerequisite_chain(cid, prerequisites, id_to_label)
    if len(chain) <= 1:
        return f"{id_to_label[cid]} has no prerequisites in {domain}."
    return f"Prerequisite chain for {id_to_label[cid]}:\n" + "\n".join(
        f"  {'  ' * i}← {label}" for i, label in enumerate(chain[1:])
    )


@mcp.tool()
def verify_source(concept: str, domain: str) -> str:
    """Return the source URL and content hash for a concept node.

    Audit chain:
        edge answer → graph commit → source_hash → source_url (fetch hint)

    Verification:
        curl -s <source_url> | sha256sum
        # compare output to source_hash

    Args:
        concept: Concept label (partial match supported).
        domain: Domain to search in (e.g. 'anthropic-sdk', 'aws-bedrock').
    """
    id_to_label, label_to_id, _, _, taxonomy, provenance = load_graph(domain)
    cid = find_concept(label_to_id, concept.lower())
    if not cid:
        return f"Concept '{concept}' not found in {domain}. Use search_concepts() to find the closest match."

    label = id_to_label[cid]
    prov = provenance.get(cid, {})
    source_url = prov.get("source_url") or "unknown"
    source_hash = prov.get("source_hash") or "sha256:not-computed"

    sentinel_notes = {
        "sha256:restricted": "Source returned 4xx/5xx — page requires auth or is gone.",
        "sha256:unavailable": "Network error at hash-compute time.",
        "sha256:no-source-url": "No source URL declared for this node.",
    }
    note = sentinel_notes.get(source_hash, "")

    lines = [
        f"## Source provenance — {label} ({domain})",
        f"",
        f"**concept:**      {label}",
        f"**taxonomy:**     {taxonomy.get(cid, 'unknown')}",
        f"**source_url:**   {source_url}",
        f"**source_hash:**  {source_hash}",
        f"**provenance:**   GuardrailDecisionV1 · v1",
        f"",
    ]
    if note:
        lines += [f"⚠ {note}", ""]
    else:
        lines += [
            "**Verification:**",
            f"```bash",
            f"curl -s '{source_url}' | sha256sum",
            f"# expected: {source_hash.removeprefix('sha256:')}",
            f"```",
            "",
            "**source_hash** is the trust anchor. **source_url** is a fetch hint — page can change silently.",
        ]
    return "\n".join(lines)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
