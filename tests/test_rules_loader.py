import json
import unittest
from pathlib import Path

from cr_agent.rules.loader import RuleMeta, RulesCatalog, load_rules_catalog, load_rules_index


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _to_dict(meta: RuleMeta) -> dict:
    return {
        "rule_id": meta.rule_id,
        "title": meta.title,
        "language": meta.language,
        "severity": meta.severity,
        "domains": list(meta.domains),
        "prompt_hint": meta.prompt_hint,
        "doc_path": str(meta.doc_path) if meta.doc_path else None,
    }


class TestRulesLoader(unittest.TestCase):
    @property
    def _paths(self):
        root = _repo_root()
        return {
            "registry": root / "coding-standards" / "registry.yaml",
            "profile": root / "coding-standards" / "profiles" / "default.yaml",
        }

    def test_catalog_grouping_and_domains(self):
        catalog = load_rules_catalog(registry_path=self._paths["registry"], profile_path=self._paths["profile"])
        self.assertIsInstance(catalog, RulesCatalog)

        rules_index = catalog.by_id
        expected_ids = {
            "GO-ERROR-002",
            "GO-CONC-001",
            "GO-SEC-001",
            "PY-UNICODE-002",
            "PY-TEST-001",
        }
        self.assertEqual(set(rules_index.keys()), expected_ids)

        self.assertEqual(rules_index["GO-ERROR-002"].domains, ("ERROR",))
        self.assertEqual(rules_index["GO-CONC-001"].domains, ("CONC", "PERF"))
        self.assertEqual(rules_index["PY-UNICODE-002"].domains, ("STYLE", "ERROR"))
        self.assertNotIn("RELIABILITY", catalog.by_domain)

        go_rule_ids = [meta.rule_id for meta in catalog.by_language["go"]]
        py_rule_ids = [meta.rule_id for meta in catalog.by_language["python"]]
        self.assertEqual(go_rule_ids, ["GO-CONC-001", "GO-ERROR-002", "GO-SEC-001"])
        self.assertEqual(py_rule_ids, ["PY-TEST-001", "PY-UNICODE-002"])

        error_domain_ids = [meta.rule_id for meta in catalog.by_domain["ERROR"]]
        self.assertEqual(error_domain_ids, ["GO-ERROR-002", "PY-UNICODE-002"])
        go_perf = [meta.rule_id for meta in catalog.by_language_domain["go"]["PERF"]]
        self.assertEqual(go_perf, ["GO-CONC-001"])
        py_style = [meta.rule_id for meta in catalog.by_language_domain["python"]["STYLE"]]
        self.assertEqual(py_style, ["PY-TEST-001", "PY-UNICODE-002"])

        summary = {
            "by_language": {lang: [m.rule_id for m in metas] for lang, metas in catalog.by_language.items()},
            "by_domain": {domain: [m.rule_id for m in metas] for domain, metas in catalog.by_domain.items()},
            "by_language_domain": {
                lang: {domain: [m.rule_id for m in metas] for domain, metas in domains.items()}
                for lang, domains in catalog.by_language_domain.items()
            },
        }
        print("\nRules catalog summary:\n" + json.dumps(summary, ensure_ascii=False, indent=2))

    def test_load_rules_index_compatibility(self):
        rules_index = load_rules_index(registry_path=self._paths["registry"], profile_path=self._paths["profile"])
        self.assertIn("GO-SEC-001", rules_index)
        payload = {rule_id: _to_dict(meta) for rule_id, meta in sorted(rules_index.items())}
        print("\nLegacy rules_index payload:\n" + json.dumps(payload, ensure_ascii=False, indent=2))
