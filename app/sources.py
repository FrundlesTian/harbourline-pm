"""Source ingestion, chunking with precise locators, and BM25 retrieval.
Only the brief, sponsor answers and the data pack (plus later change events and
human-approved decisions) are ever indexed: that is the system's whole world."""
import csv
import io
import math
import re
from collections import Counter

from . import config, db

PACK = config.DATA_PACK

FILES = {
    "BRIEF": "00_Brief_UPDATED.txt",
    "SA": "00_Sponsor_Answers_Round1.txt",
    "README": "00_README.txt",
    "EDC": "01_EDC_minutes_Jan-Mar2027.txt",
    "PR1": "02_Contractor_progress_report_Jan2027.txt",
    "PR2": "02_Contractor_progress_report_Feb2027.txt",
    "PR3": "02_Contractor_progress_report_Mar2027.txt",
    "DEL": "03_Contract_deliverables_schedule.csv",
    "RISK": "04_Seed_risk_register.csv",
    "RC": "05_Resident_consultation_responses.csv",
    "LL": "06_Lessons_learned_Seabreeze_Hub.txt",
    "NRF": "07_Grant_milestone_tranche_schedule.txt",
}
DISPLAY = {
    "BRIEF": "UPDATED MA6094 Capstone Brief.pdf",
    "SA": "Capstone Sponsor Answers Round 1.pdf",
    "PR1": "02_Contractor_progress_report_Jan2027.pdf",
    "PR2": "02_Contractor_progress_report_Feb2027.pdf",
    "PR3": "02_Contractor_progress_report_Mar2027.pdf",
}


def norm(s):
    return re.sub(r"\s+", " ", (s or "").replace(" ", " ").replace("|", " ")).strip().lower()


def _read(prefix):
    return (PACK / FILES[prefix]).read_text(encoding="utf-8-sig")


def _add(out, cid, prefix, locator, ls, le, lines):
    text = "\n".join(l.rstrip() for l in lines).strip()
    if text:
        out.append({"id": cid, "file": DISPLAY.get(prefix, FILES[prefix]), "locator": locator,
                    "line_start": ls, "line_end": le, "text": text,
                    "kind": "consultation" if prefix == "RC" else "pack"})


def chunk_brief():
    out, raw = [], _read("BRIEF")
    pages = raw.split("\f")
    line_no = 1
    for pi, page in enumerate(pages, start=1):
        lines = page.split("\n")
        para, start, k = [], None, 0
        for i, ln in enumerate(lines):
            abs_ln = line_no + i
            s = ln.strip()
            junk = (s.startswith("MA6094 Capstone Brief") or re.match(r"Page \d+ of \d+", s))
            if not s or junk:
                if para and len(" ".join(para)) > 60:
                    k += 1
                    _add(out, f"BRIEF-p{pi}-{k}", "BRIEF", f"p.{pi} para {k}", start, abs_ln - 1, para)
                    para, start = [], None
                continue
            if start is None:
                start = abs_ln
            para.append(ln)
        if para:
            k += 1
            _add(out, f"BRIEF-p{pi}-{k}", "BRIEF", f"p.{pi} para {k}", start, line_no + len(lines) - 1, para)
        line_no += len(lines) - 1
    return out


def chunk_sponsor():
    out, lines = [], _read("SA").split("\n")
    cur, start, qid = [], None, None
    for i, ln in enumerate(lines, start=1):
        s = ln.strip()
        if s.startswith("\f"):
            s = s.lstrip("\f")
        if re.match(r"Page \d+ of \d+", s) or s.startswith("Capstone Sponsor Answers"):
            continue
        m = re.match(r"Q(\d)\.", s)
        if m:
            if qid:
                _add(out, f"SA-{qid}", "SA", f"Answer {qid}", start, i - 1, cur)
            qid, cur, start = f"Q{m.group(1)}", [ln], i
            continue
        if qid:
            cur.append(ln)
        elif s and "Oct 23" not in s:
            cur.append(ln)
            start = start or i
    if qid:
        _add(out, f"SA-{qid}", "SA", f"Answer {qid}", start, len(lines), cur)
    return out


