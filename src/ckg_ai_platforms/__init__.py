"""ckg-ai-platforms - AI developer platforms as traversable knowledge graphs."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ckg-ai-platforms")
except PackageNotFoundError:
    __version__ = "0.0.0+local"

from ckg_ai_platforms.graph import (  # noqa: F401
    all_domain_stats,
    atlas_totals,
    available_domains,
    domain_stats,
    load_graph,
    find_concept,
    iter_edges,
    prerequisite_chain,
    search_all_concepts,
)

_SERVER_EXPORTS = (
    "ask_platform",
    "compare_platforms",
    "find_mcp_touchpoints",
    "get_concept_context",
    "get_platform_summary",
    "get_prerequisites",
    "list_atlas",
    "list_domains",
    "query_ckg",
    "search_concepts",
)

__all__ = [
    "__version__",
    "all_domain_stats",
    "atlas_totals",
    "available_domains",
    "domain_stats",
    "find_concept",
    "iter_edges",
    "load_graph",
    "prerequisite_chain",
    "search_all_concepts",
    *_SERVER_EXPORTS,
]


def __getattr__(name: str):
    if name in _SERVER_EXPORTS:
        from ckg_ai_platforms import server

        value = getattr(server, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'ckg_ai_platforms' has no attribute {name!r}")
