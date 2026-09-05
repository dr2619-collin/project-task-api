# macOS setup

Use the **Terminal** application for all commands in this guide.

## 1. Open Terminal

1. Press `Command+Space` to open Spotlight Search.
2. Search for **Terminal** and open it.

Check your current folder:

```bash
pwd
```

It should be your user folder, similar to `/Users/StudentName`. If it shows another location, move to your user folder:

```bash
cd "$HOME"
```

## 2. Check Git

```bash
git --version
```

If Git is not installed, follow the instructions on the [Git for macOS installation page](https://git-scm.com/install/mac). **Close and reopen Terminal** after the installation, then run `git --version` again before continuing.

## 3. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Close and reopen Terminal**, then verify the installation:

```bash
uv --version
```

Continue with [Clone the project](../README.md#clone-the-project) in the project README.
