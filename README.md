# OC Seller Finder

Find Orange County homeowners who might sell before they list, and write them
personal emails. Built to be run and changed by talking to Claude, with no
coding experience needed.

## Start here (Steve)

1. Install the **Claude** desktop app from [claude.ai/download](https://claude.ai/download)
   and sign in.
2. In the app, open **Code** and choose your **Documents** folder.
3. Paste this message and press Enter:

   > Set up my OC Seller Finder project from
   > https://github.com/grijalva10/oc-seller-finder
   > Clone it into this folder (install git first if it is missing). Then read
   > docs/SETUP.md inside it and walk me through it one step at a time. I have
   > never coded before.

Claude installs what is needed and shows you how it works with fake homes. Then
it connects your Gmail and a data source. Setup takes about 20-30 minutes.

After setup, see [docs/CHEAT_SHEET.md](docs/CHEAT_SHEET.md) for what you can say.

## How it works

```
Data source  →  Score each home  →  Find owner email  →  Claude writes email  →  Gmail draft  →  You send
(RentCast,      (signs the owner     (Tracerfy)            (personal, legal      (you review it)
 spreadsheet)    might sell)                                footer included)
```

- **Your data stays on your computer**, in `data/`. It is never uploaded to GitHub.
- **Claude never sends email.** It saves drafts. You read them and press Send.
- **Nothing costs money without asking you first.** Free test modes let you practise.

## Scoring

Each home gets points for signs that the owner might sell. You can change the
points in `settings.toml`.

| Sign | Points |
|---|---|
| Owner gets mail at a different address | 25 |
| ...and that address is out of state | +15 |
| Owned 20+ years (or 10-19 years) | 25 (15) |
| Worth 2x+ what they paid | 20 |
| Owned by a trust | 5 |
| Owner has 3+ homes on your list | 10 |

## For whoever helps with the code

- Python 3.11+, standard library only. Run with `uv run python -m sellers --help`.
- Tests: `uv run pytest`.
- `CLAUDE.md` has the rules Claude follows. `.claude/skills/` has the workflows.
  `.claude/settings.json` blocks force push, hard reset, reading `.env`, and
  sending email.
- Data sources: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).
- Third-party skills (`git-commit`, `systematic-debugging`,
  `verification-before-completion`) are MIT-licensed copies. Their licenses are
  in `.claude/skills/THIRD_PARTY_LICENSES/`.
