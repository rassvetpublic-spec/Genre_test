from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "tests" / "fixtures" / "rules_hub_interop" / "profile_v1.json"
INTEROP_PATH = ROOT / "docs" / "RULES_HUB_INTEROPERABILITY.md"
PROPERTY_SCHEMA_PATH = ROOT / "docs" / "obsidian" / "PROPERTY_SCHEMA.md"
RELATION_SCHEMA_PATH = ROOT / "docs" / "obsidian" / "RELATION_SCHEMA.md"
RESEARCH_RADAR_PATH = ROOT / "docs" / "research" / "RESEARCH_RADAR.md"

EXPECTED_DOC_TYPES = [
    "architecture",
    "protocol",
    "reference",
    "research",
    "decision",
    "runbook",
    "status",
    "index",
    "guide",
    "machine_prompt",
]

EXPECTED_STATUSES = [
    "canonical",
    "active",
    "proposal",
    "reference",
    "archived",
    "generated",
]

EXPECTED_RELATIONS = [
    "parent",
    "depends_on",
    "implementation_of",
    "supersedes",
    "superseded_by",
    "evidence_for",
    "research_for",
    "related",
]

EXPECTED_OWNERSHIP_CLASSES = [
    "canonical_document",
    "canonical_machine_state",
    "generated_projection",
    "derived_index",
    "visualization",
]

HEX40 = re.compile(r"^[0-9a-f]{40}$")


