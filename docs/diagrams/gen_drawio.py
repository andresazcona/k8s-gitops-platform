#!/usr/bin/env python3
"""Generates k8s-gitops-platform.drawio (3 pages). Python 3 stdlib only.

    python docs/diagrams/gen_drawio.py
    node drawio-export.js docs/diagrams/k8s-gitops-platform.drawio docs/diagrams
"""
import os
from xml.sax.saxutils import quoteattr

K8S = "#326CE5"
ARGO, PROM, GRAFANA, OTEL, TEMPO, K6, GHA, MONGO = (
    "#EF7B4D", "#E6522C", "#F5A800", "#425CC7", "#0E9AA7", "#7D64FF", "#24292F", "#13AA52")
USER, CICD, DATA, WARN = "#326CE5", "#8C4FFF", "#13AA52", "#B3261E"   # edge colors by flow
GREY = "#6B7280"

TITLE = "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;"


def lbl(name, detail=""):
    d = f'<br><span style="font-size:10px;opacity:0.85;">{detail}</span>' if detail else ""
    return f"<b>{name}</b>{d}"


class Page:
    def __init__(self, name, w=1900, h=1200):
        self.name, self.w, self.h = name, w, h
        self.cells, self.n, self.origin = [], 2, {}

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def add(self, value, style, x, y, w, h, parent=None):
        """x, y are absolute; they are stored relative to `parent` so groups stay movable."""
        cid, ox, oy = self._id(), 0, 0
        if parent:
            ox, oy = self.origin[parent]
        self.origin[cid] = (x, y)
        self.cells.append(
            f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(style)} vertex="1" parent="{parent or "1"}">'
            f'<mxGeometry x="{x - ox}" y="{y - oy}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def title(self, main, sub):
        self.add(f'<b style="font-size:20px;">{main}</b><br><span style="font-size:12px;color:#666;">{sub}</span>',
                 TITLE, 0, 8, self.w, 52)

    def group(self, text, x, y, w, h, fill, stroke, icon=True, color=None, size=12):
        """Dashed rounded container; optional Kubernetes `ns` icon next to the caption."""
        gid = self.add(text, "rounded=1;dashed=1;dashPattern=8 4;arcSize=3;verticalAlign=top;align=left;html=1;"
                       f"fontStyle=1;fontSize={size};fontColor={color or stroke};fillColor={fill};strokeColor={stroke};"
                       f"strokeWidth=1.5;spacingLeft={40 if icon else 12};spacingTop=8;whiteSpace=wrap;", x, y, w, h)
        if icon:
            self.k8s("ns", x + 8, y + 6, 26, parent=gid)
        return gid

    def k8s(self, kind, x, y, size=50, label="", parent=None, below=True):
        pos = "verticalLabelPosition=bottom;verticalAlign=top;" if below else "verticalLabelPosition=middle;verticalAlign=middle;"
        style = ("html=1;dashed=0;fillColor=#326CE5;strokeColor=#ffffff;fontColor=#232F3E;fontSize=11;align=center;"
                 "points=[[0.005,0.63,0],[0.1,0.2,0],[0.9,0.2,0],[0.5,0,0],[0.995,0.63,0],[0.72,0.99,0],[0.5,1,0],[0.28,0.99,0]];"
                 f"{pos}shape=mxgraph.kubernetes.icon;prIcon={kind};")
        return self.add(label, style, x, y, size, round(size * 0.96), parent)

    def tile(self, text, x, y, w, h, fill, font="#ffffff", icon=None, parent=None, size=12, stroke="none", align="center"):
        """Rounded box; with `icon` a Kubernetes icon sits inside on the left."""
        extra = 46 if icon else 6
        style = (f"rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor={fill};strokeColor={stroke};fontColor={font};"
                 f"fontSize={size};align={align};verticalAlign=middle;spacingLeft={extra};spacingRight=6;")
        tid = self.add(text, style, x, y, w, h, parent)
        if icon:
            self.k8s(icon, x + 8, y + h / 2 - 17, 36, parent=tid)
        return tid

    def note(self, text, x, y, w, h, size=11):
        return self.add(text, "rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor=#f5f5f5;strokeColor=#CCCCCC;"
                        f"fontColor=#333333;fontSize={size};align=left;verticalAlign=top;spacing=8;", x, y, w, h)

    def edge(self, src, tgt, label="", color=USER, dashed=False, width=2, via=(), exit=None, entry=None, size=10):
        ids = self._id()
        st = ("edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;"
              f"strokeColor={color};strokeWidth={width};fontSize={size};fontColor={color};labelBackgroundColor=#ffffff;")
        if dashed:
            st += "dashed=1;dashPattern=6 4;"
        if exit:
            st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry:
            st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in via)
        arr = f'<Array as="points">{pts}</Array>' if via else ""
        self.cells.append(f'<mxCell id="{ids}" value={quoteattr(label)} style={quoteattr(st)} edge="1" parent="1" '
                          f'source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')

    def xml(self):
        body = "".join(self.cells)
        return (f'<diagram name={quoteattr(self.name)} id="{self.name.lower().replace(" ", "-")}">'
                f'<mxGraphModel dx="1500" dy="900" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
                f'fold="1" page="1" pageScale="1" pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram>')


