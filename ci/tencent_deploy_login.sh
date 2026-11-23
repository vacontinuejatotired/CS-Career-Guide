#!/usr/bin/env bash
# Interactive TCR credential setup. Does not recreate services or modify ACR credentials.
set -euo pipefail
umask 077
if (( EUID != 0 )) || [[ $# != 3 || ! $1 =~ ^[0-9]+$ || ! $2 =~ ^sha256:[0-9a-f]{64}$ || ! $3 =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo 'Usage: sudo bash tencent_deploy_login.sh TCR_USERNAME FRONTEND_DIGEST BACKEND_DIGEST' >&2
  exit 2
fi
registry=ccr.ccs.tencentyun.com
base=/etc/cs-career-guide
config=$base/tcr
install -d -m 0755 "$base"
install -d -o csdeploy -g csdeploy -m 0700 "$config"
exec 9>"$base/.tcr-login.lock"
flock -n 9 || { echo 'TCR credential setup is already running' >&2; exit 1; }
staging=$(mktemp -d "$base/.tcr-login.XXXXXXXX")
cleanup() { rm -f -- "$staging/config.json"; rmdir -- "$staging"; }
trap cleanup EXIT
chown csdeploy:csdeploy "$staging"
read -rsp 'TCR registry password: ' password
printf '\n'
[[ -n $password ]]
printf '%s\n' "$password" | sudo -H -u csdeploy docker --config "$staging" login "$registry" --username "$1" --password-stdin
unset password
for component in frontend backend; do
  if [[ $component == frontend ]]; then digest=$2; else digest=$3; fi
  ref="$registry/cs-career-guide-pilot/$component-pilot@$digest"
  sudo -H -u csdeploy timeout 120 docker --config "$staging" pull "$ref"
  printf 'DEPLOY_TCR_PULL_OK %s %s\n' "$component" "$digest"
done
sudo -H -u csdeploy chmod 0600 "$staging/config.json"
sudo -H -u csdeploy mv -T -- "$staging/config.json" "$config/config.json"
echo 'DEPLOY_TCR_CREDENTIAL_SAVED'
