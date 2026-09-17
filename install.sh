#!/usr/bin/env bash
# Contributor helper: symlink skills/kilo into agent dirs.
# End users should prefer: npx skills add kl7sn/kilo -g
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

install_skill() {
  local name="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  ln -sfn "$ROOT/skills/$name" "$dest"
  echo "linked $dest -> $ROOT/skills/$name"
}

install_agent() {
  local base="$1"
  install_skill kilo "$base/kilo"
}

case "${1:-}" in
  cursor)
    install_agent "$HOME/.cursor/skills"
    ;;
  claude)
    install_agent "$HOME/.claude/skills"
    ;;
  codex)
    install_agent "$HOME/.codex/skills"
    ;;
  agents)
    install_agent "$HOME/.agents/skills"
    ;;
  all)
    install_agent "$HOME/.cursor/skills"
    install_agent "$HOME/.claude/skills"
    install_agent "$HOME/.codex/skills"
    install_agent "$HOME/.agents/skills"
    ;;
  *)
    echo "Usage: $0 {cursor|claude|codex|agents|all}"
    echo "Installs skills/kilo as a symlink into the agent skills directory."
    exit 1
    ;;
esac
