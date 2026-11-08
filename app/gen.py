"""Shared helpers for LLM generation of agent outputs.

Pattern used by every generating agent:
  1. build the SOURCES block from indexed chunks (the only world the model may use);
  2. ask DeepSeek (temperature 0, cached) for structured JSON;
  3. validate deterministically - unknown source ids, WBS codes, tags or untraceable
     dates/numbers are dropped or the whole draft is rejected;
  4. fall back to the curated baseline only when the LLM is off or validation fails,
     and record which path produced the output (`origin:<agent>` in kv + audit log)."""
from . import audit, config, db, sources

# Controlled tag vocabulary. Tags are the provenance links the Change Agent uses to find
# what an event makes stale, so generated items may only use these.
TAGS = sorted("""accessibility aac-operator analog asbestos budget childcare closures completion construction
consultation contingency data-quality design eligible-cost food-court grant hazmat lifts operator-agreements
progress reporting risk roof rooftop schedule scope success tooling tranche-2 variation""".split())


def block(prefixes, limit_chars=60000):
    """SOURCES block: '[ID] (file · locator)\\ntext' for every chunk whose id starts with
    one of the prefixes (pack, sponsor answers, change events, decisions)."""
    rows = []
    for p in prefixes:
        rows += db.q("SELECT id,file,locator,text FROM sources WHERE id LIKE ? ORDER BY rowid", (p + "%",))
    out, n = [], 0
    for r in rows:
        s = f"[{r['id']}] ({r['locator']})\n{r['text']}"
        if n + len(s) > limit_chars:
            break
        out.append(s)
        n += len(s)
    return "\n\n".join(out)


def facts_block():
    """Verified facts. Numbers and dates are evidenced by the value and the exact quote only;
    the topic label is a human description and is NOT evidence."""
    return ("(Numbers and dates may come only from 'value' and 'quote'; 'topic' is a description, not evidence.)\n" +
            "\n".join(f"[{f['id']}] value: {f['value']} {f['unit'] or ''}| quote: \"{f['quote']}\" | source {f['source_id']}"
                       f" | topic: {f['label']}" for f in db.q("SELECT * FROM facts ORDER BY CAST(SUBSTR(id,2) AS INT)")))


def known(ids):
    """Keep only source ids that exist in the index (or fact ids F.., or RISK:Rnn)."""
    out = []
    for s in ids or []:
        s = str(s).strip()
        if not s:
            continue
        if sources.get(s) or db.q1("SELECT 1 FROM facts WHERE id=?", (s,)):
            out.append(s)
        elif s.startswith("RISK:") and db.q1("SELECT 1 FROM risks WHERE id=?", (s[5:],)):
            out.append(s)
    return list(dict.fromkeys(out))


def tags(ts):
    return sorted({t for t in (ts or []) if t in TAGS})


def set_origin(agent, mode, reason="", **extra):
    info = dict(mode=mode, model=config.DEEPSEEK_MODEL if mode == "llm" else None, reason=reason, at=db.now(), **extra)
    db.kv_set("origin:" + agent, info)
    audit.log(agent, f"output generated ({mode})", "generation", agent,
              outcome="ok" if mode == "llm" or not reason else "fallback", detail=info)
    return info


def origins():
    return {a: db.kv_get("origin:" + a) for a in ("planning", "risk", "reporting", "change")}


GROUND = ("Use ONLY the SOURCES given. Never use outside knowledge or invent names, dates, amounts or owners. "
          "Every source id you output must be one of the ids shown in square brackets. "
          "If the sources do not state something, write NOT FOUND (or TBD for dates) instead of guessing. "
          "Where sources disagree, say so and cite both. Return a single JSON object only.")
