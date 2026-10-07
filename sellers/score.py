"""Give each home points for signs that the owner might sell.

The rules are simple on purpose, so you can read them and change them.
The point values come from the [scoring] part of settings.toml.
A missing fact gives zero points. It never counts against the home.
"""
import json
import re
from collections import Counter
from datetime import date


def _street(text: str | None) -> str:
    """'123 Main St.' and '123 MAIN STREET' should look the same."""
    t = re.sub(r"[^a-z0-9 ]", "", (text or "").lower())
    t = re.sub(r"\b(street|st|avenue|ave|drive|dr|road|rd|lane|ln|court|ct|way|place|pl)\b", "", t)
    return re.sub(r"\s+", " ", t).strip()


def is_absentee(p: dict) -> bool | None:
    """True if the owner gets mail somewhere else. None if we cannot tell."""
    if p.get("owner_occupied") is not None:
        return not p["owner_occupied"]
    if not p.get("mail_address"):
        return None
    return _street(p["mail_address"]) != _street(p["address"])


def years_owned(p: dict, today: date | None = None) -> int | None:
    sale = p.get("last_sale_date")
    if not sale:
        return None
    try:
        bought = date.fromisoformat(str(sale)[:10])
    except ValueError:
        return None
    today = today or date.today()
    return today.year - bought.year - ((today.month, today.day) < (bought.month, bought.day))


def score_one(p: dict, rules: dict, owner_counts: Counter, today: date | None = None) -> tuple[int, list[str]]:
    points, reasons = 0, []

    def add(rule: str, why: str) -> None:
        nonlocal points
        n = int(rules.get(rule, 0))
        if n:
            points += n
            reasons.append("+%d %s" % (n, why))

    if is_absentee(p):
        add("absentee_owner", "owner gets mail at a different address")
        state = (p.get("mail_state") or "").strip().upper()
        if state and state not in ("CA", "CALIFORNIA"):
            add("out_of_state_owner", "owner lives out of state (%s)" % state)

    years = years_owned(p, today)
    if years is not None and years >= 20:
        add("owned_20_years", "owned for %d years" % years)
    elif years is not None and years >= 10:
        add("owned_10_years", "owned for %d years" % years)

    value, paid = p.get("est_value"), p.get("last_sale_price")
    if value and paid and paid > 0 and value >= 2 * paid:
        add("high_equity", "worth about %.1fx what they paid" % (value / paid))

    if re.search(r"\btrust\b|\btr\b|\btrustee\b", (p.get("owner_name") or "").lower()):
        add("trust_owner", "owned by a trust")

    owner = (p.get("owner_name") or "").strip().upper()
    if owner and owner_counts[owner] >= 3:
        add("owns_several_homes", "owner has %d homes on your list" % owner_counts[owner])

    return points, reasons


def score_all(con, rules: dict) -> int:
    rows = [dict(r) for r in con.execute("SELECT * FROM properties")]
    owner_counts = Counter((r.get("owner_name") or "").strip().upper() for r in rows)
    for r in rows:
        points, reasons = score_one(r, rules, owner_counts)
        con.execute("UPDATE properties SET score=?, reasons=? WHERE id=?",
                    (points, json.dumps(reasons), r["id"]))
    con.commit()
    return len(rows)
