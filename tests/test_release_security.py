"""Test release security check function."""

from release import check_for_credentials, SUSPICIOUS_PATTERNS


def test_repo_has_no_credentials():
    """Verify that current repository has zero credentials or secret keys."""
    assert check_for_credentials() is True


def test_suspicious_patterns_detection():
    """Verify that regexes detect sensitive patterns."""
    prefix = "gh" + "p_"
    sample_key = prefix + ("A" * 36)
    assert any(pat.search(sample_key) for pat, _ in SUSPICIOUS_PATTERNS)

    rsa_prefix = "-----" + "BEGIN RSA PRIVATE KEY" + "-----"
    sample_private_key = rsa_prefix + "\nMIIE..."
    assert any(pat.search(sample_private_key) for pat, _ in SUSPICIOUS_PATTERNS)
