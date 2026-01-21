from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field, field_validator


# ---- Git data structures ----

@dataclass(frozen=True)
class FileContentRef:
    """Reference to file content inside the git object store."""

    repo_path: str
    commit_sha: str
    path: str
    blob_sha: Optional[str] = None
    size: Optional[int] = None
    mode: Optional[int] = None


@dataclass(frozen=True)
class FileHunk:
    header: str
    text: str
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int


@dataclass(frozen=True)
class FileDiff:
    change_type: str
    a_path: Optional[str]
    b_path: Optional[str]
    is_new_file: bool
    is_deleted_file: bool
    is_renamed_file: bool
    rename_from: Optional[str]
    rename_to: Optional[str]
    a_blob_sha: Optional[str]
    b_blob_sha: Optional[str]
    a_mode: Optional[int]
    b_mode: Optional[int]
    is_binary: bool
    patch: str
    added_lines: int
    deleted_lines: int
    before_ref: Optional[FileContentRef]
    after_ref: Optional[FileContentRef]
    hunks: List[FileHunk] = field(default_factory=list)


@dataclass(frozen=True)
class CommitDiff:
    repo_path: str
    commit_sha: str
    parent_sha: Optional[str]
    author_name: str
    author_email: str
    committed_datetime_iso: str
    message: str
    context_lines: int
    is_initial_commit: bool
    note: Optional[str] = None
    files: List[FileDiff] = field(default_factory=list)


# ---- Review result schema ----

Severity = Literal["info", "minor", "major", "critical"]
Category = Literal[
    "bug",
    "security",
    "performance",
    "concurrency",
    "reliability",
    "api",
    "style",
    "test",
    "documentation",
    "build",
    "other",
]


def _normalize_severity_value(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("warning", "warn"):
            return "minor"
    return value


class CRIssue(BaseModel):
    severity: Severity
    category: Category
    message: str = Field(..., min_length=3)
    file_path: Optional[str] = None
    hunk_id: Optional[int] = Field(default=None, ge=1)
    suggestion: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    rule_ids: List[str] = Field(default_factory=list)

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, value):
        return _normalize_severity_value(value)


class FileCRResult(BaseModel):
    file_path: str
    change_type: str
    summary: str = Field(..., min_length=3)
    overall_severity: Severity
    approved: bool
    issues: List[CRIssue] = Field(default_factory=list)
    rule_ids: List[str] = Field(default_factory=list)
    needs_human_review: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)


# ---- Tagging + tag-based review schema ----

Tag = Literal["STYLE", "ERROR", "API", "CONC", "PERF", "SEC", "TEST", "CONFIG"]


class FileTaggingLLMResult(BaseModel):
    """LLM output for tagging (file_path is filled by the caller)."""

    tags: List[Tag] = Field(default_factory=list)
    reasoning: Optional[str] = None


class FileTaggingResult(BaseModel):
    """LLM-generated tags for a single file diff."""

    file_path: str
    tags: List[Tag] = Field(default_factory=list)
    reasoning: Optional[str] = None


class TagCRLLMResult(BaseModel):
    """LLM output for a tag-specific review (file_path/tag are filled by the caller)."""

    summary: str = Field(..., min_length=3)
    overall_severity: Severity
    approved: bool
    issues: List[CRIssue] = Field(default_factory=list)
    needs_human_review: bool = False
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("overall_severity", mode="before")
    @classmethod
    def _normalize_overall_severity(cls, value):
        return _normalize_severity_value(value)


class TagCRLLMResultFallback(BaseModel):
    """Lenient parsing for tag-specific review output; fills defaults later."""

    summary: Optional[str] = None
    overall_severity: Optional[str] = None
    approved: Optional[bool] = None
    issues: List[CRIssue] = Field(default_factory=list)
    needs_human_review: Optional[bool] = False
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("overall_severity", mode="before")
    @classmethod
    def _normalize_overall_severity(cls, value):
        return _normalize_severity_value(value)

    def to_strict(self) -> TagCRLLMResult:
        summary = (self.summary or "").strip() or "未发现需要专项审查的问题。"
        severity = (
            self.overall_severity
            if self.overall_severity in ("info", "minor", "major", "critical")
            else "info"
        )
        approved = self.approved if isinstance(self.approved, bool) else True
        needs_human_review = bool(self.needs_human_review)
        return TagCRLLMResult(
            summary=summary,
            overall_severity=severity,  # type: ignore[arg-type]
            approved=approved,
            issues=self.issues or [],
            needs_human_review=needs_human_review,
            meta=self.meta or {},
        )


class TagCRResult(BaseModel):
    """Review result for one (file, tag) dimension."""

    file_path: str
    tag: Tag
    summary: str = Field(..., min_length=3)
    overall_severity: Severity
    approved: bool
    issues: List[CRIssue] = Field(default_factory=list)
    needs_human_review: bool = False
    rule_ids: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)


class AgentState(TypedDict):
    repo_path: str
    commit_diff: CommitDiff
    file_cr_result: List[FileCRResult]
    report_markdown: str
