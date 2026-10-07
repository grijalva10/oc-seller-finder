"""Quick checks that the main pieces still work. Run: uv run pytest"""
from collections import Counter
from datetime import date

import pytest

from sellers import db
from sellers.score import is_absentee, score_one
from sellers.sources import csv_file, demo, rentcast

RULES = {"absentee_owner": 25, "out_of_state_owner": 15, "owned_10_years": 15, "owned_20_years": 25,
         "high_equity": 20, "trust_owner": 5, "owns_several_homes": 10}


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    return db.connect()


def test_scoring_gives_points_with_reasons():
    home = {"address": "1 Ocean Way", "mail_address": "9 Main St", "mail_state": "TX",
            "last_sale_date": "2000-01-01", "last_sale_price": 300000, "est_value": 1500000,
            "owner_name": "SMITH FAMILY TRUST", "owner_occupied": None}
    points, reasons = score_one(home, RULES, Counter(), today=date(2026, 6, 1))
    assert points == 25 + 15 + 25 + 20 + 5
    assert len(reasons) == 5


def test_missing_facts_give_zero_points():
    points, reasons = score_one({"address": "1 Ocean Way"}, RULES, Counter())
    assert points == 0 and reasons == []


def test_same_street_written_differently_is_not_absentee():
    assert is_absentee({"address": "123 Main Street", "mail_address": "123 MAIN ST."}) is False


def test_saving_twice_does_not_duplicate_or_erase_status(con):
    homes = demo.fetch(cities=["Dana Point"], property_types=[], limit=5)
    assert db.save_properties(con, homes) == (5, 0)
    db.set_status(con, 1, "skip", "not a fit")
    assert db.save_properties(con, homes) == (0, 5)
    row = con.execute("SELECT status, notes FROM properties WHERE id=1").fetchone()
    assert row["status"] == "skip" and "not a fit" in row["notes"]


def test_do_not_contact_blocks_the_email(con):
    db.save_properties(con, [{"address": "1 A St", "email": "Owner@Example.com"}])
    db.set_status(con, 1, "do_not_contact")
    assert db.is_blocked(con, "owner@example.com")


def test_demo_emails_never_reach_real_people():
    homes = demo.fetch(cities=[], property_types=[], limit=60)
    assert all(h["email"].endswith("@example.com") for h in homes if h["email"])


def test_csv_import_understands_common_column_names(tmp_path):
    f = tmp_path / "export.csv"
    f.write_text("Site Address,Site City,Site Zip,Owner 1 First Name,Owner 1 Last Name,Mailing Address,"
                 "Mailing State,Last Sale Recording Date,Last Sale Amount\n"
                 "1 Ocean Way,Dana Point,92629,Pat,Smith,9 Main St,TX,03/15/2001,\"$450,000\"\n")
    homes, colmap, unused = csv_file.read(str(f))
    h = homes[0]
    assert h["address"] == "1 Ocean Way" and h["owner_name"] == "Pat Smith"
    assert h["last_sale_date"] == "2001-03-15" and h["last_sale_price"] == 450000
    assert unused == []


def test_rentcast_record_is_converted():
    home = rentcast.to_home({
        "addressLine1": "1 Ocean Way", "city": "Dana Point", "zipCode": "92629", "assessorID": "123-456-78",
        "lastSaleDate": "2001-03-15T00:00:00.000Z", "lastSalePrice": 450000, "ownerOccupied": False,
        "owner": {"names": ["Pat Smith", "Lee Smith"],
                  "mailingAddress": {"addressLine1": "9 Main St", "city": "Austin", "state": "TX"}},
    })
    assert home["owner_name"] == "Pat Smith & Lee Smith"
    assert home["owner_occupied"] == 0 and home["mail_state"] == "TX"
    assert home["last_sale_date"] == "2001-03-15"
