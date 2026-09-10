import unittest

from ckg_ai_platforms.graph import (
    atlas_totals,
    available_domains,
    domain_stats,
    iter_edges,
    load_graph,
    search_all_concepts,
)


class GraphAtlasTests(unittest.TestCase):
    def test_atlas_inventory_counts_packaged_csvs(self):
        self.assertEqual(len(available_domains()), 11)
        self.assertEqual(atlas_totals(), {"domains": 11, "nodes": 475, "edges": 550})

    def test_all_packaged_domains_load(self):
        for domain in available_domains():
            with self.subTest(domain=domain):
                id_to_label, label_to_id, prerequisites, dependents, taxonomy, provenance = load_graph(domain)
                self.assertTrue(id_to_label)
                self.assertTrue(label_to_id)
                self.assertTrue(prerequisites)
                self.assertTrue(dependents)
                self.assertTrue(taxonomy)
                self.assertTrue(provenance)

    def test_new_agent_platform_domains_are_included(self):
        domains = set(available_domains())
        self.assertIn("aws-bedrock-agentcore", domains)
        self.assertIn("google-gemini-agent-platform", domains)
        self.assertIn("microsoft-ai-agent-stack", domains)
        self.assertIn("palantir-foundry", domains)

    def test_relation_verbs_are_preserved(self):
        palantir_relations = {edge["relation"] for edge in iter_edges("palantir-foundry")}
        aws_relations = {edge["relation"] for edge in iter_edges("aws-bedrock-agentcore")}
        microsoft_relations = {edge["relation"] for edge in iter_edges("microsoft-ai-agent-stack")}

        self.assertIn("PART_OF", palantir_relations)
        self.assertIn("DEPLOYS", palantir_relations)
        self.assertIn("CONNECTS_TO", aws_relations)
        self.assertIn("EXPOSES", aws_relations)
        self.assertIn("SUBTYPE_OF", microsoft_relations)

    def test_mcp_search_finds_cross_platform_touchpoints(self):
        matches = search_all_concepts("mcp", limit=100)
        domains = {match["domain"] for match in matches}

        self.assertIn("anthropic-sdk", domains)
        self.assertIn("aws-bedrock-agentcore", domains)
        self.assertIn("google-gemini-agent-platform", domains)
        self.assertIn("microsoft-ai-agent-stack", domains)

    def test_metadata_matches_runtime_counts(self):
        for domain in available_domains():
            with self.subTest(domain=domain):
                stats = domain_stats(domain)
                rows = load_graph(domain)[0]
                self.assertEqual(stats["nodes"], len(rows))
                self.assertEqual(stats["edges"], len(iter_edges(domain)))


if __name__ == "__main__":
    unittest.main()
