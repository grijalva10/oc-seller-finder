"""Make data/report.html: your list of homes, in one file you open in a browser.

No server needed. Double-click the file, or ask Claude to open it.
"""
import html
import json

from .config import DATA
from .db import STATUSES, as_dict

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OC Seller Finder</title>
<style>
 body{font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f6f7f9;color:#1d2330}
 header{background:#14324f;color:#fff;padding:16px 24px}
 header h1{margin:0;font-size:20px} header p{margin:4px 0 0;opacity:.8}
 .bar{display:flex;gap:10px;flex-wrap:wrap;padding:14px 24px;background:#fff;border-bottom:1px solid #dde1e7}
 .bar input,.bar select{font:inherit;padding:7px 10px;border:1px solid #c6ccd5;border-radius:6px}
 .bar input{flex:1;min-width:200px}
 table{border-collapse:collapse;width:100%;background:#fff}
 th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #eceef2;vertical-align:top}
 th{background:#eef1f5;position:sticky;top:0;cursor:pointer;user-select:none;font-size:13px}
 td.num{text-align:right;white-space:nowrap}
 .score{font-weight:700;font-size:17px}
 .why{margin:0;padding-left:16px;color:#3c475a;font-size:13px}
 .tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;background:#e8ebf0}
 .tag.new{background:#dcebff}.tag.interested{background:#d5f5dc}.tag.do_not_contact,.tag.not_interested{background:#fbdcdc}
 .muted{color:#7a8496;font-size:13px}
 .demo{background:#fff4d6;padding:8px 24px;border-bottom:1px solid #f0d78c}
</style></head><body>
<header><h1>OC Seller Finder</h1><p>@@count@@ homes &middot; made @@made@@ &middot; higher score = more signs the owner might sell</p></header>
@@demo_note@@
<div class="bar">
 <input id="q" placeholder="Search address, owner, city..." autofocus>
 <select id="city"><option value="">All cities</option>@@city_opts@@</select>
 <select id="status"><option value="">All statuses</option>@@status_opts@@</select>
</div>
<table><thead><tr>
 <th data-k="id">ID</th><th data-k="score">Score</th><th data-k="address">Home</th><th data-k="owner_name">Owner</th>
 <th>Why it scored</th><th data-k="email">Email</th><th data-k="status">Status</th>
</tr></thead><tbody id="rows"></tbody></table>
<script>
const DATA = @@data@@, STATUS = @@statuses@@;
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let sortKey = "score", sortDir = -1;
function draw(){
  const q = document.getElementById("q").value.toLowerCase();
  const city = document.getElementById("city").value, st = document.getElementById("status").value;
  const rows = DATA.filter(p => (!city || p.city === city) && (!st || p.status === st) &&
    (!q || [p.address, p.owner_name, p.city, p.zip].join(" ").toLowerCase().includes(q)));
  rows.sort((a,b) => (a[sortKey] > b[sortKey] ? 1 : a[sortKey] < b[sortKey] ? -1 : 0) * sortDir);
  document.getElementById("rows").innerHTML = rows.map(p => `<tr>
    <td class="muted">${p.id}</td><td class="num score">${p.score}</td>
    <td><b>${esc(p.address)}</b><br><span class="muted">${esc(p.city)} ${esc(p.zip)} &middot; ${esc(p.property_type)}${p.beds ? " &middot; " + p.beds + " bd" : ""}</span></td>
    <td>${esc(p.owner_name)}<br><span class="muted">mail: ${esc([p.mail_address, p.mail_city, p.mail_state].filter(Boolean).join(", "))}</span></td>
    <td><ul class="why">${p.reasons.map(r => "<li>" + esc(r) + "</li>").join("")}</ul></td>
    <td>${p.email ? esc(p.email) : '<span class="muted">none yet</span>'}</td>
    <td><span class="tag ${p.status}" title="${esc(STATUS[p.status])}">${esc(p.status.replace(/_/g, " "))}</span>${p.notes ? '<br><span class="muted">' + esc(p.notes) + "</span>" : ""}</td>
  </tr>`).join("");
}
document.querySelectorAll("th[data-k]").forEach(th => th.onclick = () => {
  const k = th.dataset.k; sortDir = sortKey === k ? -sortDir : -1; sortKey = k; draw(); });
["q","city","status"].forEach(id => document.getElementById(id).oninput = draw);
draw();
</script></body></html>
"""


def write_report(con, made: str) -> str:
    homes = [as_dict(r) for r in con.execute("SELECT * FROM properties ORDER BY score DESC")]
    cities = sorted({h["city"] for h in homes if h["city"]})
    demo = any(h["source"] == "demo" for h in homes)
    values = {
        "count": str(len(homes)), "made": html.escape(made),
        "demo_note": '<div class="demo">This list has <b>fake demo homes</b>. Real data replaces them later.</div>' if demo else "",
        "city_opts": "".join('<option>%s</option>' % html.escape(c) for c in cities),
        "status_opts": "".join('<option value="%s">%s</option>' % (k, k.replace("_", " ")) for k in STATUSES),
        "data": json.dumps(homes).replace("</", "<\\/"),
        "statuses": json.dumps(STATUSES),
    }
    page = PAGE
    for name, value in values.items():
        page = page.replace("@@%s@@" % name, value)
    DATA.mkdir(exist_ok=True)
    path = DATA / "report.html"
    path.write_text(page, encoding="utf-8")
    return str(path)
