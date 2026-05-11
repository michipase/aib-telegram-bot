#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install python3 wkhtmltopdf libxml2-dev libxslt1-dev -y
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# Install repository-managed Git hooks.
chmod +x .githooks/pre-commit scripts/bump-version.sh
git config core.hooksPath .githooks

echo "DONE!"
