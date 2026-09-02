from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable, Iterable

API_ROOT = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
STATUS_CONTEXT = "qa-verdict-bridge"
CANONICAL_MARKER_RE = re.compile(r"QA_REQUEST_HEAD:", re.IGNORECASE)
REQUEST_RE = re.compile(
    r"QA_REQUEST_HEAD:\s*"
    r"(?:`(?P<ticked>[0-9A-Za-z]+)`(?![0-9A-Za-z])|"
    r"(?P<plain>[0-9A-Za-z]+)(?![0-9A-Za-z`]))",
    re.IGNORECASE,
)
NATURAL_PHRASE_RE = re.compile(r"\bexact(?:\s+current)?\s+head\b", re.IGNORECASE)
NATURAL_REQUEST_RE = re.compile(
    r"\bexact(?:\s+current)?\s+head\b\s*(?:(?:is|=|:)\s*)?"
    r"(?:`(?P<ticked>[0-9A-Za-z]+)`(?![0-9A-Za-z])|"
    r"(?P<plain>[0-9A-Za-z]+)(?![0-9A-Za-z`]))",
    re.IGNORECASE,
)
REVIEWED_RE = re.compile(r"\*\*Reviewed commit:\*\*\s*`([0-9a-f]{7,40})`", re.IGNORECASE)
CLEAN_PHRASE = "Codex Review: Didn't find any major issues."
CODEX_LOGINS = {"chatgpt-codex-connector", "chatgpt-codex-connector[bot]"}
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


class BridgeError(RuntimeError):
    """Raised when live GitHub evidence cannot be evaluated safely."""


@dataclass(frozen=True)
class Verdict:
    state: str
    marker: str
    reason: str


@dataclass(frozen=True)
class EvidenceComment:
    author: str
    body: str
    created_at: datetime
    updated_at: datetime | None = None
    comment_id: int = 0


