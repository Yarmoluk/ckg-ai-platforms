import csv
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Iterable

DOMAINS_DIR = Path(__file__).parent / "domains"

DEFAULT_EDGE_TYPE = "REQUIRES"


def _parse_dep(token: str) -> tuple[str, str, float | None]:
    """Split 'ID:EDGETYPE:CONFIDENCE' token.
    EDGETYPE defaults to REQUIRES. CONFIDENCE is float 0-1 or None if unreviewed.
    """
    parts = [p.strip() for p in token.split(":", 2)]
    etype = DEFAULT_EDGE_TYPE
    confidence = None

    if len(parts) >= 2 and parts[1]:
        candidate = parts[1].upper()
        try:
            confidence = float(candidate)
        except ValueError:
            etype = candidate

    if len(parts) == 3 and parts[2]:
        try:
            confidence = float(parts[2])
        except ValueError:
            pass
    return parts[0], etype, confidence


def load_domain_meta(domain: str) -> dict:
    """Return domain-level provenance: source_url, build_date."""
    meta_path = DOMAINS_DIR / "metadata.json"
    if not meta_path.exists():
        return {}
    with open(meta_path) as f:
        data = json.load(f)
    return data.get(domain, {})


def available_domains() -> list[str]:
    return sorted(p.stem for p in DOMAINS_DIR.glob("*.csv"))


def load_graph(domain: str):
    csv_path = DOMAINS_DIR / f"{domain}.csv"
    if not csv_path.exists():
        raise ValueError(f"Domain '{domain}' not found. Run list_domains() to see available domains.")

    id_to_label, label_to_id, prerequisites, dependents, taxonomy, provenance = {}, {}, defaultdict(list), defaultdict(list), {}, {}
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            cid = row["ConceptID"]
            label = row["ConceptLabel"].strip()
            raw = [t.strip() for t in row["Dependencies"].split("|") if t.strip()]
            deps = [_parse_dep(t) for t in raw]  # [(dep_id, etype, confidence), ...]
            id_to_label[cid] = label
            label_to_id[label.lower()] = cid
            taxonomy[cid] = row.get("TaxonomyID", "").strip()
            prerequisites[cid] = deps
            provenance[cid] = {
                "source_url": row.get("SourceURL", ""),
                "source_hash": row.get("source_content_hash", ""),
            }
            for dep_id, etype, confidence in deps:
                dependents[dep_id].append((cid, etype, confidence))

    return id_to_label, label_to_id, prerequisites, dependents, taxonomy, provenance


def iter_edges(domain: str, concept_id: str | None = None) -> list[dict]:
    """Return typed edges as from-concept -> to-concept records."""
    id_to_label, _, prerequisites, _, _, _ = load_graph(domain)
    rows: list[dict] = []
    for from_id, deps in prerequisites.items():
        if concept_id is not None and from_id != concept_id:
            continue
        for to_id, etype, confidence in deps:
            rows.append(
                {
                    "from_id": from_id,
                    "from_label": id_to_label.get(from_id, from_id),
                    "relation": etype,
                    "to_id": to_id,
                    "to_label": id_to_label.get(to_id, to_id),
                    "confidence": confidence,
                }
            )
    return rows


def domain_stats(domain: str) -> dict:
    """Return counts and coverage for one packaged domain."""
    id_to_label, _, prerequisites, _, taxonomy, provenance = load_graph(domain)
    edge_count = sum(len(deps) for deps in prerequisites.values())
    relation_counts = Counter(
        etype for deps in prerequisites.values() for _dep_id, etype, _confidence in deps
    )
    taxonomy_counts = Counter(taxonomy.values())
    sourced = sum(
        1
        for prov in provenance.values()
        if prov.get("source_url") and prov.get("source_hash")
    )
    meta = load_domain_meta(domain)
    return {
        "domain": domain,
        "nodes": len(id_to_label),
        "edges": edge_count,
        "source_coverage": f"{sourced}/{len(id_to_label)}",
        "description": meta.get("description", ""),
        "relation_counts": dict(sorted(relation_counts.items())),
        "taxonomy_counts": dict(sorted(taxonomy_counts.items())),
    }


def all_domain_stats() -> list[dict]:
    return [domain_stats(domain) for domain in available_domains()]


def atlas_totals() -> dict:
    stats = all_domain_stats()
    return {
        "domains": len(stats),
        "nodes": sum(row["nodes"] for row in stats),
        "edges": sum(row["edges"] for row in stats),
    }


def search_all_concepts(
    query: str,
    domains: Iterable[str] | None = None,
    limit: int = 40,
) -> list[dict]:
    """Search concept labels across domains and return ranked matches."""
    q = query.lower().strip()
    if not q:
        return []

    selected = list(domains) if domains is not None else available_domains()
    matches: list[tuple[int, str, str, str, dict]] = []
    for domain in selected:
        id_to_label, label_to_id, _, _, taxonomy, provenance = load_graph(domain)
        for label_lower, cid in label_to_id.items():
            if q not in label_lower:
                continue
            if label_lower == q:
                score = 0
            elif label_lower.startswith(q):
                score = 1
            else:
                score = 2
            prov = provenance.get(cid, {})
            matches.append(
                (
                    score,
                    domain,
                    id_to_label[cid].lower(),
                    cid,
                    {
                        "domain": domain,
                        "concept_id": cid,
                        "label": id_to_label[cid],
                        "taxonomy": taxonomy.get(cid, ""),
                        "source_url": prov.get("source_url", ""),
                        "source_hash": prov.get("source_hash", ""),
                    },
                )
            )
    matches.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    return [row for *_sort, row in matches[: max(1, min(limit, 100))]]


def find_concept(label_to_id: dict, query: str) -> str | None:
    q = query.lower().strip()
    if q in label_to_id:
        return label_to_id[q]
    for label, cid in label_to_id.items():
        if q in label:
            return cid
    return None


def bfs_subgraph(start_id: str, adj: dict, id_to_label: dict, max_depth: int) -> list[dict]:
    """DFS traversal so parent-child relationships indent correctly in text output."""
    visited: set = set()
    results: list[dict] = []

    def _dfs(cid: str, depth: int, etype, conf):
        if cid in visited or depth > max_depth:
            return
        visited.add(cid)
        results.append({
            "concept": id_to_label.get(cid, cid),
            "concept_id": cid,
            "edge_type": etype,
            "confidence": conf,
            "depth": depth,
        })
        for n, et, c in adj.get(cid, []):
            _dfs(n, depth + 1, et, c)

    _dfs(start_id, 0, None, None)
    return results


def prerequisite_chain(start_id: str, prerequisites: dict, id_to_label: dict) -> list[str]:
    visited, queue, chain = set(), deque([start_id]), []
    while queue:
        cid = queue.popleft()
        if cid in visited:
            continue
        visited.add(cid)
        chain.append(id_to_label.get(cid, cid))
        for dep_id, _etype, _conf in prerequisites.get(cid, []):
            if dep_id not in visited:
                queue.append(dep_id)
    return chain
