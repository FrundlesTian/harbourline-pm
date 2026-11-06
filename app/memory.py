"""Module 3 - Memory & Retrieval Agent.
Answers questions over the brief, sponsor answers and data pack with document + line
citations; says NOT FOUND when the pack is silent; carries human-approved decisions
forward between sessions (they are indexed as sources of kind 'decision')."""
import re

from . import audit, critic, db, llm, sources
from .agents import AGENT_CARDS

AGENT = "memory"
GENERIC = {sources.stem(w) for w in (
    "harbourline hub project community refurbishment pack data brief say tell according state current planned plan "
    "will pm council edc minute report happened happen status latest update describe explain mean main give "
    "receive received get got did does know list show").split()}
SYNONYMS = {"contractor": ["khb", "kestrel", "builder"], "grant": ["nrf", "fund"], "fund": ["nrf", "grant"],
            "aac": ["active", "ageing"], "sponsor": ["koh", "director"], "childcare": ["childhood", "child"],
            "finish": ["completion"], "start": ["possession", "commence"], "money": ["budget", "cost"]}
CUE_TYPES = [  # (question cue, evidence pattern the answer sentence must contain)
    (re.compile(r"\b(how much|cost|budget|price|amount|spend|funding gap)\b", re.I),
     re.compile(r"S\$|\$|million|\d{1,3},\d{3}|not yet estimated|\d%", re.I)),
    (re.compile(r"\b(when|date|deadline|by when|what day)\b", re.I),
     re.compile(r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec|q[1-4])\b|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|month \d+", re.I)),
    (re.compile(r"\b(how many|number of|how long|duration|threshold|limit|target|percentage|percent|rate)\b", re.I),
     re.compile(r"(?<![\d.])\d+(?:[.,]\d+)?\s*(%|weeks?|months?|days?|years?|responses?|residents?|children|complaints?|m2|m²|million)?", re.I)),
]
ITEM_NO = re.compile(r"^(\d+\.\d+|L\d\d|[A-Z]\d\d:|\d\.)\s*")
CONSULT_CUES = re.compile(r"resident|consultation|comment|survey|respon", re.I)


def _sentences(text):
    t = re.sub(r"\s+", " ", text.replace("|", " "))
    parts = re.split(r"(?<=[.;!?])\s+(?=[A-Z0-9(•])|•", t)
    return [p.strip() for p in parts if len(p.strip()) > 3 and not p.strip().endswith("?")]


def _key_terms(question):
    return [t for t in dict.fromkeys(sources.tokenize(question)) if t not in GENERIC and len(t) > 1]


def _present(term, toks):
    return term in toks or any(sources.stem(s) in toks for s in SYNONYMS.get(term, []))


def _value_ok(question, sentence):
    body = ITEM_NO.sub("", sentence)
    for cue, need in CUE_TYPES:
        if cue.search(question):
            return bool(need.search(body))
    return True


def evidence(question, k=6):
    hits, _ = sources.INDEX.search(question, k=k, include_consultation=bool(CONSULT_CUES.search(question)))
    keys = _key_terms(question)
    best_sents = []
    for h in hits[:4]:
        head = set(sources.tokenize(h["text"].split("\n")[0] + " " + h["locator"]))
        for s in _sentences(h["text"]):
            st = set(sources.tokenize(s)) | head
            cov = sum(1 for t in keys if _present(t, st)) / max(1, len(keys))
            if cov > 0:
                best_sents.append({"source_id": h["id"], "sentence": s, "coverage": round(cov, 2),
                                   "has_value": _value_ok(question, s), "score": h["score"]})
    best_sents.sort(key=lambda x: (-x["coverage"], -x["score"]))
    top_terms = set()
    for h in hits[:3]:
        top_terms |= set(sources.tokenize(h["text"] + " " + h["locator"]))
    coverage = sum(1 for t in keys if _present(t, top_terms)) / max(1, len(keys))
    return hits, best_sents, coverage, keys


def _verdict(question, hits, sents, coverage):
    """Deterministic sufficiency test. Returns (ok, reason)."""
    if not hits or hits[0]["score"] < 2.5:
        return False, "no relevant passage"
    if coverage < 0.7:
        return False, f"only {int(coverage * 100)}% of the question's key terms appear in the best passages"
    good = [s for s in sents if s["coverage"] >= 0.5]
    if not good:
        return False, "no single passage addresses the question"
    if not any(s["has_value"] for s in good):
        return False, "the question asks for a value, date or quantity but no matching passage states one"
    return True, ""


def _conflict_notes(hit_ids, keys):
    notes = []
    for c in db.q("SELECT * FROM conflicts"):
        srcs = set(db.L(c["sources"]))
        topic_terms = set(sources.tokenize(c["topic"] + " " + c["detail"]))
        if srcs & set(hit_ids) and sum(1 for t in keys if t in topic_terms) >= max(1, len(keys) // 2):
            notes.append({"id": c["id"], "topic": c["topic"], "sources": [sources.cite(s)["label"] for s in srcs]})
    return notes[:2]


def answer(question, use_llm=True):
    hits, sents, coverage, keys = evidence(question)
    ok, why = _verdict(question, hits, sents, coverage)
    mode = "extractive"
    result = None
    if use_llm and llm.available() and hits:
        ctx = "\n\n".join(f"[{h['id']}] ({h['file']} · {h['locator']})\n{h['text']}" for h in hits)
        sysmsg = next(a for a in AGENT_CARDS if a["id"] == AGENT)["system_prompt"]
        data, _ = llm.chat_json(AGENT, sysmsg,
                                f"SOURCES:\n{ctx}\n\nQUESTION: {question}\n\n"
                                'Return JSON {"not_found": bool, "answer": "...", "citations": ["source ids"]}.')
        if data:
            cites = [c for c in data.get("citations", []) if any(h["id"] == c for h in hits)]
            bad = [c for c in data.get("citations", []) if c not in cites]
            if data.get("not_found") or "NOT FOUND" in str(data.get("answer", "")).upper():
                result = {"not_found": True, "answer": "NOT FOUND", "reason": "LLM found no support in retrieved sources",
                          "citations": []}
            elif cites and not bad and not critic.trace_claim({"text": str(data.get("answer", "")), "cites": cites}):
                result = {"not_found": False, "answer": data.get("answer", ""), "citations": cites}
            else:
                audit.log(AGENT, "reject llm answer", "qa", question[:60], outcome="rejected",
                          detail={"bad_citations": bad, "reason": "unknown citation or untraceable number/date"})
            mode = "llm" if result else "extractive (llm rejected)"
    if result is None:
        if not ok:
            result = {"not_found": True, "answer": "NOT FOUND", "reason": why, "citations": []}
        else:
            good = sorted([s for s in sents if s["coverage"] >= 0.5],
                          key=lambda x: (not x["has_value"], -x["coverage"], -x["score"]))[:3]
            result = {"not_found": False,
                      "answer": " ".join(f"{s['sentence']} [{s['source_id']}]" for s in good),
                      "citations": list(dict.fromkeys(s["source_id"] for s in good))}
    result["citations"] = [sources.cite(c) for c in result["citations"]]
    result["conflicts"] = [] if result["not_found"] else _conflict_notes([h["id"] for h in hits[:4]], keys)
    result["mode"] = mode
    result["retrieved"] = [{"id": h["id"], "score": h["score"], "label": sources.cite(h["id"])["label"]} for h in hits[:5]]
    db.ex("INSERT INTO qa_log(ts,question,answer,citations,not_found,mode) VALUES(?,?,?,?,?,?)",
          (db.now(), question, result["answer"], db.J([c["id"] for c in result["citations"]]),
           1 if result["not_found"] else 0, mode))
    return result


def record_decision(text, made_by, source_note=""):
    """Carry a human decision forward: stored, audited and indexed for later sessions."""
    n = (db.q1("SELECT COUNT(*) c FROM decisions")["c"] or 0) + 1
    did = f"DL-{n:03d}"
    db.ex("INSERT INTO decisions VALUES(?,?,?,?,?)", (did, text, source_note, made_by, db.now()))
    sources.add_source(did, "Decision log (human-approved)", f"{did} by {made_by}", text, "decision")
    audit.log(made_by, "decision recorded", "decision", did, detail={"text": text}, actor_type="human")
    return did


def restore_decisions():
    for d in db.q("SELECT * FROM decisions"):
        sources.add_source(d["id"], "Decision log (human-approved)", f"{d['id']} by {d['made_by']}", d["text"], "decision")
