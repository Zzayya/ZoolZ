#!/bin/bash
# ZoolZ - Install/Update All Requirements
# This will install new packages AND upgrade existing ones

echo "🚀 Installing/Updating ZoolZ Requirements..."
echo ""

# Activate venv if it exists
if [ -d "venv" ]; then
    echo "✓ Found venv, activating..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "✓ Found .venv, activating..."
    source .venv/bin/activate
else
    echo "⚠️  No venv found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Upgrade pip first
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install/upgrade all requirements
echo ""
echo "📦 Installing/Upgrading all packages..."
pip install --upgrade -r requirements.txt

# Download spaCy model
echo ""
echo "🤖 Downloading spaCy language model..."
python -m spacy download en_core_web_lg

# Verify installations
echo ""
echo "✅ Verifying installations..."
python -c "from sentence_transformers import SentenceTransformer; print('✓ Sentence-BERT OK')"
python -c "import spacy; spacy.load('en_core_web_lg'); print('✓ spaCy OK')"
python -c "import usaddress; print('✓ usaddress OK')"
python -c "import trimesh; print('✓ Trimesh OK')"
python -c "import cv2; print('✓ OpenCV OK')"
python -c "import flask; print('✓ Flask OK')"
python -c "import celery; print('✓ Celery OK')"

echo ""
echo "🎉 All done! ZoolZ is ready to rock!"
