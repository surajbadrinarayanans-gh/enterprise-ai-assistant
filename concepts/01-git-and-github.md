# 01 · Git and GitHub

## The four places your code lives
```
Working folder  --git add-->  Staging area  --git commit-->  Local repo  --git push-->  GitHub (remote)
(files you edit)              (next commit)                  (history on your Mac)       (shared copy)
```
- **`git add <file>`** chooses what goes into the next commit. Prefer naming files over `git add .`.
- **`git commit -m "..."`** saves a snapshot **locally**. Nothing leaves your machine.
- **`git push`** uploads local commits to the remote.
- **`git push -u origin main`** (first time) links local `main` to `origin/main`; afterwards plain `git push` works.
- VS Code letters: **U** untracked · **A** added (staged) · **M** modified.

## Remotes
- A **remote** is just a saved **name + URL** in `.git/config`. `origin` is a conventional nickname.
- `git remote -v` lists them. Empty output right after `git init` is correct: nothing added yet.
- `git remote add origin <url>` adds one; `git remote set-url origin <new-url>` changes it.
- Renaming a repo on GitHub does **not** update your laptop. GitHub redirects the old URL for a while, but update it yourself.

## Identity and the noreply email
- A commit stores author name + email as **plain text**. Git never verifies it; anyone can type any email.
- GitHub links a commit to your profile by **looking up that email** in its accounts table. That only affects **display** (avatar, profile link).
- `ID+username@users.noreply.github.com` is an alias GitHub maps to your account. It hides your real email in public history and can't receive mail.
- Turn on *"Block command line pushes that expose my email"* in GitHub settings.
- Proving **who wrote** a commit needs **signed commits** ("Verified" badge). Proving **who may push** is done by SSH keys.

## SSH keys
- `ssh-keygen -t ed25519 -C "label"` creates a pair: **private key** (`id_ed25519`, never leaves your Mac) + **public key** (`id_ed25519.pub`, give to GitHub).
- **Login by challenge:** GitHub sends a random one-time string → your Mac **signs** it with the private key → GitHub **verifies** with the public key. The secret never crosses the network; a recorded signature is useless next time.
- Public key can only **verify**, never **sign**. A stolen public key is harmless.
- **Passphrase** encrypts the private key file on disk. `UseKeychain` + `ssh-add --apple-use-keychain` stores it so you don't retype it.
- **known_hosts:** the first connection asks you to confirm the **server's** fingerprint. That protects you from a fake GitHub. A later change triggers a loud warning (possible interception).
- `ssh -T git@github.com` tests auth. Everyone connects as user `git`; your key tells GitHub who you are.

## Commit messages
Conventional Commits: `type: summary in imperative mood`. Full rules in [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## .gitignore
Lists files Git must never track: `.env` (secrets), `.venv/`, `__pycache__/`, `*.tfstate`, `.DS_Store`.
A leaked API key in a public repo is found by bots within minutes. **Rotate it immediately** if it happens.

## Interview questions
1. Difference between `git commit` and `git push`?
2. What is the staging area for?
3. What is `origin`?
4. How does SSH key authentication work without sending a secret?
5. Can a stolen public key be used to push? Why not?
6. Does GitHub verify the author email on a commit? How do you prove authorship?
7. What is `known_hosts` protecting you from?
8. You committed an API key and pushed. What do you do, in order?