def legend(p, x, y):
    p.note("<b>Legend</b>", x, y, 240, 128)
    for i, (c, d, t) in enumerate([(USER, False, "user traffic"), (DATA, False, "data (MongoDB)"),
                                    (GREY, True, "telemetry / scrape")]):
        a = p.add("", "ellipse;fillColor=none;strokeColor=none;", x + 14, y + 38 + i * 28, 1, 1)
        b = p.add("", "ellipse;fillColor=none;strokeColor=none;", x + 74, y + 38 + i * 28, 1, 1)
        p.edge(a, b, "", c, d, 2)
        p.add(t, "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontColor=#333;",
              x + 88, y + 28 + i * 28, 140, 20)


# ---------------------------------------------------------------- page 1
def cluster():
    p = Page("1 Cluster architecture")
    p.title("Cluster architecture", "ingress-nginx · Argo CD · Node.js microservices · MongoDB · OpenTelemetry · Prometheus · Grafana · Tempo")
    p.add("Kubernetes cluster · kind in CI and locally (single node, v1.33) · the same manifests run on EKS / GKE",
          "rounded=1;dashed=1;dashPattern=10 5;arcSize=2;verticalAlign=top;align=left;html=1;fontStyle=1;fontSize=13;"
          f"fontColor={K8S};fillColor=#FAFBFF;strokeColor={K8S};strokeWidth=2;spacingLeft=14;spacingTop=6;", 180, 76, 1700, 1100)

    client = p.tile(lbl("Client", "browser · curl · k6"), 20, 150, 140, 64, "#ffffff", font="#232F3E", stroke="#999999")

    # left column
    p.group("ingress-nginx", 210, 110, 260, 130, "#E8F8E8", "#82B366", color="#3B6E22")
    ctrl = p.tile(lbl("ingress-nginx controller", "hostPort 80 / 443"), 228, 165, 224, 64, "#ffffff", font="#232F3E", icon="pod", stroke=K8S)
    p.group("kube-system", 210, 270, 260, 130, "#F0F0F0", "#888888", color="#555555")
    p.tile(lbl("metrics-server", "CPU metrics for the HPAs"), 228, 320, 224, 64, "#ffffff", font="#232F3E", icon="pod", stroke=K8S)
    p.group("argocd", 210, 430, 260, 130, "#FDEBE3", ARGO, color="#B4491D")
    p.tile(lbl("Argo CD", "app-of-apps · sync waves"), 228, 480, 224, 64, ARGO)
    legend(p, 210, 600)

    # shop
    shop = p.group("shop  (the four services, one reusable chart)", 520, 110, 800, 370, "#EAF1FF", K8S)
    ing = p.k8s("ing", 585, 175, 46, "Ingress", parent=shop)
    gw = p.tile(lbl("api-gateway", "Deployment · :3000 · /api/*"), 815, 165, 190, 64, "#ffffff", font="#232F3E", icon="deploy", stroke=K8S)
    p.note("<b>charts/service</b> renders per service: Deployment, Service, HPA, PDB, NetworkPolicy, ServiceMonitor "
           "(+ PrometheusRule on the gateway).", 1035, 150, 265, 90)
    user = p.tile(lbl("user-service", "register · login · JWT"), 545, 290, 190, 64, "#ffffff", font="#232F3E", icon="deploy", stroke=K8S)
    prod = p.tile(lbl("product-service", "catalog (public reads)"), 825, 290, 190, 64, "#ffffff", font="#232F3E", icon="deploy", stroke=K8S)
    order = p.tile(lbl("order-service", "orders priced from catalog"), 1105, 290, 190, 64, "#ffffff", font="#232F3E", icon="deploy", stroke=K8S)
    p.k8s("secret", 755, 385, 32, "Secret: mongodb-credentials", parent=shop)
    p.k8s("secret", 1035, 385, 32, "Secret: jwt (HS256)", parent=shop)

    # data
    data = p.group("data", 520, 505, 800, 215, "#FFF4E0", "#D79B00", color="#8A5A00")
    mongo = p.tile(lbl("MongoDB 8.0 · StatefulSet, 1 replica",
                       "database + readWrite user per service: users · products · orders"), 560, 550, 720, 70, MONGO, icon="sts")
    p.k8s("pvc", 600, 628, 32, "PVC 2Gi", parent=data)
    p.k8s("secret", 740, 628, 32, "Secret: mongodb-auth", parent=data)
    p.note("<b>NetworkPolicy</b>: only namespace shop may connect (:27017).", 990, 632, 290, 64)

    # observability
    obs = p.group("observability", 1440, 110, 420, 1030, "#F3EAFB", "#9673A6", color="#5E3F7A")
    col = p.tile(lbl("OpenTelemetry Collector", "OTLP :4318 · k8s_attributes · batch"), 1470, 190, 360, 70, OTEL)
    tempo = p.tile(lbl("Grafana Tempo", "traces · single binary · 72h retention"), 1470, 340, 360, 70, TEMPO)
    graf = p.tile(lbl("Grafana", "RED + SLO dashboard · Tempo datasource"), 1470, 490, 250, 70, GRAFANA, font="#232F3E")
    p.k8s("cm", 1760, 495, 36, "ConfigMap<br>dashboard", parent=obs)
    prom = p.tile(lbl("Prometheus", "ServiceMonitor scrape :9464 · SLO rules"), 1470, 700, 360, 70, PROM)
    am = p.tile(lbl("Alertmanager", "ErrorBudgetFastBurn · LatencySLOBreach"), 1470, 850, 360, 70, "#B3261E")
    p.note("<b>kube-prometheus-stack 92.3.1</b> also brings kube-state-metrics, node-exporter and the operator; "
           "ingress-nginx metrics are scraped too.", 1470, 960, 360, 80)

    # bottom center notes
    p.note("<b>Per-service chart</b><br>Deployment + Service (:80 to :3000)<br>HPA on CPU (dev 1-4, prod 3-12)<br>"
           "PodDisruptionBudget<br>ServiceMonitor on :9464 (OTel Prometheus exporter)<br>PrometheusRule (SLO) on the gateway<br>"
           "NetworkPolicy: default deny + explicit peers", 520, 750, 250, 190)
    p.note("<b>Hardening</b><br>non-root uid 1000, seccomp RuntimeDefault<br>read-only root fs, drop ALL capabilities<br>"
           "no service-account token<br>RollingUpdate maxUnavailable 0<br>preStop sleep 5s (no dropped requests)<br>"
           "topology spread across nodes (prod)", 795, 750, 250, 190)
    p.note("<b>dev vs prod</b><br>dev: 1-4 replicas, 50m CPU request<br>auto-sync, prune, self-heal<br>"
           "prod: 3-12 replicas, 250m CPU request<br>manual sync, 1 pod max unavailable<br>host: shop.example.com", 1070, 750, 250, 190)
    p.note("<b>Why a gateway</b>: one public entry point; user, product and order services are cluster-internal. "
           "order-service calls product-service synchronously so prices never come from the client.", 520, 960, 800, 70, 11)

    # edges (declared last, drawn on top)
    p.edge(client, ctrl, "", USER, exit=(1, 0.5), entry=(0, 0.5))
    p.edge(ctrl, ing, "", USER)
    p.edge(ing, gw, "/", USER)
    p.edge(gw, prod, "", USER)
    p.edge(gw, user, "", USER, exit=(0.5, 1), entry=(0.5, 0))
    p.edge(gw, order, "", USER, exit=(0.5, 1), entry=(0.5, 0))
    p.edge(order, prod, "price<br>lookup", USER, exit=(0, 0.5), entry=(1, 0.5))
    for src, ex in ((user, 640 - 560), (prod, 920 - 560), (order, 1200 - 560)):
        p.edge(src, mongo, "mongodb :27017" if src == prod else "", DATA, exit=(0.5, 1), entry=(ex / 720, 0))
    p.edge(shop, col, "OTLP<br>:4318", GREY, dashed=True, exit=(1, 0.31), entry=(0, 0.5))
    p.edge(shop, prom, "scrape<br>:9464", GREY, dashed=True, exit=(1, 0.92), entry=(0, 0.5), via=[(1380, 450), (1380, 735)])
    p.edge(col, tempo, "OTLP :4317", GREY, dashed=True)
    p.edge(tempo, graf, "TraceQL", GREY, dashed=True, exit=(0.35, 1), entry=(0.5, 0))
    p.edge(prom, graf, "PromQL", GREY, dashed=True, exit=(0.35, 0), entry=(0.5, 1))
    p.edge(prom, am, "alerts", WARN, dashed=True)
    return p


