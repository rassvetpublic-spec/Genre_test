from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from http.client import IncompleteRead, RemoteDisconnected
from pathlib import Path
from unittest.mock import patch

from tools.qa_verdict_bridge import (
    BridgeError,
    EvidenceComment,
    GitHubClient,
    ReviewThread,
    evaluate_evidence,
)
from tools.qa_verdict_bridge import main as bridge_main

HEAD = "a" * 40
OTHER_HEAD = "b" * 40
T0 = datetime(2026, 9, 1, 0, 0, tzinfo=UTC)


def evidence(
    author: str,
    body: str,
    *,
    minutes: int = 0,
    updated_minutes: int | None = None,
    comment_id: int = 0,
) -> EvidenceComment:
    return EvidenceComment(
        author=author,
        body=body,
        created_at=T0 + timedelta(minutes=minutes),
        updated_at=(
            T0 + timedelta(minutes=updated_minutes)
            if updated_minutes is not None
            else None
        ),
        comment_id=comment_id,
    )


def request(
    head: str = HEAD,
    *,
    minutes: int = 0,
    updated_minutes: int | None = None,
) -> EvidenceComment:
    return evidence(
        "rassvetpublic-spec",
        f"@codex review\nQA_REQUEST_HEAD: {head}",
        minutes=minutes,
        updated_minutes=updated_minutes,
        comment_id=10 + minutes,
    )


def clean(
    prefix: str = HEAD[:10],
    *,
    minutes: int = 1,
    updated_minutes: int | None = None,
) -> EvidenceComment:
    return evidence(
        "chatgpt-codex-connector[bot]",
        "Codex Review: Didn't find any major issues. Nice work!\n\n"
        f"**Reviewed commit:** `{prefix}`",
        minutes=minutes,
        updated_minutes=updated_minutes,
        comment_id=20 + minutes,
    )


