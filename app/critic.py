"""Critic Agent - deterministic checks with a STOP condition.
A draft with any STOP finding cannot be released (reporting.release refuses it)."""
import ast
import operator
import re

from . import db, risk, sources

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
          "october", "november", "december"]
REQUIRED = {
    "edc": ["What changed", "What is late", "Decisions needed", "Top five risks", "Conflicts flagged"],
    "nrf": ["Progress against the baseline programme", "Expenditure to date against eligible cost",
            "Status of each tranche condition", "Top five risks", "Conflicts flagged"],
}
ID_PAT = re.compile(r"\b(?:[A-Z]{1,4}-?\d+(?:\.\d+)*|No\.\s?\d)\b")
ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
BANNED = re.compile(r"\b(on track|on programme|on schedule|no issues|fully funded|guaranteed|approved by the fund)\b", re.I)
PERSON = re.compile(r"\b(?:Mr|Ms|Mrs|Dr)\.?\s+([A-Z][a-z]+)")


def _resolve(cite):
    """Text against which a claim's numbers may be traced."""
    if cite.startswith("RISK:"):
        r = db.q1("SELECT * FROM risks WHERE id=?", (cite[5:],))
        if not r:
            return None
        return f"{r['description']} {r['owner']} {r['trigger_cond']} {r['likelihood']} {r['impact']} {r['score']}"
    if re.fullmatch(r"F\d+", cite):
        f = db.q1("SELECT * FROM facts WHERE id=?", (cite,))
        if not f:
            return None
        src = sources.get(f["source_id"])
        return f"{f['value']} {f['quote']} " + (src["text"] if src else "")
    s = sources.get(cite)
    return s["text"] if s else None


def _nums(text):
    out = set()
    for n in NUM.findall(text):
        try:
            out.add(round(float(n.replace(",", "")), 4))
        except ValueError:
            pass
    return out


def _date_ok(y, m, d, texts):
    mi, di = int(m), int(d)
    mon = MONTHS[mi - 1]
    for t in texts:
        tl = t.lower()
        if f"{y}-{m}-{d}" in t or f"{d}/{m}/{y}" in t:
            return True
        if re.search(rf"\b0?{di}\s+{mon}", tl) or re.search(rf"\b0?{di}\s+{mon[:3]}\b", tl):
            return True
    return False


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def _eval(expr):
    def num_of(fid):
        return float(db.q1("SELECT value FROM facts WHERE id=?", (fid,))["value"].replace(",", ""))

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.Constant):
            return float(n.value)
        if isinstance(n, ast.Name):
            return num_of(n.id)
        raise ValueError("unsupported")
    return ev(ast.parse(expr, mode="eval"))


def trace_claim(claim):
    """Return list of problems for one claim (empty == fully traced)."""
    probs = []
    text = claim["text"]
    texts = []
    for c in claim.get("cites", []):
        t = _resolve(c)
        if t is None:
            probs.append(f"cites unknown source '{c}'")
        else:
            texts.append(t)
    calc_vals = set()
    for c in claim.get("calc", []):
        try:
            v = round(_eval(c["expr"]), 2)
            if abs(v - float(c["value"])) > 0.01:
                probs.append(f"computed value {c['value']} != {c['expr']} = {v}")
            calc_vals.add(round(float(c["value"]), 4))
        except Exception:
            probs.append(f"cannot evaluate formula {c.get('expr')}")
    body = ID_PAT.sub(" ", text)
    for y, m, d in ISO.findall(body):
        if not _date_ok(y, m, d, texts):
            probs.append(f"date {y}-{m}-{d} not found in cited sources")
    body = ISO.sub(" ", body)
    allowed = set().union(*[_nums(ID_PAT.sub(" ", t)) for t in texts]) if texts else set()
    allowed |= set().union(*[_nums(t) for t in texts]) if texts else set()
    allowed |= calc_vals
    has_num = False
    for n in _nums(body):
        has_num = True
        if n not in allowed:
            probs.append(f"number {n:g} not traceable to cited sources")
    if (has_num or BANNED.search(text)) and not claim.get("cites"):
        probs.append("claim has no citation")
    for p in PERSON.findall(text):
        if not any(p in t for t in texts):
            probs.append(f"person '{p}' not in cited sources")
    return probs


def check(kind, sections, claims, content, event_aware=True):
    F = []
    names = [n for n, _ in sections]
    for req in REQUIRED[kind]:
        if req not in names:
            F.append({"rule": "C3 required section", "severity": "STOP", "detail": f"missing section '{req}'"})
    for c in claims:
        for p in trace_claim(c):
            F.append({"rule": "C1 traceability", "severity": "STOP", "detail": f"{p} :: \"{c['text'][:90]}\""})
        m = BANNED.search(c["text"])
        if m and "KHB" not in c["text"]:
            F.append({"rule": "C6 unsupported status claim", "severity": "STOP",
                      "detail": f"'{m.group(0)}' stated as fact :: \"{c['text'][:90]}\""})
    # top five risks must match the register
    top = [r["id"] for r in risk.top5()]
    listed = []
    for n, ls in sections:
        if n == "Top five risks":
            listed = [c for l in ls for c in l["cites"] if c.startswith("RISK:")]
            listed = [x[5:] for x in listed]
    if "Top five risks" in names and listed != top:
        F.append({"rule": "C4 top-five risks", "severity": "STOP", "detail": f"report lists {listed}, register top 5 is {top}"})
    # NOT FOUND must be explicit for unknown required data (NRF expenditure split)
    if kind == "nrf" and "NOT FOUND" not in content:
        F.append({"rule": "C8 hidden gap", "severity": "STOP",
                  "detail": "eligible/ineligible expenditure split is not in the pack but the report does not say NOT FOUND"})
    # conflicts must be flagged, citing both sides
    if "Conflicts flagged" in names:
        conf_lines = [l for n, ls in sections if n == "Conflicts flagged" for l in ls]
        if not conf_lines:
            F.append({"rule": "C7 conflict", "severity": "STOP", "detail": "no conflicts listed though the fact sheet has conflicts"})
        for l in conf_lines:
            if len(l["cites"]) < 2:
                F.append({"rule": "C7 conflict", "severity": "STOP", "detail": f"conflict cites fewer than two sources :: {l['text'][:60]}"})
    # stale facts and unprocessed change events
    cited = {c for cl in claims for c in cl.get("cites", [])}
    for f in db.q("SELECT id, superseded_by FROM facts WHERE superseded_by IS NOT NULL"):
        if f["id"] in cited:
            F.append({"rule": "C5 stale fact", "severity": "STOP", "detail": f"{f['id']} superseded by {f['superseded_by']}"})
    if event_aware:
        for e in db.q("SELECT id, tags FROM change_events"):
            if e["id"] not in cited:
                F.append({"rule": "C5 change event not reflected", "severity": "STOP",
                          "detail": f"{e['id']} received but the draft does not reflect it"})
    if not F:
        F.append({"rule": "all", "severity": "PASS", "detail": f"{len(claims)} claims traced; required sections present"})
    return F