def load_profile() -> dict[str, Any]:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RulesHubInteroperabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_profile()
        cls.interop = read(INTEROP_PATH)
        cls.property_schema = read(PROPERTY_SCHEMA_PATH)
        cls.relation_schema = read(RELATION_SCHEMA_PATH)
        cls.research_radar = read(RESEARCH_RADAR_PATH)

    def test_profile_is_versioned_non_authoritative_and_immutably_pinned(self) -> None:
        self.assertEqual(
            self.profile["schema"],
            "genre-test-rules-hub-interop-profile-v1",
        )
        self.assertEqual(type(self.profile["schema_version"]), int)
        self.assertEqual(self.profile["schema_version"], 1)
        self.assertEqual(
            self.profile["authority_class"],
            "compatibility_fixture_evidence_only",
        )
        self.assertNotIn(
            self.profile["authority_class"],
            EXPECTED_OWNERSHIP_CLASSES,
        )

        peer = self.profile["peer"]
        self.assertEqual(peer["repository"], "rassvetpublic-spec/rassvet-rules-hub")
        self.assertEqual(
            peer["source_path"],
            "docs/GENRE_TEST_INTEROPERABILITY_PROPOSAL.md",
        )
        self.assertIsNotNone(HEX40.fullmatch(peer["revision"]))
        self.assertIsNotNone(HEX40.fullmatch(peer["source_blob"]))
        self.assertNotIn("branch", peer)
        self.assertNotIn("ref", peer)

    def test_shared_invariant_is_identical_to_local_contract(self) -> None:
        invariant = "ONE FACT -> ONE CANONICAL OWNER -> MANY VIEWS"
        self.assertEqual(self.profile["invariant"], invariant)
        self.assertIn(invariant, self.interop)
        self.assertIn(invariant, self.property_schema)

    def test_shared_document_type_vocabulary_matches_phase_zero(self) -> None:
        actual = self.profile["shared_vocabulary"]["doc_type"]
        self.assertEqual(actual, EXPECTED_DOC_TYPES)
        for value in actual:
            with self.subTest(doc_type=value):
                self.assertRegex(
                    self.property_schema,
                    rf"(?m)^\s*{re.escape(value)}\s*$",
                )

    def test_shared_status_vocabulary_matches_phase_zero(self) -> None:
        actual = self.profile["shared_vocabulary"]["status"]
        self.assertEqual(actual, EXPECTED_STATUSES)
        for value in actual:
            with self.subTest(status=value):
                self.assertRegex(
                    self.property_schema,
                    rf"(?m)^\s*{re.escape(value)}\s*$",
                )

    def test_shared_typed_relations_match_phase_zero(self) -> None:
        actual = self.profile["shared_vocabulary"]["typed_relations"]
        self.assertEqual(actual, EXPECTED_RELATIONS)
        for value in actual:
            with self.subTest(relation=value):
                self.assertIn(f"### `{value}`", self.relation_schema)

    def test_ownership_classes_have_the_same_local_meaning(self) -> None:
        actual = self.profile["shared_vocabulary"]["ownership_classes"]
        self.assertEqual(actual, EXPECTED_OWNERSHIP_CLASSES)
        for value in actual:
            with self.subTest(ownership_class=value):
                self.assertIn(f"### `{value}`", self.property_schema)
                self.assertIn(value, self.interop)

    def test_area_and_domain_fields_remain_project_local(self) -> None:
        local_fields = set(self.profile["project_local_fields"])
        self.assertEqual(
            local_fields,
            {
                "area",
                "domain_registries",
                "product_capabilities",
                "specialized_lifecycle_fields",
            },
        )
        self.assertIn("Project-local fields remain project-local", self.interop)
        self.assertIn("`area`", self.interop)

    def test_generated_projection_is_one_way_and_cannot_gain_reverse_authority(self) -> None:
        projection = self.profile["projection_semantics"]
        self.assertEqual(projection["source_class"], "canonical_machine_state")
        self.assertEqual(projection["target_class"], "generated_projection")
        self.assertEqual(projection["direction"], "one_way")
        self.assertIs(projection["reverse_authority"], False)
        self.assertIn("generated_projection", self.interop)
        self.assertIn("JSON -> generated Markdown", self.interop)
        self.assertIn("не становится owner", self.property_schema)

    def test_provenance_envelope_has_stable_owner_locator_fields(self) -> None:
        provenance = self.profile["shared_vocabulary"]["provenance"]
        self.assertEqual(provenance["required"], ["repository", "path", "revision"])
        self.assertEqual(
            provenance["classification_field_options"],
            ["classification", "ownership_class"],
        )
        for value in (
            "repository",
            "path",
            "revision",
            "classification",
            "ownership class",
        ):
            with self.subTest(field=value):
                self.assertIn(value, self.interop)

    def test_research_radar_state_is_repository_local_and_projection_only(self) -> None:
        radar = self.profile["research_radar"]
        self.assertIs(radar["shared_structure_only"], True)
        self.assertIs(radar["shared_mutable_state"], False)
        self.assertEqual(radar["canonical_machine_state_format"], "JSON")
        self.assertEqual(radar["generated_projection_format"], "Markdown")
        self.assertIn("JSON -> generated Markdown", self.interop)
        self.assertIn("shared mutable Research Radar state", self.interop)
        self.assertIn("canonical in JSON", self.research_radar)
        self.assertIn("generated projection only", self.research_radar)
        self.assertIn("`JSON -> Markdown`", self.research_radar)

    def test_forbidden_cross_project_semantics_are_explicit(self) -> None:
        forbidden = set(self.profile["forbidden_cross_project_semantics"])
        self.assertEqual(
            forbidden,
            {
                "shared_mutable_vault",
                "shared_mutable_research_radar_state",
                "peer_repository_authority_override",
                "live_peer_branch_ci_dependency",
                "cross_repository_canonical_mutation",
                "bidirectional_json_markdown_state_sync",
            },
        )
        for phrase in (
            "one shared mutable Vault",
            "one shared mutable Research Radar state",
            "direct cross-repository mutation",
            "bidirectional JSON/Markdown state synchronization",
            "live `peer/main`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.interop)

    def test_compatibility_fixture_never_uses_live_peer_branch_as_authority(self) -> None:
        peer = self.profile["peer"]
        self.assertIsNotNone(HEX40.fullmatch(peer["revision"]))
        self.assertNotIn("main", peer)
        self.assertNotIn("branch", peer)
        self.assertNotIn("ref", peer)
        self.assertIn("never live `peer/main`", self.interop)


if __name__ == "__main__":
    unittest.main()
