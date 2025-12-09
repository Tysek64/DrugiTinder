#!/bin/bash
set -e
# Usage: ./populate.sh <container-name> <host-port>

# 1. Resolve Paths
SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" && \
  pwd
)"

# ASSUMPTION: The Rust project is located at ../tinder_optimizer relative to this script
# Adjust this path if your folder structure differs
RUST_PROJECT_DIR="$SCRIPT_DIR/population_rewritten"

# 2. Validate Container
CONTAINER_NAME=${1:-pdb-demo}
if ! docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
  echo "Error: Container '$CONTAINER_NAME' is not running"
  exit 1
fi

echo ">>> Populating data for: $CONTAINER_NAME"

# 3. Dynamic Port Resolution
# We must find the host port that maps to the container's internal 5432
HOST_PORT=$(docker port "$CONTAINER_NAME" 5432 | head -n 1 | awk -F: '{print $2}')

if [ -z "$HOST_PORT" ]; then
    echo "Error: Could not determine port for $CONTAINER_NAME"
    exit 1
fi

echo ">>> Detected DB at localhost:$HOST_PORT"

# 4. Export Env Vars for Rust
# The Rust app's db/mod.rs must read these specific env vars to connect successfully
export DB_HOST=localhost
export DB_PORT="$HOST_PORT"
export DB_USER=kbd
export DB_PASS=kochamy_bazy_danych
export DB_NAME=pdb_demo

# 5. Execute Rust Application
if [ ! -d "$RUST_PROJECT_DIR" ]; then
    echo "CRITICAL: Rust project directory not found at $RUST_PROJECT_DIR"
    exit 1
fi

cd "$RUST_PROJECT_DIR" || exit 1

if [ ! -f "Cargo.toml" ]; then
    echo "CRITICAL: Cargo.toml not found in $RUST_PROJECT_DIR"
    exit 1
fi

echo ">>> Building and Running tinder_optimizer (Release Mode)..."
# --release is mandatory for the performance requirements (hashing/bulk inserts)
# --quiet reduces compilation noise
cargo run --release 

echo ">>> Population Sequence Complete."
