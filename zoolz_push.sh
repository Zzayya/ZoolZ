#!/usr/bin/env bash
# ZoolZ → GitHub one-shot (creates or overwrites <your-login>/ZoolZ)
set -euo pipefail

# Always run from the script's folder (project root)
cd "$(dirname "$0")"

# --- prerequisites (light checks) ---
command -v git >/dev/null || { echo "❌ git not found."; exit 1; }
command -v gh  >/dev/null || { echo "❌ GitHub CLI (gh) not found."; exit 1; }

# Ensure you're logged in (non-interactive if already logged in)
if ! gh auth status >/dev/null 2>&1; then
  gh auth login
fi

# Figure out your GitHub username automatically (e.g., 'Zzayya')
owner="$(gh api user -q .login)"
repo_name="ZoolZ"
repo="${owner}/${repo_name}"

# --- git init & commit ---
git init
git config user.name  "Isaiah J. Miro"
git config user.email "isaiahjmiro@gmail.com"

# Create a sensible .gitignore if missing
if [ ! -f ".gitignore" ]; then
  cat > .gitignore <<'GITIGNORE'
# macOS
.DS_Store

# VS Code
.vscode/

# Python
__pycache__/
*.pyc
.venv/
venv/
dist/
build/
.pytest_cache/
.ipynb_checkpoints/
.python-version

# Node
node_modules/

# Swift / Xcode
DerivedData/
build/
*.xcuserstate
*.xcworkspace
*.xcodeproj/project.xcworkspace/
*.xcuserdata/
.swiftpm/
Package.resolved

# Env & logs
.env
.env.*
*.log
GITIGNORE
fi

git add -A
msg="${1:-initial push}"
git commit -m "$msg" || true
git branch -M main

# --- ensure a REAL repo named "ZoolZ" exists, then push to it (SSH) ---
# Try to create it every time; if it already exists, ignore the error.
gh repo create "${repo_name}" --private >/dev/null 2>&1 || true

git remote remove origin 2>/dev/null || true
git remote add origin "git@github.com:${repo}.git"

# Overwrite remote with local contents
git push -u origin main --force

echo "✅ Done. Remote: https://github.com/${repo}"