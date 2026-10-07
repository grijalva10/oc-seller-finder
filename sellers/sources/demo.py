"""Fake Orange County homes for practice. No real people, no API key needed.

Every email uses example.com, a domain that can never reach a real person.
"""
import random
from datetime import date, timedelta

NAME = "demo"
NEEDS_KEY = None
ABOUT = "Fake practice homes. Free. Use this to learn the system before you pay for data."

CITIES = {
    "San Clemente": "92672", "Dana Point": "92629", "San Juan Capistrano": "92675",
    "Laguna Niguel": "92677", "Mission Viejo": "92691", "Irvine": "92618",
    "Newport Beach": "92660", "Huntington Beach": "92648", "Costa Mesa": "92626",
}
STREETS = ["Calle Del Mar", "Vista Ridge", "Ocean View Dr", "Avenida Pico", "Camino Real",
           "Sea Breeze Ln", "Harbor Ct", "Oak Canyon Rd", "Monarch Bay Dr", "Pacific Way"]
FIRST = ["Alex", "Jordan", "Sam", "Taylor", "Casey", "Morgan", "Riley", "Jamie", "Drew", "Avery"]
LAST = ["Sample", "Tester", "Example", "Demo", "Placeholder", "Fakename", "Notreal", "Mockley"]
AWAY = [("Phoenix", "AZ", "85001"), ("Austin", "TX", "73301"), ("Boise", "ID", "83701"),
        ("Irvine", "CA", "92618"), ("Los Angeles", "CA", "90001")]
TYPES = ["Single Family"] * 4 + ["Condo", "Townhouse"]


def fetch(cities: list[str], property_types: list[str], limit: int = 60, **_) -> list[dict]:
    rng = random.Random(42)  # same fake homes every time
    cities = [c for c in cities if c in CITIES] or list(CITIES)
    landlord = "%s FAMILY TRUST" % rng.choice(LAST).upper()
    out = []
    for i in range(limit):
        city = cities[i % len(cities)]
        address = "%d %s" % (rng.randint(100, 39999), rng.choice(STREETS))
        bought = date.today() - timedelta(days=rng.randint(1, 35) * 365 + rng.randint(0, 364))
        paid = rng.randint(30, 160) * 10_000
        years = (date.today() - bought).days / 365
        value = int(paid * (1 + 0.06 * years) // 10_000 * 10_000)
        first, last = rng.choice(FIRST), rng.choice(LAST)
        owner = "%s %s. %s" % (first.upper(), chr(65 + i % 26), last.upper())
        if rng.random() < 0.2:
            owner = "%s FAMILY TRUST" % last.upper()
        if i % 15 == 0:
            owner = landlord
        away = rng.random() < 0.35 or owner == landlord
        mail = (("%d Main St" % rng.randint(10, 999),) + rng.choice(AWAY)) if away else (address, city, "CA", CITIES[city])
        out.append({
            "apn": "DEMO-%03d-%03d-%02d" % (rng.randint(100, 999), rng.randint(100, 999), i),
            "address": address, "city": city, "zip": CITIES[city],
            "property_type": rng.choice(TYPES),
            "beds": rng.randint(2, 5), "baths": rng.choice([2, 2.5, 3, 3.5]),
            "sqft": rng.randint(12, 40) * 100, "year_built": rng.randint(1960, 2015),
            "owner_name": owner,
            "mail_address": mail[0], "mail_city": mail[1], "mail_state": mail[2], "mail_zip": mail[3],
            "owner_occupied": None,
            "last_sale_date": bought.isoformat(), "last_sale_price": paid, "est_value": value,
            "email": "%s.%s@example.com" % (first.lower(), last.lower()) if rng.random() < 0.6 else None,
            "phone": None,
            "source": NAME,
        })
    wanted = set(property_types or [])
    return [p for p in out if not wanted or p["property_type"] in wanted]