# ---------------------------------------------------------------- page 2
def gitops():
    p = Page("2 GitOps delivery flow")
    p.title("GitOps delivery flow", "GitHub Actions · GHCR · Argo CD app-of-apps · dev auto-sync · prod manual sync")
    dev = p.tile(lbl("Developer", "feature branch / pull request"), 20, 165, 180, 70, "#ffffff", font="#232F3E", stroke="#999999")
    repo = p.tile(lbl("GitHub repo (main)", "andresazcona/k8s-gitops-platform<br>charts · apps · envs · gitops · platform"),
                  290, 140, 230, 120, "#ffffff", font="#232F3E", stroke=GHA)

    act = p.group("GitHub Actions · ci.yml, promote.yml (no cloud credentials)", 620, 110, 700, 340, "#F6F8FA", GHA, icon=False)
    unit = p.tile(lbl("unit", "node --test x4"), 635, 160, 150, 64, GHA, parent=act)
    val = p.tile(lbl("validate", "helm lint + template<br>kubeconform -strict"), 810, 160, 150, 64, GHA, parent=act)
    e2e = p.tile(lbl("e2e", "kind + docker build<br>helm install + k6 smoke"), 985, 160, 150, 64, GHA, parent=act)
    rel = p.tile(lbl("release (main only)", "build + push :sha<br>bump envs/dev tag"), 1160, 160, 150, 64, GHA, parent=act)
    p.note("Pull requests run unit + validate + e2e. Only a push to main also runs release. "
           "Images are built once and tagged with the commit SHA (immutable).", 635, 260, 360, 66)
    prom_job = p.tile(lbl("promote (manual dispatch)", "opens a PR: envs/prod tag := dev tag"), 1010, 350, 300, 70, GHA, parent=act)
    for a, b in ((unit, val), (val, e2e), (e2e, rel)):
        p.edge(a, b, "", GHA, width=2)

    ghcr = p.tile(lbl("GHCR", "ghcr.io/andresazcona/<br>k8s-gitops-platform/&lt;svc&gt;:&lt;sha&gt;"), 1440, 150, 260, 90, "#0969DA")

    # dev cluster
    dv = p.group("Dev cluster · automated sync (prune + self-heal)", 60, 540, 860, 600, "#F2F7FF", K8S, icon=False)
    dargo = p.tile(lbl("Argo CD", "polls git ~3 min (or webhook)"), 90, 620, 250, 70, ARGO)
    droot = p.tile(lbl("platform-dev", "root Application · gitops/apps<br>values-dev.yaml: autoSync = true"), 90, 740, 250, 80, "#ffffff", font="#232F3E", stroke=ARGO, icon="ns")
    p.note("<b>AppProject shop</b> (wave -10) allows only this repo + the pinned chart repos and the namespaces "
           "shop, data, observability, ingress-nginx, kube-system.", 90, 860, 250, 100)
    p.note("Child Applications start only when the previous wave is Healthy (custom Application health check in "
           "gitops/bootstrap/argocd-values.yaml).", 90, 980, 250, 100)
    waves = [("-3", "kube-prometheus-stack · metrics-server", "CRDs + metrics first"),
             ("-2", "ingress-nginx · tempo", "entry + trace backend"),
             ("-1", "opentelemetry-collector", "needs Tempo"),
             ("0", "mongodb · dashboards", "data layer, Grafana CM"),
             ("1", "user-service · product-service", "need MongoDB"),
             ("2", "order-service", "calls product-service"),
             ("3", "api-gateway", "last: routes to the rest")]
    wave_ids = []
    for i, (w, names, why) in enumerate(waves):
        y = 620 + i * 66
        wave_ids.append(p.tile(f'<b>wave {w}</b>  {names}<br><span style="font-size:10px;color:#444;">{why}</span>',
                               400, y, 490, 54, "#ffffff", font="#232F3E", stroke=K8S, align="left"))
    for a, b in zip(wave_ids, wave_ids[1:]):
        p.edge(a, b, "", K8S, width=1.5)
    p.tile("<b>Healthy dev</b>: 4 services, HPA 1-4, SLO rules loaded", 400, 1090, 490, 36, "#D5E8D4", font="#232F3E", stroke="#82B366", size=11)
    p.edge(dargo, droot, "", ARGO)

    # prod cluster
    pv = p.group("Prod cluster · manual sync (OutOfSync until reviewed)", 1000, 540, 840, 600, "#F2FAF2", "#82B366", icon=False, color="#3B6E22")
    pargo = p.tile(lbl("Argo CD", "same app-of-apps, other cluster"), 1030, 620, 260, 70, ARGO)
    proot = p.tile(lbl("platform-prod", "root Application · gitops/apps<br>values-prod.yaml: autoSync = false"), 1030, 740, 260, 80, "#ffffff", font="#232F3E", stroke=ARGO, icon="ns")
    oos = p.tile(lbl("Applications: OutOfSync", "diff shows the new image tag"), 1030, 870, 260, 64, "#FFF2CC", font="#232F3E", stroke="#D6B656")
    rev = p.tile(lbl("Reviewer reads the diff, clicks Sync", "or: argocd app sync &lt;name&gt;"), 1030, 960, 260, 64, "#ffffff", font="#232F3E", stroke="#D6B656")
    p.note("<b>envs/prod/values.yaml</b><br>image tag (promoted from dev)<br>HPA 3-12 replicas at 65% CPU<br>"
           "requests 250m / 256Mi<br>topologySpread across nodes<br>PDB maxUnavailable 1<br>host shop.example.com", 1340, 620, 270, 150)
    p.note("<b>Rollback</b> = git revert on main (dev) or on the promotion PR (prod); Argo CD converges to the previous tag.",
           1340, 800, 270, 90)
    p.note("<b>Same chart, same sync waves</b>: only envs/&lt;env&gt;/values.yaml and the autoSync flag differ.", 1340, 920, 270, 70)
    p.edge(pargo, proot, "", ARGO)
    p.edge(proot, oos, "", "#D6B656")
    p.edge(oos, rev, "", "#D6B656")

    # flow edges with numbers
    p.edge(dev, repo, "1  git push / PR", CICD)
    p.edge(repo, act, "2  triggers", CICD, exit=(1, 0.3), entry=(0, 0.2))
    p.edge(rel, ghcr, "3  docker push :sha", CICD, exit=(1, 0.5), entry=(0, 0.5))
    p.edge(rel, repo, "4  commit  deploy: dev -> sha", CICD, dashed=True, exit=(0.5, 0), entry=(0.5, 0), via=[(1235, 80), (405, 80)])
    p.edge(repo, dargo, "5  Argo CD sees new commit", ARGO, exit=(0.2, 1), entry=(0.5, 0), via=[(336, 500), (215, 500)])
    p.edge(prom_job, repo, "6  PR: promote to prod", CICD, dashed=True, exit=(0, 0.5), entry=(1, 0.8), via=[(570, 385), (570, 236)])
    p.edge(repo, pargo, "7  merge PR: prod OutOfSync", ARGO, exit=(0.8, 1), entry=(0.5, 0), via=[(474, 500), (1160, 500)])
    ok = p.tile("<b>Healthy prod</b>: waves roll out in order", 1030, 1070, 260, 40, "#D5E8D4", font="#232F3E", stroke="#82B366", size=11)
    p.edge(rev, ok, "8  manual Sync", "#B8860B", width=2)
    p.edge(ghcr, pv, "kubelets pull :sha", GREY, dashed=True, exit=(0.5, 1), entry=(0.85, 0))
    return p


