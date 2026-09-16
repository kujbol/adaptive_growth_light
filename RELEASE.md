# Release Instructions

To release a new version of the **Adaptive Growth Light** integration so that HACS users can seamlessly update it, use the automated Python release script.

This script automatically:
1. **Performs a security audit**: Scans all repository files to ensure no private keys, API tokens, or secrets are accidentally committed.
2. Bumps the integration version in `custom_components/adaptive_growth_light/manifest.json`.
3. Bumps the frontend card version (`CARD_VERSION`) in `custom_components/adaptive_growth_light/frontend/adaptive-growth-light-card.js`.
4. Commits the changes to the `main` branch.
5. Creates and pushes the required lightweight Git tag (`vX.Y.Z`) so HACS can detect the new release.
6. Creates a GitHub release with auto-generated release notes using `gh release create`.

### How to use:

Preview and validate the release without making any changes:

```bash
python3 release.py --dry-run
```

Or dry run a specific version:

```bash
python3 release.py 1.0.1 --dry-run
```

Execute the release:

```bash
python3 release.py 1.0.1
```

Or auto-bump the patch version:

```bash
python3 release.py
```

Once the script finishes successfully, the tag is pushed and HACS will automatically detect the new release version and prompt users to update.
