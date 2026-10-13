# Install

## From GitHub, Claude Code

```
claude plugin marketplace add dgonzo/claude-plugins
claude plugin install writing@dgonzo
```

## From a release zip, Claude Code

Unzip `claude-plugins-<version>.zip` to a folder and keep that folder. Claude Code reads the plugin from it at every session start. Then:

```
claude plugin marketplace add ./<folder>
claude plugin install writing@dgonzo
```

To upgrade, unzip the new zip over the same folder. Then start a new session or run `/reload-plugins`.

## From a release file, Cowork

Open the `writing-<version>.plugin` file. The menu route also works: Customize > Plugins > Add > Upload plugin.

## Verify a new install

Ask "what is the writing rule on bold". Write a test file with an em-dash aside. The lint hook fires.
