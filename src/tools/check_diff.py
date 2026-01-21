from __future__ import annotations

import argparse
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from tools.git_tools import get_last_commit_diff


def _load_env() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
    else:
        load_dotenv(override=False)


def _resolve_repo_path(repo_arg: str | None) -> Path:
    if repo_arg:
        return Path(repo_arg).expanduser().resolve()
    env_repo = os.getenv("CR_REPO_PATH")
    if not env_repo:
        raise SystemExit("Missing repo path: pass --repo or set CR_REPO_PATH in .env")
    return Path(env_repo).expanduser().resolve()


def _print_file_diff(file_diff) -> None:
    path = file_diff.b_path or file_diff.a_path or "<unknown>"
    flags = []
    if file_diff.is_new_file:
        flags.append("new")
    if file_diff.is_deleted_file:
        flags.append("deleted")
    if file_diff.is_renamed_file:
        flags.append("renamed")
    flag_text = f" [{'|'.join(flags)}]" if flags else ""

    print(f"\n=== {path} ({file_diff.change_type}){flag_text}")
    print(f"Added lines: {file_diff.added_lines}, deleted lines: {file_diff.deleted_lines}")
    print(f"Hunks: {len(file_diff.hunks)}")
    if file_diff.is_binary:
        print("Binary diff omitted.")
        return
    if not (file_diff.patch or "").strip():
        print("No patch content.")
        return
    print(file_diff.patch.rstrip())


def main() -> None:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    parser = argparse.ArgumentParser(description="Print last commit diff for a repo path.")
    parser.add_argument("--repo", help="Repository path (overrides CR_REPO_PATH).")
    args = parser.parse_args()

    _load_env()
    repo_path = _resolve_repo_path(args.repo)
    result = get_last_commit_diff({"repo_path": str(repo_path)})
    commit_diff = result["commit_diff"]

    print(f"Repo: {commit_diff.repo_path}")
    print(f"Commit: {commit_diff.commit_sha}")
    print(f"Parent: {commit_diff.parent_sha}")
    print(f"Message: {commit_diff.message}")
    print(f"Context lines: {commit_diff.context_lines}")
    print(f"Files: {len(commit_diff.files)}")
    if commit_diff.note:
        print(f"Note: {commit_diff.note}")

    for file_diff in commit_diff.files:
        _print_file_diff(file_diff)


if __name__ == "__main__":
    main()
