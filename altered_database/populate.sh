#!/bin/bash
set -e
# usage: populate.sh <container-name> <host-port>

# handle relative paths
SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" && \
  pwd
)"
PYTHON_SCRIPT_DIR="$SCRIPT_DIR/../skrypt"
POPULATE_SCRIPT="$PYTHON_SCRIPT_DIR/populateDB.py"


# getting docker container

CONTAINER_NAME=${1:-pdb-demo}
if ! docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
  echo "Error: Container '$CONTAINER_NAME' is not running"
  exit 1
fi

echo ">>> Populating data for: $CONTAINER_NAME"

# looking for the host port wired to postgres container internal DB port
HOST_PORT=$(docker port "$CONTAINER_NAME" 5432 | head -n 1 | awk -F: '{print $2}')

if [ -z "$HOST_PORT" ]; then
    echo "Error: Could not determine port for $CONTAINER_NAME"
    exit 1
fi

# setting up python environment

export DB_HOST=localhost
export DB_PORT="$HOST_PORT"
export DB_USER=kbd
export DB_PASS=kochamy_bazy_danych
export DB_NAME=pdb_demo

cd "$PYTHON_SCRIPT_DIR" || { echo "Error: Python directory not found at $PYTHON_SCRIPT_DIR"; exit 1; }

if [ -f ".venv/bin/activate" ]; then
    echo ">>> Sourcing virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo ">>> Sourcing virtual environment (venv)..."
    source venv/bin/activate
else
    echo "----------------------------------------------------------------"
    echo "ERROR: Virtual environment not found!"
    echo "Checked: $PYTHON_DIR/.venv and $PYTHON_DIR/venv"
    echo "Please create it explicitly:"
    echo "  cd $PYTHON_DIR"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "----------------------------------------------------------------"
    exit 1
fi

python3 "$POPULATE_SCRIPT"

echo ">>> Populating the DATABASE finished. Hopefully it will help populate"
