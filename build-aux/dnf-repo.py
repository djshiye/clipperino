#!/usr/bin/python3
"""Assemble the signed, version-independent DNF repository served by GitHub Pages.

    dnf-repo.py --app macropad --url https://djshiye.github.io/macropad-fedora \
                --title Macropad --new new-rpms/ --site site/ [--prev dir/ | --fetch]

Runs in a Fedora container after the new packages were signed, with the signing key in
gpg's keyring (repomd.xml is signed with it) and createrepo_c + python3-rpm installed.

Layout of the site:
    rpm/                   every package (newest --keep builds of each name.arch) + repodata/
    fedora-44/ .. -50/     legacy repodata only, for the old ".../fedora-$releasever/" .repo
                           files; its package locations point into rpm/ (xml:base), so
                           nothing is stored twice
    RPM-GPG-KEY-djshiye    the public signing key
    <app>.repo             the repository definition (the RPM also ships it)
    index.html             a small landing page
"""
import argparse
import gzip
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

import rpm

NS = {"repo": "http://linux.duke.edu/metadata/repo", "common": "http://linux.duke.edu/metadata/common"}
KEY_NAME = "RPM-GPG-KEY-djshiye"


def log(msg):
    print(f"==> {msg}", flush=True)


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, **kw)


def header(path):
    out = run("rpm", "-qp", "--nosignature", "--qf",
              "%{NAME}\t%{ARCH}\t%{EPOCHNUM}\t%{VERSION}\t%{RELEASE}\t%{SOURCERPM}", path,
              capture_output=True).stdout
    name, arch, epoch, version, release, sourcerpm = out.split("\t")
    if sourcerpm == "(none)":
        arch = "src"
    return name, arch, (epoch, version, release)


def signed_ok(path):
    """True when the package's digests and signature verify against the imported key."""
    res = subprocess.run(["rpm", "-K", path], capture_output=True, text=True)
    return res.returncode == 0 and "signatures OK" in res.stdout


def fetch(url, dest):
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def fetch_previous(url, dest):
    """Download the packages of the live rpm/ repository (if there is one)."""
    base = f"{url}/rpm/"
    try:
        with urllib.request.urlopen(base + "repodata/repomd.xml", timeout=60) as r:
            repomd = ET.fromstring(r.read())
    except urllib.error.HTTPError as e:
        log(f"no live repository at {base} yet (HTTP {e.code}); starting fresh")
        return
    primary = repomd.find("repo:data[@type='primary']/repo:location", NS).get("href")
    with urllib.request.urlopen(base + primary, timeout=60) as r:
        data = r.read()
    root = ET.fromstring(gzip.decompress(data) if primary.endswith(".gz") else data)
    for loc in root.iterfind("common:package/common:location", NS):
        href = loc.get("href")
        name = os.path.basename(href)
        if "/" in href.strip("/") or not name.endswith(".rpm"):
            continue  # only plain files in rpm/ itself
        log(f"keeping candidate {name}")
        fetch(base + href, os.path.join(dest, name))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--app", required=True, help="package and .repo file name")
    p.add_argument("--url", required=True, help="site URL, no trailing slash")
    p.add_argument("--title", required=True)
    p.add_argument("--summary", default="")
    p.add_argument("--new", required=True, help="directory with the new, signed packages")
    p.add_argument("--site", required=True, help="output directory (created)")
    p.add_argument("--repo-file", required=True)
    p.add_argument("--key", required=True, help="armored public key")
    p.add_argument("--icon", help="SVG icon for the landing page")
    p.add_argument("--prev", help="directory with the previously published packages")
    p.add_argument("--fetch", action="store_true", help="download previous packages from --url")
    p.add_argument("--keep", type=int, default=3)
    p.add_argument("--legacy", default="fedora-{N}",
                   help="legacy path template, {N} is the Fedora release")
    p.add_argument("--legacy-releases", default="44-50", help='"44-50", or "none"')
    a = p.parse_args()

    site = a.site
    pool = os.path.join(site, "rpm")
    os.makedirs(pool, exist_ok=True)

    # rpm -K needs the key in the rpm database.
    run("rpm", "--import", a.key)

    candidates = []  # (path, is_new)
    for f in sorted(os.listdir(a.new)):
        if f.endswith(".rpm"):
            candidates.append((os.path.join(a.new, f), True))
    prev = a.prev
    tmp = None
    if a.fetch and not prev:
        tmp = prev = tempfile.mkdtemp()
        fetch_previous(a.url, prev)
    if prev and os.path.isdir(prev):
        for f in sorted(os.listdir(prev)):
            if f.endswith(".rpm"):
                candidates.append((os.path.join(prev, f), False))
    if not any(new for _, new in candidates):
        sys.exit("no new packages")

    groups = {}
    for path, new in candidates:
        name, arch, evr = header(path)
        if name.endswith(("-debuginfo", "-debugsource")):
            continue
        if not signed_ok(path):
            if new:
                sys.exit(f"{os.path.basename(path)} is not signed with the repository key")
            log(f"dropping {os.path.basename(path)}: not signed with the repository key")
            continue
        groups.setdefault((name, arch), {})[os.path.basename(path)] = (evr, path)

    for (name, arch), files in sorted(groups.items()):
        order = sorted(files.items(), key=lambda kv: _Cmp(kv[1][0]), reverse=True)
        for fname, (_, path) in order[: a.keep]:
            log(f"publish {fname}")
            shutil.copy2(path, os.path.join(pool, fname))
        for fname, _ in order[a.keep:]:
            log(f"prune   {fname}")
    if tmp:
        shutil.rmtree(tmp)

    def sign_repomd(repodata):
        repomd = os.path.join(repodata, "repomd.xml")
        run("gpg", "--batch", "--yes", "--detach-sign", "--armor", "-o", repomd + ".asc", repomd)

    log("createrepo_c rpm/")
    run("createrepo_c", "--general-compress-type", "gz", pool)
    sign_repomd(os.path.join(pool, "repodata"))

    legacy = [] if a.legacy_releases == "none" else range(
        int(a.legacy_releases.split("-")[0]), int(a.legacy_releases.split("-")[-1]) + 1)
    for n in legacy:
        out = os.path.join(site, a.legacy.format(N=n))
        os.makedirs(out, exist_ok=True)
        log(f"legacy metadata {a.legacy.format(N=n)}/ -> rpm/")
        run("createrepo_c", "--general-compress-type", "gz", "--baseurl", f"{a.url}/rpm/",
            "--outputdir", out, pool, stdout=subprocess.DEVNULL)
        sign_repomd(os.path.join(out, "repodata"))

    shutil.copy2(a.key, os.path.join(site, KEY_NAME))
    shutil.copy2(a.repo_file, os.path.join(site, f"{a.app}.repo"))
    if a.icon:
        shutil.copy2(a.icon, os.path.join(site, "icon.svg"))
    open(os.path.join(site, ".nojekyll"), "w").close()
    fpr = fingerprint(a.key)
    with open(os.path.join(site, "index.html"), "w") as f:
        f.write(landing_page(a, fpr, sorted(os.listdir(pool))))
    log(f"site ready in {site} (key {fpr})")


