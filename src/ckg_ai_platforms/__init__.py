"""ckg-ai-platforms — AI developer platforms as traversable knowledge graphs."""
__version__ = "0.1.0"

from ckg_ai_platforms.server import (  # noqa: F401
    ask_platform,
    list_domains,
    search_concepts,
    query_ckg,
    get_prerequisites,
)
from ckg_ai_platforms.graph import (  # noqa: F401
    available_domains,
    load_graph,
    find_concept,
    prerequisite_chain,
)
