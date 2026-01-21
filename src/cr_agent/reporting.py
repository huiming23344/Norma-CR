from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from markdown_it import MarkdownIt

from cr_agent.models import CRIssue, CommitDiff, FileCRResult, FileDiff, FileHunk
from cr_agent.rules import get_rules_catalog


def render_markdown_report(
    *,
    repo_path: str,
    commit_diff: CommitDiff,
    file_results: Iterable[FileCRResult],
) -> str:
    renderer = _MarkdownReportRenderer(repo_path=Path(repo_path), commit_diff=commit_diff)
    return renderer.render(list(file_results))


def render_html_report(
    *,
    repo_path: str,
    commit_diff: CommitDiff,
    file_results: Iterable[FileCRResult],
) -> str:
    markdown = render_markdown_report(
        repo_path=repo_path,
        commit_diff=commit_diff,
        file_results=file_results,
    )
    return _wrap_markdown_as_html(markdown)


def render_ndjson_report(
    *,
    repo_path: str,
    commit_diff: CommitDiff,
    file_results: Iterable[FileCRResult],
) -> str:
    renderer = _MarkdownReportRenderer(repo_path=Path(repo_path), commit_diff=commit_diff)
    records = renderer.iter_issue_records(list(file_results))
    return "\n".join(json.dumps(record, ensure_ascii=False) for record in records)


def _wrap_markdown_as_html(markdown: str) -> str:
    rendered = _render_markdown_as_html(markdown)
    return "\n".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "  <meta charset=\"utf-8\">",
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "  <title>Code Review Report</title>",
            "  <style>",
            "    body { font-family: monospace; margin: 24px; }",
            "    pre { white-space: pre-wrap; word-wrap: break-word; }",
            "  </style>",
            "</head>",
            "<body>",
            rendered,
            "</body>",
            "</html>",
        ]
    )


def _render_markdown_as_html(markdown: str) -> str:
    md = MarkdownIt("gfm-like", {"html": False, "linkify": True})
    return md.render(markdown)


def write_markdown_report(
    *,
    repo_path: str,
    commit_diff: CommitDiff,
    file_results: Iterable[FileCRResult],
    custom_dir: Optional[str] = None,
    report_text: Optional[str] = None,
    ndjson_text: Optional[str] = None,
    file_name: Optional[str] = None,
    report_format: str = "md",
) -> Tuple[Path, Optional[Path]]:
    report_md = report_text or render_markdown_report(
        repo_path=repo_path,
        commit_diff=commit_diff,
        file_results=file_results,
    )
    target_dir = Path(custom_dir).expanduser().resolve() if custom_dir else Path(repo_path)
    target_dir.mkdir(parents=True, exist_ok=True)

    normalized_format = report_format.strip().lower()
    if normalized_format not in {"md", "html"}:
        raise ValueError(f"CR_REPORT_FORMAT must be 'md' or 'html', got '{report_format}'")

    base_name = file_name or "code_review_report.md"
    if normalized_format == "html":
        report_name = "cr_report.html"
    else:
        report_name = Path(base_name).with_suffix(".md").name
    report_path = target_dir / report_name
    if normalized_format == "html":
        report_html = _wrap_markdown_as_html(report_md)
        report_path.write_text(report_html, encoding="utf-8")
    else:
        report_path.write_text(report_md, encoding="utf-8")

    ndjson_path: Optional[Path] = None
    if ndjson_text is not None:
        ndjson_name = Path(base_name).with_suffix(".ndjson").name
        ndjson_path = target_dir / ndjson_name
        ndjson_path.write_text(ndjson_text, encoding="utf-8")

    return report_path, ndjson_path


def summarize_to_cli(*, commit_diff: CommitDiff, file_results: Iterable[FileCRResult], report_path: Optional[Path] = None) -> None:
    files_count = len(list(file_results))
    title = (commit_diff.message or "").strip().splitlines()[0] if commit_diff else ""
    print(f"[CR] {title or '变更'} | 文件 {files_count} | 报告: {report_path or '未写入'}")


