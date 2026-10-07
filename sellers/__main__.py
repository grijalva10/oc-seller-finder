"""The commands. Claude runs these for you. You can run them yourself too:

    uv run python -m sellers <command>

Commands:
    sources                     list data sources and whether each one is ready
    pull <source> [--limit N]   get homes from a data source (demo, rentcast)
    import <file.csv>           load homes from a spreadsheet you exported
    find-emails [--n 5] [--test]
                                look up owner emails/phones with Tracerfy (costs money
                                unless --test)
    score                       give every home points (uses settings.toml)
    top [--n 10] [--city X] [--need-email] [--status new] [--json]
                                show the best homes to contact next
    show <id>                   everything we know about one home
    mark <id> <status> [--note "..."]
                                update where a home is in your process
    block <email>               never email this address again
    report                      make data/report.html and open it
    export                      save everything to data/export.csv
    reset-demo                  remove the fake demo homes
"""
import argparse
import csv
import importlib
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from . import db
from .config import DATA, api_key, settings
from .report import write_report
from .score import score_all

SOURCES = ["demo", "csv_file", "rentcast"]


def load_source(name: str):
    try:
        return importlib.import_module("sellers.sources." + name)
    except ModuleNotFoundError:
        sys.exit("Unknown data source %r. Run: uv run python -m sellers sources" % name)


def cmd_sources(_args):
    for name in SOURCES:
        src = load_source(name)
        if not src.NEEDS_KEY:
            ready = "ready"
        elif api_key(src.NEEDS_KEY):
            ready = "ready (key found)"
        else:
            ready = "needs %s in .env" % src.NEEDS_KEY
        print("%-10s %-24s %s" % (src.NAME, ready, src.ABOUT))


def _save_and_score(con, homes):
    added, updated = db.save_properties(con, homes)
    score_all(con, settings().get("scoring", {}))
    print("Added %d new homes, refreshed %d. Scores updated." % (added, updated))


def cmd_pull(args):
    src = load_source(args.source)
    if args.source == "csv_file":
        sys.exit("To load a spreadsheet, use: uv run python -m sellers import <file.csv>")
    if src.NEEDS_KEY and not api_key(src.NEEDS_KEY):
        sys.exit("%s needs an API key. Put %s=... in the .env file. See docs/DATA_SOURCES.md."
                 % (src.NAME, src.NEEDS_KEY))
    area = settings().get("area", {})
    cities = [args.city] if args.city else area.get("cities", [])
    homes = src.fetch(cities=cities, property_types=area.get("property_types", []), limit=args.limit,
                      min_years_owned=area.get("min_years_owned", 0),
                      key=api_key(src.NEEDS_KEY) if src.NEEDS_KEY else None)
    print("Got %d homes from %s." % (len(homes), src.NAME))
    _save_and_score(db.connect(), homes)


def cmd_import(args):
    from .sources import csv_file
    homes, colmap, unused = csv_file.read(args.file)
    if not homes:
        sys.exit("No rows found in %s." % args.file)
    print("Read %d rows. Matched columns:" % len(homes))
    for field, col in colmap.items():
        print("  %-16s <- %s" % (field, col))
    if "address" not in colmap:
        sys.exit("Could not find the property address column. Add its name to ALIASES in sellers/sources/csv_file.py.")
    if unused:
        print("Columns not used: %s" % ", ".join(unused))
    _save_and_score(db.connect(), homes)


def cmd_find_emails(args):
    from . import contacts
    key = api_key(contacts.NEEDS_KEY)
    if not args.test and not key:
        sys.exit("Tracerfy needs an API key. Put TRACERFY_API_KEY=... in .env, or use --test to practise for free.")
    con = db.connect()
    rows = con.execute("""SELECT * FROM properties WHERE status='new' AND (email IS NULL OR email='')
                          AND source != 'demo' ORDER BY score DESC LIMIT ?""" if not args.test else
                       """SELECT * FROM properties WHERE status='new' AND (email IS NULL OR email='')
                          ORDER BY score DESC LIMIT ?""", (args.n,)).fetchall()
    if not rows:
        print("No homes need an email right now.")
        return
    found = 0
    for r in rows:
        result = contacts.lookup(dict(r), key, args.test)
        email, phone = contacts.best_contact(result)
        if args.test and email:
            # Practice data must never reach a real inbox.
            email = email.split("@")[0] + "@example.com"
        if email or phone:
            found += 1
            con.execute("UPDATE properties SET email=COALESCE(email, ?), phone=COALESCE(phone, ?) WHERE id=?",
                        (email, phone, r["id"]))
            con.execute("INSERT INTO history (property_id, at, what) VALUES (?, ?, ?)",
                        (r["id"], db.now(), "contact found%s: %s %s" % (" (TEST, fake)" if args.test else "",
                                                                      email or "", phone or "")))
        print("#%-4d %s: %s" % (r["id"], r["address"], email or phone or "nothing found"))
    con.commit()
    print("Found contact info for %d of %d homes.%s" % (found, len(rows),
          " These are FAKE test results." if args.test else ""))


