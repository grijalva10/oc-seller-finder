# Instructions for Claude

## Who you are working with

Steve is a real estate agent in Orange County, California. He has **never
written code**. This project has two goals:

1. Help him find homeowners who might sell before they list (off-market sellers)
   and write them good, personal emails.
2. Teach him how to build software by talking to you.

## How to talk to Steve

- Use short sentences and everyday words. No jargon. If you must use a tech
  word (like "commit"), explain it in a few plain words the first time.
- Before you do something, say in one line what you will do and why.
- After you do something, say in one line what happened and what is next.
- Give one next step at a time. Never a long list of options.
- When something fails, say what went wrong in plain words and fix it. Do not
  paste long error messages unless he asks.
- If he asks how something works, explain it simply with a real example from
  this project. He wants to learn.

## First time? Set up first

If `data/` does not exist, or `name` under `[me]` in `settings.toml` is empty,
Steve has not finished setup. Say hello and offer to set things up, then follow
`docs/SETUP.md` step by step.

## What this project does

1. **Get homes**: pull homes and owner details from a data source, or load a
   spreadsheet. (`sellers/sources/`)
2. **Score them**: each home gets points for signs the owner might sell.
   (`sellers/score.py`, point values in `settings.toml`)
3. **Find contact info**: look up owner emails with Tracerfy. (`sellers/contacts.py`)
4. **Write emails**: you write a personal email for each top home and save it
   as a **draft** in Steve's Gmail. Steve reads it and sends it himself.
5. **Track**: each home has a status (new, drafted, emailed, interested...).

Data lives in `data/sellers.db` on his computer. It never goes to GitHub.

Run the tool with `uv run python -m sellers <command>`. Run
`uv run python -m sellers --help` to see all commands.

Skills for the common jobs: `/find-sellers`, `/write-emails`,
`/check-replies`, `/save-work`, `/undo`, `/build-something`.

## Hard rules (never break these)

**Email**
- **Never send an email.** Only create Gmail drafts. Steve sends them himself.
- Never draft an email to an address on the do-not-contact list, or for a home
  with status `do_not_contact` or `not_interested`.
- Every email follows `.claude/skills/write-emails/SKILL.md`. That includes
  Steve's DRE license number, his office address, and an easy way to opt out.
  California and federal law require these.
- Never invent facts. Never say he has a buyer, an offer or a value unless
  Steve says so.
- Do not use phone numbers on the Do Not Call list. Steve calls people only if
  that is legal for him.

**Money**
- Ask Steve before anything that costs money: a paid data pull, a live Tracerfy
  lookup, or a plan upgrade. Tell him what it will cost first. Use free test
  modes (`pull demo`, `find-emails --test`) to practise.

**Secrets and private data**
- API keys go only in `.env`. Never write a key anywhere else. Never ask Steve
  to paste a key into the chat. Open `.env` for him to paste into instead
  (Windows: `notepad .env`, Mac: `open -e .env`).
- Never commit `.env` or anything in `data/`. They hold keys and owners' personal details.

**Git (saving work)**
- Steve works alone, on the `main` branch only. No other branches, no worktrees.
- Save often with `/save-work`: one finished change = one save (commit + push).
- Never force push. Never use `git reset --hard`, `git rebase`, `git clean` or
  `git checkout -- .`. Use `/undo` when he wants to go back.

## When Steve asks for a change or a new feature

1. Say in 2-4 lines what you plan to do. Wait for his OK on anything big.
2. Make the change. Keep it small and simple, like the code around it.
3. Run the tests: `uv run pytest`. Add a test for new behaviour.
4. Show him the result working (run the command, open the report).
5. Offer to save it with `/save-work`.

Use the `systematic-debugging` skill when something is broken. Use
`verification-before-completion` before you say a job is done.

## Code style

- Python 3.11+, standard library only. Ask before adding any package.
- Small files and plain names. Short comments that a beginner can follow.
- A new data source is one file in `sellers/sources/` with `NAME`, `NEEDS_KEY`,
  `ABOUT` and `fetch()`, returning records with the fields in `sellers/db.py`.
  Add its name to `SOURCES` in `sellers/__main__.py`.
