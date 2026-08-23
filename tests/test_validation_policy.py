from genre_test.validation_policy import should_recheck


def test_old_versions_filter():
    assert should_recheck(
        "old_versions",
        "0.3.0",
        "0.2.1",
        "high",
        "primary",
        "STABLE",
    )
    assert not should_recheck(
        "old_versions",
        "0.3.0",
        "0.3.0",
        "high",
        "primary",
        "STABLE",
    )


def test_unstable_filter():
    assert should_recheck(
        "unstable",
        "0.3.0",
        "0.3.0",
        "medium",
        "primary",
        "STABLE",
    )
    assert should_recheck(
        "unstable",
        "0.3.0",
        "0.3.0",
        "high",
        "hybrid",
        "STABLE",
    )
    assert should_recheck(
        "unstable",
        "0.3.0",
        "0.3.0",
        "high",
        "primary",
        "CRITICAL",
    )
    assert not should_recheck(
        "unstable",
        "0.3.0",
        "0.3.0",
        "high",
        "primary",
        "STABLE",
    )