class QaVerdictBridgeTests(unittest.TestCase):
    def evaluate(
        self,
        *,
        comments: list[EvidenceComment],
        threads: list[ReviewThread] | None = None,
        pr_author: str = "rassvetpublic-spec",
        resolved_sha: str = HEAD,
    ):
        return evaluate_evidence(
            head_sha=HEAD,
            pr_author=pr_author,
            comments=comments,
            threads=threads or [],
            resolve_prefix=lambda _prefix: resolved_sha,
        )

    def test_missing_exact_head_request_is_pending(self) -> None:
        verdict = self.evaluate(comments=[])
        self.assertEqual(verdict.state, "pending")
        self.assertEqual(verdict.marker, f"QA_BLOCKED {HEAD}")

    def test_stale_request_cannot_authorize_current_head(self) -> None:
        verdict = self.evaluate(comments=[request(OTHER_HEAD), clean()])
        self.assertEqual(verdict.state, "pending")
        self.assertIn("exact-head", verdict.reason)

    def test_request_without_codex_result_remains_pending(self) -> None:
        verdict = self.evaluate(comments=[request()])
        self.assertEqual(verdict.state, "pending")
        self.assertIn("not present yet", verdict.reason)

    def test_wrong_reviewer_does_not_count_as_codex(self) -> None:
        fake_clean = evidence(
            "some-other-bot",
            "Codex Review: Didn't find any major issues.\n"
            f"**Reviewed commit:** `{HEAD[:10]}`",
            minutes=1,
        )
        verdict = self.evaluate(comments=[request(), fake_clean])
        self.assertEqual(verdict.state, "pending")

    def test_valid_exact_head_clean_review_normalizes_to_success(self) -> None:
        verdict = self.evaluate(comments=[request(), clean()])
        self.assertEqual(verdict.state, "success")
        self.assertEqual(verdict.marker, f"QA_APPROVED {HEAD}")

    def test_same_timestamp_uses_issue_comment_id_for_strict_ordering(self) -> None:
        same_time_clean = clean(minutes=0)
        verdict = self.evaluate(comments=[request(minutes=0), same_time_clean])
        self.assertEqual(verdict.state, "success")

    def test_same_timestamp_older_comment_id_cannot_satisfy_request(self) -> None:
        older_clean = evidence(
            "chatgpt-codex-connector[bot]",
            "Codex Review: Didn't find any major issues.\n"
            f"**Reviewed commit:** `{HEAD[:10]}`",
            comment_id=5,
        )
        verdict = self.evaluate(comments=[older_clean, request()])
        self.assertEqual(verdict.state, "pending")

    def test_edited_request_uses_mutation_time_not_creation_time(self) -> None:
        edited_request = request(minutes=0, updated_minutes=3)
        earlier_clean = clean(minutes=2)
        verdict = self.evaluate(comments=[edited_request, earlier_clean])
        self.assertEqual(verdict.state, "pending")
        self.assertIn("not present yet", verdict.reason)

    def test_clean_after_edited_request_can_approve(self) -> None:
        edited_request = request(minutes=0, updated_minutes=3)
        later_clean = clean(minutes=4)
        verdict = self.evaluate(comments=[edited_request, later_clean])
        self.assertEqual(verdict.state, "success")

    def test_codex_cannot_review_its_own_pull_request(self) -> None:
        verdict = self.evaluate(
            comments=[request(), clean()],
            pr_author="chatgpt-codex-connector[bot]",
        )
        self.assertEqual(verdict.state, "error")
        self.assertEqual(verdict.marker, f"QA_BLOCKED {HEAD}")

    def test_reviewed_prefix_resolving_to_other_commit_fails(self) -> None:
        verdict = self.evaluate(
            comments=[request(), clean()],
            resolved_sha=OTHER_HEAD,
        )
        self.assertEqual(verdict.state, "failure")
        self.assertEqual(verdict.marker, f"QA_CHANGES_REQUESTED {HEAD}")

    def test_unresolved_review_thread_blocks_clean_signal(self) -> None:
        thread = ReviewThread(
            is_resolved=False,
            is_outdated=False,
            comments=(
                evidence(
                    "chatgpt-codex-connector[bot]",
                    "Please fix this finding.",
                    minutes=1,
                ),
            ),
        )
        verdict = self.evaluate(comments=[request(), clean(minutes=2)], threads=[thread])
        self.assertEqual(verdict.state, "failure")
        self.assertIn("unresolved", verdict.reason)

    def test_codex_finding_without_clean_signal_requests_changes(self) -> None:
        thread = ReviewThread(
            is_resolved=True,
            is_outdated=False,
            comments=(
                evidence(
                    "chatgpt-codex-connector[bot]",
                    "Actionable finding",
                    minutes=1,
                ),
            ),
        )
        codex_review = evidence(
            "chatgpt-codex-connector[bot]",
            "Here are some automated review suggestions for this pull request.",
            minutes=1,
        )
        verdict = self.evaluate(comments=[request(), codex_review], threads=[thread])
        self.assertEqual(verdict.state, "failure")

    def test_later_codex_thread_evidence_supersedes_earlier_clean_signal(self) -> None:
        thread = ReviewThread(
            is_resolved=True,
            is_outdated=False,
            comments=(
                evidence(
                    "chatgpt-codex-connector[bot]",
                    "New finding after clean review",
                    minutes=3,
                ),
            ),
        )
        verdict = self.evaluate(comments=[request(), clean(minutes=2)], threads=[thread])
        self.assertEqual(verdict.state, "failure")
        self.assertIn("review-thread", verdict.reason)

    def test_edited_thread_evidence_uses_mutation_time(self) -> None:
        thread = ReviewThread(
            is_resolved=True,
            is_outdated=False,
            comments=(
                evidence(
                    "chatgpt-codex-connector[bot]",
                    "Finding edited after clean review",
                    minutes=1,
                    updated_minutes=3,
                ),
            ),
        )
        verdict = self.evaluate(comments=[request(), clean(minutes=2)], threads=[thread])
        self.assertEqual(verdict.state, "failure")

    def test_timestamp_ambiguous_thread_evidence_fails_closed(self) -> None:
        thread = ReviewThread(
            is_resolved=True,
            is_outdated=False,
            comments=(
                evidence(
                    "chatgpt-codex-connector[bot]",
                    "Same-timestamp thread evidence",
                    minutes=2,
                ),
            ),
        )
        verdict = self.evaluate(comments=[request(), clean(minutes=2)], threads=[thread])
        self.assertEqual(verdict.state, "failure")
        self.assertIn("timestamp-ambiguous", verdict.reason)

    def test_later_top_level_codex_signal_supersedes_clean_signal(self) -> None:
        newer = evidence(
            "chatgpt-codex-connector[bot]",
            "I found a later issue that needs attention.",
            minutes=3,
            comment_id=30,
        )
        verdict = self.evaluate(comments=[request(), clean(minutes=2), newer])
        self.assertEqual(verdict.state, "failure")
        self.assertIn("top-level", verdict.reason)

    def test_edited_top_level_codex_signal_supersedes_clean_signal(self) -> None:
        newer = evidence(
            "chatgpt-codex-connector[bot]",
            "Finding edited after clean review.",
            minutes=1,
            updated_minutes=3,
            comment_id=30,
        )
        verdict = self.evaluate(comments=[request(), clean(minutes=2), newer])
        self.assertEqual(verdict.state, "failure")

    def test_later_clean_signal_can_supersede_earlier_top_level_finding(self) -> None:
        finding = evidence(
            "chatgpt-codex-connector[bot]",
            "Earlier finding",
            minutes=1,
            comment_id=21,
        )
        verdict = self.evaluate(
            comments=[request(), finding, clean(minutes=2)],
        )
        self.assertEqual(verdict.state, "success")

    def test_codex_response_without_reviewed_commit_marker_is_blocked(self) -> None:
        incomplete = evidence(
            "chatgpt-codex-connector[bot]",
            "Codex Review: Didn't find any major issues.",
            minutes=1,
        )
        verdict = self.evaluate(comments=[request(), incomplete])
        self.assertEqual(verdict.state, "error")
        self.assertEqual(verdict.marker, f"QA_BLOCKED {HEAD}")

    def test_commit_resolution_error_fails_closed(self) -> None:
        def fail(_prefix: str) -> str:
            raise RuntimeError("ambiguous prefix")

        verdict = evaluate_evidence(
            head_sha=HEAD,
            pr_author="rassvetpublic-spec",
            comments=[request(), clean()],
            threads=[],
            resolve_prefix=fail,
        )
        self.assertEqual(verdict.state, "error")
        self.assertIn("could not be resolved safely", verdict.reason)

    def test_invalid_current_head_is_rejected(self) -> None:
        with self.assertRaises(BridgeError):
            evaluate_evidence(
                head_sha="abc",
                pr_author="rassvetpublic-spec",
                comments=[],
                threads=[],
                resolve_prefix=lambda value: value,
            )


