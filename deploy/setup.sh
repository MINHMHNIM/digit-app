#!/usr/bin/env bash
set -euo pipefail

THU_MUC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NGUOI_DUNG="$(id -un)"
TEN_DICH_VU="digit-app"

echo "==> [1/5] Cai Python va cong cu can thiet"
sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get update -y
sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y python3-venv python3-pip curl

echo "==> [2/5] Tao moi truong ao va cai thu vien"
python3 -m venv "$THU_MUC/.venv"
"$THU_MUC/.venv/bin/pip" install --upgrade pip
"$THU_MUC/.venv/bin/pip" install -r "$THU_MUC/requirements.txt"

echo "==> [3/5] Huan luyen model"
cd "$THU_MUC"
"$THU_MUC/.venv/bin/python" -m app.model

echo "==> [4/5] Dang ky app thanh dich vu he thong (tu chay khi may khoi dong)"
sed -e "s|__THU_MUC__|$THU_MUC|g" -e "s|__NGUOI_DUNG__|$NGUOI_DUNG|g" \
  "$THU_MUC/deploy/$TEN_DICH_VU.service" | sudo tee "/etc/systemd/system/$TEN_DICH_VU.service" > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable "$TEN_DICH_VU"
sudo systemctl restart "$TEN_DICH_VU"

echo "==> [5/5] Kiem tra app"
for lan in $(seq 1 20); do
  if curl -fs http://localhost/health > /dev/null; then
    break
  fi
  sleep 1
done
if ! curl -fs http://localhost/health > /dev/null; then
  echo "App chua chay duoc. Xem log bang lenh: sudo journalctl -u $TEN_DICH_VU -n 50"
  exit 1
fi

TOKEN="$(curl -fs -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || true)"
IP_CONG_KHAI="$(curl -fs -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 || echo '<IP-cong-khai-cua-may>')"

echo
echo "Deploy xong! Mo trinh duyet va vao: http://$IP_CONG_KHAI"
