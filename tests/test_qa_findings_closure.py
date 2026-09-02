from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tools.qa_findings_closure import evaluate_findings_closure
from tools.qa_verdict_bridge import EvidenceComment, ReviewThread

REVIEWED = "a" * 40
CURRENT = "b" * 40
OTHER = "c" * 40
T0 = datetime(2026, 9, 2, 10, 0, tzinfo=UTC)
OWNER = "rassvetpublic-spec"
CODEX = "chatgpt-codex-connector[bot]"


def c(author: str, body: str, minute: int, cid: int) -> EvidenceComment:
    return EvidenceComment(author=author, body=body, created_at=T0 + timedelta(minutes=minute), comment_id=cid)


def request() -> EvidenceComment:
    return c(OWNER, f"@codex review\nQA_REQUEST_HEAD: {REVIEWED}", 0, 10)


def finding_thread(*, resolved: bool = True, fix_head: str = CURRENT, newer: bool = False) -> ReviewThread:
    comments = [
        c(CODEX, "P1: fix this regression", 1, 20),
        c(OWNER, f"Fixed as requested.\nQA_FIX_HEAD: {fix_head}", 3, 30),
    ]
    if newer:
        comments.append(c(CODEX, "P1: new finding after closure", 6, 40))
    return ReviewThread(is_resolved=resolved, is_outdated=False, comments=tuple(comments))


def closure(*, current: str = CURRENT, reviewed: str = REVIEWED, minute: int = 5) -> EvidenceComment:
    return c(
        OWNER,
        f"QA_FINDINGS_CLOSED: {current}\nQA_REVIEWED_HEAD: {reviewed}",
        minute,
        50,
    )


def evaluate(*, comments=None, threads=None, descendant=True):
    return evaluate_findings_closure(
        head_sha=CURRENT,
        pr_author=OWNER,
        repository_owner=OWNER,
        comments=comments if comments is not None else [request(), closure()],
        threads=threads if threads is not None else [finding_thread()],
        is_descendant=lambda _base, _head: descendant,
    )


def test_valid_one_pass_findings_closure_approves_current_descendant_head() -> None:
    verdict = evaluate()
    assert verdict is not None
    assert verdict.state == "success"
    assert verdict.marker == f"QA_APPROVED {CURRENT}"


def test_no_closure_marker_leaves_clean_review_bridge_authoritative() -> None:
    verdict = evaluate_findings_closure(
        head_sha=CURRENT,
        pr_author=OWNER,
        repository_owner=OWNER,
        comments=[request()],
        threads=[finding_thread()],
        is_descendant=lambda _base, _head: True,
    )
    assert verdict is None


def test_stale_closure_fails_closed() -> None:
    verdict = evaluate(comments=[request(), closure(current=OTHER)])
    assert verdict is not None
    assert verdict.state == "error"
    assert verdict.marker == f"QA_BLOCKED {CURRENT}"


def test_unresolved_codex_finding_remains_blocking() -> None:
    verdict = evaluate(threads=[finding_thread(resolved=False)])
    assert verdict is not None
    assert verdict.state == "failure"
    assert verdict.marker == f"QA_CHANGES_REQUESTED {CURRENT}"


def test_missing_exact_current_fix_marker_fails_closed() -> None:
    verdict = evaluate(threads=[finding_thread(fix_head=OTHER)])
    assert verdict is not None
    assert verdict.state == "error"
    assert verdict.marker == f"QA_BLOCKED {CURRENT}"


def test_non_descendant_current_head_is_rejected() -> None:
    verdict = evaluate(descendant=False)
    assert verdict is not None
    assert verdict.state == "failure"
    assert verdict.marker == f"QA_CHANGES_REQUESTED {CURRENT}"


def test_newer_codex_thread_evidence_after_closure_is_blocking() -> None:
    verdict = evaluate(threads=[finding_thread(newer=True)])
    assert verdict is not None
    assert verdict.state == "failure"


def test_duplicate_reviewed_head_requests_are_ambiguous() -> None:
    second = c(OWNER, f"@codex review\nexact current head {REVIEWED}", 0, 11)
    verdict = evaluate(comments=[request(), second, closure()])
    assert verdict is not None
    assert verdict.state == "error"


def test_malformed_closure_marker_fails_closed() -> None:
    bad = c(OWNER, f"QA_FINDINGS_CLOSED: {CURRENT[:10]}\nQA_REVIEWED_HEAD: {REVIEWED}", 5, 50)
    verdict = evaluate(comments=[request(), bad])
    assert verdict is not None
    assert verdict.state == "error"


def test_closure_must_follow_per_finding_fix_evidence() -> None:
    verdict = evaluate(comments=[request(), closure(minute=2)])
    assert verdict is not None
    assert verdict.state == "error"
