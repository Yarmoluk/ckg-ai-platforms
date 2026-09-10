"""
ckg-ai-platforms - AI developer platforms as traversable knowledge graphs.

11 domains. 475 nodes. 550 typed CSV edges. MCP-native.

Domains: LangChain, LangGraph, OpenAI API, Anthropic SDK, Hugging Face,
         AWS Bedrock, AWS Bedrock AgentCore, Vertex AI, Gemini Enterprise
         Agent Platform, Microsoft AI Agent Stack, Palantir Foundry.

Use this when an agent needs compact platform context: search concepts,
compare vendor vocabulary, inspect MCP touchpoints, traverse typed edges,
and verify source URLs plus SHA-256 hashes.

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
from importlib.metadata import PackageNotFoundError, version

from mcp.server import MCPServer
from .graph import (
    all_domain_stats,
    atlas_totals,
    available_domains,
    bfs_subgraph,
    domain_stats,
    find_concept,
    iter_edges,
    load_domain_meta,
    load_graph,
    prerequisite_chain,
    search_all_concepts,
)

_DOMAIN_HINTS: dict[str, list[str]] = {
    "langchain":     ["langchain", "lcel", "chain", "langsmith", "runnable", "agent executor"],
    "langgraph":     ["langgraph", "graph state", "state machine", "state graph", "cycl"],
    "openai-api":    ["openai", "gpt", "chat completion", "embeddings", "assistants", "dall-e", "whisper"],
    "anthropic-sdk": ["anthropic", "claude", "messages api", "tool use", "prompt caching", "computer use"],
    "huggingface":   ["huggingface", "hugging face", "transformers", "hub", "spaces", "datasets", "inference api"],
    "aws-bedrock":   ["bedrock", "aws bedrock", "amazon bedrock", "converse api", "guardrails", "knowledge base"],
    "aws-bedrock-agentcore": ["agentcore", "bedrock agentcore", "strands", "gateway target", "agentcore runtime"],
    "vertex-ai":     ["vertex", "google cloud", "vertex ai", "model garden", "gemini", "palm"],
    "google-gemini-agent-platform": ["gemini enterprise", "adk", "agent development kit", "a2a", "agent engine"],
    "microsoft-ai-agent-stack": ["microsoft", "azure ai foundry", "semantic kernel", "mcp plugin", "azure agent"],
    "palantir-foundry": ["palantir", "palantir foundry", "ontology", "object type", "link type", "aip agent"],
}


def _detect_domain(question: str) -> str | None:
    q = question.lower()
    best: list[str] = []
    top = 0
    for domain, hints in _DOMAIN_HINTS.items():
        score = sum(1 for h in hints if h in q)
        if score > top:
            top, best = score, [domain]
        elif score == top and score > 0:
            best.append(domain)
    return best[0] if len(best) == 1 else None


def _package_version() -> str:
    try:
        return version("ckg-ai-platforms")
    except PackageNotFoundError:
        return "0.0.0+local"


def _selected_domains(domains: str = "") -> tuple[list[str], list[str]]:
    available = available_domains()
    if not domains.strip():
        return available, []
    requested = [part.strip() for part in domains.split(",") if part.strip()]
    selected = [domain for domain in requested if domain in available]
    invalid = [domain for domain in requested if domain not in available]
    return selected, invalid


def _hash_for_command(source_hash: str) -> str:
    for prefix in ("sha256:", "sha256-canon:"):
        if source_hash.startswith(prefix):
            return source_hash.removeprefix(prefix)
    return source_hash


def _concept_context(domain: str, cid: str) -> dict:
    id_to_label, _, _, _, taxonomy, provenance = load_graph(domain)
    prov = provenance.get(cid, {})
    outgoing = iter_edges(domain, cid)
    incoming = [edge for edge in iter_edges(domain) if edge["to_id"] == cid]
    return {
        "domain": domain,
        "concept": {
            "id": cid,
            "label": id_to_label.get(cid, cid),
            "taxonomy": taxonomy.get(cid, ""),
            "source_url": prov.get("source_url", ""),
            "source_hash": prov.get("source_hash", ""),
        },
        "outgoing_relationships": outgoing,
        "incoming_relationships": incoming,
    }


mcp = MCPServer(
    "ckg-ai-platforms",
    title="AI Platform Atlas CKG",
    description="Source-pinned CKG atlas for AI developer and agent platforms.",
    version=_package_version(),
    instructions=(
        "CKG server for AI developer platforms as typed, source-pinned graphs. "
        "Call list_atlas first, then compare_platforms, find_mcp_touchpoints, "
        "get_concept_context, query_ckg, or verify_source. "
        "Edges are declared in packaged CSV files and traversed without model inference."
    ),
)


@mcp.tool()
def list_atlas() -> dict:
    """Return the packaged atlas inventory with counts and source coverage."""
    stats = all_domain_stats()
    return {
        "package": "ckg-ai-platforms",
        "version": _package_version(),
        "transport": "stdio",
        "privacy": "local MCP server; no telemetry and no outbound API calls at query time",
        "totals": atlas_totals(),
        "domains": stats,
        "common_workflows": [
            "search_concepts(query, domain) to find platform vocabulary",
            "compare_platforms(query) to see which vendors use a term",
            "find_mcp_touchpoints() to locate MCP-related nodes",
            "get_concept_context(domain, concept) to inspect direct typed edges",
            "verify_source(domain, concept) to inspect source URL and hash",
        ],
    }


@mcp.tool()
def get_platform_summary(domain: str) -> dict:
    """Return node counts, relation counts, taxonomy counts, and coverage for one domain.

    Args:
        domain: One packaged domain, e.g. palantir-foundry or aws-bedrock-agentcore.
    """
    return domain_stats(domain)


@mcp.tool()
def compare_platforms(query: str, domains: str = "", limit: int = 40) -> dict:
    """Search a term across platform graphs and group matches by domain.

    Args:
        query: Concept text to look for, e.g. MCP, memory, agent, ontology, tool.
        domains: Optional comma-separated domain filter.
        limit: Maximum matches to return across all domains.
    """
    selected, invalid = _selected_domains(domains)
    matches = search_all_concepts(query, selected, limit=limit)
    grouped: dict[str, list[dict]] = {}
    for match in matches:
        grouped.setdefault(match["domain"], []).append(match)
    return {
        "query": query,
        "searched_domains": selected,
        "invalid_domains": invalid,
        "match_count": len(matches),
        "matches_by_domain": grouped,
    }


@mcp.tool()
def find_mcp_touchpoints(domains: str = "", limit_per_domain: int = 8) -> dict:
    """Return MCP-related concepts and direct relationships across platform graphs.

    Args:
        domains: Optional comma-separated domain filter.
        limit_per_domain: Maximum MCP concepts returned per domain.
    """
    selected, invalid = _selected_domains(domains)
    by_domain: dict[str, list[dict]] = {}
    seen: set[tuple[str, str]] = set()

    for term in ("mcp", "model context protocol"):
        for match in search_all_concepts(term, selected, limit=100):
            key = (match["domain"], match["concept_id"])
            if key in seen:
                continue
            seen.add(key)
            context = _concept_context(match["domain"], match["concept_id"])
            row = {
                "concept": context["concept"],
                "outgoing_relationships": context["outgoing_relationships"],
                "incoming_relationships": context["incoming_relationships"],
            }
            bucket = by_domain.setdefault(match["domain"], [])
            if len(bucket) < max(1, min(limit_per_domain, 25)):
                bucket.append(row)

    return {
        "searched_domains": selected,
        "invalid_domains": invalid,
        "domains_with_mcp": sorted(by_domain),
        "touchpoints_by_domain": by_domain,
    }


@mcp.tool()
def get_concept_context(concept: str, domain: str, depth: int = 1) -> dict:
    """Return source-pinned direct relationships and shallow traversal for a concept.

    Args:
        concept: Concept label; partial match supported.
        domain: Domain to search in.
        depth: Optional traversal depth for upstream/downstream paths, 1-5.
    """
    id_to_label, label_to_id, prerequisites, dependents, taxonomy, provenance = load_graph(domain)
    cid = find_concept(label_to_id, concept)
    if cid is None:
        sample = [
            {"concept_id": sample_id, "label": id_to_label[sample_id]}
            for sample_id in list(id_to_label)[:10]
        ]
        return {
            "error": f"Concept '{concept}' not found in {domain}.",
            "sample_concepts": sample,
        }

    max_depth = max(1, min(depth, 5))
    prov = provenance.get(cid, {})
    return {
        "domain": domain,
        "concept": {
            "id": cid,
            "label": id_to_label[cid],
            "taxonomy": taxonomy.get(cid, ""),
            "source_url": prov.get("source_url", ""),
            "source_hash": prov.get("source_hash", ""),
        },
        "outgoing_relationships": iter_edges(domain, cid),
        "incoming_relationships": [edge for edge in iter_edges(domain) if edge["to_id"] == cid],
        "upstream_traversal": bfs_subgraph(cid, prerequisites, id_to_label, max_depth=max_depth),
        "downstream_traversal": bfs_subgraph(cid, dependents, id_to_label, max_depth=max_depth),
    }


@mcp.tool()
def ask_platform(question: str, domain: str = "") -> str:
    """Answer a question about an AI platform by traversing the relevant CKG.

    Auto-detects the platform from the question if domain is not specified.

    Args:
        question: Your question about an AI platform concept or workflow.
        domain: Optional packaged domain. Call list_domains or list_atlas first.
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
        f"# CKG: {domain} - {concept_label}",
        f"Taxonomy: {taxonomy.get(cid, 'unknown')}",
        "",
        "## Declared upstream relationships",
    ]
    for label in chain[1:]:
        lines.append(f"  <- {label}")

    lines += ["", "## Direct downstream references"]
    for entry in subgraph:
        if entry["concept"] != concept_label and entry["depth"] == 1:
            lines.append(f"  {entry['edge_type']}: {entry['concept']}")

    if meta:
        lines += ["", f"Domain: {meta.get('description', '')}"]
    lines.append(f"\nSource: ckg-ai-platforms {_package_version()} - graphifymd.com")
    return "\n".join(lines)