@dataclass(frozen=True)
class ReviewThread:
    is_resolved: bool
    is_outdated: bool
    comments: tuple[EvidenceComment, ...]


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BridgeError(f"invalid GitHub timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _normalized_login(login: str) -> str:
    return login.strip().lower()


def _is_codex(login: str) -> bool:
    return _normalized_login(login) in CODEX_LOGINS


def _bound_candidates(
    body: str,
    *,
    marker_re: re.Pattern[str],
    request_re: re.Pattern[str],
) -> set[str] | None:
    markers = list(marker_re.finditer(body))
    matches = list(request_re.finditer(body))
    if len(matches) != len(markers):
        return None

    candidates: set[str] = set()
    for match in matches:
        token = (match.group("ticked") or match.group("plain") or "").lower()
        if not HEX40_RE.fullmatch(token):
            return None
        candidates.add(token)
    return candidates


def _request_head(body: str) -> str | None:
    if "@codex" not in body.lower() or "review" not in body.lower():
        return None

    canonical = _bound_candidates(
        body,
        marker_re=CANONICAL_MARKER_RE,
        request_re=REQUEST_RE,
    )
    natural = _bound_candidates(
        body,
        marker_re=NATURAL_PHRASE_RE,
        request_re=NATURAL_REQUEST_RE,
    )
    if canonical is None or natural is None:
        return None

    candidates = canonical | natural
    return next(iter(candidates)) if len(candidates) == 1 else None


def _reviewed_prefix(body: str) -> str | None:
    match = REVIEWED_RE.search(body)
    return match.group(1).lower() if match else None


def _clean_signal(body: str) -> bool:
    return CLEAN_PHRASE.lower() in body.lower()


def _marker(kind: str, head_sha: str) -> str:
    return f"{kind} {head_sha}"


def _effective_time(item: EvidenceComment) -> datetime:
    return item.updated_at or item.created_at


def _comment_key(item: EvidenceComment) -> tuple[datetime, int]:
    return _effective_time(item), item.comment_id


def evaluate_evidence(
    *,
    head_sha: str,
    pr_author: str,
    comments: Iterable[EvidenceComment],
    threads: Iterable[ReviewThread],
    resolve_prefix: Callable[[str], str],
) -> Verdict:
    head_sha = head_sha.lower()
    if not HEX40_RE.fullmatch(head_sha):
        raise BridgeError("current PR head must be an exact 40-char lowercase SHA")

    ordered_comments = sorted(comments, key=_comment_key)
    exact_requests = [
        item
        for item in ordered_comments
        if not _is_codex(item.author) and _request_head(item.body) == head_sha
    ]
    if not exact_requests:
        return Verdict(
            "pending",
            _marker("QA_BLOCKED", head_sha),
            "no recognized exact-head QA review request is present yet",
        )

    request = exact_requests[-1]
    request_key = _comment_key(request)
    codex_after_request = [
        item
        for item in ordered_comments
        if _is_codex(item.author) and _comment_key(item) > request_key
    ]
    if not codex_after_request:
        return Verdict(
            "pending",
            _marker("QA_BLOCKED", head_sha),
            "exact-head review requested; independent Codex result not present yet",
        )

    if _is_codex(pr_author):
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "PR author is the configured reviewer identity; independence cannot be established",
        )

    thread_list = list(threads)
    unresolved = [thread for thread in thread_list if not thread.is_resolved]
    if unresolved:
        return Verdict(
            "failure",
            _marker("QA_CHANGES_REQUESTED", head_sha),
            f"{len(unresolved)} unresolved pull-request review thread(s)",
        )

    clean_candidates: list[tuple[EvidenceComment, str]] = []
    for item in codex_after_request:
        if not _clean_signal(item.body):
            continue
        prefix = _reviewed_prefix(item.body)
        if prefix is None:
            continue
        clean_candidates.append((item, prefix))

    if not clean_candidates:
        request_time = _effective_time(request)
        has_codex_findings = any(
            any(
                _is_codex(comment.author) and _effective_time(comment) >= request_time
                for comment in thread.comments
            )
            for thread in thread_list
        )
        if has_codex_findings:
            return Verdict(
                "failure",
                _marker("QA_CHANGES_REQUESTED", head_sha),
                "Codex findings exist after the exact-head request and no later clean signal is present",
            )
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "Codex responded but no recognized exact-head clean-review signal is present",
        )

    clean_comment, reviewed_prefix = clean_candidates[-1]
    clean_key = _comment_key(clean_comment)

    later_top_level = [
        item
        for item in ordered_comments
        if _is_codex(item.author) and _comment_key(item) > clean_key
    ]
    if later_top_level:
        return Verdict(
            "failure",
            _marker("QA_CHANGES_REQUESTED", head_sha),
            "newer top-level Codex evidence supersedes the latest clean-review signal",
        )

    clean_time = _effective_time(clean_comment)
    later_thread_evidence = any(
        _is_codex(comment.author) and _effective_time(comment) >= clean_time
        for thread in thread_list
        for comment in thread.comments
    )
    if later_thread_evidence:
        return Verdict(
            "failure",
            _marker("QA_CHANGES_REQUESTED", head_sha),
            "Codex review-thread evidence is newer than or timestamp-ambiguous with the latest clean-review signal",
        )

    try:
        resolved_sha = resolve_prefix(reviewed_prefix).lower()
    except Exception as exc:  # fail closed on API/resolution ambiguity
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            f"reviewed commit prefix could not be resolved safely: {exc}",
        )

    if not HEX40_RE.fullmatch(resolved_sha):
        return Verdict(
            "error",
            _marker("QA_BLOCKED", head_sha),
            "reviewed commit resolver did not return an exact 40-char SHA",
        )
    if resolved_sha != head_sha:
        return Verdict(
            "failure",
            _marker("QA_CHANGES_REQUESTED", head_sha),
            f"Codex reviewed {resolved_sha}, not current head {head_sha}",
        )

    return Verdict(
        "success",
        _marker("QA_APPROVED", head_sha),
        "independent exact-head Codex clean review normalized by repository contract",
    )


