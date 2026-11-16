#!/usr/bin/env bash
# Keeps the server in step with GitHub: if the branch the server runs (main) has new
# commits, it updates the code and restarts the website. Run every 5 minutes by the
# ar-cooling-update timer (installed by setup.sh), so a push goes live within minutes.
#
#   Run it now:     sudo systemctl start ar-cooling-update
#   See its log:    sudo journalctl -u ar-cooling-update -n 20
#
# Covers code, templates, static files and social posts. Changes to the server setup
# itself (Caddyfile, ar-cooling.service, new system packages) still need setup.sh.
set -euo pipefail

APP_DIR=/opt/ar-cooling

main() {   # inside a function, so updating this file mid-run is safe
  cd "$APP_DIR"
  local branch current latest old_requirements
  branch="$(git rev-parse --abbrev-ref HEAD)"
  git fetch -q origin "$branch"
  current="$(git rev-parse HEAD)"
  latest="$(git rev-parse "origin/$branch")"
  [[ "$current" == "$latest" ]] && exit 0

  old_requirements="$(git rev-parse HEAD:requirements.txt)"
  git checkout -q -B "$branch" "origin/$branch"
  if [[ "$(git rev-parse HEAD:requirements.txt)" != "$old_requirements" ]]; then
    "$APP_DIR/.venv/bin/pip" install -q -r requirements.txt
  fi
  systemctl restart ar-cooling
  echo "Updated $branch ${current:0:7} -> ${latest:0:7}: $(git log -1 --format=%s)"
}

main "$@"
