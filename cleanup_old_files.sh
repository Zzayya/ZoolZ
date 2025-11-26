#!/bin/bash
# ZoolZ File Cleanup Script
# Moves development status files to docs/archive/

echo "🧹 ZoolZ File Cleanup Script"
echo "============================"
echo ""

# Create archive directory
echo "📁 Creating archive directory..."
mkdir -p docs/archive/development-logs

# Count files to move
FILE_COUNT=$(ls -1 *_COMPLETE.md *_STATUS.md *_PLAN.md *_SUMMARY.md CLEANING_CHECKLIST.md CLAUDE_LOOP.md QUICK_REFERENCE.md 2>/dev/null | wc -l)

echo "📦 Found $FILE_COUNT development documentation files to archive"
echo ""

# Move status files
echo "🚚 Moving files to docs/archive/development-logs/..."

# Move all status and completion docs
mv CAD_SYSTEM_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv CLAUDE_LOOP.md docs/archive/development-logs/ 2>/dev/null
mv CLEANING_CHECKLIST.md docs/archive/development-logs/ 2>/dev/null
mv COMPLETE_STATUS_REPORT.md docs/archive/development-logs/ 2>/dev/null
mv CONTROL_PANEL_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv COOKIE_CUTTER_TEST_PLAN.md docs/archive/development-logs/ 2>/dev/null
mv DATASET_INTELLIGENCE_SYSTEM.md docs/archive/development-logs/ 2>/dev/null
mv DATA_COLLECTION_GUIDE.md docs/archive/development-logs/ 2>/dev/null
mv FINAL_STATUS.md docs/archive/development-logs/ 2>/dev/null
mv FIX_MODELING_UI.md docs/archive/development-logs/ 2>/dev/null
mv LOGIN_FIXED.md docs/archive/development-logs/ 2>/dev/null
mv ML_ACTIVATION_LEVER_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv ML_IMPROVEMENTS_PLAN.md docs/archive/development-logs/ 2>/dev/null
mv ML_UI_IMPROVEMENTS_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv MODELING_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv MODELING_PRODUCTION_PLAN.md docs/archive/development-logs/ 2>/dev/null
mv MODELING_STATUS.md docs/archive/development-logs/ 2>/dev/null
mv MODELING_SYSTEM_DEEP_ANALYSIS.md docs/archive/development-logs/ 2>/dev/null
mv MODELING_TOOLS_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv MODELING_UI_FIXES_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv MODELING_UPGRADES_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv NEXT_STEPS_AND_PLANNING.md docs/archive/development-logs/ 2>/dev/null
mv PHASE_1_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv POLISH_BREAKDOWN.md docs/archive/development-logs/ 2>/dev/null
mv QUICK_REFERENCE.md docs/archive/development-logs/ 2>/dev/null
mv SESSION_RESTART_SUMMARY.md docs/archive/development-logs/ 2>/dev/null
mv SESSION_SUMMARY_COMPLETE.md docs/archive/development-logs/ 2>/dev/null
mv TEMPORAL_SYSTEM_COMPLETE.md docs/archive/development-logs/ 2>/dev/null

echo "✅ Files archived!"
echo ""

# Show what's left in root
echo "📄 Remaining files in root directory:"
ls -1 *.md 2>/dev/null | grep -v CODE_REVIEW_REPORT.md
echo ""

# Show archived files
ARCHIVED_COUNT=$(ls -1 docs/archive/development-logs/*.md 2>/dev/null | wc -l)
echo "📦 Total files archived: $ARCHIVED_COUNT"
echo ""

echo "✨ Cleanup complete!"
echo ""
echo "Files are now organized:"
echo "  - Root directory: Only essential files (README.md)"
echo "  - docs/archive/development-logs/: All development status files"
echo ""
echo "You can safely delete the archive folder if you don't need the history:"
echo "  rm -rf docs/archive/development-logs/"
