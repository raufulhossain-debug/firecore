#!/usr/bin/env bash
set -euo pipefail

# FireCore repo bootstrap — run this once after unzipping.
# Usage:
#   cd firecore
#   chmod +x setup.sh
#   ./setup.sh            # uses default repo name "firecore"
#   ./setup.sh my-repo    # override repo name

REPO_NAME="${1:-firecore}"
GH_USER=$(gh auth status 2>&1 | grep -oP 'Logged in to github.com account \K\S+' || true)

echo "=== FireCore repo bootstrap ==="

# 1. Ensure gh CLI is authenticated
if ! gh auth status &>/dev/null; then
    echo "GitHub CLI not authenticated. Running 'gh auth login'..."
    gh auth login
    GH_USER=$(gh auth status 2>&1 | grep -oP 'Logged in to github.com account \K\S+')
fi
echo "Authenticated as: $GH_USER"

# 2. Create private repo on GitHub
echo "Creating private repo: $GH_USER/$REPO_NAME ..."
gh repo create "$REPO_NAME" --private --source=. --push 2>/dev/null || {
    # If repo already exists, just init + push
    echo "Repo may already exist. Initializing and pushing..."
    git init -b main
    git add -A
    git commit -m "feat: initial scaffold — rules engine, SKU library, solver, API, static demo

- 5 packages: rules_engine, sku_library, site_intel, solver, api
- LA City ADU jurisdiction (LAMC §12.22 A.33, Gov Code §65852.2)
- FireCore-1200 SKU with 4 variants (std, compact 2-story, flood pier, hillside stepped)
- Parametric best-fit solver with EXACT/MINOR/MAJOR/NO_FIT outcomes
- FastAPI service with /evaluate, /site-intel, /jurisdictions, /skus endpoints
- Static HTML demo with Leaflet map + 9 LA preset parcels
- 24 tests passing across all packages
- CI workflow (GitHub Actions, Python 3.11 + 3.12 matrix)
- CODEOWNERS routing for jurisdiction YAML and SKU YAML reviews"
    git remote add origin "https://github.com/$GH_USER/$REPO_NAME.git"
    git push -u origin main
}

echo ""
echo "Done! Repo live at: https://github.com/$GH_USER/$REPO_NAME"
echo ""
echo "Next steps:"
echo "  1. Go to repo Settings → Branches → add 'main' protection rule"
echo "  2. Require PR reviews (enforces CODEOWNERS routing)"
echo "  3. Require CI to pass before merge"