@dataclass
class _MarkdownReportRenderer:
    repo_path: Path
    commit_diff: CommitDiff
    _file_index: Dict[str, FileDiff] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        index: Dict[str, FileDiff] = {}
        for fd in self.commit_diff.files:
            if fd.a_path:
                index[fd.a_path] = fd
            if fd.b_path:
                index[fd.b_path] = fd
        self._file_index = index

    def render(self, results: List[FileCRResult]) -> str:
        overview = self._render_overview(results)
        rule_issues_md, general_issues_md = self._render_issues(results)

        parts = [
            "# Code Review Report",
            "## 概述",
            overview,
            "## Rule Issues",
            rule_issues_md or "_无带 rule_id 的问题。_",
            "## General Issues",
            general_issues_md or "_无未关联 rule 的问题。_",
        ]
        return "\n\n".join(part for part in parts if part is not None)

    def _render_overview(self, results: List[FileCRResult]) -> str:
        files_count = len(results)
        approvals = sum(1 for r in results if r.approved)
        needs_review = sum(1 for r in results if r.needs_human_review)
        commit_title = (self.commit_diff.message or "").strip().splitlines()[0] if self.commit_diff else ""

        lines = [
            f"- 变更摘要：{commit_title or '（无提交信息）'}",
            f"- 文件数：{files_count}（通过 {approvals}，需人工 {needs_review}）",
        ]
        breakdown = self._render_file_issue_breakdown(results)
        if breakdown:
            lines.append("")
            lines.append(breakdown)
        return "\n".join(lines)

    def _render_file_issue_breakdown(self, results: List[FileCRResult]) -> str:
        with_rule: Dict[str, int] = {}
        no_rule: Dict[str, int] = {}

        for fr in results:
            for issue in fr.issues:
                file_path = issue.file_path or fr.file_path or "<unknown>"
                rule_id = self._extract_rule_id(issue, fr)
                if rule_id:
                    with_rule[file_path] = with_rule.get(file_path, 0) + 1
                else:
                    no_rule[file_path] = no_rule.get(file_path, 0) + 1

        sections = [
            "### 文件问题分布（含 rule_id）",
            self._render_issue_count_table(with_rule) or "_无带 rule_id 的问题。_",
            "### 文件问题分布（无 rule_id）",
            self._render_issue_count_table(no_rule) or "_无未关联 rule 的问题。_",
        ]
        return "\n\n".join(sections)

    @staticmethod
    def _render_issue_count_table(counts: Dict[str, int]) -> Optional[str]:
        if not counts:
            return None
        rows = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        lines = ["| 文件 | Issue 数 |", "| --- | --- |"]
        lines.extend(f"| {path} | {count} |" for path, count in rows)
        return "\n".join(lines)

    def _render_issues(self, results: List[FileCRResult]) -> Tuple[str, str]:
        with_rule: List[str] = []
        general: List[str] = []

        for fr in results:
            for issue in fr.issues:
                rule_id = self._extract_rule_id(issue, fr)
                block = self._render_issue_block(issue, fr, rule_id=rule_id)
                if rule_id:
                    with_rule.append(block)
                else:
                    general.append(block)

        return "\n\n".join(with_rule), "\n\n".join(general)

    def iter_issue_records(self, results: List[FileCRResult]) -> Iterable[Dict[str, object]]:
        for fr in results:
            for issue in fr.issues:
                rule_id = self._extract_rule_id(issue, fr)
                location = self._format_location(issue, fr)
                hunk = self._find_hunk(issue, fr)
                yield {
                    "rule_id": rule_id,
                    "file": issue.file_path or fr.file_path,
                    "hunk_id": issue.hunk_id,
                    "hunk_header": hunk.header if hunk else None,
                    "hit": bool(rule_id),
                    "severity": issue.severity,
                    "message": issue.message,
                    "location": location,
                    "approved": fr.approved,
                }

    def _extract_rule_id(self, issue: CRIssue, file_result: FileCRResult) -> Optional[str]:
        if issue.rule_ids:
            return ",".join(str(rid) for rid in issue.rule_ids if rid)

        extras = getattr(issue, "model_extra", {}) or {}
        if "rule_id" in extras:
            value = extras["rule_id"]
            if value:
                return str(value)

        per_tag = file_result.meta.get("per_tag") or []
        for entry in per_tag:
            if isinstance(entry, dict) and "meta" in entry and isinstance(entry["meta"], dict):
                rid = entry["meta"].get("rule_id")
                if rid:
                    return str(rid)
        return None

    def _render_issue_block(self, issue: CRIssue, fr: FileCRResult, *, rule_id: Optional[str]) -> str:
        location = self._format_location(issue, fr)
        rule_title = self._lookup_rule_title(rule_id)
        rule_hint = self._lookup_rule_hint(rule_id)
        header = f"### [{rule_id}] {rule_title}" if rule_id else f"### {location}"

        lines = [header]
        lines.append(f"- 说明：{issue.message}")
        if issue.suggestion:
            lines.append(f"- 建议：{issue.suggestion}")
        if rule_id:
            lines.append(f"- 规则说明：{rule_hint}")
        if location:
            lines.append(f"- 位置：{location}")
        hunk = self._find_hunk(issue, fr)
        if hunk:
            lines.append(f"- Hunk：{hunk.header}")
        lines.append(f"- 严重级别：{issue.severity}")

        code_block = self._render_code_context(issue, fr)
        if code_block:
            lines.append("```")
            lines.append(code_block)
            lines.append("```")

        return "\n".join(lines)

    def _format_location(self, issue: CRIssue, fr: FileCRResult) -> str:
        path = issue.file_path or fr.file_path or "<unknown>"
        if issue.hunk_id:
            return f"{path}#hunk-{issue.hunk_id}"
        return path

    def _render_code_context(self, issue: CRIssue, fr: FileCRResult) -> Optional[str]:
        hunk = self._find_hunk(issue, fr)
        if hunk:
            return hunk.text
        return None

    def _find_hunk(self, issue: CRIssue, fr: FileCRResult) -> Optional[FileHunk]:
        hunk_id = issue.hunk_id
        if not hunk_id:
            return None
        path = issue.file_path or fr.file_path
        if not path:
            return None
        file_diff = self._file_index.get(path)
        if not file_diff:
            return None
        if 1 <= hunk_id <= len(file_diff.hunks):
            return file_diff.hunks[hunk_id - 1]
        return None

    @staticmethod
    def _lookup_rule_title(rule_id: Optional[str]) -> str:
        if not rule_id:
            return "未关联规则"
        try:
            meta = get_rules_catalog().by_id.get(rule_id)
        except Exception:
            meta = None
        return meta.title if meta and meta.title else rule_id

    @staticmethod
    def _lookup_rule_hint(rule_id: Optional[str]) -> str:
        if not rule_id:
            return "无规则说明"
        try:
            meta = get_rules_catalog().by_id.get(rule_id)
        except Exception:
            meta = None
        if meta:
            parts = [meta.prompt_hint or "", meta.raw.get("description", "")]
            text = "；".join(p.strip() for p in parts if p and str(p).strip())
            return text or "无规则说明"
        return "无规则说明"
