#!/usr/bin/env bash
# Local dev cluster WITHOUT Argo CD: kind + ingress-nginx + MongoDB + the four services built from this checkout.
# It installs the same charts and values Argo CD would, so what works here works under GitOps.
#   scripts/up.sh            core (what CI runs)
#   OBS=1 scripts/up.sh      also kube-prometheus-stack, Tempo and the OpenTelemetry Collector
# Needs: docker, kind, kubectl, helm, openssl.  Tear down with: kind delete cluster --name shop
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/lib.sh

CLUSTER=${CLUSTER:-shop}
TAG=${TAG:-local}

kind get clusters | grep -qx "$CLUSTER" || kind create cluster --name "$CLUSTER" --config kind/kind-config.yaml
kubectl config use-context "kind-$CLUSTER"

addon() { # name [helm args]: install the pinned chart with the dev values, exactly as the app-of-apps would
  local name repo version ns files=()
  read -r name repo version ns < <(addons | grep "^$1 ")
  shift
  [[ -f platform/$name/values.yaml ]] && files+=(-f "platform/$name/values.yaml")
  [[ -f platform/$name/values-dev.yaml ]] && files+=(-f "platform/$name/values-dev.yaml")
  helm upgrade --install "$name" "$name" --repo "$repo" --version "$version" -n "$ns" --create-namespace \
    "${files[@]}" "$@" --wait --timeout 10m
}

echo "== images"
for values in apps/*/values.yaml; do
  svc=$(basename "$(dirname "$values")")
  image="$(awk '/repository:/{print $2}' "$values"):$TAG"
  docker build -q -f apps/Dockerfile -t "$image" "apps/$svc"
  kind load docker-image "$image" --name "$CLUSTER"
done

echo "== platform"
scripts/secrets.sh
# The monitoring CRDs must exist before anything asks for a ServiceMonitor: install the stack first, or turn it off.
if [[ -n ${OBS:-} ]]; then
  addon kube-prometheus-stack
  addon ingress-nginx
else
  addon ingress-nginx --set controller.metrics.serviceMonitor.enabled=false
fi
addon metrics-server
if [[ -n ${OBS:-} ]]; then addon tempo; addon opentelemetry-collector; fi
kubectl apply -k platform/mongodb
kubectl -n data rollout status statefulset/mongodb --timeout=5m
[[ -n ${OBS:-} ]] && kubectl apply -k platform/dashboards

echo "== services"
# ServiceMonitor/PrometheusRule are CRDs of the monitoring stack: only render them when it is installed.
obs=(--set serviceMonitor.enabled=false --set slo.enabled=false)
[[ -n ${OBS:-} ]] && obs=(--set serviceMonitor.enabled=true)
for values in apps/*/values.yaml; do
  svc=$(basename "$(dirname "$values")")
  helm upgrade --install "$svc" charts/service -n shop -f "$values" -f envs/dev/values.yaml \
    --set image.tag="$TAG" "${obs[@]}" --wait --timeout 5m
done

curl -fsS --retry 30 --retry-delay 2 --retry-connrefused http://localhost/healthz >/dev/null
echo "ready: http://localhost/api/products  (smoke test: k6 run k6/smoke.js)"
