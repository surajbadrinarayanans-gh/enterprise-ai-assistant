# 03 · Python projects, virtual environments and imports

## Three different things (two of ours are called `eka`)
| Thing | What it is | Ours |
|---|---|---|
| **Project folder** | Directory containing `pyproject.toml` | `app/` |
| **Project name** | Text inside `pyproject.toml`: `name = "eka"` | `eka` |
| **Package** | Folder of importable code, containing `__init__.py` | `app/src/eka/` |

Folder name and project name are independent. Renaming `app/` → `backend/` keeps the name `eka`;
the venv path becomes `backend/.venv/bin/python` (run `uv sync` once after moving, since venvs record their location).

**Analogy:** folder = house · project name = nameplate on the door · package = a room inside.

## Layout
```
app/                         PROJECT
├── pyproject.toml           what I want (ranges): "fastapi>=0.165"
├── uv.lock                  exactly what I got: every package incl. dependencies-of-dependencies, + hashes
├── .python-version          which Python (3.12)
├── .venv/                   ENVIRONMENT (never committed; rebuildable)
│   ├── bin/python  ->  ~/.local/share/uv/python/cpython-3.12-.../python3.12   (symlink)
│   └── lib/python3.12/site-packages/   installed packages: fastapi/, eka.pth (pointer to src/)
└── src/eka/                 PACKAGE (your code)
    ├── __init__.py          marks the folder as importable
    └── main.py
```
- **src layout:** package sits under `src/` so Python imports the *installed* version, catching packaging mistakes early.
- The build backend (`uv_build`) expects `src/<project-name>/__init__.py`. Name mismatch → *"Expected a Python module at src/app/__init__.py"*.
- **Editable install:** `uv sync` installs your own package as a pointer (`eka.pth`), so code edits apply without reinstalling.
- **Commit:** `pyproject.toml`, `uv.lock`, `.python-version`, `src/`. **Never commit:** `.venv/`.

## uv commands
| Command | Does |
|---|---|
| `uv python install 3.12` | download a Python into uv's shared store (never touch macOS's own Python) |
| `uv init` | create project files |
| `uv add <pkg>` | write to `pyproject.toml` → resolve versions into `uv.lock` → install into `.venv` |
| `uv sync` | make `.venv` exactly match `pyproject.toml` + `uv.lock` |
| `uv run <cmd>` | run a command with `.venv/bin` first on PATH, no activation needed |
| `uv run which python` | show the project's interpreter path |

uv walks **up** directories to find the nearest `pyproject.toml` (Git does the same for `.git`).

## How `import` works
`import fastapi` searches the folders in `sys.path`, which includes **the site-packages of the Python that is running**.
Each interpreter has its own site-packages. So **which interpreter decides which packages exist.**

| Interpreter | fastapi? |
|---|---|
| `/usr/bin/python3` (macOS) | ❌ `ModuleNotFoundError` |
| `app/.venv/bin/python` | ✅ |

Useful probes: `sys.executable` (who am I?), `module.__file__` (where was this loaded from?).

## Why one shared interpreter + symlinks
The interpreter never differs between projects; only packages do. So: interpreter **shared** once, packages **per project**.
Saves disk, makes venv creation instant, one place to patch. uv also caches downloaded packages globally.

## Editor vs runtime
Pylance (VS Code) **reads** code using the **selected interpreter**. It auto-detects `.venv` only at the opened folder's root.
Fix: *Python: Select Interpreter* → `./app/.venv/bin/python`, or `.vscode/settings.json`:
`"python.defaultInterpreterPath": "${workspaceFolder}/app/.venv/bin/python"`.
**Editor errors are not runtime errors.** Check whether the code actually runs before changing it.

## ModuleNotFoundError checklist
1. Which Python is running? (`which python`, `sys.executable`)
2. Is the package installed for **that** Python? (`pyproject.toml`, venv site-packages)
3. Fix: run via `uv run`, or point the tool (IDE, Docker, CI) at the venv's Python.

## Interview questions
1. Difference between `pyproject.toml` and a lock file? Why commit the lock file?
2. Why use a virtual environment at all?
3. An import works on your laptop but fails in Docker/CI. How do you debug it?
4. What does `__init__.py` do?
5. Why shouldn't you `pip install` into the system Python?
6. What is an editable install?
