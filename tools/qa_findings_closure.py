from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Callable, Iterable

from tools.qa_verdict_bridge import (
    API_ROOT,
    BridgeError,
    EvidenceComment,
    GitHubClient,
    HEX40_RE,
    ReviewThread,
    Verdict,
    _comment_key,
    _effective_time,
    _is_codex,
    _marker,
    _normalized_login,
    _request_head,
)

CLOSED_MARKER = "QA_FINDINGS_CLOSED:"
REVIEWED_MARKER = "QA_REVIEWED_HEAD:"
FIX_MARKER = "QA_FIX_HEAD:"
CLOSED_RE = re.compile(r"QA_FINDINGS_CLOSED:\s*`?([0-9A-Za-z]+)`?", re.IGNORECASE)
REVIEWED_RE = re.compile(r"QA_REVIEWED_HEAD:\s*`?([0-9A-Za-z]+)`?", re.IGNORECASE)
FIX_RE = re.compile(r"QA_FIX_HEAD:\s*`?([0-9A-Za-z]+)`?", re.IGNORECASE)


def _exact_marker(body: str, literal: str, pattern: re.Pattern[str]) -> str | None:
    marker_count = body.lower().count(literal.lower())
    matches = list(pattern.finditer(body))
    if marker_count == 0:
        return None
    if marker_count != 1 or len(matches) != 1:
        raise BridgeError(f"{literal} must appear exactly once")
    token = matches[0].group(1).lower()
    if not HEX40_RE.fullmatch(token):
        raise BridgeError(f"{literal} must bind one exact 40-char SHA")
    return token


def _closure_pair(body: str) -> tuple[str, str] | None:
    has_any = CLOSED_MARKER.lower() in body.lower() or REVIEWED_MARKER.lower() in body.lower()
    if not has_any:
        return None
    closed = _exact_marker(body, CLOSED_MARKER, CLOSED_RE)
    reviewed = _exact_marker(body, REVIEWED_MARKER, REVIEWED_RE)
    if closed is None or reviewed is None:
        raise BridgeError("findings closure requires both closure markers")
    return closed, reviewed


def _fix_head(body: str) -> str | None:
    return _exact_marker(body, FIX_MARKER, FIX_RE)


