import json
import unittest
from pathlib import Path

from cr_agent.rules.loader import RuleMeta, load_rules_index


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _to_dict(meta: RuleMeta) -> dict:
    return {
        "rule_id": meta.rule_id,
        "title": meta.title,
        "language": meta.language,
        "severity": meta.severity,
        "prompt_hint": meta.prompt_hint,
        "applies": meta.applies,
        "signals": meta.signals,
        "doc_path": str(meta.doc_path) if meta.doc_path else None,
    }


class TestRulesLoader(unittest.TestCase):
    def test_load_rules_index_prints_current_config(self):
        root = _repo_root()
        registry_path = root / "coding-standards" / "registry.yaml"
        profile_path = root / "coding-standards" / "profiles" / "default.yaml"

        rules_index = load_rules_index(registry_path=registry_path, profile_path=profile_path)

        self.assertIn("GO-ERROR-002", rules_index)
        self.assertIn("GO-CONC-001", rules_index)
        self.assertIn("PY-UNICODE-002", rules_index)
        self.assertEqual(rules_index["GO-CONC-001"].severity, "warning")

        payload = {rule_id: _to_dict(meta) for rule_id, meta in sorted(rules_index.items())}
        print("\nParsed rules_index:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
