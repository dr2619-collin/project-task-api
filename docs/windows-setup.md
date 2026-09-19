# Windows setup

Use **Windows Terminal with a PowerShell tab** for all commands in this guide.

## 1. Open Windows Terminal

1. Open the Windows **Start** menu.
2. Search for **Terminal** and open **Windows Terminal**.
3. Confirm that the active tab is labeled **PowerShell**. If it is not, select the arrow next to the **+** button and choose **PowerShell**.

<img src="images/windows-terminal-powershell-dropdown.png" alt="Windows Terminal dropdown with PowerShell selected" width="700">

*The exact appearance may vary depending on the installed Windows Terminal version.*

Check your current folder:

```powershell
pwd
```

It should be your user folder, similar to `C:\Users\StudentName`. If it shows another location, such as `C:\Windows\System32`, move to your user folder:

```powershell
cd $HOME
```

## 2. Check Git

```powershell
git --version
```

If Windows reports that `git` is not recognized, download and install [Git for Windows](https://git-scm.com/install/windows). **Close and reopen Windows Terminal** after the installation, then run `git --version` again before continuing.

## 3. Install uv

Run this command in the PowerShell tab:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Close and reopen Windows Terminal**, then verify the installation:

```powershell
uv --version
```

## 4. Clone the project (skip if already done)

If you have not already cloned the repository, run:

```powershell
cd $HOME
git clone https://github.com/dr2619-collin/project-task-api.git
cd project-task-api
git switch module-05
```

If the project is already cloned, skip these commands and open a terminal in
the existing `project-task-api` folder.

## 5. Set up PostgreSQL

1. Download the [PostgreSQL Windows installer](https://www.postgresql.org/download/windows/) and choose PostgreSQL 18 for Windows.

2. Run the installer:

   - Keep the default port, `5432`.
   - Set the PostgreSQL superuser password to `postgres` for this local course project.
   - Keep **PostgreSQL Server**, **Command Line Tools**, and **pgAdmin 4** selected.
   - **Stack Builder is optional and is not needed for this course.** You can skip it.

The installer starts PostgreSQL as a Windows service. You normally do not need to start it manually before working on the project.

3. From the `project-task-api` folder, run the course database setup script. Enter `postgres` when prompted for the password:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d postgres -f scripts\setup_database.sql
```

The script creates the `project_task` database and its local database user
account if they do not already exist. It leaves existing resources in place,
so it is safe to run again.

4. Confirm that the database was created. You can use pgAdmin 4:

   - Open **pgAdmin 4**.
   - Connect to the local server on port `5432` with username `postgres` and password `postgres`.
   - Expand **Databases** and confirm that `project_task` is listed.

   Or use PowerShell:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d project_task -W -c "\dt"
```

## Add PostgreSQL to the Windows PATH

The full path works for the setup commands above. To use `psql` without typing
its full path in future commands, add PostgreSQL's `bin` folder to `PATH`:

1. Open the Windows **Start** menu and search for **Environment Variables**.
2. Select **Edit the system environment variables**.
3. Click **Environment Variables**.
4. Under **User variables**, select `Path` and click **Edit**.
5. Click **New** and add:

```text
C:\Program Files\PostgreSQL\18\bin
```

6. Click **OK** on each window.
7. Close and reopen Windows Terminal.
8. Verify the command is available:

```powershell
psql --version
```

If PostgreSQL was installed in a different folder, add that installation's
`bin` folder instead.

## Start and stop PostgreSQL

PostgreSQL runs as a Windows service. Find its exact service name with:

```powershell
Get-Service *postgres*
```

Use the service name shown by that command in these examples:

```powershell
# Start PostgreSQL for this session.
Start-Service -Name "postgresql-x64-18"

# Stop PostgreSQL when you are finished.
Stop-Service -Name "postgresql-x64-18"
```

To prevent PostgreSQL from starting automatically when Windows boots, open
Windows Terminal as Administrator and run:

```powershell
Set-Service -Name "postgresql-x64-18" -StartupType Manual
```

This changes only the service startup behavior. It does not delete the
`project_task` database or any of its data.
