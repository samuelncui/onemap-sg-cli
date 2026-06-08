#!/usr/bin/env bash
# Install onemap-sg-cli Hermes skill with one command.
# Usage: curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-skill.sh | bash

set -euo pipefail

SKILL_DIR="${HOME}/.hermes/skills/onemap-sg-cli"
SKILL_URL="https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/SKILL.md"

mkdir -p "${SKILL_DIR}"
echo "→ Downloading SKILL.md..."
curl -sSL "${SKILL_URL}" -o "${SKILL_DIR}/SKILL.md"
echo "✓ Skill installed to ${SKILL_DIR}/SKILL.md"
echo "  Run /reset in Hermes to load the new skill."
