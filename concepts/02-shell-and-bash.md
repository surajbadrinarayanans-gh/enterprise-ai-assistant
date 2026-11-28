# 02 · Shell and Bash

## Running scripts
- **Shebang** `#!/bin/bash` (first line) tells the OS which program runs the script.
- **`chmod +x script.sh`** gives execute permission so it can run as `./script.sh`.
- **`bash -c "text"`** runs the text as commands instead of reading a script file.
- **`$( command )`** runs the command and substitutes its output (command substitution).
- **`curl URL | bash`** pipes downloaded text into bash. The `bash -c "$(curl ...)"` form downloads the **whole** script before running, so a dropped connection can't run half a script.
- Running scripts from the internet is a trust decision. Read before you run.

## curl
| Flag | Meaning |
|---|---|
| `-f` | fail on HTTP errors (4xx/5xx) instead of printing the error page |
| `-s` | silent: no progress bar |
| `-S` | still show errors when silent |
| `-L` | follow redirects (301/302). Not followed by default |
| `-i` | include response headers in the output |
| `-I` | headers only (HEAD request) |

## PATH and `which`
- **PATH** is the ordered list of folders the shell searches when you type a command. First match wins.
- **`which <cmd>`** prints which program would run.
- The shell knows nothing about a project's venv unless something puts `.venv/bin` on PATH (`uv run` or activating).

## Files and redirection
| Command | Meaning |
|---|---|
| `>` | write output to a file, **overwriting** it |
| `>>` | **append** to a file |
| `cat > file <<'EOF' ... EOF` | write the lines between markers to a file (heredoc) |
| `rm file` | delete permanently. No trash can, so check the name first |
| `mkdir -p a/b/c` | create folders including parents; no error if they exist |
| `touch file` | create an empty file (or update its timestamp) |
| `ls -l` | long listing; symlinks show as `name -> target` |
| `ls -a` | include hidden files (names starting with `.`) |
| `grep word file` | print lines containing `word` |
| `pbcopy < file` | copy file contents to the Mac clipboard |

## Symlinks
A **symbolic link** is a tiny file that points to another path, like a shortcut.
`.venv/bin/python -> ~/.local/share/uv/python/.../python3.12`.

## Interview questions
1. What does the shebang do? What happens without `chmod +x`?
2. Why use `-L` with curl? What happens without it on a redirect?
3. What is PATH? Why does `which python3` print the system Python inside a project folder?
4. Difference between `>` and `>>`?
5. What is a symlink, and where have you seen one used?
