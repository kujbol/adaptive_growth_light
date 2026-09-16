"""Test release security check and dry-run functions."""

import subprocess
import sys
from release import check_for_credentials, determine_version, SUSPICIOUS_PATTERNS


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


def test_determine_version():
    """Verify version bumping and explicit version parsing."""
    assert determine_version(None, "1.0.0") == "1.0.1"
    assert determine_version("1.2.0", "1.0.0") == "1.2.0"
    assert determine_version("v2.0.0", "1.0.0") == "2.0.0"


def test_release_dry_run():
    """Verify that release.py --dry-run completes successfully with exit code 0."""
    result = subprocess.run(
        [sys.executable, "release.py", "--dry-run"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "DRY RUN VALIDATION" in result.stdout
    assert "DRY RUN SUCCESSFUL" in result.stdout
