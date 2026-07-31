#!/usr/bin/env zsh

# Get script directory
SCRIPT_DIR="${0:a:h}"

# Change to script directory
cd "$SCRIPT_DIR" || {
    echo "[ERROR] Cannot change to directory: $SCRIPT_DIR"
    echo "Please check if the path is correct"
    read "?Press Enter to exit..."
    exit 1
}

echo "========================================"
echo "Bilibili Favorite Sync Tool"
echo "========================================"
echo "Working directory: $(pwd)"
echo

# Check if uv is installed
if ! command -v uv >/dev/null 2>&1; then
    echo "[ERROR] uv command not found"
    echo "Please install uv first: https://github.com/astral-sh/uv"
    read "?Press Enter to exit..."
    exit 1
fi

# Check if main.py exists
if [[ ! -f "main.py" ]]; then
    echo "[ERROR] main.py not found"
    echo "Please make sure the script is in the project root directory"
    read "?Press Enter to exit..."
    exit 1
fi

# Run main program using uv (uv will manage virtual environment automatically)
echo "Starting program..."
echo
uv run main.py

# Check program execution result
if [[ $? -ne 0 ]]; then
    echo
    echo "[WARNING] Program exited with error code: $?"
else
    echo
    echo "[SUCCESS] Program completed successfully"
fi

echo
read "?Press Enter to exit..."
