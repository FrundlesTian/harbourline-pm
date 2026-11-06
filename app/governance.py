"""Governance layer: bias & fairness check on the resident consultation, audit export,
checkpoint register. The bias check must be signed off (HC7) before the summary is used."""
import csv
import io
from collections import Counter, defaultdict

from . import audit, config, db

THEMES = {
    "Childcare": ["childcare", "100 places", "child"],
    "Active ageing / seniors": ["active ageing", "senior centre", "senior", "parents need", "乐龄", "warga emas", "முதியோர்"],
    "Lifts & barrier-free access": ["lift", "wheelchair", "ramps", "电梯", "lif "],
    "Noise & working hours": ["noise", "sundays", "噪音", "周末"],
    "Sports hall": ["sports hall"],
    "Food court affordability": ["food court", "kopi", "drinks stall"],
    "Rooftop garden (support)": ["rooftop garden sounds lovely"],
    "Rooftop garden (oppose)": ["rooftop garden is a waste"],
    "Communication & trust": ["consulted earlier", "poster was unclear", "who will run", "nothing happened"],
}
TRANSLATIONS = {  # gloss for reviewers; meaning only, used for theme tagging transparency
    "施工噪音太大，希望周末不要动工。": "Construction noise is too loud; please no works at weekends.",
    "希望早日有乐龄中心，楼下就方便了。": "Hope for an active ageing centre soon; it would be convenient downstairs.",
    "电梯不能停，老人家上不了楼。": "The lifts cannot stop; elderly people cannot go upstairs.",
    "Tolong pastikan lif boleh digunakan semasa kerja pengubahsuaian.": "Please make sure the lift can be used during renovation works.",
    "Pusat warga emas sangat diperlukan di kawasan ini.": "A senior citizens' centre is badly needed in this area.",
    "முதியோர் மையம் மிகவும் தேவை.": "A senior centre is very much needed.",
}


def _rows():
    return list(csv.DictReader(open(config.DATA_PACK / "05_Resident_consultation_responses.csv", encoding="utf-8-sig")))


def themes_of(comment):
    c = comment.lower() + " "
    return [t for t, kws in THEMES.items() if any(k in c for k in kws)]


def _rank(weights):
    return [t for t, _ in sorted(weights.items(), key=lambda x: (-x[1], x[0]))]


