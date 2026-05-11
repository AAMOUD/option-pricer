#!/usr/bin/env bash
set -e

PYTHON=$(which python3)
PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)

# Check Python dev headers
if ! $PYTHON -c "import sysconfig; import os; assert os.path.exists(sysconfig.get_path('include'))" 2>/dev/null; then
    echo "Python dev headers not found. Install them first:"
    echo "  sudo apt-get install python${PYTHON_VERSION}-dev"
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi

source venv/bin/activate
pip install -q pybind11 numpy streamlit plotly requests

# Compile directly with g++ (no cmake needed)
INCLUDES=$(python3 -m pybind11 --includes)
SUFFIX=$(python3-config --extension-suffix)

mkdir -p build
g++ -O3 -march=native -Wall -shared -std=c++17 -fPIC \
    $INCLUDES \
    cpp/pricer.cpp cpp/bindings.cpp \
    -o build/pricer_cpp${SUFFIX}

echo ""
echo "Build complete -> build/pricer_cpp${SUFFIX}"
echo "Run the app with:"
echo "  source venv/bin/activate && streamlit run frontend/app.py"
