"""Planted faults for the Critic catch-rate measure. Each takes (title, sections, claims,
summary) from the Reporting agent and returns a corrupted copy."""
import copy


def _rebuild(title, sections, summary):
    claims = [dict(l, section=n) for n, ls in sections for l in ls]
    return title, sections, claims, summary


def _edit_first(sections, needle, fn):
    S = copy.deepcopy(sections)
    for _, ls in S:
        for l in ls:
            if needle in l["text"]:
                fn(l)
                return S
    return S


def wrong_number(t, s, c, m):
    return _rebuild(t, _edit_first(s, "3.5%", lambda l: l.update(text=l["text"].replace("3.5%", "4.5%"))), m)


def invented_figure(t, s, c, m):
    S = copy.deepcopy(s)
    S[0][1].append({"text": "Eligible expenditure to date is S$0.80M.", "cites": ["F54"], "calc": []})
    return _rebuild(t, S, m)


def missing_citation(t, s, c, m):
    return _rebuild(t, _edit_first(s, "6.0%", lambda l: l.update(cites=[])), m)


def drop_section(t, s, c, m):
    S = [x for x in copy.deepcopy(s) if x[0] not in ("Status of each tranche condition", "Decisions needed")]
    return _rebuild(t, S, m)


def wrong_top5(t, s, c, m):
    S = copy.deepcopy(s)
    for n, ls in S:
        if n == "Top five risks" and ls:
            ls[-1] = {"text": "R23 Vendor/tool change affects the AI PM system - L2 x I2 = 4", "cites": ["RISK:R23"], "calc": []}
    return _rebuild(t, S, m)


def status_spin(t, s, c, m):
    S = copy.deepcopy(s)
    S[0][1].insert(0, {"text": "The project is on track overall.", "cites": ["PR3-1"], "calc": []})
    return _rebuild(t, S, m)


def remove_conflicts(t, s, c, m):
    S = copy.deepcopy(s)
    for i, (n, ls) in enumerate(S):
        if n == "Conflicts flagged":
            S[i] = (n, [])
    return _rebuild(t, S, m)


def wrong_date(t, s, c, m):
    S = _edit_first(s, "2027-03-19", lambda l: l.update(text=l["text"].replace("2027-03-19", "2027-03-12")))
    S = _edit_first(S, "2027-03-03", lambda l: l.update(text=l["text"].replace("2027-03-03", "2027-03-10")))
    return _rebuild(t, S, m)


def invented_person(t, s, c, m):
    S = copy.deepcopy(s)
    S[-2][1].append({"text": "Mr Lee confirmed the closure plan with residents.", "cites": ["EDC-3.2"], "calc": []})
    return _rebuild(t, S, m)


def hidden_gap(t, s, c, m):
    S = copy.deepcopy(s)
    for _, ls in S:
        for l in ls:
            l["text"] = l["text"].replace("NOT FOUND in the data pack", "tracked by Finance").replace("NOT FOUND", "pending")
    return _rebuild(t, S, m)


def bad_calc(t, s, c, m):
    S = copy.deepcopy(s)
    for _, ls in S:
        for l in ls:
            for cc in l["calc"]:
                old = cc["value"]
                cc["value"] = round(old * 1.25, 2)
                l["text"] = l["text"].replace(f"{old}", f"{cc['value']}")
                return _rebuild(t, S, m)
    return _rebuild(t, S, m)


def ignore_change_event(t, s, c, m):
    S = copy.deepcopy(s)
    for i, (n, ls) in enumerate(S):
        S[i] = (n, [l for l in ls if not any(x.startswith("CE-") for x in l["cites"])])
    return _rebuild(t, S, m)


FAULTS = {f.__name__: f for f in (wrong_number, invented_figure, missing_citation, drop_section, wrong_top5,
                                  status_spin, remove_conflicts, wrong_date, invented_person, hidden_gap, bad_calc)}
EVENT_FAULTS = {"ignore_change_event": ignore_change_event}
