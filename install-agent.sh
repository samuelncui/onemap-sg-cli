#!/usr/bin/env bash
# Install onemap-sg-cli instructions for your AI agent(s).
#
# Usage:
#   curl -sSL https://.../install-agent.sh | bash              # auto-detect & install to all found
#   curl -sSL https://.../install-agent.sh | bash -s all       # install to ALL agents
#   curl -sSL https://.../install-agent.sh | bash -s hermes    # Hermes only
#   curl -sSL https://.../install-agent.sh | bash -s cursor    # Cursor only
#   (also: claude, cline, copilot, windsurf, aider, agents)

set -euo pipefail

AGENT="${1:-auto}"
BASE_URL="https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main"

# ── Helper ──
install_one() {
  local name="$1" target="$2" source="$3" append="$4" detect="$5"

  if [ -n "$detect" ] && ! eval "$detect" 2>/dev/null; then
    return 1  # not detected
  fi

  mkdir -p "$(dirname "$target")"

  if [ "$append" = true ] && [ -f "$target" ]; then
    if grep -q "onemap-sg-cli" "$target" 2>/dev/null; then
      echo "  ✓ $name — already installed (skipped)"
    else
      echo "" >> "$target"
      echo "<!-- onemap-sg-cli instructions -->" >> "$target"
      curl -sSL "$source" >> "$target"
      echo "  ✓ $name — appended to $target"
    fi
  else
    curl -sSL "$source" -o "$target"
    echo "  ✓ $name — written to $target"
  fi
  return 0
}

# ── Install by agent ──
install_hermes()   { install_one hermes   "$HOME/.hermes/skills/onemap-sg-cli/SKILL.md"    "$BASE_URL/SKILL.md"  false "test -d $HOME/.hermes"; }
install_cursor()   { install_one cursor   "$PWD/.cursor/rules/onemap-sg-cli.mdc"            "$BASE_URL/AGENTS.md" false "test -d $PWD/.cursor -o -f $PWD/AGENTS.md"; }
install_claude()   { install_one claude   "$PWD/CLAUDE.md"                                  "$BASE_URL/AGENTS.md" true  "test -f $PWD/CLAUDE.md -o command -v claude &>/dev/null"; }
install_cline()    { install_one cline    "$PWD/.clinerules"                                "$BASE_URL/AGENTS.md" true  "test -f $PWD/.clinerules"; }
install_copilot()  { install_one copilot  "$PWD/.github/copilot-instructions.md"            "$BASE_URL/AGENTS.md" true  "test -d $PWD/.github"; }
install_windsurf() { install_one windsurf "$PWD/.windsurfrules"                             "$BASE_URL/AGENTS.md" false "test -f $PWD/.windsurfrules -o -f $PWD/AGENTS.md"; }
install_aider()    { install_one aider    "$PWD/CONVENTIONS.md"                             "$BASE_URL/AGENTS.md" true  "test -f $PWD/.aider.conf.yml -o -f $PWD/CONVENTIONS.md"; }
install_agents()   { install_one agents   "$PWD/AGENTS.md"                                  "$BASE_URL/AGENTS.md" false "true"; }

ALL_AGENTS=(hermes cursor claude cline copilot windsurf aider agents)

# ── Resolve agent list ──
AGENTS_TO_INSTALL=()

case "$AGENT" in
  all)
    AGENTS_TO_INSTALL=("${ALL_AGENTS[@]}")
    ;;
  auto)
    for a in "${ALL_AGENTS[@]}"; do
      if "install_$a" 2>/dev/null; then
        AGENTS_TO_INSTALL+=("$a")
      fi
    done
    echo ""
    echo "Done. ${#AGENTS_TO_INSTALL[@]} agent(s) updated. Restart to load."
    exit 0
    ;;
  *)
    if ! declare -f "install_$AGENT" &>/dev/null; then
      echo "Unknown agent: $AGENT. Valid: ${ALL_AGENTS[*]}"
      exit 1
    fi
    AGENTS_TO_INSTALL=("$AGENT")
    ;;
esac

echo "→ Installing onemap-sg-cli instructions for: ${AGENTS_TO_INSTALL[*]}"
echo ""

INSTALLED=0
for a in "${AGENTS_TO_INSTALL[@]}"; do
  if "install_$a"; then
    INSTALLED=$((INSTALLED + 1))
  fi
done

echo ""
echo "Done. $INSTALLED agent(s) updated. Restart your agent(s) to load."
