#!/usr/bin/env bash
# Creates the namespaces and the three Secrets the platform expects, only if they do not exist yet
# (MongoDB reads its passwords once, on first start, so they must stay stable across runs).
# In a real cluster these come from a secret manager (External Secrets / Sealed Secrets), never from git.
set -euo pipefail

for ns in shop data; do kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -; done
pw() { openssl rand -hex 16; }

if ! kubectl -n data get secret mongodb-auth >/dev/null 2>&1; then
  u=$(pw) p=$(pw) o=$(pw)
  kubectl -n data create secret generic mongodb-auth --from-literal=root-password="$(pw)" \
    --from-literal=user-service="$u" --from-literal=product-service="$p" --from-literal=order-service="$o"
  kubectl -n shop create secret generic mongodb-credentials \
    --from-literal=user-service="$u" --from-literal=product-service="$p" --from-literal=order-service="$o"
fi
kubectl -n shop get secret jwt >/dev/null 2>&1 || kubectl -n shop create secret generic jwt --from-literal=secret="$(pw)"