class ReviewThreadCompletenessTests(unittest.TestCase):
    def test_nested_review_comment_pagination_fails_closed(self) -> None:
        client = GitHubClient("token", "rassvetpublic-spec/Genre_test")
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [
                                {
                                    "isResolved": True,
                                    "isOutdated": False,
                                    "comments": {
                                        "nodes": [],
                                        "pageInfo": {"hasNextPage": True},
                                    },
                                }
                            ],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }
        }
        with (
            patch.object(client, "_request_json", return_value=response),
            self.assertRaisesRegex(BridgeError, "incomplete evidence"),
        ):
            client.review_threads(188)

    def test_outer_review_thread_pagination_requires_cursor(self) -> None:
        client = GitHubClient("token", "rassvetpublic-spec/Genre_test")
        response = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [],
                            "pageInfo": {"hasNextPage": True, "endCursor": None},
                        }
                    }
                }
            }
        }
        with (
            patch.object(client, "_request_json", return_value=response),
            self.assertRaisesRegex(BridgeError, "no end cursor"),
        ):
            client.review_threads(188)


class WorkflowMutationCoverageTests(unittest.TestCase):
    def test_workflow_rechecks_deleted_and_review_evidence(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "qa-verdict-bridge.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("types: [created, edited, deleted]", workflow)
        self.assertIn("pull_request_review:", workflow)
        self.assertIn("types: [submitted, edited, dismissed]", workflow)
        self.assertIn("pull_request_review_comment:", workflow)
        self.assertIn("github.event.pull_request.number || github.event.issue.number", workflow)


class LiveFailureStatusTests(unittest.TestCase):
    def test_live_evidence_api_failure_writes_error_status_on_known_head(self) -> None:
        class FakeClient:
            def __init__(self, _token: str, _repository: str) -> None:
                self.statuses = []

            def get_pr(self, _pr_number: int):
                return {"head": {"sha": HEAD}, "user": {"login": "author"}}

            def issue_comments(self, _pr_number: int):
                raise BridgeError("API unavailable")

            def review_threads(self, _pr_number: int):
                raise AssertionError("must not continue after issue-comment failure")

            def set_status(self, head_sha, verdict, target_url):
                self.statuses.append((head_sha, verdict, target_url))

        fake = FakeClient("token", "repo/name")
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "token"}, clear=False),
            patch("tools.qa_verdict_bridge.GitHubClient", return_value=fake),
        ):
            exit_code = bridge_main(
                ["--repository", "rassvetpublic-spec/Genre_test", "--pr", "188"]
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(len(fake.statuses), 1)
        head_sha, verdict, _target_url = fake.statuses[0]
        self.assertEqual(head_sha, HEAD)
        self.assertEqual(verdict.state, "error")
        self.assertEqual(verdict.marker, f"QA_BLOCKED {HEAD}")
        self.assertIn("could not be evaluated completely", verdict.reason)

    def test_low_level_transport_error_writes_error_status_on_known_head(self) -> None:
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "token"}, clear=False),
            patch.object(
                GitHubClient,
                "get_pr",
                return_value={"head": {"sha": HEAD}, "user": {"login": "author"}},
            ),
            patch.object(GitHubClient, "set_status") as set_status,
            patch(
                "tools.qa_verdict_bridge.urllib.request.urlopen",
                side_effect=RemoteDisconnected("connection dropped"),
            ),
        ):
            exit_code = bridge_main(
                ["--repository", "rassvetpublic-spec/Genre_test", "--pr", "188"]
            )

        self.assertEqual(exit_code, 2)
        set_status.assert_called_once()
        head_sha, verdict, _target_url = set_status.call_args.args
        self.assertEqual(head_sha, HEAD)
        self.assertEqual(verdict.state, "error")
        self.assertEqual(verdict.marker, f"QA_BLOCKED {HEAD}")
        self.assertIn("could not be evaluated completely", verdict.reason)

    def test_incomplete_http_response_writes_error_status_on_known_head(self) -> None:
        with (
            patch.dict("os.environ", {"GITHUB_TOKEN": "token"}, clear=False),
            patch.object(
                GitHubClient,
                "get_pr",
                return_value={"head": {"sha": HEAD}, "user": {"login": "author"}},
            ),
            patch.object(GitHubClient, "set_status") as set_status,
            patch(
                "tools.qa_verdict_bridge.urllib.request.urlopen",
                side_effect=IncompleteRead(b"partial", 100),
            ),
        ):
            exit_code = bridge_main(
                ["--repository", "rassvetpublic-spec/Genre_test", "--pr", "188"]
            )

        self.assertEqual(exit_code, 2)
        set_status.assert_called_once()
        head_sha, verdict, _target_url = set_status.call_args.args
        self.assertEqual(head_sha, HEAD)
        self.assertEqual(verdict.state, "error")
        self.assertEqual(verdict.marker, f"QA_BLOCKED {HEAD}")
        self.assertIn("could not be evaluated completely", verdict.reason)


if __name__ == "__main__":
    unittest.main()
