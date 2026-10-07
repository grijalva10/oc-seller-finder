"""The local database: one file, data/sellers.db. It never goes to GitHub.

Every data source turns its records into the same shape (the FIELDS below),
so the rest of the program does not care where a home came from.
"""
import json
import re
import sqlite3
from datetime import datetime

from .config import DATA

DB_PATH = DATA / "sellers.db"

# The shape every data source must produce. Missing values are None.
FIELDS = [
    "apn", "address", "city", "zip", "property_type", "beds", "baths", "sqft", "year_built",
    "owner_name", "mail_address", "mail_city", "mail_state", "mail_zip", "owner_occupied",
    "last_sale_date", "last_sale_price", "est_value", "email", "phone", "source",
]

# Where each home is in your process.
STATUSES = {
    "new": "Not looked at yet",
    "skip": "You decided not to contact",
    "drafted": "Email draft is waiting in Gmail",
    "emailed": "You sent the email",
    "replied": "Owner replied",
    "interested": "Owner is open to talking",
    "not_interested": "Owner said no",
    "do_not_contact": "Never contact again",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    apn TEXT, address TEXT NOT NULL, city TEXT, zip TEXT, property_type TEXT,
    beds REAL, baths REAL, sqft INTEGER, year_built INTEGER,
    owner_name TEXT, mail_address TEXT, mail_city TEXT, mail_state TEXT, mail_zip TEXT,
    owner_occupied INTEGER,
    last_sale_date TEXT, last_sale_price INTEGER, est_value INTEGER,
    email TEXT, phone TEXT, source TEXT, updated_at TEXT,
    score INTEGER NOT NULL DEFAULT 0,
    reasons TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'new',
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS do_not_contact (
    email TEXT PRIMARY KEY,
    added_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES properties(id),
    at TEXT NOT NULL,
    what TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DATA.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def property_key(rec: dict) -> str:
    """One home = one key. Use the parcel number (APN) when we have it."""
    if rec.get("apn"):
        return "apn:" + re.sub(r"[^0-9A-Za-z]", "", str(rec["apn"]))
    addr = re.sub(r"[^a-z0-9]", "", (rec.get("address") or "").lower())
    return "addr:%s:%s" % (addr, (rec.get("zip") or "")[:5])


def save_properties(con: sqlite3.Connection, records: list[dict]) -> tuple[int, int]:
    """Add new homes and refresh known ones. Never erases your status or notes.
    Returns (added, updated)."""
    added = updated = 0
    for rec in records:
        if not rec.get("address"):
            continue
        row = {f: rec.get(f) for f in FIELDS}
        key = property_key(rec)
        old = con.execute("SELECT id FROM properties WHERE key=?", (key,)).fetchone()
        if old:
            # Only overwrite a field when the new record actually has a value.
            sets = ", ".join("%s=COALESCE(?, %s)" % (f, f) for f in FIELDS)
            con.execute("UPDATE properties SET %s, updated_at=? WHERE id=?" % sets,
                        [row[f] for f in FIELDS] + [now(), old["id"]])
            updated += 1
        else:
            cols = ", ".join(FIELDS)
            marks = ", ".join("?" for _ in FIELDS)
            con.execute("INSERT INTO properties (key, %s, updated_at) VALUES (?, %s, ?)" % (cols, marks),
                        [key] + [row[f] for f in FIELDS] + [now()])
            added += 1
    con.commit()
    return added, updated


def set_status(con: sqlite3.Connection, prop_id: int, status: str, note: str = "") -> None:
    if status not in STATUSES:
        raise ValueError("Unknown status %r. Use one of: %s" % (status, ", ".join(STATUSES)))
    row = con.execute("SELECT email FROM properties WHERE id=?", (prop_id,)).fetchone()
    if not row:
        raise ValueError("No home with id %s" % prop_id)
    con.execute("UPDATE properties SET status=? WHERE id=?", (status, prop_id))
    what = "status -> " + status + (": " + note if note else "")
    con.execute("INSERT INTO history (property_id, at, what) VALUES (?, ?, ?)", (prop_id, now(), what))
    if note:
        con.execute("UPDATE properties SET notes = CASE WHEN notes='' THEN ? ELSE notes || char(10) || ? END WHERE id=?",
                    ("%s %s" % (now()[:10], note),) * 2 + (prop_id,))
    if status == "do_not_contact" and row["email"]:
        block_email(con, row["email"])
    con.commit()


def block_email(con: sqlite3.Connection, email: str) -> None:
    con.execute("INSERT OR IGNORE INTO do_not_contact (email, added_at) VALUES (?, ?)",
                (email.strip().lower(), now()))
    con.commit()


def is_blocked(con: sqlite3.Connection, email: str | None) -> bool:
    if not email:
        return False
    return con.execute("SELECT 1 FROM do_not_contact WHERE email=?",
                       (email.strip().lower(),)).fetchone() is not None


def as_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["reasons"] = json.loads(d.get("reasons") or "[]")
    return d