@mcp.tool()
def list_domains() -> str:
    """List all available AI platform domains in this package."""
    domains = available_domains()
    lines = [f"Available domains ({len(domains)}):"]
    for d in sorted(domains):
        lines.append(f"  - {d}")
    lines.append("\nUse list_atlas(), compare_platforms(), get_concept_context(), query_ckg(), or ask_platform().")
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
        f"## {concept_label} [{taxonomy.get(cid, '')}] - {domain}",
        "",
        "### Declared upstream relationships",
    ]
    for label in chain[1:]:
        lines.append(f"  <- {label}")

    lines += ["", "### Direct and downstream references"]
    for entry in subgraph:
        if entry["concept"] != concept_label:
            lines.append(f"  -> {entry['concept']} [{entry['edge_type']}]")
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
    return f"Declared upstream chain for {id_to_label[cid]}:\n" + "\n".join(
        f"  {'  ' * i}<- {label}" for i, label in enumerate(chain[1:])
    )


@mcp.tool()
def verify_source(concept: str, domain: str) -> str:
    """Return the source URL and content hash for a concept node.

    Audit chain:
        edge answer -> graph commit -> source_hash -> source_url (fetch hint)

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
        "sha256:restricted": "Source returned 4xx/5xx - page requires auth or is gone.",
        "sha256:unavailable": "Network error at hash-compute time.",
        "sha256:no-source-url": "No source URL declared for this node.",
    }
    note = sentinel_notes.get(source_hash, "")

    lines = [
        f"## Source provenance - {label} ({domain})",
        f"",
        f"**concept:**      {label}",
        f"**taxonomy:**     {taxonomy.get(cid, 'unknown')}",
        f"**source_url:**   {source_url}",
        f"**source_hash:**  {source_hash}",
        f"**hash_scope:**   {'canonicalized content' if source_hash.startswith('sha256-canon:') else 'raw source bytes'}",
        f"**provenance:**   GuardrailDecisionV1 - v1",
        f"",
    ]
    if note:
        lines += [f"Warning: {note}", ""]
    else:
        lines += [
            "**Verification:**",
            f"```bash",
            f"curl -s '{source_url}' | sha256sum",
            f"# expected: {_hash_for_command(source_hash)}",
            f"```",
            "",
            "**source_hash** is the trust anchor. **source_url** is a fetch hint - page can change silently.",
        ]
        if source_hash.startswith("sha256-canon:"):
            lines.append("This node uses a canonicalized-content hash; raw HTTP bytes may not match directly.")
    return "\n".join(lines)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
