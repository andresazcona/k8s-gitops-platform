# Shared by validate.sh and up.sh. "name repoURL version namespace" for every pinned add-on chart
# in the app-of-apps, so versions live in exactly one place (gitops/apps/values.yaml).
addons() { awk '/- name:/{n=$3} /repoURL:/{r=$2} /version:/{v=$2} /^    namespace:/{print n, r, v, $2}' gitops/apps/values.yaml; }
