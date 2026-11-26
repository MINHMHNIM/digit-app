#!/usr/bin/env bash
set -euo pipefail

THU_MUC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$THU_MUC"

echo "==> Lay code moi tu GitHub"
git pull

echo "==> Cai them thu vien neu co thay doi"
"$THU_MUC/.venv/bin/pip" install -r requirements.txt

echo "==> Huan luyen lai model va khoi dong lai app"
"$THU_MUC/.venv/bin/python" -m app.model
sudo systemctl restart digit-app

sleep 2
sudo systemctl --no-pager status digit-app | head -n 5 || true
