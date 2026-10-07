"""Find owner emails and phones with Tracerfy ("skip tracing").

Costs money: about 5 Tracerfy credits per owner found (roughly $0.02-0.04).
No charge when Tracerfy finds nobody. Use --test first: it calls Tracerfy's
free practice server, which returns fake people.
Docs: https://www.tracerfy.com/skip-tracing-api-documentation/
"""
import json
import urllib.error
import urllib.request

NEEDS_KEY = "TRACERFY_API_KEY"
LIVE_URL = "https://tracerfy.com/v1/api/trace/lookup/"
TEST_URL = "https://mock.tracerfy.com/v1/api/trace/lookup/"


def lookup(home: dict, key: str, test: bool) -> dict:
    body = {"address": home["address"], "city": home.get("city") or "", "state": "CA",
            "zip": home.get("zip") or "", "find_owner": True}
    req = urllib.request.Request(TEST_URL if test else LIVE_URL, data=json.dumps(body).encode(),
                                 method="POST", headers={"Authorization": "Bearer " + (key or "test"),
                                                         "Content-Type": "application/json",
                                                         "User-Agent": "oc-seller-finder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise SystemExit("Tracerfy says the API key is wrong. Check TRACERFY_API_KEY in .env.")
        if e.code == 402:
            raise SystemExit("Your Tracerfy account is out of credits. Add credits on tracerfy.com.")
        raise SystemExit("Tracerfy error %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:300]))


def best_contact(result: dict) -> tuple[str | None, str | None]:
    """Pick the top email and top phone of the living property owner."""
    people = [p for p in result.get("persons") or [] if not p.get("deceased")]
    owners = [p for p in people if p.get("property_owner")] or people
    if not owners:
        return None, None
    person = owners[0]
    emails = sorted(person.get("emails") or [], key=lambda e: e.get("rank", 99))
    # Skip numbers on the Do Not Call list.
    phones = sorted((p for p in person.get("phones") or [] if not p.get("dnc")), key=lambda p: p.get("rank", 99))
    return (emails[0]["email"] if emails else None), (phones[0]["number"] if phones else None)