def cmd_score(_args):
    n = score_all(db.connect(), settings().get("scoring", {}))
    print("Scored %d homes." % n)


def cmd_top(args):
    con = db.connect()
    statuses = [x.strip() for x in args.status.split(",") if x.strip()]
    sql = "SELECT * FROM properties WHERE status IN (%s)" % ",".join("?" for _ in statuses)
    params = list(statuses)
    if args.city:
        sql += " AND city=?"
        params.append(args.city)
    if args.need_email:
        sql += " AND email IS NOT NULL AND email != ''"
    sql += " ORDER BY score DESC, id LIMIT ?"
    rows = [db.as_dict(r) for r in con.execute(sql, params + [args.n * 3])]
    if statuses == ["new"]:
        rows = [r for r in rows if not db.is_blocked(con, r["email"])]
    rows = rows[: args.n]
    if args.json:
        print(json.dumps(rows, indent=1))
        return
    if not rows:
        print("No new homes to show. Pull more data, or check your filters.")
    for r in rows:
        print("#%-4d score %-3d %s, %s  |  owner: %s  |  email: %s  |  %s"
              % (r["id"], r["score"], r["address"], r["city"], r["owner_name"], r["email"] or "none",
                 r["status"]))
        for why in r["reasons"]:
            print("        " + why)


def cmd_show(args):
    con = db.connect()
    row = con.execute("SELECT * FROM properties WHERE id=?", (args.id,)).fetchone()
    if not row:
        sys.exit("No home with id %s" % args.id)
    home = db.as_dict(row)
    home["email_blocked"] = db.is_blocked(con, home["email"])
    home["history"] = [dict(h) for h in con.execute(
        "SELECT at, what FROM history WHERE property_id=? ORDER BY id", (args.id,))]
    print(json.dumps(home, indent=1))


def cmd_mark(args):
    try:
        db.set_status(db.connect(), args.id, args.status, args.note or "")
    except ValueError as e:
        sys.exit(str(e))
    print("Home #%d is now: %s" % (args.id, args.status))


def cmd_block(args):
    db.block_email(db.connect(), args.email)
    print("%s will never be emailed again." % args.email)


def cmd_report(args):
    path = write_report(db.connect(), datetime.now().strftime("%b %d, %Y %I:%M %p"))
    print("Report saved: %s" % path)
    if not args.no_open:
        webbrowser.open(Path(path).as_uri())


def cmd_export(_args):
    con = db.connect()
    rows = [dict(r) for r in con.execute("SELECT * FROM properties ORDER BY score DESC")]
    path = DATA / "export.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            for r in rows:
                # Stop spreadsheet apps from running cell text as a formula.
                w.writerow({k: ("'" + v if isinstance(v, str) and v[:1] in "=+-@" else v) for k, v in r.items()})
    print("Saved %d homes to %s" % (len(rows), path))


def cmd_reset_demo(_args):
    con = db.connect()
    ids = [r[0] for r in con.execute("SELECT id FROM properties WHERE source='demo'")]
    con.executemany("DELETE FROM history WHERE property_id=?", [(i,) for i in ids])
    con.execute("DELETE FROM properties WHERE source='demo'")
    con.execute("DELETE FROM do_not_contact WHERE email LIKE '%@example.com'")
    con.commit()
    print("Removed %d demo homes." % len(ids))


def main(argv=None):
    p = argparse.ArgumentParser(prog="sellers", description="Find off-market home sellers in Orange County.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sources").set_defaults(fn=cmd_sources)
    s = sub.add_parser("pull")
    s.add_argument("source")
    s.add_argument("--limit", type=int, default=50)
    s.add_argument("--city")
    s.set_defaults(fn=cmd_pull)
    s = sub.add_parser("import")
    s.add_argument("file")
    s.set_defaults(fn=cmd_import)
    s = sub.add_parser("find-emails")
    s.add_argument("--n", type=int, default=5)
    s.add_argument("--test", action="store_true")
    s.set_defaults(fn=cmd_find_emails)
    sub.add_parser("score").set_defaults(fn=cmd_score)
    s = sub.add_parser("top")
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--city")
    s.add_argument("--need-email", action="store_true")
    s.add_argument("--status", default="new", help="comma-separated, e.g. drafted,emailed")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_top)
    s = sub.add_parser("show")
    s.add_argument("id", type=int)
    s.set_defaults(fn=cmd_show)
    s = sub.add_parser("mark")
    s.add_argument("id", type=int)
    s.add_argument("status", choices=list(db.STATUSES))
    s.add_argument("--note")
    s.set_defaults(fn=cmd_mark)
    s = sub.add_parser("block")
    s.add_argument("email")
    s.set_defaults(fn=cmd_block)
    s = sub.add_parser("report")
    s.add_argument("--no-open", action="store_true")
    s.set_defaults(fn=cmd_report)
    sub.add_parser("export").set_defaults(fn=cmd_export)
    sub.add_parser("reset-demo").set_defaults(fn=cmd_reset_demo)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
