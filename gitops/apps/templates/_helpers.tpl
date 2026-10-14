{{- define "app.header" -}}
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {{ .name }}
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: {{ .wave | quote }}
  finalizers:
    - resources-finalizer.argocd.argoproj.io
{{- end -}}

{{- define "app.syncPolicy" -}}
destination:
  server: https://kubernetes.default.svc
  namespace: {{ .app.namespace }}
syncPolicy:
  {{- if .root.Values.autoSync }}
  automated:
    prune: true
    selfHeal: true
  {{- end }}
  syncOptions:
    - CreateNamespace=true
    {{- if .app.serverSideApply }}
    - ServerSideApply=true
    {{- end }}
{{- end -}}
