#!/usr/bin/env bash
# Static validation of everything Argo CD would apply. Runs in CI and locally; needs helm, kubectl (for kustomize), kubeconform.
set -euo pipefail
cd "$(dirname "$0")/.."

K8S_VERSION=${K8S_VERSION:-1.33.0}
CRD_SCHEMAS='https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json'
kc() {
  kubeconform -strict -summary -kubernetes-version "$K8S_VERSION" \
    -schema-location default -schema-location "$CRD_SCHEMAS" "$@"
}
source scripts/lib.sh

echo "== lint"
helm lint --strict charts/service -f apps/api-gateway/values.yaml -f envs/dev/values.yaml
for env in dev prod; do helm lint --strict gitops/apps -f "gitops/apps/values-$env.yaml"; done

for env in dev prod; do
  for values in apps/*/values.yaml; do
    svc=$(basename "$(dirname "$values")")
    echo "== $svc ($env)"
    helm template "$svc" charts/service -n shop -f "$values" -f "envs/$env/values.yaml" | kc
  done

  echo "== app-of-apps ($env)"
  helm template platform gitops/apps -f "gitops/apps/values-$env.yaml" | kc

  while read -r name repo version _; do
    echo "== add-on $name $version ($env)"
    files=(-f "platform/$name/values.yaml")
    [[ -f platform/$name/values.yaml ]] || files=()
    [[ -f platform/$name/values-$env.yaml ]] && files+=(-f "platform/$name/values-$env.yaml")
    helm template "$name" "$name" --repo "$repo" --version "$version" -n "$name" "${files[@]}" | kc
  done < <(addons)
done

for dir in platform/mongodb platform/dashboards; do
  echo "== $dir"
  kubectl kustomize "$dir" | kc
done

echo "== bootstrap"
kc gitops/bootstrap/root-*.yaml
