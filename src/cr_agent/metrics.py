from __future__ import annotations

import json
import os
import sys
import uuid
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

from cr_agent.models import CommitDiff, FileCRResult


def _now_iso_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _diff_lines_changed(commit_diff: CommitDiff | None) -> int:
    if not commit_diff:
        return 0
    total = 0
    for fd in commit_diff.files:
        total += max(0, fd.added_lines) + max(0, fd.deleted_lines)
    return total


def _rule_hit_counts(file_results: Iterable[FileCRResult]) -> Tuple[int, Dict[str, int]]:
    counts: Dict[str, int] = {}
    total_hits = 0
    for fr in file_results:
        for issue in fr.issues:
            for rule_id in issue.rule_ids:
                if not rule_id:
                    continue
                counts[rule_id] = counts.get(rule_id, 0) + 1
                total_hits += 1
    return total_hits, counts


def build_metrics_payload(
    *,
    repo_path: str,
    commit_diff: CommitDiff | None,
    file_results: Iterable[FileCRResult],
) -> Dict[str, object]:
    repo_name = os.getenv("MODULE_NAME") or os.getenv("CR_REPO_NAME") or Path(repo_path).name
    code_change_id = os.getenv("CHANGE_URL") or "unknown"
    agent_version = os.getenv("CR_AGENT_VERSION", "unknown")
    ruleset_version = os.getenv("CR_RULESET_VERSION", "unknown")
    agent_run_id = str(uuid.uuid4())
    reported_at = _now_iso_utc()
    diff_lines = _diff_lines_changed(commit_diff)
    triggered_total_hits, rule_hits = _rule_hit_counts(file_results)

    return {
        "repo": repo_name,
        "code_change_id": code_change_id,
        "agent_run_id": agent_run_id,
        "reported_at": reported_at,
        "diff_lines": diff_lines,
        "agent_version": agent_version,
        "ruleset_version": ruleset_version,
        "triggered_total_hits": triggered_total_hits,
        "rule_hits": rule_hits,
    }


def send_metrics_report(payload: Dict[str, object], *, base_url: str, timeout: float = 5.0) -> None:
    if not base_url:
        return
    url = f"{base_url.rstrip('/')}/v1/metrics/agent-runs"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    print(f"[CR] Metrics request: {json.dumps(payload, ensure_ascii=False)}")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            text = body.decode("utf-8", errors="replace") if body else ""
            status = getattr(response, "status", None)
            print(f"[CR] Metrics response: status={status} body={text}")
    except Exception as exc:  # pragma: no cover - non-fatal metrics reporting
        print(f"[WARN] Metrics report failed: {exc}", file=sys.stderr)