def bias_check():
    rows = _rows()
    n = len(rows)
    age = Counter(r["age_band"] for r in rows)
    chan = Counter(r["channel"] for r in rows)
    lang = Counter(r["language"] for r in rows)
    raw, eng_only, rew = Counter(), Counter(), defaultdict(float)
    by_age_theme = defaultdict(Counter)
    for r in rows:
        ts = themes_of(r["comment"])
        for t in ts:
            raw[t] += 1
            by_age_theme[r["age_band"]][t] += 1
            rew[t] += 1.0 / age[r["age_band"]] / len(age)
            if r["language"] == "en":
                eng_only[t] += 1
    raw_rank, rew_rank, eng_rank = _rank(raw), _rank(rew), _rank(eng_only)
    under45 = sum(v for k, v in age.items() if k in ("18-24", "25-34", "35-44"))
    online_u45 = sum(1 for r in rows if r["channel"] == "online" and r["age_band"] in ("18-24", "25-34", "35-44"))
    non_en = [r for r in rows if r["language"] != "en"]
    rating = {a: round(sum(int(r["rating_1to5"]) for r in rows if r["age_band"] == a) / c, 2) for a, c in age.items()}
    uniq = len({r["comment"] for r in rows})
    findings = [
        {"id": "B1", "severity": "high",
         "text": f"Online channel supplied {chan['online']}/{n} responses ({round(chan['online'] / n * 100, 1)}%); "
                 f"{online_u45} of them from under-45s. Seabreeze saw the same skew (L06).", "sources": ["RC (computed)", "LL-L06"]},
        {"id": "B2", "severity": "high",
         "text": f"Residents 65+ gave {age['65+']} responses ({round(age['65+'] / n * 100, 1)}%) although they are the main users of the active ageing centre; "
                 f"under-45s gave {under45} ({round(under45 / n * 100, 1)}%). Estate age profile: NOT FOUND in pack, so true representativeness cannot be computed.",
         "sources": ["RC (computed)", "BRIEF-p3-4"]},
        {"id": "B3", "severity": "high",
         "text": f"{len(non_en)} non-English responses (zh {lang['zh']}, ms {lang['ms']}, ta {lang['ta']}) all come via paper/town hall "
                 f"({sum(1 for r in non_en if r['age_band'] in ('45-54', '55-64', '65+'))} from residents 45+) and are about seniors, lifts or noise. "
                 f"An English-only summary would drop {raw['Active ageing / seniors'] - eng_only['Active ageing / seniors']} of "
                 f"{raw['Active ageing / seniors']} active-ageing comments and {raw['Lifts & barrier-free access'] - eng_only['Lifts & barrier-free access']} of "
                 f"{raw['Lifts & barrier-free access']} lift/access comments"
                 + (f"; theme order would change to {eng_rank[:4]}." if eng_rank[:4] != raw_rank[:4] else "."), "sources": ["RC (computed)"]},
        {"id": "B4", "severity": "medium",
         "text": f"Theme priority by raw count: {raw_rank[:4]}; with each age band weighted equally: {rew_rank[:4]}. "
                 + ("Order CHANGES under re-weighting - report both." if raw_rank[:4] != rew_rank[:4] else "Top order unchanged."),
         "sources": ["RC (computed)"]},
        {"id": "B5", "severity": "medium",
         "text": f"Only {uniq} distinct comment texts across {n} responses - heavy repetition; check for template or campaign submissions before weighting.",
         "sources": ["RC (computed)"]},
        {"id": "B6", "severity": "low",
         "text": f"Mean rating by age band: {rating}. Town hall drew about 40 residents (EDC 4.5) and gave {chan['townhall']} responses.",
         "sources": ["RC (computed)", "EDC-4.5"]},
    ]
    actions = [
        "Translate and include all non-English comments in the summary (glosses provided).",
        "Show theme priorities both raw and age-re-weighted; do not present raw counts as 'what residents want'.",
        "Recommend a second, multilingual paper / door-to-door round targeted at 55+ residents (Seabreeze L06).",
        "Flag repeated identical wording; Community Engagement to confirm whether submissions are independent.",
        "Hold the consultation summary (D15) for HC7 sign-off before it is handed to KHB as design input.",
    ]
    result = {"n": n, "age": dict(age), "channel": dict(chan), "language": dict(lang),
              "themes_raw": dict(raw), "themes_reweighted": {k: round(v, 4) for k, v in rew.items()},
              "themes_english_only": dict(eng_only), "rank_raw": raw_rank, "rank_reweighted": rew_rank,
              "rank_english_only": eng_rank, "by_age_theme": {k: dict(v) for k, v in by_age_theme.items()},
              "rating_by_age": rating, "translations": TRANSLATIONS, "findings": findings, "actions": actions}
    cur = db.q1("SELECT * FROM bias_checks WHERE id='BIAS-1'")
    if not cur or cur["result"] != db.J(result):
        db.ex("INSERT OR REPLACE INTO bias_checks VALUES(?,?,?,?)", ("BIAS-1", db.now(), db.J(result), "awaiting HC7"))
        audit.log("governance", "bias & fairness check written", "bias_check", "BIAS-1", detail={"findings": len(findings)})
    return result


def sign_off_bias(approver, decision, comment=""):
    audit.record_approval("HC7", "bias_check", "BIAS-1", approver, decision, comment)
    db.ex("UPDATE bias_checks SET status=? WHERE id='BIAS-1'", ("signed off" if decision == "approved" else "rejected",))


def audit_export_csv():
    rows = db.q("SELECT * FROM audit_log ORDER BY id")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "ts", "run_id", "actor", "actor_type", "action", "target_type", "target_id", "outcome", "detail"])
    for r in rows:
        w.writerow([r[k] for k in ("id", "ts", "run_id", "actor", "actor_type", "action", "target_type", "target_id", "outcome", "detail")])
    return buf.getvalue()


def approvals_export_csv():
    rows = db.q("SELECT * FROM approvals ORDER BY id")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "ts", "checkpoint", "checkpoint_name", "item_type", "item_id", "approver", "role", "decision", "comment"])
    for r in rows:
        w.writerow([r["id"], r["ts"], r["checkpoint"], audit.CHECKPOINTS[r["checkpoint"]]["name"], r["item_type"], r["item_id"],
                    r["approver"], r["role"], r["decision"], r["comment"]])
    return buf.getvalue()


def checkpoint_map():
    out = []
    for k, v in audit.CHECKPOINTS.items():
        n = db.q1("SELECT COUNT(*) c FROM approvals WHERE checkpoint=?", (k,))["c"]
        out.append(dict(v, id=k, approvals=n))
    return out
