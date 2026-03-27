#!/usr/bin/env bash
set -euo pipefail
command -v cargo >/dev/null && cargo --version || echo "cargo missing"
command -v codex >/dev/null && codex --help >/dev/null && echo "codex ok" || echo "codex missing"
command -v claude >/dev/null && echo "claude ok" || echo "claude missing"
