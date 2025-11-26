#!/bin/bash
# Remove old development files from Git/GitHub ONLY
# Files will remain on your local MacBook

echo "🧹 Removing development files from Git (keeping local copies)"
echo "============================================================="
echo ""

# Add files to .gitignore first
echo "📝 Adding files to .gitignore..."
cat >> .gitignore << 'EOL'

# Development status and planning files (keep local, exclude from git)
CAD_SYSTEM_COMPLETE.md
CLAUDE_LOOP.md
CLEANING_CHECKLIST.md
COMPLETE_STATUS_REPORT.md
CONTROL_PANEL_COMPLETE.md
COOKIE_CUTTER_TEST_PLAN.md
DATASET_INTELLIGENCE_SYSTEM.md
DATA_COLLECTION_GUIDE.md
FINAL_STATUS.md
FIX_MODELING_UI.md
LOGIN_FIXED.md
ML_ACTIVATION_LEVER_COMPLETE.md
ML_IMPROVEMENTS_PLAN.md
ML_UI_IMPROVEMENTS_COMPLETE.md
MODELING_COMPLETE.md
MODELING_PRODUCTION_PLAN.md
MODELING_STATUS.md
MODELING_SYSTEM_DEEP_ANALYSIS.md
MODELING_TOOLS_COMPLETE.md
MODELING_UI_FIXES_COMPLETE.md
MODELING_UPGRADES_COMPLETE.md
NEXT_STEPS_AND_PLANNING.md
PHASE_1_COMPLETE.md
POLISH_BREAKDOWN.md
QUICK_REFERENCE.md
SESSION_RESTART_SUMMARY.md
SESSION_SUMMARY_COMPLETE.md
TEMPORAL_SYSTEM_COMPLETE.md
EOL

echo "✅ Files added to .gitignore"
echo ""

# Remove from git tracking (--cached keeps local files)
echo "🗑️  Removing files from Git tracking (local files preserved)..."

git rm --cached CAD_SYSTEM_COMPLETE.md 2>/dev/null
git rm --cached CLAUDE_LOOP.md 2>/dev/null
git rm --cached CLEANING_CHECKLIST.md 2>/dev/null
git rm --cached COMPLETE_STATUS_REPORT.md 2>/dev/null
git rm --cached CONTROL_PANEL_COMPLETE.md 2>/dev/null
git rm --cached COOKIE_CUTTER_TEST_PLAN.md 2>/dev/null
git rm --cached DATASET_INTELLIGENCE_SYSTEM.md 2>/dev/null
git rm --cached DATA_COLLECTION_GUIDE.md 2>/dev/null
git rm --cached FINAL_STATUS.md 2>/dev/null
git rm --cached FIX_MODELING_UI.md 2>/dev/null
git rm --cached LOGIN_FIXED.md 2>/dev/null
git rm --cached ML_ACTIVATION_LEVER_COMPLETE.md 2>/dev/null
git rm --cached ML_IMPROVEMENTS_PLAN.md 2>/dev/null
git rm --cached ML_UI_IMPROVEMENTS_COMPLETE.md 2>/dev/null
git rm --cached MODELING_COMPLETE.md 2>/dev/null
git rm --cached MODELING_PRODUCTION_PLAN.md 2>/dev/null
git rm --cached MODELING_STATUS.md 2>/dev/null
git rm --cached MODELING_SYSTEM_DEEP_ANALYSIS.md 2>/dev/null
git rm --cached MODELING_TOOLS_COMPLETE.md 2>/dev/null
git rm --cached MODELING_UI_FIXES_COMPLETE.md 2>/dev/null
git rm --cached MODELING_UPGRADES_COMPLETE.md 2>/dev/null
git rm --cached NEXT_STEPS_AND_PLANNING.md 2>/dev/null
git rm --cached PHASE_1_COMPLETE.md 2>/dev/null
git rm --cached POLISH_BREAKDOWN.md 2>/dev/null
git rm --cached QUICK_REFERENCE.md 2>/dev/null
git rm --cached SESSION_RESTART_SUMMARY.md 2>/dev/null
git rm --cached SESSION_SUMMARY_COMPLETE.md 2>/dev/null
git rm --cached TEMPORAL_SYSTEM_COMPLETE.md 2>/dev/null

echo "✅ Files removed from Git tracking"
echo ""

# Show status
echo "📊 Git status:"
git status --short
echo ""

echo "✨ Done!"
echo ""
echo "What happened:"
echo "  ✅ Files are still on your MacBook"
echo "  ✅ Files added to .gitignore"
echo "  ✅ Files removed from Git tracking"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit: git commit -m 'Remove development files from repository'"
echo "  3. Push: git push"
echo ""
echo "After push, files will be removed from GitHub but stay on your Mac!"
