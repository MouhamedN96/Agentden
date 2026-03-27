#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$HOME/.config/systemd/user"
cp templates/systemd/personal-agentd.service "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now personal-agentd
systemctl --user status personal-agentd --no-pager
