# Install

| Where you work | Route | Time |
|---|---|---|
| Claude.ai, Cowork and Claude Code | Add the marketplace in claude.ai | One minute |
| Claude Code only | One terminal command | One command |
| A team repo | Commit two settings to the repo | Once per repo |
| No GitHub access | Release files | One upload |

## Claude.ai and Cowork

1. Open Customize, then Plugins.
2. Select Add, then Add marketplace.
3. Enter `dgonzo/dgonzo-plugins` and select Sync.
4. Find Writing under Discover and select Add.
5. Turn on Sync automatically so new versions arrive on their own.

## Claude Code

Run this in a terminal:

```
claude plugin install writing --marketplace dgonzo/dgonzo-plugins
```

Inside a session, type the same as a slash command:

```
/plugin install writing --marketplace dgonzo/dgonzo-plugins
```

Both need Claude Code 2.1.275 or later. On an older version, add the marketplace first:

```
claude plugin marketplace add dgonzo/dgonzo-plugins
claude plugin install writing@dgonzo
```

## A team repo

Add this to `.claude/settings.json` in the repo and commit it. Anyone who opens the repo in Claude Code and trusts the folder is offered the plugin.

```json
{
  "extraKnownMarketplaces": {
    "dgonzo": { "source": { "source": "github", "repo": "dgonzo/dgonzo-plugins" } }
  },
  "enabledPlugins": { "writing@dgonzo": true }
}
```

## Release files, without GitHub

Each release ships two files.

| File | Surface | How to install |
|---|---|---|
| `writing-<version>.plugin` | Cowork | Open the file, or Customize > Plugins > Add > Upload plugin |
| `dgonzo-plugins-<version>.zip` | Claude Code | Unzip to a folder you keep, then run the two commands below |

```
claude plugin marketplace add ./<folder>
claude plugin install writing@dgonzo
```

To upgrade, unzip the new zip over the same folder. Then start a new session or run `/reload-plugins`.

## Installs from before the rename

The repo was `dgonzo/claude-plugins` until version 2.0.1. GitHub redirects the old name, so old installs keep updating. The install ID stays `writing@dgonzo`. To point an old install at the new name, run:

```
claude plugin marketplace remove dgonzo
claude plugin install writing --marketplace dgonzo/dgonzo-plugins
```

## Check a new install

1. Ask "what is the writing rule on bold". The answer quotes Rule 5.
2. In Claude Code, write a Markdown file with an em-dash aside. The lint hook reports it.
