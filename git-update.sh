#!/usr/bin/env bash
set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

# Ensure update_repo.sh exists and is executable
if [ ! -f "./update_repo.sh" ]; then
  echo "Error: update_repo.sh not found in $SCRIPT_DIR"
  exit 1
fi
chmod +x ./update_repo.sh

# Detect current branch (defaults to main if detection fails)
CURRENT_BRANCH=$(git symbolic-ref --quiet --short HEAD || echo "main")

echo "Starting update for branch: $CURRENT_BRANCH"

# Call update_repo.sh, passing all arguments.
# It will handle adding, committing, and pushing.
./update_repo.sh --remote origin --branch "$CURRENT_BRANCH" --push "$@"

