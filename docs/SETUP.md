# Setup (Claude follows this with Steve)

Claude: do one step at a time. Say in one line what each step is for. Skip a
step that is already done. Steve has never coded, so you run the commands, and
he only clicks or types when a step says so.

Find out first: is this a Mac or Windows? Use the matching commands below.

## 1. Tools

Check each tool. Install only what is missing.

| Tool | What it is (say this to Steve) | Check | Install on Windows | Install on Mac |
|---|---|---|---|---|
| git | Keeps a history of every change, so nothing is lost | `git --version` | `winget install --id Git.Git -e` | `xcode-select --install` (Steve clicks Install in the pop-up) |
| uv | Runs the Python program and installs Python for us | `uv --version` | `winget install --id astral-sh.uv -e` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| gh | Connects to GitHub, where your work is backed up | `gh --version` | `winget install --id GitHub.cli -e` | `brew install gh` if `brew` works. If not, download the macOS zip for this Mac (arm64 or amd64) from https://github.com/cli/cli/releases/latest, unzip it, and put `bin/gh` in `~/.local/bin`. |

After you install something on Windows, new commands may not work until a new
terminal starts. If a command is "not found" right after you install it, use its
full path, or ask Steve to restart the Claude app.

## 2. Try it with fake homes

Show Steve that it works before you ask him for anything.

```
uv run python -m sellers pull demo
uv run python -m sellers top --n 3
uv run python -m sellers report
```

Explain the report in 2-3 lines: each row is a home, the score is the number of
signs that the owner might sell, and "Why it scored" lists them. Tell him these
are fake homes for practice.

## 3. About Steve

Ask these one at a time. Save the answers in `settings.toml`.

1. Under `[me]`: his name, brokerage, DRE license number, phone, and office
   postal address. Say why: the law requires the license number and a postal
   address in emails to sellers.
2. Under `[area]`: which Orange County cities to start with. Suggest 2-3.
   Ask which home types: Single Family, Condo, Townhouse, Multi-Family.

## 4. Gmail

1. Check that you have the Gmail connector (tools with `Gmail` in the name).
2. If you do not have it, tell Steve: "Go to claude.ai, open Settings, then
   Connectors, and connect Gmail with your work Google account. Then come back
   and start a new chat in this folder." Stop here until he has done that.
3. Test it. Ask for his email address, then create a **draft** (do not send it)
   to himself with the subject "OC Seller Finder test" and a one-line body.
   Ask him to look in his Gmail Drafts folder. Then he can delete it.

## 5. Real data (pick one; he can add more later)

Explain the choices in `docs/DATA_SOURCES.md` in a few lines. Recommend
**RentCast** as the free start (50 requests a month at no cost; 1 request = 1 city).

To add a key:
1. Steve signs up on the provider's website and copies his API key.
2. Copy `.env.example` to `.env` if `.env` does not exist yet.
3. Open `.env` for him (Windows: `notepad .env`, Mac: `open -e .env`). He pastes
   the key after the `=` on the right line, saves, and closes the file.
   **Never ask him to paste a key into the chat.**
4. Run `uv run python -m sellers sources`. It should say "ready (key found)".
5. Remove the fake homes: `uv run python -m sellers reset-demo`.
6. Pull one city first: `uv run python -m sellers pull rentcast --city "<city>"`.
   This uses 1 request. Then show the top homes.

If he has CRMLS, he can also export a list from Realist and load it (see
`/find-sellers`).

## 6. His own copy on GitHub

This backs up his work and lets him undo mistakes. It is free.

1. Ask if he has a GitHub account. If not, he signs up at https://github.com/signup.
2. Sign in: run `gh auth login --hostname github.com --git-protocol https --web`
   in the background. Read the one-time code it prints, show it to Steve, and
   have him enter it on the GitHub page that opens. If that does not work, ask
   him to type `! gh auth login` in this chat and follow the questions.
3. Run `gh auth setup-git`.
4. Make his private copy:
   ```
   git remote rename origin upstream
   gh repo create oc-seller-finder --private --source . --remote origin --push
   ```
   Check that `git remote -v` shows his account for `origin`.
5. Ask if he wants Jeff to be able to help. If yes, run
   `gh api -X PUT repos/<his-username>/oc-seller-finder/collaborators/grijalva10`.
   Jeff gets an invite by email.

## 7. Done

1. Save the settings with `/save-work`.
2. Tell Steve:
   - "From now on, open the Claude app, start a new **Code** session, and pick
     the `oc-seller-finder` folder. Then just tell me what you want."
   - Show him `docs/CHEAT_SHEET.md`: the things he can say.
3. Suggest a first real task: "Ask me to find sellers in <his city>, then write
   5 emails."
