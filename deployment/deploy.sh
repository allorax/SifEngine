#!/usr/bin/env bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "========================================="
echo " SIFEngine Production Deployment Script"
echo "========================================="
echo "Project Path: ${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

# Step 1: Verify Python Environment & Dependencies
echo "--> Checking Python environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "--> Installing backend dependencies..."
pip install -q -r requirements.txt

# Step 2: Initialize Database & Apply Schema/Indexes
echo "--> Initializing database schemas & high-performance WAL indexes..."
python -c "from app.database import init_database; init_database(); print('✓ Database initialized with SQLite WAL mode and indexes.')"

# Step 3: Execute Test Suite
echo "--> Running verification unit tests..."
export MPLBACKEND=Agg
python -m pytest tests/ -q --tb=short
echo "✓ All backend unit tests passed."

# Step 4: Build Frontend Static Bundle
echo "--> Building frontend production bundle..."
cd frontend
npm install --silent
npm run build
cd "${PROJECT_ROOT}"
echo "✓ Frontend built successfully into frontend/dist"

# Step 5: Verify Backend Server Connectivity
echo "--> Verifying backend startup capability..."
python -c "import app.main; print('✓ App module imported cleanly.')"

echo ""
echo "========================================="
echo "✓ SIFEngine Deployment Preparation Complete!"
echo "  Backend Service: systemctl start sifengine-backend"
echo "  Frontend Static Path: ${PROJECT_ROOT}/frontend/dist"
echo "========================================="
