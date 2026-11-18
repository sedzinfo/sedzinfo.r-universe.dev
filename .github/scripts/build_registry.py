"""Rebuild packages.json, the registry of the R-universe https://<owner>.r-universe.dev.

Run by .github/workflows/registry.yml every day and on demand. It
- lists the owner's public repositories that are neither forks nor archived (GitHub API),
- finds the R packages in each: a DESCRIPTION with a NAMESPACE beside it, at the root of the
  repository or in a folder directly under it (rwf keeps its package in rwf/),
- writes packages.json: for each package the name in its DESCRIPTION, the Git url of its repository
  and, when the package is not at the root, its subdir. No branch is set, so R-universe builds the
  default branch of each repository, as its documentation recommends.
The file is rewritten only when its content changes. If GitHub cannot be reached (an error other than
404), nothing is written, so a short outage does not drop packages from the universe.
To leave a package out, add its name to EXCLUDE.

Run locally from the repository root:  python .github/scripts/build_registry.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "sedzinfo")
EXCLUDE = set()                                   # package names to leave out, e.g. {"covid"}
NOT_PACKAGES = {"renv", "packrat", "inst", "tests", "revdep", "vignettes", "docs"}   # folders whose DESCRIPTION is not a package
REGISTRY = Path("packages.json")


def fetch(url, api=False):
    """Return the body of url, or None on 404. Any other failure stops the script."""
    headers = {"User-Agent": f"{OWNER}-registry-bot"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        if os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        sys.exit(f"::error::{url} answered {error.code}; packages.json was not changed")
    except (urllib.error.URLError, TimeoutError) as error:
        sys.exit(f"::error::{url} could not be reached ({error}); packages.json was not changed")


def public_repos():
    """The owner's public repositories that are neither forks nor archived, sorted by name."""
    repos, page = [], 1
    while True:
        batch = json.loads(fetch(f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&page={page}", api=True))
        if not batch:
            return sorted(repos, key=lambda r: r["name"].lower())
        repos += [r for r in batch if not (r["fork"] or r["archived"] or r["private"])]
        page += 1


def package_dirs(repo):
    """Folders of repo ("" for the root, or one folder down) that hold an R package."""
    body = fetch(f"https://api.github.com/repos/{OWNER}/{repo['name']}/git/trees/{repo['default_branch']}?recursive=1", api=True)
    if body is None:                              # empty repository
        return []
    tree = json.loads(body)
    if tree.get("truncated"):
        print(f"::warning::{repo['name']}: GitHub listed only part of its files; a package in it may be missed")
    files = {entry["path"] for entry in tree["tree"] if entry["type"] == "blob"}
    dirs = [""] + sorted({path.split("/")[0] for path in files if path.count("/") == 1} - NOT_PACKAGES)
    prefix = lambda d: f"{d}/" if d else ""
    return [d for d in dirs if prefix(d) + "DESCRIPTION" in files and prefix(d) + "NAMESPACE" in files]


def package_name(repo, subdir):
    """The Package: field of the DESCRIPTION in subdir of repo."""
    path = f"{subdir}/DESCRIPTION" if subdir else "DESCRIPTION"
    body = fetch(f"https://raw.githubusercontent.com/{OWNER}/{repo['name']}/{repo['default_branch']}/{path}")
    for line in (body or b"").decode("utf-8", "replace").splitlines():
        if line.startswith("Package:"):
            return line.split(":", 1)[1].strip()
    return None


entries = {}
for repo in public_repos():
    for subdir in package_dirs(repo):
        name = package_name(repo, subdir)
        where = f"{repo['name']}/{subdir}" if subdir else repo["name"]
        if not name:
            print(f"::warning::{where}: DESCRIPTION has no Package: field; left out")
        elif name in EXCLUDE:
            print(f"{name} ({where}): in EXCLUDE; left out")
        elif name in entries:
            print(f"::warning::{name} is in {entries[name]['url']} and in {where}; R-universe takes one, so {where} is left out")
        else:
            entries[name] = {"package": name, "url": f"https://github.com/{OWNER}/{repo['name']}"}
            if subdir:
                entries[name]["subdir"] = subdir
            print(f"{name}: {where}")

text = json.dumps([entries[k] for k in sorted(entries, key=str.lower)], indent=2) + "\n"
if REGISTRY.exists() and REGISTRY.read_text(encoding="utf-8") == text:
    print(f"{REGISTRY}: unchanged ({len(entries)} packages)")
else:
    REGISTRY.write_text(text, encoding="utf-8", newline="\n")
    print(f"{REGISTRY}: written ({len(entries)} packages)")
