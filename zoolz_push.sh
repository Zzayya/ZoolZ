#!/usr/bin/env bash
# Zoolz → GitHub one-shot (create or overwrite isaiahmiro/Zoolz)
set -euo pipefail

REPO="isaiahmiro/Zoolz"

# Always operate from the script's folder (your project root)
cd "$(dirname "$0")"

# --- prerequisites -----------------------------------------------------------
if ! command -v git >/dev/null 2>&1; then
  echo "❌ Git not found. Install Xcode Command Line Tools first:"
  echo "   xcode-select --install"
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing GitHub CLI with Homebrew..."
    brew install gh
  else
    echo "❌ Homebrew not found. Install it from https://brew.sh, then rerun."
    exit 1
  fi
fi

# Login once (browser prompt)
if ! gh auth status >/dev/null 2>&1; then
  gh auth login
fi

# --- git setup ---------------------------------------------------------------
git init
git config user.name  "Isaiah J. Miro"
git config user.email "isaiahjmiro@gmail.com"

# Create a sensible .gitignore if missing
if [ ! -f ".gitignore" ]; then
  cat > .gitignore <<'EOF'
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
.pnpm-store/
.yarn/

# Swift / Xcode
DerivedData/
build/
*.xcuserstate
*.xcworkspace
*.xcodeproj/project.xcworkspace/
*.xcuserdata/
.swiftpm/
Package.resolved

# JetBrains
.idea/

# Env & logs
.env
.env.*
*.log

# Misc
Thumbs.db
EOF
fi

git add -A

# allow a custom commit message: ./zoolz_push.sh "my message"
msg="${1:-Initial commit}"
git commit -m "$msg" || true
git branch -M main

# --- create or overwrite remote ---------------------------------------------
if gh repo view "$REPO" >/dev/null 2>&1; then
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/$REPO.git"
  git push -u origin main --force
else
  gh repo create "$REPO" --private --source=. --remote=origin --push
fi

echo "✅ Done. Remote: $(git remote get-url origin)"