class GitHubClient:
    def __init__(self, token: str, repository: str) -> None:
        if "/" not in repository:
            raise BridgeError("repository must be owner/name")
        self.token = token
        self.repository = repository
        self.owner, self.name = repository.split("/", 1)

    def _request_json(
        self,
        url: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "genre-test-qa-verdict-bridge",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise BridgeError(f"GitHub API HTTP {exc.code}: {detail}") from exc
        except (OSError, http.client.HTTPException, json.JSONDecodeError) as exc:
            raise BridgeError(f"GitHub API request failed: {exc}") from exc

    def get_pr(self, pr_number: int) -> dict[str, Any]:
        data = self._request_json(f"{API_ROOT}/repos/{self.repository}/pulls/{pr_number}")
        if not isinstance(data, dict):
            raise BridgeError("unexpected pull-request response")
        return data

    def issue_comments(self, pr_number: int) -> list[EvidenceComment]:
        output: list[EvidenceComment] = []
        page = 1
        while True:
            data = self._request_json(
                f"{API_ROOT}/repos/{self.repository}/issues/{pr_number}/comments?per_page=100&page={page}"
            )
            if not isinstance(data, list):
                raise BridgeError("unexpected issue-comments response")
            for item in data:
                try:
                    created_at = _parse_time(str(item["created_at"]))
                    updated_at = _parse_time(str(item.get("updated_at") or item["created_at"]))
                    output.append(
                        EvidenceComment(
                            author=str(item["user"]["login"]),
                            body=str(item.get("body") or ""),
                            created_at=created_at,
                            updated_at=updated_at,
                            comment_id=int(item["id"]),
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    raise BridgeError("malformed issue-comment evidence") from exc
            if len(data) < 100:
                break
            page += 1
        return output

    def review_threads(self, pr_number: int) -> list[ReviewThread]:
        query = """
        query($owner:String!, $name:String!, $number:Int!, $cursor:String) {
          repository(owner:$owner, name:$name) {
            pullRequest(number:$number) {
              reviewThreads(first:100, after:$cursor) {
                nodes {
                  isResolved
                  isOutdated
                  comments(first:100) {
                    nodes {
                      databaseId
                      body
                      createdAt
                      updatedAt
                      author { login }
                    }
                    pageInfo { hasNextPage }
                  }
                }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
        """
        cursor: str | None = None
        threads: list[ReviewThread] = []
        while True:
            payload = {
                "query": query,
                "variables": {
                    "owner": self.owner,
                    "name": self.name,
                    "number": pr_number,
                    "cursor": cursor,
                },
            }
            data = self._request_json(GRAPHQL_URL, method="POST", payload=payload)
            if not isinstance(data, dict) or data.get("errors"):
                detail = data.get("errors") if isinstance(data, dict) else data
                raise BridgeError(f"GraphQL review-thread query failed: {detail}")
            try:
                container = data["data"]["repository"]["pullRequest"]["reviewThreads"]
                nodes = container["nodes"]
                page_info = container["pageInfo"]
            except (KeyError, TypeError) as exc:
                raise BridgeError("malformed GraphQL review-thread response") from exc
            for node in nodes:
                try:
                    comment_container = node["comments"]
                    comment_page_info = comment_container["pageInfo"]
                    comment_nodes = comment_container["nodes"]
                except (KeyError, TypeError) as exc:
                    raise BridgeError("malformed GraphQL review-thread comment response") from exc
                if comment_page_info.get("hasNextPage"):
                    raise BridgeError(
                        "review-thread comment evidence exceeds one GraphQL page; "
                        "bridge refuses incomplete evidence"
                    )
                comments: list[EvidenceComment] = []
                for item in comment_nodes:
                    try:
                        author = item.get("author") or {}
                        created_at = _parse_time(str(item["createdAt"]))
                        updated_at = _parse_time(str(item.get("updatedAt") or item["createdAt"]))
                        comments.append(
                            EvidenceComment(
                                author=str(author.get("login") or ""),
                                body=str(item.get("body") or ""),
                                created_at=created_at,
                                updated_at=updated_at,
                                comment_id=int(item.get("databaseId") or 0),
                            )
                        )
                    except (KeyError, TypeError, ValueError) as exc:
                        raise BridgeError("malformed review-thread comment evidence") from exc
                threads.append(
                    ReviewThread(
                        is_resolved=bool(node["isResolved"]),
                        is_outdated=bool(node["isOutdated"]),
                        comments=tuple(comments),
                    )
                )
            try:
                has_next_page = bool(page_info["hasNextPage"])
                end_cursor = page_info["endCursor"]
            except (KeyError, TypeError) as exc:
                raise BridgeError("malformed GraphQL review-thread pagination") from exc
            if not has_next_page:
                break
            if not end_cursor:
                raise BridgeError("GraphQL review-thread pagination has no end cursor")
            cursor = str(end_cursor)
        return threads

    def resolve_commit(self, prefix: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{7,40}", prefix.lower()):
            raise BridgeError("invalid reviewed commit prefix")
        data = self._request_json(f"{API_ROOT}/repos/{self.repository}/commits/{prefix}")
        try:
            sha = str(data["sha"]).lower()
        except (KeyError, TypeError) as exc:
            raise BridgeError("malformed commit-resolution response") from exc
        if not HEX40_RE.fullmatch(sha):
            raise BridgeError("commit resolution returned a non-exact SHA")
        return sha

    def set_status(self, head_sha: str, verdict: Verdict, target_url: str | None) -> None:
        payload: dict[str, Any] = {
            "state": verdict.state,
            "context": STATUS_CONTEXT,
            "description": verdict.marker[:140],
        }
        if target_url:
            payload["target_url"] = target_url
        self._request_json(
            f"{API_ROOT}/repos/{self.repository}/statuses/{head_sha}",
            method="POST",
            payload=payload,
        )


def _summary(verdict: Verdict, head_sha: str, pr_number: int) -> str:
    return (
        "## QA verdict bridge\n\n"
        f"- PR: `#{pr_number}`\n"
        f"- exact head: `{head_sha}`\n"
        f"- status context: `{STATUS_CONTEXT}`\n"
        f"- state: `{verdict.state}`\n"
        f"- normalized marker: `{verdict.marker}`\n"
        f"- reason: {verdict.reason}\n"
    )


def _blocked_error(head_sha: str, reason: str) -> Verdict:
    return Verdict("error", _marker("QA_BLOCKED", head_sha), reason)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize exact-head GitHub Codex QA evidence")
    parser.add_argument("--repository", required=True, help="owner/name")
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--mode", choices=("pending", "evaluate"), default="evaluate")
    parser.add_argument("--target-url", default=None)
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("QA bridge ERROR: GITHUB_TOKEN is required", file=sys.stderr)
        return 2

    client = GitHubClient(token, args.repository)
    head_sha: str | None = None
    try:
        pr = client.get_pr(args.pr)
        head_sha = str(pr["head"]["sha"]).lower()
        pr_author = str(pr["user"]["login"])
        if not HEX40_RE.fullmatch(head_sha):
            raise BridgeError("GitHub PR returned invalid exact head SHA")

        if args.mode == "pending":
            verdict = Verdict(
                "pending",
                _marker("QA_BLOCKED", head_sha),
                "new exact head requires a fresh bound independent QA review",
            )
        else:
            try:
                comments = client.issue_comments(args.pr)
                threads = client.review_threads(args.pr)
                verdict = evaluate_evidence(
                    head_sha=head_sha,
                    pr_author=pr_author,
                    comments=comments,
                    threads=threads,
                    resolve_prefix=client.resolve_commit,
                )
            except (BridgeError, KeyError, TypeError) as exc:
                verdict = _blocked_error(
                    head_sha,
                    f"live QA evidence could not be evaluated completely: {exc}",
                )
                client.set_status(head_sha, verdict, args.target_url)
                print(f"QA bridge ERROR: {exc}", file=sys.stderr)
                summary = _summary(verdict, head_sha, args.pr)
                print(summary)
                summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
                if summary_path:
                    with open(summary_path, "a", encoding="utf-8", newline="\n") as handle:
                        handle.write(summary)
                return 2
        client.set_status(head_sha, verdict, args.target_url)
    except (BridgeError, KeyError, TypeError) as exc:
        print(f"QA bridge ERROR: {exc}", file=sys.stderr)
        if head_sha is not None and HEX40_RE.fullmatch(head_sha):
            try:
                client.set_status(
                    head_sha,
                    _blocked_error(head_sha, f"bridge execution failed closed: {exc}"),
                    args.target_url,
                )
            except BridgeError as status_exc:
                print(f"QA bridge ERROR status write failed: {status_exc}", file=sys.stderr)
        return 2

    summary = _summary(verdict, head_sha, args.pr)
    print(summary)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())