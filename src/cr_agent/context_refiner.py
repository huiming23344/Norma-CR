from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ValidationError

from cr_agent.models import CommitDiff, CRIssue, FileCRResult, FileDiff, FileHunk


class _ContextRefineItem(BaseModel):
    issue_index: int = Field(..., ge=0)
    context_snippet: str = ""


class _ContextRefineResult(BaseModel):
    items: List[_ContextRefineItem] = Field(default_factory=list)


@dataclass
class ContextRefiner:
    llm: object
    min_hunk_lines: int = 30
    min_snippet_lines: int = 5
    max_snippet_lines: int = 10

    def __post_init__(self) -> None:
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是代码审查报告的“上下文精炼器”。\n"
                    "输入是一个 diff hunk 以及若干 issue，你需要从 hunk 中为每个 issue 提取最小且有效的上下文片段。\n"
                    "要求：\n"
                    "1) 每个 issue 输出 5~10 行左右的片段，尽量短但要能支撑 issue 的定位；\n"
                    "2) 必须来自原始 hunk，保留 diff 标记（+/-/空格），不要编造新行；\n"
                    "3) 只返回片段本身，不要添加额外说明；\n"
                    "4) 如果找不到明确对应片段，输出空字符串。\n"
                    "输出必须符合结构化 JSON 模式。",
                ),
                (
                    "human",
                    "hunk_text:\n{hunk_text}\n\n"
                    "issues_json:\n{issues_json}\n\n"
                    "min_lines: {min_lines}\n"
                    "max_lines: {max_lines}\n",
                ),
            ]
        )
        self._chain = self._prompt | self.llm.with_structured_output(_ContextRefineResult)

    async def refine(
        self,
        *,
        commit_diff: CommitDiff,
        file_results: Sequence[FileCRResult],
    ) -> List[FileCRResult]:
        file_index = _build_file_index(commit_diff.files)
        for fr in file_results:
            for (hunk_id, hunk), issue_indices in _group_issues_by_hunk(fr, file_index).items():
                if not hunk or not _should_refine_hunk(hunk, self.min_hunk_lines):
                    continue
                issues_payload = _build_issues_payload(fr, issue_indices)
                if not issues_payload:
                    continue
                await self._refine_hunk(fr, hunk, issues_payload)
        return list(file_results)

    async def _refine_hunk(
        self,
        fr: FileCRResult,
        hunk: FileHunk,
        issues_payload: List[Dict[str, object]],
    ) -> None:
        try:
            result = await self._chain.ainvoke(
                {
                    "hunk_text": hunk.text,
                    "issues_json": json.dumps(issues_payload, ensure_ascii=False),
                    "min_lines": self.min_snippet_lines,
                    "max_lines": self.max_snippet_lines,
                }
            )
        except (ValidationError, ValueError):
            return
        if not isinstance(result, _ContextRefineResult):
            return
        for item in result.items:
            _apply_context_snippet(fr, item, self.max_snippet_lines)


def _build_file_index(files: Sequence[FileDiff]) -> Dict[str, FileDiff]:
    index: Dict[str, FileDiff] = {}
    for fd in files:
        if fd.a_path:
            index[fd.a_path] = fd
        if fd.b_path:
            index[fd.b_path] = fd
    return index


def _group_issues_by_hunk(
    fr: FileCRResult, file_index: Dict[str, FileDiff]
) -> Dict[Tuple[int, Optional[FileHunk]], List[int]]:
    grouped: Dict[Tuple[int, Optional[FileHunk]], List[int]] = {}
    for idx, issue in enumerate(fr.issues):
        hunk = _find_hunk(issue, fr, file_index)
        if not issue.hunk_id or not hunk:
            continue
        key = (issue.hunk_id, hunk)
        grouped.setdefault(key, []).append(idx)
    return grouped


def _find_hunk(issue: CRIssue, fr: FileCRResult, file_index: Dict[str, FileDiff]) -> Optional[FileHunk]:
    hunk_id = issue.hunk_id
    if not hunk_id:
        return None
    path = issue.file_path or fr.file_path
    if not path:
        return None
    file_diff = file_index.get(path)
    if not file_diff:
        return None
    if 1 <= hunk_id <= len(file_diff.hunks):
        return file_diff.hunks[hunk_id - 1]
    return None


def _should_refine_hunk(hunk: FileHunk, min_hunk_lines: int) -> bool:
    lines = hunk.text.splitlines()
    if not lines:
        return False
    body_lines = lines[1:] if lines[0].startswith("@@") else lines
    return len(body_lines) > min_hunk_lines


def _build_issues_payload(fr: FileCRResult, issue_indices: List[int]) -> List[Dict[str, object]]:
    payload: List[Dict[str, object]] = []
    for idx in issue_indices:
        issue = fr.issues[idx]
        payload.append(
            {
                "issue_index": idx,
                "message": issue.message,
                "suggestion": issue.suggestion or "",
            }
        )
    return payload


def _apply_context_snippet(fr: FileCRResult, item: _ContextRefineItem, max_lines: int) -> None:
    if item.issue_index < 0 or item.issue_index >= len(fr.issues):
        return
    snippet = (item.context_snippet or "").strip()
    if not snippet:
        return
    lines = snippet.splitlines()
    if len(lines) > max_lines:
        snippet = "\n".join(lines[:max_lines]).rstrip()
    fr.issues[item.issue_index].context_snippet = snippet
