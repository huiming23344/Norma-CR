from __future__ import annotations

import os
from collections import defaultdict
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cr_agent.rules.loader import load_rules_catalog


def _load_env() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
    else:
        load_dotenv(override=False)


def _repo_root() -> Path:
    return ROOT


def _rules_dir() -> Path:
    value = os.getenv("CR_RULES_DIR")
    if not value:
        return _repo_root() / "coding-standards" / "rules"
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (_repo_root() / path).resolve()
    return path


def _print_rules(catalog) -> None:
    print("\n=== 按语言 -> domain 分组 ===")
    for language in sorted(catalog.by_language.keys()):
        print(f"\n[{language}]")
        domain_map = catalog.by_language_domain.get(language, {})
        for domain in sorted(domain_map.keys()):
            print(f"  [{domain}]")
            for meta in domain_map[domain]:
                doc = str(meta.doc_path) if meta.doc_path else "-"
                print(f"  - {meta.rule_id}: {meta.title} (doc: {doc})")


def main():
    _load_env()
    rules_dir = _rules_dir()
    catalog = load_rules_catalog(rules_dir=rules_dir)
    print(f"Loaded {len(catalog.by_id)} rules from {rules_dir}")
    _print_rules(catalog)


if __name__ == "__main__":
    main()
