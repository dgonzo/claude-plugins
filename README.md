# dgonzo plugins

Claude plugins by David Gonzalez. One so far: Writing. It adds a house writing standard and working style for chat, Cowork and Claude Code.

## Install

Claude.ai and Cowork: open Customize > Plugins > Add > Add marketplace. Enter `dgonzo/dgonzo-plugins` and add Writing.

Claude Code:

```
claude plugin install writing --marketplace dgonzo/dgonzo-plugins
```

Team repos, older Claude Code versions and installs without GitHub are in [INSTALL.md](INSTALL.md).

## Plugins

| Plugin | Contents |
|---|---|
| [Writing](plugins/writing/README.md) | writing standard, working style, readability review, prose linter, lint hook |

The Writing plugin cuts linter findings by about 75 percent against a bare session. See [the plugin-vs-naked eval](evals/plugin-vs-naked/README.md).
