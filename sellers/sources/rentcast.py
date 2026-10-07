"""RentCast: owner name, mailing address and last sale for homes in a city.

Free plan: 50 requests a month. One request returns up to 500 homes.
Docs: https://developers.rentcast.io/reference/property-records
"""
import json
import urllib.error
import urllib.parse
import urllib.request

NAME = "rentcast"
NEEDS_KEY = "RENTCAST_API_KEY"
ABOUT = "Owner names + mailing addresses. Free for 50 requests/month, then $74/month."

URL = "https://api.rentcast.io/v1/properties"


def _get(params: dict, key: str) -> list[dict]:
    req = urllib.request.Request(URL + "?" + urllib.parse.urlencode(params),
                                 headers={"X-Api-Key": key, "Accept": "application/json",
                                          "User-Agent": "oc-seller-finder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        if e.code == 401:
            raise SystemExit("RentCast says the API key is wrong. Check RENTCAST_API_KEY in .env.")
        if e.code == 429:
            raise SystemExit("RentCast says you used up your requests for now. Try again later.")
        raise SystemExit("RentCast error %d: %s" % (e.code, body))


def to_home(p: dict) -> dict:
    owner = p.get("owner") or {}
    mail = owner.get("mailingAddress") or {}
    occupied = p.get("ownerOccupied")
    return {
        "apn": p.get("assessorID"),
        "address": p.get("addressLine1") or p.get("formattedAddress"),
        "city": p.get("city"), "zip": p.get("zipCode"),
        "property_type": p.get("propertyType"),
        "beds": p.get("bedrooms"), "baths": p.get("bathrooms"),
        "sqft": p.get("squareFootage"), "year_built": p.get("yearBuilt"),
        "owner_name": " & ".join(owner.get("names") or []) or None,
        "mail_address": mail.get("addressLine1"), "mail_city": mail.get("city"),
        "mail_state": mail.get("state"), "mail_zip": mail.get("zipCode"),
        "owner_occupied": None if occupied is None else int(bool(occupied)),
        "last_sale_date": (p.get("lastSaleDate") or "")[:10] or None,
        "last_sale_price": p.get("lastSalePrice"),
        # RentCast property records have no market value. Its value
        # estimate is a separate paid request, so we leave this empty.
        "est_value": None,
        "email": None, "phone": None, "source": NAME,
    }


def fetch(cities: list[str], property_types: list[str], limit: int = 50, key: str = "",
          min_years_owned: int = 0, **_) -> list[dict]:
    """One request per city. Each request counts against your monthly plan."""
    homes = []
    for city in cities:
        params = {"city": city, "state": "CA", "limit": max(1, min(limit, 500))}
        if property_types:
            params["propertyType"] = "|".join(property_types)
        if min_years_owned:
            # Only homes whose last sale was at least this many years ago.
            params["saleDateRange"] = "%d:*" % (min_years_owned * 365)
        found = _get(params, key)
        print("  %s: %d homes" % (city, len(found)))
        homes += [to_home(p) for p in found if p.get("addressLine1") or p.get("formattedAddress")]
    return homes
