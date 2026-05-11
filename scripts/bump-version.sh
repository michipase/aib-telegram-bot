#!/usr/bin/env bash
set -euo pipefail

VERSION_FILE="VERSION"

if [[ ! -f "$VERSION_FILE" ]]; then
  echo "0.0.0" > "$VERSION_FILE"
fi

CURRENT_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

if [[ ! "$CURRENT_VERSION" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  echo "Invalid VERSION format in $VERSION_FILE: '$CURRENT_VERSION'. Expected MAJOR.MINOR.PATCH" >&2
  exit 1
fi

MAJOR="${BASH_REMATCH[1]}"
MINOR="${BASH_REMATCH[2]}"
PATCH="${BASH_REMATCH[3]}"
PATCH=$((PATCH + 1))
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

printf '%s\n' "$NEW_VERSION" > "$VERSION_FILE"
git add "$VERSION_FILE"

echo "Version bumped: $CURRENT_VERSION -> $NEW_VERSION" >&2