def chunk_edc():
    out, lines = [], _read("EDC").split("\n")
    meeting, mdate, cur, start, item = None, "", [], None, None
    head = []
    for i, ln in enumerate(lines, start=1):
        m = re.match(r"MEETING (\d) — (.+)", ln)
        if m:
            if item:
                _add(out, f"EDC-{item}", "EDC", f"Meeting {meeting} ({mdate}), item {item}", start, i - 1, cur)
                item = None
            meeting, mdate = m.group(1), m.group(2).strip()
            continue
        mi = re.match(r"(\d\.\d+) ", ln)
        if mi:
            if item:
                _add(out, f"EDC-{item}", "EDC", f"Meeting {meeting} ({mdate}), item {item}", start, i - 1, cur)
            item, cur, start = mi.group(1), [ln], i
            continue
        if item and ln.startswith("    "):
            cur.append(ln)
        elif item and ln.startswith("Additional attendee"):
            pass
        elif meeting is None and ln.strip() and not ln.startswith("="):
            head.append((i, ln))
    if item:
        _add(out, f"EDC-{item}", "EDC", f"Meeting {meeting} ({mdate}), item {item}", start, len(lines), cur)
    if head:
        _add(out, "EDC-attendees", "EDC", "Header (standing attendees)", head[0][0], head[-1][0], [h[1] for h in head])
    return out


def chunk_pr(prefix):
    out, lines = [], _read(prefix).split("\n")
    sec, cur, start = "header", [], 1
    for i, ln in enumerate(lines, start=1):
        m = re.match(r"(\d)\. (.+)", ln)
        if m:
            _add(out, f"{prefix}-{sec}", prefix, f"Report No.{prefix[-1]} §{sec}", start, i - 1, cur)
            sec, cur, start = m.group(1), [ln], i
        else:
            if ln.startswith("Contract completion date"):
                _add(out, f"{prefix}-{sec}", prefix, f"Report No.{prefix[-1]} §{sec}", start, i - 1, cur)
                sec, cur, start = "footer", [ln], i
            else:
                cur.append(ln)
    _add(out, f"{prefix}-{sec}", prefix, f"Report No.{prefix[-1]} §{sec}", start, len(lines), cur)
    return out


def chunk_ll():
    out, lines = [], _read("LL").split("\n")
    cur, start, lid = [], 1, "header"
    for i, ln in enumerate(lines, start=1):
        m = re.match(r"(L\d\d) ", ln)
        if m:
            _add(out, f"LL-{lid}", "LL", "Header" if lid == "header" else lid, start, i - 1, cur)
            lid, cur, start = m.group(1), [ln], i
        else:
            cur.append(ln)
    _add(out, f"LL-{lid}", "LL", lid, start, len(lines), cur)
    return out


def chunk_nrf():
    out, lines = [], _read("NRF").split("\n")
    cur, start, cid, section = [], 1, "header", ""
    def flush(end):
        if cur:
            loc = "Header" if cid == "header" else (f"Tranche table row {cid}" if cid.startswith("T") else f"Clause {cid}")
            _add(out, f"NRF-{cid}", "NRF", loc + (f" ({section})" if section and cid != "header" else ""), start, end, cur)
    for i, ln in enumerate(lines, start=1):
        sh = re.match(r"(\d)\. ([A-Z ]+)$", ln.strip())
        cl = re.match(r"\s+(\d\.\d) ", ln)
        tr = re.match(r"\s+\| (T\d)\s+\|", ln)
        if sh:
            flush(i - 1); cur, start, cid, section = [], i, f"s{sh.group(1)}", sh.group(2).title()
            cur = [ln]; continue
        if cl or tr:
            flush(i - 1)
            cid, cur, start = (cl.group(1) if cl else tr.group(1)), [ln], i
            continue
        if ln.strip().startswith("| Tranche") or ln.strip().startswith("|----"):
            continue
        cur.append(ln)
    flush(len(lines))
    # Drop section-heading-only chunks
    return [c for c in out if not re.fullmatch(r"\d\. [A-Z ]+", c["text"].strip())]


def chunk_csv(prefix, idcol):
    out = []
    raw = _read(prefix)
    lines = raw.split("\n")
    hdr_line = 1
    body = raw
    if lines[0].startswith('"#') or lines[0].startswith("#"):
        _add(out, f"{prefix}-note", prefix, "File note (row 1)", 1, 1, [lines[0].strip('"')])
        body = "\n".join(lines[1:])
        hdr_line = 2
    reader = csv.DictReader(io.StringIO(body))
    for n, row in enumerate(reader):
        ln = hdr_line + 1 + n
        rid = row[idcol]
        text = f"{rid}: " + "; ".join(f"{k}: {v}" for k, v in row.items() if k != idcol and v not in (None, ""))
        _add(out, f"{prefix}-{rid}", prefix, f"row {rid}", ln, ln, [text])
    return out


