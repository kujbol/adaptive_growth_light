#!/usr/bin/env python3
"""Release automation script for Adaptive Growth Light.

Bumps manifest.json & frontend card versions, performs security/credential checks,
commits, tags, pushes, and creates a GitHub release via gh CLI.

Supports --dry-run mode to validate security and preview actions without making changes.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).parent.resolve()
MANIFEST_PATH = ROOT_DIR / "custom_components" / "adaptive_growth_light" / "manifest.json"
JS_PATH = ROOT_DIR / "custom_components" / "adaptive_growth_light" / "frontend" / "adaptive-growth-light-card.js"

# Security check regexes
SUSPICIOUS_PATTERNS = [
    (re.compile(r"gh[opsu]_[A-Za-z0-9_]{36,255}"), "GitHub Token"),
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
    (re.compile(r"""(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"""), "Generic Secret/Token"),
]

IGNORED_SCAN_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
IGNORED_SCAN_FILES = {"release.py"}


def check_for_credentials() -> bool:
    """Scan the repository for potential secrets, tokens, or private keys."""
    print("🔍 Scanning repository for accidental credentials or secrets...")
    found_issues = []

    for path in ROOT_DIR.rglob("*"):
        if not path.is_file():
            continue
        # Skip ignored directories
        if any(part in IGNORED_SCAN_DIRS for part in path.parts):
            continue
        if path.name in IGNORED_SCAN_FILES:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in SUSPICIOUS_PATTERNS:
                matches = pattern.findall(content)
                if matches:
                    rel_path = path.relative_to(ROOT_DIR)
                    found_issues.append(f"  - [{desc}] in {rel_path}: {matches[0][:10]}***")
        except Exception as e:
            print(f"Warning: Could not scan {path}: {e}")

    if found_issues:
        print("\n❌ SECURITY CHECK FAILED! Potential credentials/keys detected:")
        for issue in found_issues:
            print(issue)
        print("\nPlease remove any credentials before making a release.")
        return False

    print("✅ Security scan passed! No credentials or secrets found.")
    return True


def determine_version(requested_version: str | None, current_version: str) -> str:
    """Determine target version from argument or by bumping patch version."""
    if requested_version:
        return requested_version.lstrip("v")

    parts = current_version.split(".")
    if len(parts) >= 3 and parts[-1].isdigit():
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)

    raise ValueError(f"Cannot auto-bump current version '{current_version}'. Please specify manually.")


def run_dry_run(target_version: str, current_version: str) -> None:
    """Execute dry-run validation without modifying files or git."""
    print("\n--- 🚀 DRY RUN VALIDATION ---")
    print(f"Current version : {current_version}")
    print(f"Target version  : {target_version}")
    print(f"Manifest file   : {MANIFEST_PATH.relative_to(ROOT_DIR)} (exists: {MANIFEST_PATH.exists()})")
    print(f"Card JS file    : {JS_PATH.relative_to(ROOT_DIR)} (exists: {JS_PATH.exists()})")

    # Check Git status
    git_status = subprocess.run(
        ["git", "status", "--short"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if git_status:
        print("\nUncommitted changes that would be included:")
        for line in git_status.splitlines():
            print(f"  {line}")
    else:
        print("\nWorking tree is clean.")

    # Check GitHub CLI
    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
    gh_path = shutil.which("gh", path=env["PATH"])
    print(f"\nGitHub CLI (gh) : {'Found at ' + gh_path if gh_path else 'Not found (manual release needed)'}")

    print("\nActions that would be taken in real run:")
    print(f"  1. Update {MANIFEST_PATH.name} version -> {target_version}")
    print(f"  2. Update {JS_PATH.name} CARD_VERSION -> {target_version}")
    print(f"  3. git add . && git commit -m 'chore: release v{target_version}'")
    print(f"  4. git push origin main")
    print(f"  5. git tag v{target_version} && git push origin v{target_version}")
    print(f"  6. gh release create v{target_version} --generate-notes")
    print("\n✨ DRY RUN SUCCESSFUL: All checks and validations passed!")


def main():
    parser = argparse.ArgumentParser(description="Release automation for Adaptive Growth Light")
    parser.add_argument("version", nargs="?", default=None, help="Target version (e.g. 1.0.1)")
    parser.add_argument("--dry-run", action="store_true", help="Preview release actions without modifying anything")
    args = parser.parse_args()

    if not check_for_credentials():
        sys.exit(1)

    if not MANIFEST_PATH.exists():
        print(f"Error: {MANIFEST_PATH} does not exist.")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    current_version = manifest.get("version", "0.0.0")

    try:
        version = determine_version(args.version, current_version)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.dry_run:
        run_dry_run(version, current_version)
        return

    print(f"Bumping version from {current_version} to {version}...")

    # 1. Update manifest.json
    manifest["version"] = version
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    # 2. Update frontend card JS if present
    if JS_PATH.exists():
        with open(JS_PATH, "r", encoding="utf-8") as f:
            js_content = f.read()

        js_content = re.sub(
            r'const CARD_VERSION = ".*?";',
            f'const CARD_VERSION = "{version}";',
            js_content,
        )

        with open(JS_PATH, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"Updated {JS_PATH.name} to version {version}")

    print("Files updated successfully. Proceeding with Git commit and push...")

    # 3. Git commit and push
    try:
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", f"chore: release v{version}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
        else:
            print("Working tree clean, skipping commit.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to commit/push to main: {e}")
        sys.exit(1)

    # 4. Tag release
    print(f"Tagging release v{version}...")
    try:
        subprocess.run(["git", "tag", f"v{version}"], check=True)
        subprocess.run(["git", "push", "origin", f"v{version}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to tag/push release: {e}")
        sys.exit(1)

    # 5. Create GitHub Release
    print(f"Creating GitHub Release v{version}...")
    env = os.environ.copy()
    env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"

    if shutil.which("gh", path=env["PATH"]):
        try:
            subprocess.run(
                ["gh", "release", "create", f"v{version}", "--generate-notes"],
                check=True,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to create GitHub release: {e}")
            print("The tag was pushed, but you may need to create the release manually on GitHub.")
    else:
        print("⚠️ GitHub CLI (gh) is not installed. The tag was pushed, but the release could not be created automatically.")
        print("Please install gh or create the release manually on GitHub.")

    print(f"✅ Release v{version} deployed successfully!")


if __name__ == "__main__":
    main()
