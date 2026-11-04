#!/bin/sh
# Install <app>-<evr> in a clean Fedora container from the published repository,
# with signature checks on, the way a user would.
#
#   verify-install.sh new    <app> <site-url> <evr>
#       dnf config-manager addrepo --from-repofile=<site-url>/<app>.repo
#   verify-install.sh legacy <app> <site-url> <evr> <old-baseurl>
#       an old, hand-added .repo file pointing at <old-baseurl> (with $releasever);
#       the package must replace it with the new one.
set -eu
setup=$1 app=$2 url=$3 evr=$4 legacy=${5:-}
repo=/etc/yum.repos.d/$app.repo

# GitHub Pages can take a minute or two after a deploy to serve the new files.
install_pkg() {
    i=0
    until dnf -y --refresh install "$app-$evr"; do
        i=$((i + 1))
        [ "$i" -lt 20 ] || { echo "$app-$evr never became installable" >&2; exit 1; }
        echo "--- not there yet, retrying in 30 s ($i/20)"
        sleep 30
    done
}

case $setup in
new)
    dnf install -y dnf5-plugins
    # Pages may serve the previous .repo file for a few minutes after a deploy.
    i=0
    while :; do
        rm -f "$repo"
        dnf config-manager addrepo --from-repofile="$url/$app.repo"
        grep -q "^baseurl=$url/rpm/\$" "$repo" && break
        i=$((i + 1))
        [ "$i" -lt 20 ] || { echo "$url/$app.repo is still the old file" >&2; exit 1; }
        echo "--- old .repo file still served, retrying in 30 s ($i/20)"
        sleep 30
    done
    cat "$repo"
    grep -qx 'gpgcheck=1' "$repo"
    grep -qx 'repo_gpgcheck=1' "$repo"
    install_pkg
    ;;
legacy)
    # What `addrepo` wrote for the old per-Fedora repository.
    cat > "$repo" <<EOF
[$app]
name=$app
baseurl=$legacy
enabled=1
gpgcheck=0
metadata_expire=1h
EOF
    install_pkg
    echo "--- repository file after the install:"
    cat "$repo"
    grep -q "^baseurl=$url/rpm/\$" "$repo" || { echo "the package did not take over $repo" >&2; exit 1; }
    ls -l /etc/yum.repos.d/
    # From now on the signed repository and its key are used.
    dnf -y --refresh reinstall "$app-$evr"
    ;;
*)
    echo "usage: $0 new|legacy app site-url evr [old-baseurl]" >&2; exit 2 ;;
esac

# The installed package and the one in the repository are signed with our key.
rpm -q "$app-$evr"
rpm -q gpg-pubkey --qf '%{NAME}-%{VERSION}-%{RELEASE}\t%{SUMMARY}\n'
cd "$(mktemp -d)"
dnf download "$app-$evr"
rpm -K ./*.rpm
rpm -K ./*.rpm | grep -q 'digests signatures OK'
rpm -q --qf 'Signature: %{SIGPGP:pgpsig}\n' "$app"
echo "OK: $app-$evr installed from $url with gpgcheck and repo_gpgcheck on"
