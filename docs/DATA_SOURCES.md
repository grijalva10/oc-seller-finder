# Data sources

Where to get owner names, mailing addresses and contact info for Orange County
homes. Prices were checked on each provider's website in October 2026. Prices
change, so check them again before you pay.

**Built in** means the code to use it is already in this project.

## Home and owner data

| Source | Built in? | Cost | What you get | Notes |
|---|---|---|---|---|
| **Demo** | Yes | Free | Fake homes | For practice only |
| **Spreadsheet (CSV) import** | Yes | Free with tools you already pay for | Whatever your export has | Works with **Realist** (part of CRMLS), PropStream and most list sellers. Follow your MLS rules about using exported data. |
| **[RentCast](https://www.rentcast.io/api)** | Yes | Free: 50 requests/month. $74/month for 1,000 | Owner name(s), owner mailing address, owner-occupied yes/no, last sale date and price, beds, baths, square feet | **Best place to start.** 1 request = up to 500 homes in one city. The tool asks only for homes owned 10+ years, to save requests. It has no home value, so the "high equity" points do not apply. Key: [app.rentcast.io](https://app.rentcast.io) → API. |
| [PropertyRadar](https://www.propertyradar.com/pricing) | No | About $99-119/month. 30-day API trial | Strong filters (equity, absentee, years owned). 250 phone/email lookups a month included | Good next step if RentCast works for you. For your own use only. Free trial has no exports. |
| [ATTOM](https://api.developer.attomdata.com/docs) | No | 30-day free trial. Paid price only from sales | Owner details, absentee filter by zip | Big, reliable data company. Try the trial if you want to compare. |
| [Realie](https://www.realie.ai/pricing) | No | Free: 25 tokens/month. $50/month | Owner, last sale, value, equity | Their website terms may not allow commercial use. Get it in writing before you use it. |
| [RealEstateAPI](https://developer.realestateapi.com/) | No | About $599/month (not confirmed) | Best filters of all | Too expensive to start. |
| [BatchData](https://batchdata.io/pricing) | No | From $1,000/month | Everything | Too expensive to start. |
| Orange County GIS | No | Free | Parcel maps | **No owner names.** California keeps them off the public county map. Not useful by itself. |

## Owner emails and phones ("skip tracing")

| Source | Built in? | Cost | Notes |
|---|---|---|---|
| **[Tracerfy](https://www.tracerfy.com/pricing)** | Yes (`find-emails`) | About $0.02-0.04 per owner found. Nothing if not found. No monthly fee | Up to 5 emails and 3 phones per owner. Free test mode (`--test`) gives fake results. Key: tracerfy.com → API. |
| PropertyRadar | No | 250/month in the plan, then $0.08 each | Only if you use PropertyRadar for data |

## Rules for using this data

- **Email**: every email needs your name, DRE number, a real postal address,
  and an easy way to say "stop". The `/write-emails` skill adds these. Stop
  right away when someone asks.
- **Phone**: do not call or text numbers on the Do Not Call list. The tool
  already leaves those numbers out. Check the rules with your broker before
  you call.
- Ask your broker if your brokerage has its own rules for prospecting.

## Add a new source

Ask Claude: "Add <name> as a data source." Claude follows `/build-something`.
Each source is one file in `sellers/sources/` with the same simple shape as
`rentcast.py`.