def chunk_readme():
    lines = _read("README").split("\n")
    out = []
    _add(out, "README-pack", "README", "Data pack README", 1, len(lines), lines)
    return out


def all_chunks():
    ch = []
    ch += chunk_brief() + chunk_sponsor() + chunk_readme() + chunk_edc()
    ch += chunk_pr("PR1") + chunk_pr("PR2") + chunk_pr("PR3")
    ch += chunk_csv("DEL", "id") + chunk_csv("RISK", "risk_id") + chunk_csv("RC", "response_id")
    ch += chunk_ll() + chunk_nrf()
    return ch


def ingest():
    """(Re)load pack chunks. Change-event and decision sources are kept."""
    db.ex("DELETE FROM sources WHERE kind IN ('pack','consultation')")
    rows = all_chunks()
    db.exmany("INSERT OR REPLACE INTO sources(id,file,locator,line_start,line_end,text,kind) VALUES(?,?,?,?,?,?,?)",
              [(c["id"], c["file"], c["locator"], c["line_start"], c["line_end"], c["text"], c["kind"]) for c in rows])
    INDEX.invalidate()
    return len(rows)


def add_source(sid, file, locator, text, kind):
    db.ex("INSERT OR REPLACE INTO sources(id,file,locator,line_start,line_end,text,kind) VALUES(?,?,?,?,?,?,?)",
          (sid, file, locator, 1, text.count("\n") + 1, text, kind))
    INDEX.invalidate()


def get(sid):
    return db.q1("SELECT * FROM sources WHERE id=?", (sid,))


def cite(sid):
    s = get(sid)
    if not s:
        return {"id": sid, "label": f"{sid} (MISSING SOURCE)", "missing": True}
    lines = f"L{s['line_start']}" + (f"-{s['line_end']}" if s["line_end"] != s["line_start"] else "")
    return {"id": sid, "file": s["file"], "locator": s["locator"], "lines": lines,
            "label": f"{s['file']} · {s['locator']} · {lines}"}


# ------------------------------------------------------------------ retrieval
STOP = set("""a an the of to in on at for by and or is are was were be been it its this that these those
what which who whom when where why how do does did has have had with from as into than then there their
about any all can could would should will shall may might our your we you they he she i me my not no
much many many per vs""".split())

CJK = re.compile(r"[㐀-鿿஀-௿]")


def stem(t):
    """Very small suffix stripper (consistent for query and index)."""
    if t.isdigit() or len(t) <= 3:
        return t
    for suf in ("ies", "ing", "ed", "es", "s"):
        if len(t) > 4 and t.endswith(suf) and not t.endswith("ss"):
            t = t[: -len(suf)] + ("y" if suf == "ies" else "")
            break
    if len(t) > 3 and t[-1] == t[-2] and t[-1] not in "aeiouls":
        t = t[:-1]
    if len(t) > 3 and t.endswith("e"):
        t = t[:-1]
    return t


def tokenize(text, keep_stop=False):
    text = (text or "").lower()
    toks = []
    for w in re.findall(r"[a-z]+|\d+(?:[.,]\d+)*", text):
        if not keep_stop and w in STOP:
            continue
        toks.append(stem(w))
    cj = "".join(ch for ch in text if CJK.match(ch))
    toks += list(cj) + [cj[i:i + 2] for i in range(len(cj) - 1)]
    return toks


class BM25:
    def __init__(self):
        self.docs = None

    def invalidate(self):
        self.docs = None

    def build(self):
        rows = db.q("SELECT id,text,kind,file,locator FROM sources")
        self.docs = rows
        self.tf = [Counter(tokenize(r["text"] + " " + r["locator"])) for r in rows]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 1
        df = Counter()
        for t in self.tf:
            df.update(t.keys())
        n = len(rows)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def search(self, query, k=6, include_consultation=False):
        if self.docs is None:
            self.build()
        qt = tokenize(query)
        scores = []
        for i, tf in enumerate(self.tf):
            if not include_consultation and self.docs[i]["kind"] == "consultation":
                continue
            s = 0.0
            for w in qt:
                if w in tf:
                    f = tf[w]
                    s += self.idf.get(w, 0) * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * self.len[i] / self.avg))
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        return [dict(self.docs[i], score=round(s, 3)) for s, i in scores[:k]], qt


INDEX = BM25()
