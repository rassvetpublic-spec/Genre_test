from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tools.qa_verdict_bridge import EvidenceComment, evaluate_evidence

HEAD = "a" * 40
OTHER_HEAD = "b" * 40
T0 = datetime(2026, 9, 2, 7, 0, tzinfo=UTC)


def _comment(author: str, body: str, *, minutes: int, comment_id: int) -> EvidenceComment:
    return EvidenceComment(
        author=author,
        body=body,
        created_at=T0 + timedelta(minutes=minutes),
        comment_id=comment_id,
    )


def _natural_request(body: str) -> EvidenceComment:
    return _comment("rassvetpublic-spec", body, minutes=0, comment_id=10)


def _clean() -> EvidenceComment:
    return _comment(
        "chatgpt-codex-connector[bot]",
        "Codex Review: Didn't find any major issues. :tada:\n\n"
        f"**Reviewed commit:** `{HEAD[:10]}`",
        minutes=1,
        comment_id=20,
    )


def _evaluate(request: EvidenceComment):
    return evaluate_evidence(
        head_sha=HEAD,
        pr_author="rassvetpublic-spec",
        comments=[request, _clean()],
        threads=[],
        resolve_prefix=lambda _prefix: HEAD,
    )


def test_natural_exact_current_head_request_authorizes_later_clean_review() -> None:
    request = _natural_request(
        "@codex review\n\n"
        f"Please re-evaluate the exact current head `{HEAD}` after the finding fix. "
        "Limit review to verification only."
    )
    verdict = _evaluate(request)
    assert verdict.state == "success"
    assert verdict.marker == f"QA_APPROVED {HEAD}"


def test_natural_exact_head_request_without_current_word_is_supported() -> None:
    request = _natural_request(
        f"@codex review\nVerify exact head: `{HEAD}` and do not expand scope."
    )
    assert _evaluate(request).state == "success"


def test_abbreviated_natural_exact_head_remains_blocked() -> None:
    request = _natural_request(
        f"@codex review\nPlease verify the exact current head `{HEAD[:10]}`."
    )
    verdict = _evaluate(request)
    assert verdict.state == "pending"
    assert verdict.marker == f"QA_BLOCKED {HEAD}"


def test_multiple_natural_exact_head_candidates_are_ambiguous_and_blocked() -> None:
    request = _natural_request(
        "@codex review\n"
        f"Compare exact current head `{HEAD}` with exact head `{OTHER_HEAD}`."
    )
    verdict = _evaluate(request)
    assert verdict.state == "pending"
    assert verdict.marker == f"QA_BLOCKED {HEAD}"


def test_generic_full_commit_mention_is_not_an_exact_head_request() -> None:
    request = _natural_request(
        f"@codex review\nPlease review commit `{HEAD}` after the fix."
    )
    verdict = _evaluate(request)
    assert verdict.state == "pending"
    assert verdict.marker == f"QA_BLOCKED {HEAD}"


def test_trailing_alphanumeric_contamination_is_blocked() -> None:
    request = _natural_request(
        f"@codex review\nPlease verify exact current head `{HEAD}b`."
    )
    verdict = _evaluate(request)
    assert verdict.state == "pending"
    assert verdict.marker == f"QA_BLOCKED {HEAD}"


def test_valid_full_sha_plus_abbreviated_candidate_is_blocked() -> None:
    request = _natural_request(
        "@codex review\n"
        f"Verify exact current head `{HEAD}`; also check exact head `{HEAD[:10]}`."
    )
    verdict = _evaluate(request)
    assert verdict.state == "pending"
    assert verdict.marker == f"QA_BLOCKED {HEAD}"


def test_repeated_same_full_sha_is_deduplicated() -> None:
    request = _natural_request(
        "@codex review\n"
        f"Verify exact current head `{HEAD}`; confirm exact head `{HEAD}`."
    )
    verdict = _evaluate(request)
    assert verdict.state == "success"
    assert verdict.marker == f"QA_APPROVED {HEAD}"


def test_canonical_binding_plus_malformed_natural_binding_is_blocked() -> None:
    request = _natural_request(
        "@codex review\n"
        f"QA_REQUEST_HEAD: {HEAD}\n"
        f"Please also verify exact current head `{HEAD[:10]}`."
    )
    verdict = _evaluate(request)
    assert verdict.state == "pending"
    assert verdict.marker == f"QA_BLOCKED {HEAD}"
