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

## 4. Clone the project (skip if already done)

If you have not already cloned the repository, run:

```bash
cd "$HOME"
git clone https://github.com/dr2619-collin/project-task-api.git
cd project-task-api
git switch module-05
```

If the project is already cloned, skip these commands and open a terminal in
the existing `project-task-api` folder.

## 5. Set up PostgreSQL

1. Install PostgreSQL 18:

```bash
brew install postgresql@18
```

2. Start PostgreSQL manually. Homebrew initializes a local database cluster at `/opt/homebrew/var/postgresql@18`. To run PostgreSQL only when you choose, start and stop that cluster manually:

```bash
# Start PostgreSQL in the background for this development session.
/opt/homebrew/opt/postgresql@18/bin/pg_ctl \
  -D /opt/homebrew/var/postgresql@18 \
  -l /opt/homebrew/var/postgresql@18/server.log start

# Stop PostgreSQL when you are finished.
/opt/homebrew/opt/postgresql@18/bin/pg_ctl \
  -D /opt/homebrew/var/postgresql@18 stop
```

Optional: add short commands to `~/.aliases`:

```bash
alias pgstart='pg_ctl -D /opt/homebrew/var/postgresql@18 start'
alias pgstop='pg_ctl -D /opt/homebrew/var/postgresql@18 stop'
alias pgstatus='pg_ctl -D /opt/homebrew/var/postgresql@18 status'
```

Reload the aliases in the current terminal:

```bash
source ~/.aliases
```

You can then use `pgstart`, `pgstop`, and `pgstatus`. Make sure `~/.aliases` is sourced by your `~/.zshrc` or `~/.bashrc`.

3. Create the course database and its local database user account from the `project-task-api` folder:

```bash
psql -d postgres -f scripts/setup_database.sql
```

`-d postgres` tells `psql` to connect to PostgreSQL's existing administrative database named `postgres`. The setup script runs there because `project_task` does not exist yet.

The script creates the local database user account `postgres` with password `postgres` when it does not already exist, then creates the `project_task` database owned by that account. It leaves existing resources in place, so it is safe to run again.