# ---------------------------------------------------------------- page 3
def observability():
    p = Page("3 Observability and SLOs")
    p.title("Observability pipeline and SLOs", "OpenTelemetry auto-instrumentation · OTLP · Collector · Tempo · Prometheus · Grafana · alert rules")

    shop = p.group("shop namespace · Node.js 24 + @opentelemetry/auto-instrumentations-node (preloaded with --require)",
                   40, 90, 520, 560, "#EAF1FF", K8S)
    svcs = []
    for i, (n, d) in enumerate([("api-gateway", "http · express"), ("user-service", "http · express · mongodb · mongoose"),
                                ("product-service", "http · express · mongodb · mongoose"),
                                ("order-service", "http · express · mongodb · mongoose · undici")]):
        svcs.append(p.tile(lbl(n, d), 70, 170 + i * 110, 380, 70, "#ffffff", font="#232F3E", icon="pod", stroke=K8S, parent=shop))
    p.note("Config is env only (OTEL_*): OTEL_TRACES_EXPORTER=otlp, OTEL_METRICS_EXPORTER=prometheus, "
           "OTEL_SEMCONV_STABILITY_OPT_IN=http (stable names: http_server_request_duration).", 70, 578, 440, 62, 10)

    col = p.tile(lbl("OpenTelemetry Collector", "otlp receiver :4318 (http) / :4317 (grpc)<br>k8s_attributes -> memory_limiter -> batch"),
                 700, 130, 330, 90, OTEL)
    tempo = p.tile(lbl("Grafana Tempo", "OTLP gRPC :4317 · 72h · TraceQL"), 1130, 130, 300, 90, TEMPO)
    prom = p.tile(lbl("Prometheus", "ServiceMonitor: scrape /metrics :9464 every 15s<br>"
                      "PrometheusRule: recording + alert rules"), 700, 270, 330, 100, PROM)
    am = p.tile(lbl("Alertmanager", "routes severity=critical / warning"), 700, 440, 330, 70, "#B3261E")
    graf = p.tile(lbl("Grafana", "sidecar loads ConfigMaps labelled grafana_dashboard=1<br>"
                      "datasources: Prometheus + Tempo"), 1130, 270, 300, 90, GRAFANA, font="#232F3E")
    cm = p.k8s("cm", 1500, 296, 40, "ConfigMap<br>shop-red-dashboard", None)
    p.note("<b>Dashboard: Shop / RED + SLO</b><br>Rate: requests/s per service<br>Errors: 5xx ratio per service<br>"
           "Duration: p95 latency per service<br>Stat tiles: availability, % under 250 ms<br>HPA replicas: current vs desired", 1470, 110, 240, 150)

    p.edge(shop, col, "traces<br>OTLP :4318", GREY, dashed=True, exit=(1, 0.152), entry=(0, 0.5))
    p.edge(col, tempo, "OTLP/gRPC :4317", GREY, dashed=True)
    p.edge(shop, prom, "metrics<br>pull :9464", GREY, dashed=True, exit=(1, 0.41), entry=(0, 0.5))
    p.edge(prom, graf, "PromQL", GREY, dashed=True)
    p.edge(tempo, graf, "TraceQL", GREY, dashed=True, exit=(0.5, 1), entry=(0.5, 0))
    p.edge(prom, am, "firing alerts", WARN, dashed=True)
    p.edge(cm, graf, "sidecar", GREY, dashed=True, exit=(0, 0.5), entry=(1, 0.5))

    # SLO definitions
    p.add('<b style="font-size:15px;">Service level objectives (gateway = user-facing boundary)</b>',
          "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;", 40, 690, 900, 30)
    p.tile('<b>SLO 1 · Availability 99.5%</b><br><span style="font-size:11px;">SLI: share of gateway requests that are not 5xx (probe routes excluded)<br>'
           'window: 30 days · error budget: 0.5% of requests (~3h 36m of full outage)</span>',
           40, 735, 560, 90, "#ffffff", font="#232F3E", stroke=WARN, align="left")
    p.tile('<b>SLO 2 · Latency</b><br><span style="font-size:11px;">SLI: share of gateway requests served in under 250 ms<br>'
           'objective: 95% of requests (p95 &lt; 250 ms)</span>', 40, 845, 560, 80, "#ffffff", font="#232F3E", stroke="#D6B656", align="left")
    a1 = p.tile('<b>Alert ErrorBudgetFastBurn · critical</b><br><span style="font-size:11px;">burn rate &gt; 14.4x on BOTH 1h and 5m windows '
                '(5xx ratio &gt; 7.2%), for 2m<br>spends 2% of the 30-day budget in 1 hour (SRE workbook multi-window)<br>'
                'the short window makes it reset fast once the incident is over</span>',
                660, 730, 590, 100, "#FDECEA", font="#232F3E", stroke=WARN, align="left")
    a2 = p.tile('<b>Alert LatencySLOBreach · warning</b><br><span style="font-size:11px;">share of requests under 250 ms &lt; 95% '
                'over 30m, for 10m<br>needs a histogram bucket boundary at 0.25 s (OTel default buckets have it)</span>',
                660, 845, 590, 80, "#FFF8E1", font="#232F3E", stroke="#D6B656", align="left")
    p.note("<b>Recording rules</b> (per service)<br>slo:error_ratio:rate5m, :rate1h<br>slo:fast_ratio:rate30m<br><br>"
           "<b>Metric labels used</b><br>http_response_status_code, http_route, service, namespace", 1310, 735, 330, 200)
    p.edge(p.add("", "ellipse;fillColor=none;strokeColor=none;", 600, 780, 1, 1), a1, "", WARN, width=1.5)
    p.edge(p.add("", "ellipse;fillColor=none;strokeColor=none;", 600, 885, 1, 1), a2, "", "#D6B656", width=1.5)

    # tracing story
    p.note("<b>What a trace shows</b><br>One request through the gateway fans out to user / product / order spans, "
           "including the MongoDB call and order-service's HTTP call to product-service (W3C trace context propagates automatically). "
           "Spans carry k8s.namespace, k8s.pod and deployment.environment from the collector.", 40, 960, 560, 130)
    p.note("<b>Capacity link</b><br>The k6 load test (k6/load.js) hammers /api/users/login (scrypt, CPU bound). "
           "CPU crosses the 70% HPA target, replicas go 1 -> 4, and the HPA panel plus the p95 panel show the recovery.", 660, 960, 590, 130)
    p.note("<b>Not in scope</b>: logs (stdout only), exemplars, long-term storage (Tempo runs on local disk; use S3 / GCS in a real cluster).",
           1310, 960, 330, 130)
    return p


def main():
    pages = [cluster(), gitops(), observability()]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "k8s-gitops-platform.drawio")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write('<mxfile host="app.diagrams.net">' + "".join(pg.xml() for pg in pages) + "</mxfile>\n")
    print(out)


if __name__ == "__main__":
    main()