class _Cmp:
    def __init__(self, evr):
        self.evr = evr

    def __lt__(self, other):
        return rpm.labelCompare(self.evr, other.evr) < 0


def fingerprint(keyfile):
    out = run("gpg", "--batch", "--with-colons", "--import-options", "show-only", "--import",
              keyfile, capture_output=True).stdout
    return next(l.split(":")[9] for l in out.splitlines() if l.startswith("fpr:"))


def landing_page(a, fpr, files):
    e = html.escape
    repo_url = f"{a.url}/{a.app}.repo"
    pkgs = [f for f in files if f.endswith(".rpm") and not f.endswith(".src.rpm")]
    latest = e(pkgs[-1]) if pkgs else ""
    fpr_spaced = " ".join(fpr[i:i + 4] for i in range(0, len(fpr), 4))
    icon = '<img class="icon" src="icon.svg" alt="">' if a.icon else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(a.title)} for Fedora</title>
{'<link rel="icon" href="icon.svg">' if a.icon else ''}
<style>
  :root {{ color-scheme: light dark; --bg: #f6f7f9; --card: #ffffff; --text: #1c1f24; --dim: #5c6470;
          --line: #e2e5ea; --code: #f0f2f5; --accent: #3584e4; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #0d0f12; --card: #16191e; --text: #eceff3; --dim: #9aa3ae; --line: #262b33;
            --code: #1e2228; --accent: #62a0ea; }} }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px 16px;
         background: var(--bg); color: var(--text);
         font: 15px/1.55 "Adwaita Sans", "Inter", system-ui, sans-serif; }}
  main {{ width: min(680px, 100%); background: var(--card); border: 1px solid var(--line);
         border-radius: 20px; padding: 28px 24px;
         box-shadow: 0 1px 2px rgba(0,0,0,.06), 0 12px 32px rgba(0,0,0,.08); }}
  header {{ display: flex; gap: 16px; align-items: center; margin-bottom: 18px; }}
  .icon {{ width: 64px; height: 64px; }}
  h1 {{ margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -.01em; }}
  .sub {{ margin: 2px 0 0; color: var(--dim); }}
  h2 {{ margin: 22px 0 8px; font-size: 13px; font-weight: 600; text-transform: uppercase;
        letter-spacing: .06em; color: var(--dim); }}
  pre {{ margin: 0; padding: 14px 16px; overflow-x: auto; background: var(--code);
        border: 1px solid var(--line); border-radius: 13px; font-size: 13px; }}
  code {{ font-family: "Adwaita Mono", ui-monospace, monospace; }}
  .pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
          background: color-mix(in srgb, var(--accent) 14%, transparent); color: var(--accent);
          font-size: 12px; font-weight: 600; }}
  p.note {{ color: var(--dim); font-size: 13px; margin: 8px 0 0; }}
  .fpr {{ font-family: "Adwaita Mono", ui-monospace, monospace; font-size: 12px; word-break: break-word; }}
  a {{ color: var(--accent); }}
  footer {{ margin-top: 22px; font-size: 13px; color: var(--dim); }}
</style>
</head>
<body>
<main>
  <header>{icon}<div><h1>{e(a.title)}</h1><p class="sub">{e(a.summary) or "DNF repository for Fedora"}</p></div></header>
  <span class="pill">&#10003; Signed packages &middot; any current Fedora</span>
  <h2>Install</h2>
  <pre><code>sudo dnf config-manager addrepo --from-repofile={e(repo_url)}
sudo dnf install {e(a.app)}</code></pre>
  <p class="note">dnf asks once to trust the signing key below. The package keeps its repository
  file up to date from then on.</p>
  <h2>Signing key</h2>
  <p class="fpr"><a href="{KEY_NAME}">{KEY_NAME}</a><br>{e(fpr_spaced)}</p>
  {f'<h2>Latest build</h2><p class="fpr">{latest}</p>' if latest else ''}
  <footer><a href="https://github.com/djshiye/{e(a.url.rsplit('/', 1)[-1])}">Source on GitHub</a></footer>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
