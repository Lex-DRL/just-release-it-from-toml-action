<div align="center">
  
# Just release it! (from TOML) 📦 Action

*Easiest-to-setup GitHub release for python projects:<br />
just read version from `pyproject.toml`, build changelog and release it!*<br />
</div>

Originally created to assist with releasing custom nodes for [ComfyUI](https://github.com/Comfy-Org/ComfyUI), but can be used for any python packages that rely on `pyproject.toml` for build/publishing.

## Output

An example of generated release: https://github.com/Lex-DRL/test-ComfyUI-dummy/releases

## Just set it up!

**ULTRA-TL;DR**:
- Just use the action in your GitHub workflow.
- It should "just work" for a usual solo-dev project.

TL;DR:
- Have a `pyproject.toml` file in the repo root.
- Make sure it contains the `version` field under the main `[project]` section:
  ```toml
  [project]
  # ...
  version = "1.2.3"
  ```
- Create a GitHub workflow file under `.github\workflows\` - name it something like `release.yml`.
- Put the following code inside it (replace `main` with your default branch, if it has a different name):
  <details>
  <summary>Workflow code</summary>

  ```yaml
  name: Release
  
  on:
    push:
      branches:
        - main
      paths:
        - "pyproject.toml"
    workflow_dispatch:  # Allows to manually run the workflow, too
  
  permissions:
    contents: write  # Necessary to publish a release
  
  jobs:
    publish-release:
      name: Publish a release
      runs-on: ubuntu-latest
      steps:
        - name: ♻️ Check out code
          uses: actions/checkout@v6
          with:
            fetch-depth: 0  # Critical for changelog + first-release support
  
        - name: "📦 Just release it!"
          id: just-release-it
          uses: Lex-DRL/just-release-it-action@v1
  ```
  </details>
- The `📦 Just release it!` action doesn't require any extra configuration, unless you want to override defaults... which are already good enough for most repos.
- Make sure you have a release or a tag **on GitHub** for the latest previous version, and it is made on the right commit. Create at least the tag if you don't have any yet (i.e., if you were releasing directly to a package registry). Name it like `v1.2.3` / just `1.2.3` (with your version, obviously).
  - If you don't do so, your first release published with `📦 Just release it!` will contain **THE ENTIRE GIT HISTORY** as the changelog.

## What does it do, specifically?

The action:
- Reads the current version from `pyproject.toml` (using [SebRollen/toml-action](https://github.com/SebRollen/toml-action)).
- [Standardizes it](https://github.com/Lex-DRL/standardize-version-action) for the release name/tag.
- Detects the changelog range: from the last published release to the latest commit in the branch.
- Builds a changelog (using [orhun/git-cliff-action](https://github.com/orhun/git-cliff-action) + a custom config).
- Publishes the release (using [softprops/action-gh-release](https://github.com/softprops/action-gh-release)).
- Most of the heavy-lifting in the action is done with python, so the action also sets it up in the runner.

## How to name commits? (to categorize them properly)

In short, you don't need to do anything special. Just continue naming your commits in the same (at least somewhat logical) way that you already do.

The action is intentionally built to catch any naming scheme that's used widely. Specifically, it detects:
- [Conventional Commits](https://www.conventionalcommits.org/) - so `feat:`, `fix:`, `upd:`, `ci:`, `bld:` etc. prefixes.
- [GitMoji](https://gitmoji.dev/) - i.e. prefixing commit titles with emoji to classify them.
- Some natural-language words that the titles start with, like: `Adds ...`, `Fixes ...`, `New ...`
- Breaking changes are detected by the `prefix!:` or `prefix(subcategory)!:` format (so, with `!`) from Conventional Commits, as well as by `BREAKING CHANGES:` section somewhere in commit body.
- ... and even some common typos are caught.

> [!NOTE]
> For PRs, only the title is scanned. So, to detect breaking changes in them, use any of the title prefixes.
> 
> Regular merges and plain commits also catch the `BREAKING CHANGES:` section in commit body.

## What categories are detected?

The `git-cliff` tool (used internally) relies on regexes to classify commits. So the table below isn't exhaustive, because it would be insane to list all the spelling variations here.

GitHub or your browser might "prettify" some unicode characters into actual emojis - so it might look like some emojis appear twice. They're not - check the raw text of this ReadMe.

Listed in the order of priority:

| Name | Emoji prefix | [CC](https://www.conventionalcommits.org/) prefix | Natural text |
|---|---|---|---|
| `💥 Breaking Changes 💥` | 💥 ❗ ❕ ‼️ ‼ | `any!` `any(cat)!` | `Breaks ...`, `Breaking ...` etc; `BREAKING CHANGES:` section in the comment body |
| `⚠️ Deprecations` | ⚠️ ⚠ | `depr` | `Deprecated ...`, `Deprecates ...`, `Deprecation`, etc. |
| `↩️ Rollbacks` | ↩️ ↩ ↶ 🔙 ⏪️ ⏪ | - | `Revert ...`, `Reverts ...`, `Undo ...`, `Roll back...` |
| `✨ New Features` | ✨ 🌟 ⭐ 🎉 | `new` `feat` `feature` `add` `support` | `Adds ...`, `Supports ...`, `Supporting ...` |
| `🚀 Improvements` | 🚀 🚩 🚸 ♿️ | `upd` `enh` `enhance` `impr` `improve` | `Changes ...`, `Enhancing ...`, `Improvement ...`, `Better ...`, `Robust ...` |
| `🛠️ Fixes` | 🛠️ 🛠 🐛 🩹 🚑️ 🚑 🚨 🥅 | `bug` `fix` `bugfix` | `Fixes ...`, `Correct ...`, `Properly ...` |
| `⚡ Performance` | ⚡️⚡ | `prf` `perf` | `Performance ...` |
| `🔒 Security` | 🔒 🔐 🛡️ 🛡 | `sec` `security` | `Security ...` |
| `📝 Documentation` | 📝 📄 💬 | `doc` `docs` `readme` | `Documentation ...`, `Documents ...` |
| `♻️ Refactor` | ♻️ ♻ 🚚 | `refac` `refactor` `reimpl` `rename` | `Re-factored ...`, `Fully refactoriing ...`, `Re-implemented ...`, `Renames ...` |
| `🔬 Tests` | 🔬 🧪 ⚗️ ✅ 🦺 | `tst` `test` | `Tested ...`, `Testing ...` |
| `🎨 Code Style` | 🎨 | `fmt` `format` `stl` `style` | `Formatting ...`, `Code format ...`, `Code style ...` |
| `📦 Build/Packaging` | 📦 | `bld` `build` `pyproject` `setup.cfg` `setup.py` `requirements.txt` | `Building ...` |
| `🤖 CI/CD` | 🤖 👷 | `ci` `cd` | - |
| `🧹 Maintenance` | 🧹 🙈 💸 | `chr` `chore` `clean` `cleanup` `maintain` `git` `github` `gitignore` `gitattr` `gitattributes` | - |
| `Version` | 🔖 🏷️ 🏷 | `ver` `version` `bump` `release` | `v1...`, `v2...`, `ver3...` with any numbers |
| `🔀 Other changes` / `⚙️ What's changed` | - | - | All other commits |

## Action inputs / overrides / HowTos

By default, the action is configured to "just work" out of the box in the most general case, no extra configuration required. However, you can override defaults using the `with:` statement in your workflow:

```yaml
        - name: "📦 Just release it!"
          id: just-release-it
          uses: Lex-DRL/just-release-it-action@v1
          with:
            cat-breaking: '‼️ BREAKS ‼️'
```

Below are the available action inputs, grouped by their use case.

### Version source

Where to read version from:
- `project-toml-file`: local path to the TOML file containing the version. Default: `pyproject.toml`
- `project-toml-version-field`: in that file, what field to read. Default: `project.version`

### Dynamic version

(i.e., fetching version dynamically from a dedicated python file)

> [!WARNING]
> **TODO** 🚧🏗️: Planned but not yet implemented

### Attached files

- `attach-files`: Glob of files to attach (e.g. `dist/*`). Leave empty (default) for source-only release. Note: it's your responsibility to prepare these files with the previous steps in the workflow.

### Python setup and skipped steps

> [!NOTE]
> - Empty string (`''`) and `'false'` are treated as disabled.
> - Everything else (including a string made of nothing but spaces) is treated as enabled.

- `skip-python-setup`: Internally, the action uses python, so it installs it during the run. However, if you already set it up in your workflow (i.e., you run `actions/setup-python` yourself), you can skip it inside the action. Default: `false` (do the python setup).
- `python-version`: If you let the action set up python, this specifies which version to use. Default: `3.x` (latest Python 3 available).
- `skip-version-standardize`: Skip [standardization of the version string](https://github.com/Lex-DRL/standardize-version-action) and use the raw version value instead. Default: `false` (standardize the version).

### Release status

- `is-pre-release`: Override pre-release status:
  - `''` (empty, default) - let the version-standardizing step to decide (or `false` if this step is skipped).
  - `false` - force regular release.
  - `true` or any other value - force pre-release.
- `is-draft`: Create release as draft. Default: `false`

### Alert blocks for important categories

By default, three "warning" categories (`💥 Breaking Changes 💥`, `⚠️ Deprecations`, `↩️ Rollbacks`) are formatted as GitHub's alerts.
- `cat-alert-blocks`: set to `false` to disable that behavior and format them the same way as all other categories. Default: `true`

### Category names

You're free to rename the category titles, as they're shown in the release notes. However, please make sure each of them stays unique and doesn't contain any HTML tags - or it might lead to an unexpected behavior.
- `cat-breaking`: 💥 Breaking Changes 💥
- `cat-depr`: ⚠️ Deprecations
- `cat-revert`: ↩️ Rollbacks
- `cat-feat`: ✨ New Features
- `cat-enhance`: 🚀 Improvements
- `cat-fix`: 🛠️ Fixes
- `cat-perf`: ⚡ Performance
- `cat-security`: 🔒 Security
- `cat-doc`: 📝 Documentation
- `cat-refactor`: ♻️ Refactor
- `cat-test`: 🔬 Tests
- `cat-style`: 🎨 Code Style
- `cat-build`: 📦 Build/Packaging
- `cat-ci`: 🤖 CI/CD
- `cat-chore`: 🧹 Maintenance
- `cat-version`: Version
- `cat-unclassified-multi`: 🔀 Other changes - the title used for an unclassified / "Other Changes" category, when any other categories are also detected for a release.
- `cat-unclassified-only`: ⚙️ What's changed - The title used when **only** the unclassified / "Other Changes" category (and optionally, "Version") is detected for a release.

### Your own `git-cliff` config

You can **fully** override how this action generates release notes by providing your own config - to add your own categories, change the matching keywords, etc. However, at this point why using this action at all? You're probably better off just using [orhun/git-cliff-action](https://github.com/orhun/git-cliff-action) directly.

Maybe, if you miss some features, you should open an [issue](https://github.com/Lex-DRL/just-release-it-action/issues) or a [PR](https://github.com/Lex-DRL/just-release-it-action/pulls)? Still, it's your choice:
- `cliff-config-file`: An in-repo path to your own TOML file (e.g. `git-cliff.toml`).

### GitHub token

- `github-token`: For extremely fancy use cases, provide a custom token yourself. Alternatively, a global workflow-level `GITHUB_TOKEN` environment variable could be used instead. Default... is the default token. Don't touch it unless you **really** know what you're doing and why.

## Outputs

The action also provides outputs for you to use in later steps:
- `tag`: Final tag name - with "v" prefix if version was standardized. Otherwise, the raw version extracted from TOML as-is.
- `raw-version`: Version without "v" prefix, if it was standardized. Otherwise, the raw version extracted from TOML as-is.
- `is-pre`: Whether the release is created as a pre-release.
- `changelog`: The generated release notes.
