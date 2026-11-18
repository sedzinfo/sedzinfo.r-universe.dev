# sedzinfo.r-universe.dev

This repository tells [R-universe](https://r-universe.dev) which R packages make up
**[sedzinfo.r-universe.dev](https://sedzinfo.r-universe.dev)**: the statistics and psychometrics
packages of [sedzinfo](https://sedzinfo.github.io), and the Shiny apps built as R packages with
[golem](https://thinkr-open.github.io/golem/). It holds no package code, only the list,
[packages.json](packages.json), and the bot that keeps that list up to date.

## What R-universe does with it

R-universe reads `packages.json` and, for every package in it:

- builds the package from its GitHub repository: the source package and binaries for Windows, macOS
  and Linux, so it installs without compiling, with no need for CRAN;
- checks it with `R CMD check` on each system and shows the results;
- publishes its help pages and articles, and lists it in the search of
  [r-universe.dev](https://r-universe.dev);
- builds it again after each change to its repository, usually within an hour.

The builds run in [github.com/r-universe/sedzinfo](https://github.com/r-universe/sedzinfo). The packages,
with the state of their builds, are at
[sedzinfo.r-universe.dev/packages](https://sedzinfo.r-universe.dev/packages).

## Install a package

```r
install.packages("rwf", repos = c("https://sedzinfo.r-universe.dev", "https://cloud.r-project.org"))
```

The second address, CRAN, supplies the packages it depends on. To use the universe in every session,
put this in your `.Rprofile`:

```r
options(repos = c(sedzinfo = "https://sedzinfo.r-universe.dev", CRAN = "https://cloud.r-project.org"))
```

## The bot that keeps packages.json up to date

`packages.json` is written by a bot, so don't edit it by hand. The workflow
[registry.yml](.github/workflows/registry.yml) runs the script
[build_registry.py](.github/scripts/build_registry.py) every day at 04:37 UTC, whenever either file
changes, and on demand from the Actions tab ("Run workflow"). The script:

1. lists the public repositories of sedzinfo on GitHub, leaving out forks and archived ones;
2. finds the R packages in them: a `DESCRIPTION` file with a `NAMESPACE` beside it, at the root of the
   repository or in a folder directly under it (rwf keeps its package in `rwf/`);
3. writes `packages.json`, with, for each package, its name from `DESCRIPTION`, the address of its
   repository and, when it is not at the root, its folder (`subdir`). It names no branch, so
   R-universe builds the default branch of each repository;
4. commits the file, as github-actions[bot], only when the list has changed.

So a new public package joins the universe within a day, and a package whose repository is deleted,
archived or made private leaves it. If GitHub cannot be reached, the script stops without touching
`packages.json`, so an outage never drops a package.

GitHub pauses the scheduled runs of a repository that has had no commits for 60 days. If a new package
does not appear, check the Actions tab and enable the workflow again.

## Leave a package out

Add its name to `EXCLUDE` at the top of [build_registry.py](.github/scripts/build_registry.py), for
example `EXCLUDE = {"covid"}`, and push. The change starts the bot, which takes the package out of
`packages.json`; R-universe then removes it.

## Run the bot by hand

From the root of this repository:

```sh
python .github/scripts/build_registry.py
```

It needs only Python. A GitHub token in `GITHUB_TOKEN` is optional: without one, GitHub allows 60
requests an hour, which is enough.

## Setup, done once

- This repository is public and named `sedzinfo.r-universe.dev`, as R-universe requires.
- The [R-universe GitHub app](https://github.com/apps/r-universe/installations/new) is installed on
  the sedzinfo account.

More in the [R-universe documentation](https://docs.r-universe.dev).
