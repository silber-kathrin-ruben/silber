"""Holt die Zusagen aus Tally und schreibt buffet.json (nur Buffet-Bereich + Gericht, keine Namen)."""
import json, os, re, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

FORM = "o92dZV"
KEY = os.environ["TALLY_API_KEY"]
KATS = ["Salat", "Hauptgericht", "Fingerfood & Snacks", "Brot & Dips", "Nachtisch", "Getränke"]

def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KEY}", "User-Agent": "silber-buffet"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

questions, subs, page = [], [], 1
while True:
    d = get(f"https://api.tally.so/forms/{FORM}/submissions?filter=completed&page={page}&limit=500")
    questions = d.get("questions", questions)
    subs += d.get("submissions", [])
    if not d.get("hasMore"):
        break
    page += 1

# Frage-IDs und Antwortoptionen anhand der Fragetitel finden
qid, opts = {}, {}
for q in questions:
    title = (q.get("title") or "").strip()
    qid[title] = q.get("id")
    for f in q.get("fields", []) or []:
        for o in f.get("options", []) or []:
            opts[o.get("id")] = o.get("text")

def ans(sub, title):
    for r in sub.get("responses", []):
        if r.get("questionId") == qid.get(title):
            a = r.get("answer")
            vals = a if isinstance(a, list) else [a]
            vals = [opts.get(v, v) if isinstance(v, str) else v for v in vals]
            return str(vals[0]) if vals and vals[0] is not None else ""
    return ""

def clean(t):
    t = re.sub(r"[<>`\\\r\n]", " ", t)
    return re.sub(r"\s+", " ", t).strip()[:60]

buffet = []
for s in subs:
    if not ans(s, "Kommst du?").startswith("Ja"):
        continue
    kat = ans(s, "Was bringst du zum Buffet mit?")
    was = clean(ans(s, "Und was genau?"))
    if kat in KATS:
        buffet.append({"kat": kat, "was": was})

old = {}
try:
    old = json.load(open("buffet.json", encoding="utf-8"))
except Exception:
    pass
if old.get("buffet") == buffet:
    print("Keine Änderung.")
else:
    stand = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y, %H:%M Uhr")
    json.dump({"stand": stand, "buffet": buffet}, open("buffet.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Aktualisiert: {len(buffet)} Beiträge.")