def evaluate_findings_closure(
    *,
    head_sha: str,
    pr_author: str,
    repository_owner: str,
    comments: Iterable[EvidenceComment],
    threads: Iterable[ReviewThread],
    is_descendant: Callable[[str, str], bool],
) -> Verdict | None:
    head_sha = head_sha.lower()
    if not HEX40_RE.fullmatch(head_sha):
        raise BridgeError("current PR head must be an exact 40-char lowercase SHA")
    if _is_codex(pr_author):
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "PR author is the configured reviewer identity; independence cannot be established",
        )

    owner = _normalized_login(repository_owner)
    ordered_comments = sorted(comments, key=_comment_key)
    owner_closures: list[tuple[EvidenceComment, str, str]] = []
    for item in ordered_comments:
        if _normalized_login(item.author) != owner:
            continue
        try:
            pair = _closure_pair(item.body)
        except BridgeError as exc:
            return Verdict("error", _marker("QA_BLOCKED", head_sha), str(exc))
        if pair is not None:
            owner_closures.append((item, pair[0], pair[1]))

    if not owner_closures:
        return None
    if len(owner_closures) != 1:
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "findings closure evidence is ambiguous; exactly one repository-owner closure comment is required",
        )

    closure, closed_head, reviewed_head = owner_closures[0]
    if closed_head != head_sha:
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            f"findings closure is stale for {closed_head}, not current head {head_sha}",
        )
    if reviewed_head == head_sha:
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "findings closure requires a reviewed ancestor head distinct from current fixed head",
        )

    reviewed_requests = [
        item
        for item in ordered_comments
        if not _is_codex(item.author) and _request_head(item.body) == reviewed_head
    ]
    if len(reviewed_requests) != 1:
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "findings closure requires exactly one recognized substantive QA request for the reviewed head",
        )
    request = reviewed_requests[0]
    request_time = _effective_time(request)

    thread_list = list(threads)
    codex_threads = [
        thread
        for thread in thread_list
        if any(_is_codex(c.author) for c in thread.comments)
    ]
    unresolved_codex = [thread for thread in codex_threads if not thread.is_resolved]
    if unresolved_codex:
        return Verdict(
            "failure",
            _marker("QA_CHANGES_REQUESTED", head_sha),
            f"{len(unresolved_codex)} unresolved Codex review thread(s) remain",
        )

    finding_threads = [
        thread
        for thread in codex_threads
        if any(_is_codex(c.author) and _effective_time(c) >= request_time for c in thread.comments)
    ]
    if not finding_threads:
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "findings closure has no independent Codex finding bound to the reviewed-head request",
        )

    fix_times = []
    for thread in finding_threads:
        codex_items = [c for c in thread.comments if _is_codex(c.author)]
        latest_codex_time = max(_effective_time(c) for c in codex_items)
        valid_fix = None
        for comment in thread.comments:
            if _normalized_login(comment.author) != owner or _effective_time(comment) <= latest_codex_time:
                continue
            try:
                fix_head = _fix_head(comment.body)
            except BridgeError as exc:
                return Verdict("error", _marker("QA_BLOCKED", head_sha), str(exc))
            if fix_head == head_sha:
                valid_fix = comment
        if valid_fix is None:
            return Verdict(
                "error",
                _marker("QA_BLOCKED", head_sha),
                "every Codex finding thread must contain a later repository-owner QA_FIX_HEAD bound to current head",
            )
        fix_times.append(_effective_time(valid_fix))

    closure_time = _effective_time(closure)
    if any(t >= closure_time for t in fix_times):
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "closure marker must be later than every per-finding fix marker",
        )

    newer_top_level = [
        item for item in ordered_comments if _is_codex(item.author) and _effective_time(item) >= closure_time
    ]
    newer_thread = [
        c
        for thread in thread_list
        for c in thread.comments
        if _is_codex(c.author) and _effective_time(c) >= closure_time
    ]
    if newer_top_level or newer_thread:
        return Verdict(
            "failure",
            _marker("QA_CHANGES_REQUESTED", head_sha),
            "newer Codex evidence exists after findings closure",
        )

    try:
        descendant = bool(is_descendant(reviewed_head, head_sha))
    except Exception as exc:
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            f"reviewed-head lineage could not be verified safely: {exc}",
        )
    if not descendant:
        return Verdict(
            "failure",
            _marker("QA_CHANGES_REQUESTED", head_sha),
            f"current head {head_sha} is not a verified descendant of reviewed head {reviewed_head}",
        )

    return Verdict(
        "success",
        _marker("QA_APPROVED", head_sha),
        "independent one-pass Codex findings are fully resolved on a verified descendant current head",
    )


class FindingsClosureClient(GitHubClient):
    def is_descendant(self, reviewed_head: str, current_head: str) -> bool:
        if not HEX40_RE.fullmatch(reviewed_head) or not HEX40_RE.fullmatch(current_head):
            raise BridgeError("lineage comparison requires exact 40-char SHAs")
        data = self._request_json(
            f"{API_ROOT}/repos/{self.repository}/compare/{reviewed_head}...{current_head}"
        )
        if not isinstance(data, dict):
            raise BridgeError("unexpected commit-compare response")
        status = str(data.get("status") or "")
        merge_base = str((data.get("merge_base_commit") or {}).get("sha") or "").lower()
        return status == "ahead" and merge_base == reviewed_head


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize one-pass QA findings closure evidence")
    parser.add_argument("--repository", required=True, help="owner/name")
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--target-url", default=None)
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("QA findings bridge ERROR: GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    client = FindingsClosureClient(token, args.repository)
    try:
        pr = client.get_pr(args.pr)
        head_sha = str(pr["head"]["sha"]).lower()
        pr_author = str(pr["user"]["login"])
        comments = client.issue_comments(args.pr)
        threads = client.review_threads(args.pr)
        verdict = evaluate_findings_closure(
            head_sha=head_sha,
            pr_author=pr_author,
            repository_owner=client.owner,
            comments=comments,
            threads=threads,
            is_descendant=client.is_descendant,
        )
        if verdict is None:
            return 0
        client.set_status(head_sha, verdict, args.target_url)
    except (BridgeError, KeyError, TypeError) as exc:
        print(f"QA findings bridge ERROR: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
