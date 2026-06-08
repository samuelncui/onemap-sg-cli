#!/usr/bin/env bash
# Install onemap-sg-cli instructions for your AI agent.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash              # auto-detect
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s hermes     # Hermes
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s cursor     # Cursor
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s claude     # Claude Code
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s agents     # AGENTS.md (universal)
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s cline      # Cline
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s copilot    # GitHub Copilot
#   curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh | bash -s aider      # Aider

set -euo pipefail

AGENT="${1:-auto}"
INSTRUCTIONS_URL="https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/AGENTS.md"

# Resolve target path based on agent
case "$AGENT" in
  hermes)
    TARGET="${HOME}/.hermes/skills/onemap-sg-cli/SKILL.md"
    INSTRUCTIONS_URL="https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/SKILL.md"
    ;;
  cursor)
    TARGET="${PWD}/.cursor/rules/onemap-sg-cli.mdc"
    ;;
  claude)
    TARGET="${PWD}/CLAUDE.md"
    APPEND=true
    ;;
  cline)
    TARGET="${PWD}/.clinerules"
    APPEND=true
    ;;
  copilot)
    TARGET="${PWD}/.github/copilot-instructions.md"
    APPEND=true
    ;;
  winds|windsurf)
    TARGET="${PWD}/.windsurfrules"
    ;;
  aider)
    TARGET="${PWD}/CONVENTIONS.md"
    APPEND=true
    ;;
  agents|auto|*)
    TARGET="${PWD}/AGENTS.md"
    ;;
esac

mkdir -p "$(dirname "$TARGET")"

echo "→ Agent: $AGENT"
echo "→ Target: $TARGET"

if [ "${APPEND:-false}" = true ] && [ -f "$TARGET" ]; then
  echo "→ Appending to existing $TARGET..."
  echo "" >> "$TARGET"
  echo "<!-- onemap-sg-cli instructions -->" >> "$TARGET"
  curl -sSL "$INSTRUCTIONS_URL" >> "$TARGET"
else
  echo "→ Downloading instructions..."
  curl -sSL "$INSTRUCTIONS_URL" -o "$TARGET"
fi

echo "✓ Done. Target: $TARGET"
echo "  Restart your agent to load the new instructions."
