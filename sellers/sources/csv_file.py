"""Load homes from a spreadsheet file (.csv).

Works with exports from Realist (free with CRMLS), PropStream, and most list
sellers. Column names differ between tools, so ALIASES maps the common ones.
If a column is not recognized, add its name to ALIASES.
"""
import csv
import re
from datetime import datetime

NAME = "csv"
NEEDS_KEY = None
ABOUT = "Load a .csv file you exported (Realist, PropStream, etc). Free with tools you already have."

# our field name -> column names other tools use (lowercase, letters and digits only)
ALIASES = {
    "apn": ["apn", "parcelnumber", "parcelid", "assessorparcelnumber", "apnformatted"],
    "address": ["siteaddress", "propertyaddress", "address", "situsaddress", "streetaddress", "situsfulladdress"],
    "city": ["sitecity", "propertycity", "city", "situscity"],
    "zip": ["sitezip", "propertyzip", "zip", "zipcode", "situszip", "sitezipcode"],
    "property_type": ["propertytype", "landuse", "usecode", "landusedescription", "propertyusetype"],
    "beds": ["bedrooms", "beds", "bed"],
    "baths": ["bathrooms", "baths", "totalbathrooms", "bath"],
    "sqft": ["buildingsqft", "livingsqft", "sqft", "squarefeet", "livingarea", "buildingsquarefeet"],
    "year_built": ["yearbuilt", "effectiveyearbuilt", "yrbuilt"],
    "owner_name": ["ownername", "owner", "owner1fullname", "ownernames", "owner1name"],
    "mail_address": ["mailingaddress", "owneraddress", "mailaddress", "mailingstreet"],
    "mail_city": ["mailingcity", "ownercity", "mailcity"],
    "mail_state": ["mailingstate", "ownerstate", "mailstate"],
    "mail_zip": ["mailingzip", "ownerzip", "mailzip", "mailingzipcode"],
    "owner_occupied": ["owneroccupied", "owneroccupancy"],
    "last_sale_date": ["saledate", "lastsaledate", "lastsalerecordingdate", "recordingdate", "lastsalesdate"],
    "last_sale_price": ["saleprice", "lastsaleprice", "lastsaleamount", "lastsalesprice"],
    "est_value": ["estvalue", "estimatedvalue", "avm", "marketvalue", "estimatedmarketvalue"],
    "email": ["email", "email1", "owneremail", "emailaddress"],
    "phone": ["phone", "phone1", "ownerphone", "mobile", "phonenumber"],
}
# Some tools split the owner name into first + last columns.
FIRST_NAME = ["owner1firstname", "ownerfirstname", "firstname"]
LAST_NAME = ["owner1lastname", "ownerlastname", "lastname"]


def _simple(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _number(text: str):
    t = re.sub(r"[^0-9.]", "", text or "")
    if not t:
        return None
    n = float(t)
    return int(n) if n.is_integer() else n


def _date(text: str):
    text = (text or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y%m%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            pass
    return None


def _yes_no(text: str):
    t = (text or "").strip().lower()
    if t in ("y", "yes", "true", "1", "owner occupied", "o"):
        return 1
    if t in ("n", "no", "false", "0", "absentee", "a"):
        return 0
    return None


def read(path: str) -> tuple[list[dict], dict, list[str]]:
    """Return (homes, column_map, unused_columns)."""
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return [], {}, []
    headers = list(rows[0].keys())
    by_simple = {_simple(h): h for h in headers if h}
    colmap = {}
    for field, names in ALIASES.items():
        for n in names:
            if n in by_simple:
                colmap[field] = by_simple[n]
                break
    first = next((by_simple[n] for n in FIRST_NAME if n in by_simple), None)
    last = next((by_simple[n] for n in LAST_NAME if n in by_simple), None)

    homes = []
    for r in rows:
        get = lambda f: (r.get(colmap[f]) or "").strip() if f in colmap else ""
        owner = get("owner_name") or " ".join(x for x in [(r.get(first) or "").strip() if first else "",
                                                          (r.get(last) or "").strip() if last else ""] if x)
        homes.append({
            "apn": get("apn") or None, "address": get("address"), "city": get("city") or None,
            "zip": get("zip")[:5] or None, "property_type": get("property_type") or None,
            "beds": _number(get("beds")), "baths": _number(get("baths")), "sqft": _number(get("sqft")),
            "year_built": _number(get("year_built")), "owner_name": owner or None,
            "mail_address": get("mail_address") or None, "mail_city": get("mail_city") or None,
            "mail_state": get("mail_state") or None, "mail_zip": get("mail_zip")[:5] or None,
            "owner_occupied": _yes_no(get("owner_occupied")),
            "last_sale_date": _date(get("last_sale_date")), "last_sale_price": _number(get("last_sale_price")),
            "est_value": _number(get("est_value")), "email": get("email") or None,
            "phone": get("phone") or None, "source": NAME,
        })
    used = set(colmap.values()) | {first, last}
    return homes, colmap, [h for h in headers if h and h not in used]
