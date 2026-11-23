#!/usr/bin/env bash
# Manual Tencent-host pilot. Writes only to dedicated test image repositories.
set -euo pipefail
umask 077
if [[ $# != 3 || ! $1 =~ ^[0-9a-f]{40}$ || ! $2 =~ ^[1-9][0-9]*$ || ! $3 =~ ^(frontend|backend|all|source-only)$ ]]; then
  echo 'Usage: tencent_pilot.sh FULL_MASTER_SHA MASTER_PUSH_RUN_ID frontend|backend|all|source-only' >&2
  exit 2
fi
sha=$1 run=$2 selected=$3
repo=$HOME/cs-career-guide-pilot.git
origin=git@cs-career-tcr-github:vacontinuejatotired/CS-Career-Guide.git
ssh_config=$HOME/.ssh/cs_career_tcr_github_config
[[ -f $ssh_config && -r $ssh_config ]] || { echo 'Missing dedicated GitHub SSH config' >&2; exit 1; }
export GIT_SSH_COMMAND='ssh -F "$HOME/.ssh/cs_career_tcr_github_config"'
cfg=$HOME/.docker-tcr-pilot
registry=ccr.ccs.tencentyun.com
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
exec 9>"$HOME/.cs-career-tcr-pilot.lock"
flock -n 9 || { echo 'Another pilot is active' >&2; exit 1; }
timeout 55 python3 -B "$script_dir/tencent_pilot_gate.py" "$sha" "$run"
G() { git --git-dir="$repo" "$@"; }
D() { sudo -n docker "$@"; }
T() { sudo -n timeout -k 10 "$1" docker --config "$cfg" "${@:2}"; }
GIT_TERMINAL_PROMPT=0 timeout -k 5 90 git --git-dir="$repo" -c protocol.version=2 \
  fetch --no-tags "$origin" refs/heads/master:refs/remotes/origin/master
[[ $(G rev-parse 'refs/remotes/origin/master^{commit}') == "$sha" ]] || {
  echo 'Requested SHA is not the fetched master tip; stop' >&2; exit 1;
}
work=$(mktemp -d /tmp/cs-tcr-pilot.XXXXXXXX)
builder=cs-tcr-pilot-${work##*.}
container=
builder_initialized=false
cleanup() {
  if [[ -n $container ]]; then D rm -f "$container" >/dev/null 2>&1 || :; fi
  if "$builder_initialized"; then D buildx rm "$builder" >/dev/null 2>&1 || :; fi
  if [[ -d $work/source ]]; then G worktree remove --force "$work/source" || :; fi
  rm -f -- "$work/buildkit.toml" "$work/push.log" "$work/page.html"
  rmdir -- "$work" || :
}
trap cleanup EXIT
# The parent is 0700; runtime users still need to read files copied into images.
( umask 022; G worktree add -q --detach "$work/source" "$sha" )
[[ $(stat -c '%a' "$work/source/frontend/nginx.conf") == 644 ]] || {
  echo 'Unexpected checkout permissions for frontend/nginx.conf' >&2; exit 1;
}
if [[ $selected == source-only ]]; then
  printf 'PILOT_SOURCE_VERIFIED %s %s\n' "$sha" "$run"
  exit 0
fi
cat >"$work/buildkit.toml" <<'TOML'
[registry."docker.io"]
  mirrors = ["mirror.ccs.tencentyun.com"]
[worker.oci]
  max-parallelism = 2
TOML
builder_initialized=true
D buildx create --name "$builder" --driver docker-container \
  --driver-opt image=mirror.ccs.tencentyun.com/moby/buildkit:buildx-stable-1,memory=2g,cpu-period=100000,cpu-quota=200000 \
  --buildkitd-config "$work/buildkit.toml"
components=("$selected")
[[ $selected != all ]] || components=(frontend backend)
for component in "${components[@]}"; do
  image=cs-career-guide-$component-pilot:sha-$sha
  container=$builder-$component
  build_args=()
  runtime_args=(--memory 96m --cpus .25 -p 127.0.0.1::8080)
  if [[ $component == backend ]]; then
    build_args=(--build-arg USE_TENCENT_BUILD_MIRRORS=1)
    runtime_args=(--memory 512m --cpus .5 -e SECRET_KEY=pilot-only-key
      -e ALLOWED_HOSTS=localhost,127.0.0.1 -e DJANGO_SETTINGS_MODULE=cs_career_guide.settings_sqlite
      -e DB_PATH=/tmp/cs-career-guide.sqlite3 -e STATIC_ROOT=/tmp/staticfiles
      -e MEDIA_ROOT=/tmp/media -e LANCEDB_PATH=/tmp/lancedb)
  fi
  time sudo -n timeout -k 10 720 docker buildx build --builder "$builder" --platform linux/amd64 \
    --load --progress plain --provenance=false --sbom=false -t "$image" \
    "${build_args[@]}" "$work/source/$component"
  D run -d --name "$container" --cap-drop ALL --security-opt no-new-privileges \
    "${runtime_args[@]}" "$image" >/dev/null
  if [[ $component == backend ]]; then
    for ((i=0; i<90; i++)); do
      state=$(D inspect --format '{{.State.Status}} {{.State.Health.Status}}' "$container")
      case $state in
        'running healthy') break ;;
        'exited '*|*' unhealthy') break ;;
      esac
      sleep 2
    done
    [[ $state == 'running healthy' ]] || { D logs --tail 30 "$container"; exit 1; }
  else
    base=http://$(D port "$container" 8080/tcp)
    for ((i=0; i<30; i++)); do
      curl -fsS --max-time 3 "$base/" -o "$work/page.html" && break
      sleep 1
    done
    grep -Fq '<div id="app"></div>' "$work/page.html"
    curl -fsS --max-time 5 "$base/login" -o "$work/page.html"
    grep -Fq '<div id="app"></div>' "$work/page.html"
    [[ $(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$base/api/") == 404 ]]
    [[ $(curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$base/company-api") == 503 ]]
    curl -fsS --max-time 10 "$base/models/vad/silero_vad_legacy.onnx" -o /dev/null
  fi
  D rm -f "$container" >/dev/null
  container=
  target=$registry/cs-career-guide-pilot/$component-pilot
  tagged=$target:sha-$sha
  expected=$(D image inspect --format '{{.Id}}' "$image")
  D tag "$image" "$tagged"
  time T 300 push "$tagged" | tee "$work/push.log"
  digest=$(sed -nE 's/.*digest: (sha256:[0-9a-f]{64}) .*/\1/p' "$work/push.log" | sort -u)
  [[ $digest =~ ^sha256:[0-9a-f]{64}$ ]]
  time T 120 pull "$target@$digest"
  [[ $(D image inspect --format '{{.Id}}' "$target@$digest") == "$expected" ]]
  if [[ -n ${CS_CAREER_TCR_RECEIPT_FILE:-} ]]; then
    printf '%s %s@%s\n' "$component" "$target" "$digest" >> "$CS_CAREER_TCR_RECEIPT_FILE"
  fi
  printf 'PILOT_VERIFIED %s %s %s@%s\n' "$sha" "$component" "$target" "$digest"
done
