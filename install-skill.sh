#!/usr/bin/env bash
# Legacy wrapper: install onemap-sg-cli skill for Hermes.
# Use install-agent.sh for multi-agent support.
exec bash -c "$(curl -sSL https://raw.githubusercontent.com/samuelncui/onemap-sg-cli/main/install-agent.sh)" - hermes
