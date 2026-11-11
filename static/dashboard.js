/* Harbourline AI PM - visual dashboard, process flowchart and admin console.
   Plain SVG, no libraries. Loaded before app.js; uses its helpers ($, esc, chip, api, table…) at call time. */

const SVGNS = "http://www.w3.org/2000/svg";
const ROLE_ORDER = ["admin", "project_manager", "group_leader", "supervisor"];
const STATE_ICON = { approved: "✓", rejected: "✕", pending: "…", "n/a": "–" };

/* ---------- shared tooltip (hover layer for every chart mark with data-tip) */
const tip = document.createElement("div");
tip.id = "viztip"; tip.hidden = true; document.body.appendChild(tip);
document.addEventListener("mousemove", (e) => {
  const t = e.target.closest && e.target.closest("[data-tip]");
  if (!t) { tip.hidden = true; return; }
  tip.innerHTML = t.dataset.tip; tip.hidden = false;
  const r = tip.getBoundingClientRect();
  let x = e.clientX + 14, y = e.clientY + 14;
  if (x + r.width > innerWidth - 8) x = e.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = e.clientY - r.height - 14;
  tip.style.left = x + "px"; tip.style.top = y + "px";
});
document.addEventListener("scroll", () => (tip.hidden = true), true);

const tipAttr = (html) => `data-tip="${esc(html)}"`;

/* ---------- process flowchart -------------------------------------------- */
function flowChart(d) {
  const f = d.flow, cp = d.checkpoints;
  const W = 1180, H = 560, NW = 150, NH = 56, GW = 78, GH = 40;
  const rep = f.reports || {};
  const repTotal = Object.values(rep).reduce((a, b) => a + b, 0);
  const handoff = (a, b) => (f.handoffs.find((h) => h.from_agent === a && h.to_agent === b) || {});
  // node: [id, x(center), y(center), title, subtitle, state, tab]
  const st = (n) => (n > 0 ? "done" : "idle");
  const nodes = [
    ["src", 95, 230, "Data pack & brief", `${f.sources} chunks · ${f.facts} facts`, st(f.facts), "overview"],
    ["plan", 270, 90, "1 · Planning agent", `${f.planning.wbs} WBS · ${f.planning.gaps} gaps`, st(f.planning.wbs), "planning"],
    ["pm", 560, 90, "2 · PM tool agent", `${f.pm.issues} board items`, st(f.pm.issues), "pm"],
    ["board", 850, 90, f.pm.backend === "jira" ? `Jira Cloud · ${f.pm.project}` : "Mock board (SQLite)", f.pm.issues ? "synced · read back" : "not written", st(f.pm.issues), "pm"],
    ["mem", 270, 370, "3 · Memory agent", `${f.memory.questions} Q&A · ${f.memory.decisions} decisions`, st(f.memory.questions), "memory"],
    ["risk", 560, 230, "4 · Risk & what-if", `${f.risk.risks} risks · ${f.risk.whatifs} what-ifs`, f.risk.stale ? "warn" : st(f.risk.risks), "risk"],
    ["rep", 850, 230, "5 · Reporting agent", `${repTotal} report versions`, st(repTotal), "reports"],
    ["critic", 1080, 230, "Critic", f.critic_stops ? `${f.critic_stops} draft(s) STOPPED` : `${rep.critic_passed || 0} passed`, f.critic_stops ? "stop" : st(repTotal), "reports"],
    ["readers", 1080, 370, "EDC / NRF readers", `${rep.released || 0} released`, st(rep.released || 0), "reports"],
    ["ce", 415, 370, "Change event", `${f.change.events} injected`, st(f.change.events), "change", 104],
    ["chg", 560, 370, "6 · Change agent", `${f.change.stale} stale items`, f.change.pending ? "warn" : st(f.change.events), "change"],
    ["apply", 850, 370, "Plan · register · board", "updated after HC6", f.change.events && !f.change.pending ? "done" : "idle", "change"],
    ["bias", 560, 480, "Bias & fairness check", f.bias || "not run", f.bias ? (f.bias === "signed off" ? "done" : "warn") : "idle", "governance"],
    ["summary", 850, 480, "Consultation summary", f.bias === "signed off" ? "cleared for design input" : "held", f.bias === "signed off" ? "done" : "idle", "governance"],
  ];
  const gates = [
    ["g12", 415, 90, ["HC1", "HC2"]], ["g3", 705, 90, ["HC3"]], ["g4", 705, 230, ["HC4"]],
    ["g5", 1080, 300, ["HC5"]], ["g6", 705, 370, ["HC6"]], ["g7", 705, 480, ["HC7"]],
  ];
  const pos = {};
  nodes.forEach(([id, x, y, , , , , w]) => (pos[id] = { x, y, w: w || NW, h: NH }));
  gates.forEach(([id, x, y]) => (pos[id] = { x, y, w: GW, h: GH }));
  const gateState = (ids) => {
    const s = ids.map((i) => cp[i].state);
    return s.includes("rejected") ? "rejected" : s.includes("pending") ? "pending" : s.every((x) => x === "approved") ? "approved" : s.includes("approved") ? "pending" : "n/a";
  };
  // edges: [from, to, label, kind]  kind: flow | handoff | update
  const ho = (a, b) => { const h = handoff(a, b); return h.n ? `hand-off ×${h.n}` : ""; };
  const edges = [
    ["src", "plan", "", "flow"], ["src", "mem", "", "flow"], ["src", "bias", "", "flow"],
    ["plan", "g12", "", "flow"], ["g12", "pm", "", "flow"], ["pm", "g3", "diff preview", "flow"], ["g3", "board", "write", "flow"],
    ["plan", "risk", ho("planning", "risk"), "handoff"], ["risk", "g4", "", "flow"], ["g4", "rep", ho("risk", "reporting"), "handoff"],
    ["rep", "critic", ho("reporting", "critic"), "handoff"], ["critic", "g5", "", "flow"], ["g5", "readers", "", "flow"],
    ["ce", "chg", "", "flow"], ["chg", "g6", "", "flow"], ["g6", "apply", "", "flow"],
    ["bias", "g7", "", "flow"], ["g7", "summary", "", "flow"],
  ];
  const active = (id) => { const n = nodes.find((x) => x[0] === id); return n ? n[5] !== "idle" : gateState(gates.find((g) => g[0] === id)[3]) === "approved"; };
  const path = (a, b) => {
    const A = pos[a], B = pos[b];
    if (Math.abs(A.x - B.x) < 4) { // vertical
      const y1 = A.y + (B.y > A.y ? A.h / 2 : -A.h / 2), y2 = B.y - (B.y > A.y ? B.h / 2 : -B.h / 2);
      return { d: `M${A.x},${y1} L${B.x},${y2}`, lx: A.x + 8, ly: (y1 + y2) / 2, room: 999, anchor: "start" };
    }
    const x1 = A.x + A.w / 2, x2 = B.x - B.w / 2;
    if (Math.abs(A.y - B.y) < 4) return { d: `M${x1},${A.y} L${x2},${B.y}`, lx: (x1 + x2) / 2, ly: A.y - 7, room: x2 - x1, anchor: "middle" };
    const mx = x1 + 22;
    const r = 8, dir = B.y > A.y ? 1 : -1;
    return { d: `M${x1},${A.y} L${mx - r},${A.y} Q${mx},${A.y} ${mx},${A.y + r * dir} L${mx},${B.y - r * dir} Q${mx},${B.y} ${mx + r},${B.y} L${x2},${B.y}`,
      lx: mx + 6, ly: (A.y + B.y) / 2, room: 999, anchor: "start" };
  };
  let svg = `<svg class="flowsvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Process flow">
    <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--edge)"/></marker>
    <marker id="arr-on" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--accent)"/></marker></defs>
    <g class="lanes">
      <text x="14" y="22" class="lane">Plan &amp; build</text>
      <line x1="10" x2="${W - 10}" y1="160" y2="160"/><text x="14" y="178" class="lane">Risk &amp; reporting</text>
      <line x1="10" x2="${W - 10}" y1="300" y2="300" class="faint"/><text x="14" y="318" class="lane">Memory &amp; change</text>
      <line x1="10" x2="${W - 10}" y1="430" y2="430"/><text x="14" y="448" class="lane">Governance</text>
    </g>`;
  edges.forEach(([a, b, label, kind]) => {
    const p = path(a, b), on = active(a);
    svg += `<path d="${p.d}" class="edge ${kind} ${on ? "on" : ""}" marker-end="url(#${on ? "arr-on" : "arr"})"/>`;
    if (label && p.room >= label.length * 6) svg += `<text x="${p.lx}" y="${p.ly}" class="elabel" text-anchor="${p.anchor}">${esc(label)}</text>`;
  });
  nodes.forEach(([id, x, y, title, sub, state, tab, w = NW]) => {
    const allowed = canView(tab);
    svg += `<g class="fnode ${state} ${allowed ? "link" : ""}" ${allowed ? `data-go="${tab}"` : ""} ${tipAttr(`<b>${esc(title)}</b><br>${esc(sub)}<br><span class='muted'>${allowed ? "Click to open" : "Not visible to your role"}</span>`)}>
      <rect x="${x - w / 2}" y="${y - NH / 2}" width="${w}" height="${NH}" rx="9"/>
      <text x="${x}" y="${y - 4}" class="t">${esc(title)}</text><text x="${x}" y="${y + 14}" class="s">${esc(sub)}</text></g>`;
  });
  gates.forEach(([id, x, y, ids]) => {
    const s = gateState(ids);
    const who = ids.map((i) => `${i}: ${esc(cp[i].state)}${cp[i].by ? " · " + esc(cp[i].by) : ""}${cp[i].waiting ? ` · ${cp[i].waiting} waiting` : ""}`).join("<br>");
    svg += `<g class="gate ${s.replace("/", "")}" ${tipAttr(`<b>Human checkpoint</b><br>${who}<br><span class='muted'>${esc(ids.map((i) => cp[i].role).join(" / "))}</span>`)}>
      <rect x="${x - GW / 2}" y="${y - GH / 2}" width="${GW}" height="${GH}" rx="${GH / 2}"/>
      <text x="${x}" y="${y + 4}">${STATE_ICON[s]} ${ids.join("·")}</text></g>`;
  });
  svg += `<g class="auditbar" ${tipAttr("Every agent write, human approval, login and blocked attempt is appended here. Never erased by reset.")}>
    <rect x="10" y="${H - 34}" width="${W - 20}" height="26" rx="6"/>
    <text x="${W / 2}" y="${H - 16}">Audit log · ${d.kpis.approvals} approvals · ${d.kpis.blocked} blocked / rejected attempts · append-only</text></g></svg>`;
  return svg;
}

function flowLegend() {
  const item = (cls, label) => `<span class="lg"><i class="sw ${cls}"></i>${label}</span>`;
  return `<div class="legend">${item("n-done", "Output produced")}${item("n-idle", "Not run yet")}${item("n-warn", "Needs attention")}${item("n-stop", "Critic STOP")}
    ${item("g-approved", "Checkpoint approved")}${item("g-pending", "Awaiting a human")}${item("g-rejected", "Rejected")}
    <span class="lg"><i class="sw line"></i>Hand-off (machine, no copy-paste)</span></div>`;
}

/* ---------- checkpoint track -------------------------------------------- */
function checkpointTrack(cp, roles) {
  return `<div class="hctrack">${Object.values(cp).sort((a, b) => a.id.localeCompare(b.id)).map((c) => `
    <div class="hc ${c.state.replace("/", "")}" ${tipAttr(`<b>${esc(c.id)} · ${esc(c.name)}</b><br>Approvals logged: ${c.approvals}${c.ts ? "<br>Last: " + esc(c.ts) : ""}`)}>
      <div class="hcid"><span class="dot">${STATE_ICON[c.state]}</span>${esc(c.id)}</div>
      <div class="hcname">${esc(c.name)}</div>
      <div class="hcmeta">${statusChip(c.state === "n/a" ? "not started" : c.state)}${c.waiting ? ` ${chip(c.waiting + " waiting", "warn")}` : ""}</div>
      <div class="hcmeta muted">${c.by ? "by " + esc(c.by) : "&nbsp;"}</div>
      <div class="hcmeta">${c.owner_roles.map((r) => `<span class="rolechip r-${r}">${esc(roleLabel(r, roles))}</span>`).join("")}</div>
    </div>`).join("")}</div>`;
}

/* ---------- charts ------------------------------------------------------- */
function heatmap(risks) {
  const grid = {};
  risks.forEach((r) => { const k = `${r.likelihood}-${r.impact}`; (grid[k] = grid[k] || []).push(r); });
  const C = 46, P = 30;
  let s = `<svg viewBox="0 0 ${P + C * 5 + 4} ${C * 5 + 30}" class="heatsvg" role="img" aria-label="Risk heat map">`;
  for (let l = 5; l >= 1; l--) {
    const y = (5 - l) * C;
    s += `<text x="${P - 8}" y="${y + C / 2 + 4}" class="ax" text-anchor="end">L${l}</text>`;
    for (let i = 1; i <= 5; i++) {
      const x = P + (i - 1) * C, rs = grid[`${l}-${i}`] || [], sc = l * i;
      const band = sc >= 20 ? 4 : sc >= 12 ? 3 : sc >= 6 ? 2 : 1;
      s += `<g ${rs.length ? tipAttr(`<b>L${l} × I${i} = ${sc}</b><br>${rs.map((r) => `${esc(r.id)} · ${esc(r.description.slice(0, 70))}`).join("<br>")}`) : ""}>
        <rect x="${x + 1}" y="${y + 1}" width="${C - 2}" height="${C - 2}" rx="5" class="hb${band}"/>
        ${rs.length ? `<text x="${x + C / 2}" y="${y + C / 2 + 5}" class="hv">${rs.length}</text>` : ""}</g>`;
    }
  }
  for (let i = 1; i <= 5; i++) s += `<text x="${P + (i - 1) * C + C / 2}" y="${C * 5 + 18}" class="ax" text-anchor="middle">I${i}</text>`;
  return s + `</svg><div class="legend small"><span class="lg"><i class="sw hb1"></i>1–5</span><span class="lg"><i class="sw hb2"></i>6–11</span><span class="lg"><i class="sw hb3"></i>12–19</span><span class="lg"><i class="sw hb4"></i>20–25</span></div>`;
}

function hbars(rows, { max, fmt = (v) => v, cls = () => "", tipf } = {}) {
  max = max || Math.max(1, ...rows.map((r) => r.value));
  return `<div class="hbars">${rows.map((r) => `<div class="hbrow" ${tipAttr(tipf ? tipf(r) : `<b>${esc(r.label)}</b>: ${fmt(r.value)}`)}>
    <span class="hbl">${esc(r.label)}</span><span class="hbt"><i class="hbf ${cls(r)}" style="width:${(r.value / max) * 100}%"></i></span><span class="hbv">${fmt(r.value)}</span></div>`).join("")}</div>`;
}

function stackBar(parts, total) {
  total = total || parts.reduce((a, p) => a + p.value, 0) || 1;
  return `<div class="stack">${parts.filter((p) => p.value).map((p) => `<i class="${p.cls}" style="flex:${p.value}" ${tipAttr(`<b>${esc(p.label)}</b>: ${p.value} (${Math.round((p.value / total) * 100)}%)`)}></i>`).join("")}</div>
   <div class="legend small">${parts.map((p) => `<span class="lg"><i class="sw ${p.cls}"></i>${esc(p.label)} · <b>${p.value}</b></span>`).join("")}</div>`;
}

function gantt(ms) {
  const dated = ms.filter((m) => /^\d{4}-\d{2}/.test(m.date || ""));
  const toT = (s) => new Date(s.length === 7 ? s + "-01" : s).getTime();
  const t0 = new Date("2027-01-01").getTime(), t1 = new Date("2029-03-01").getTime();
  const L = 190, R = 90, W = 900, RH = 22, H = ms.length * RH + 34;
  const X = (t) => L + ((t - t0) / (t1 - t0)) * (W - L - R);
  let s = `<svg viewBox="0 0 ${W} ${H}" class="ganttsvg" role="img" aria-label="Milestone timeline">`;
  for (let y = 2027; y <= 2029; y++) for (const m of [0, 6]) {
    const t = new Date(`${y}-${String(m + 1).padStart(2, "0")}-01`).getTime();
    if (t > t1) continue;
    s += `<line x1="${X(t)}" x2="${X(t)}" y1="18" y2="${H - 6}" class="grid"/><text x="${X(t)}" y="12" class="ax" text-anchor="middle">${m ? "Jul" : y}</text>`;
  }
  s += `<text x="${W - R + 30}" y="12" class="ax" text-anchor="middle">TBD</text><line x1="${W - R + 8}" x2="${W - R + 8}" y1="18" y2="${H - 6}" class="grid"/>`;
  const yOf = {}, xOf = {};
  ms.forEach((m, i) => { yOf[m.id] = 30 + i * RH; xOf[m.id] = /^\d{4}-\d{2}/.test(m.date || "") ? X(toT(m.date)) : W - R + 30; });
  const mtip = (m) => tipAttr(`<b>${esc(m.id)} · ${esc(m.name)}</b><br>${m.date ? esc(m.date) : "TBD"} · ${esc(m.rel_month)} · WBS ${esc(m.wbs_code)}${m.depends_on.length ? "<br>after " + esc(m.depends_on.join(", ")) : ""}${m.note ? "<br>" + esc(m.note) : ""}`);
  ms.forEach((m, i) => {
    const y = yOf[m.id];
    s += `<g class="mrow" ${mtip(m)}><rect x="0" y="${y - RH / 2}" width="${W}" height="${RH}" class="rowhit ${i % 2 ? "odd" : ""}"/>
      <text x="8" y="${y + 4}" class="ml">${esc(m.id)} <tspan class="mn">${esc(m.name.length > 24 ? m.name.slice(0, 23) + "…" : m.name)}</tspan></text></g>`;
  });
  ms.forEach((m) => m.depends_on.forEach((p) => {
    if (xOf[p] === undefined) return;
    const x1 = xOf[p], y1 = yOf[p], x2 = xOf[m.id], y2 = yOf[m.id];
    s += `<path d="M${x1},${y1} C${x1 + 18},${y1} ${x2 - 18},${y2} ${x2},${y2}" class="dep"/>`;
  }));
  ms.forEach((m) => {
    const y = yOf[m.id], x = xOf[m.id], tbd = !dated.includes(m), risky = /CONFLICT|NOT FOUND|AT RISK/.test(m.note || "");
    s += `<path ${mtip(m)} d="M${x},${y - 7} L${x + 7},${y} L${x},${y + 7} L${x - 7},${y} z" class="ms ${tbd ? "tbd" : ""} ${risky ? "risky" : ""}"/>`;
  });
  return s + `</svg><div class="legend small"><span class="lg"><i class="sw ms"></i>Dated milestone</span><span class="lg"><i class="sw ms tbd"></i>TBD / not in pack</span><span class="lg"><i class="sw ms risky"></i>Conflict / at risk</span><span class="lg"><i class="sw line"></i>Dependency</span></div>`;
}

function activityChart(rows) {
  if (!rows.length) return `<p class="muted">No activity yet.</p>`;
  const ts = rows.map((r) => new Date(r.ts).getTime()).filter((x) => !isNaN(x));
  const lo = Math.min(...ts), hi = Math.max(...ts), span = hi - lo;
  const steps = [[60e3, "min"], [300e3, "5 min"], [3600e3, "hour"], [86400e3, "day"], [7 * 86400e3, "week"]];
  const [step, unit] = steps.find(([s]) => span / s <= 40) || steps[steps.length - 1];
  const start = Math.floor(lo / step) * step, n = Math.floor((hi - start) / step) + 1;
  const kinds = ["agent", "human", "system"];
  const buckets = Array.from({ length: n }, (_, i) => ({ t: start + i * step, agent: 0, human: 0, system: 0 }));
  rows.forEach((r) => { const t = new Date(r.ts).getTime(); if (isNaN(t)) return; const b = buckets[Math.floor((t - start) / step)]; if (b && b[r.actor_type] !== undefined) b[r.actor_type]++; });
  const max = Math.max(1, ...buckets.map((b) => b.agent + b.human + b.system));
  const W = 1100, H = 190, L = 34, B = 24, bw = Math.max(3, Math.min(26, (W - L - 8) / n - 2));
  const fmt = (t) => { const d = new Date(t); return unit === "day" || unit === "week" ? d.toISOString().slice(5, 10) : d.toTimeString().slice(0, 5); };
  let s = `<svg viewBox="0 0 ${W} ${H}" class="actsvg" role="img" aria-label="Audit activity">`;
  [0, 0.5, 1].forEach((f) => { const y = H - B - f * (H - B - 10); s += `<line x1="${L}" x2="${W}" y1="${y}" y2="${y}" class="grid"/><text x="${L - 6}" y="${y + 4}" class="ax" text-anchor="end">${Math.round(max * f)}</text>`; });
  buckets.forEach((b, i) => {
    const x = L + 4 + i * ((W - L - 8) / n);
    let y = H - B;
    kinds.forEach((k) => {
      if (!b[k]) return;
      const h = (b[k] / max) * (H - B - 10);
      s += `<rect x="${x}" y="${y - h}" width="${bw}" height="${Math.max(1, h - 2)}" class="c-${k}"/>`;
      y -= h;
    });
    s += `<rect x="${x - 1}" y="10" width="${bw + 2}" height="${H - B - 10}" class="hit" ${tipAttr(`<b>${fmt(b.t)}</b> (per ${unit})<br>agent ${b.agent} · human ${b.human} · system ${b.system}`)}/>`;
    if (i % Math.ceil(n / 8) === 0) s += `<text x="${x + bw / 2}" y="${H - 8}" class="ax" text-anchor="middle">${fmt(b.t)}</text>`;
  });
  return s + `</svg><div class="legend small">${kinds.map((k) => `<span class="lg"><i class="sw c-${k}"></i>${k} · <b>${rows.filter((r) => r.actor_type === k).length}</b></span>`).join("")}<span class="muted">bucket = ${unit}</span></div>`;
}

function approvalsChart(rows) {
  const ids = ["HC1", "HC2", "HC3", "HC4", "HC5", "HC6", "HC7"];
  const by = Object.fromEntries(ids.map((i) => [i, { approved: 0, rejected: 0 }]));
  rows.forEach((r) => { if (by[r.checkpoint]) by[r.checkpoint][r.decision] = r.c; });
  const max = Math.max(1, ...ids.map((i) => by[i].approved + by[i].rejected));
  return `<div class="cols">${ids.map((i) => {
    const a = by[i].approved, r = by[i].rejected;
    return `<div class="col" ${tipAttr(`<b>${i}</b><br>approved ${a} · rejected ${r}`)}><div class="colbar">
      ${r ? `<i class="seg rej" style="height:${(r / max) * 100}%"></i>` : ""}${a ? `<i class="seg app" style="height:${(a / max) * 100}%"></i>` : ""}</div>
      <b>${a + r}</b><span>${i}</span></div>`;
  }).join("")}</div><div class="legend small"><span class="lg"><i class="sw app"></i>approved</span><span class="lg"><i class="sw rej"></i>rejected</span></div>`;
}

/* ---------- Dashboard view ---------------------------------------------- */
function canView(tab) { return !!(ME && ME.views.includes(tab)); }
function roleLabel(r, roles) {
  const x = (roles || ROLES_META)[r]; if (!x) return r;
  return window.HCH_I18N.language === "zh" ? x.label_zh : x.label;
}

async function vDashboard() {
  const d = await api("/api/dashboard");
  const k = d.kpis;
  const gapParts = d.gaps ? (() => {
    const g = d.gaps, sum = (re) => Object.entries(g).filter(([s]) => re.test(s)).reduce((a, [, v]) => a + v, 0);
    return [{ label: "Answered", value: sum(/^Answered/), cls: "s-ok" }, { label: "Partially answered", value: sum(/^Partial/), cls: "s-warn" }, { label: "Open", value: sum(/^Open/), cls: "s-stop" }];
  })() : null;
  const repOrder = ["draft", "critic_stopped", "critic_passed", "released", "stale"];
  const rep = d.flow.reports || {};
  main.innerHTML = `
  <h1>Visual dashboard</h1>
  <p class="lead">Live view of the whole governed process for <b>${esc(ME.name)}</b> (${esc(roleLabel(ME.role))}). Sections your role may not open are omitted by the server, not just hidden.</p>
  <div class="grid kpis">
    ${[["Verified facts", k.facts], ["WBS elements", k.wbs], ["Risks", k.risks], ["Report versions", k.reports],
       ["Open sponsor questions", k.open_gaps, k.open_gaps ? "warn" : ""], ["Pending HC6 actions", k.pending_actions, k.pending_actions ? "warn" : ""],
       ["Approvals logged", k.approvals], ["Blocked / rejected", k.blocked, k.blocked ? "stop" : ""]]
      .map(([l, v, c]) => `<div class="stat ${c || ""}"><b>${v}</b><span>${l}</span></div>`).join("")}
  </div>
  ${d.demo ? demoPanel(d.demo, true) : ""}
  <h2>End-to-end process flow</h2>
  <div class="card flowcard"><div class="flowscroll">${flowChart(d)}</div>${flowLegend()}</div>
  <h2>Human checkpoints HC1–HC7</h2>
  ${checkpointTrack(d.checkpoints)}
  <div class="dgrid">
    ${d.risks ? `<div class="card"><h3>Risk heat map (likelihood × impact)</h3><div class="heatwrap">${heatmap(d.risks)}</div></div>
    <div class="card"><h3>Top risks by score</h3>${hbars(d.risks.slice(0, 8).map((r) => ({ label: r.id, value: r.score, r })), { max: 25, cls: (x) => x.value >= 20 ? "s-stop" : x.value >= 12 ? "s-warn" : "", tipf: (x) => `<b>${esc(x.r.id)} · ${x.value}</b> (L${x.r.likelihood}×I${x.r.impact})<br>${esc(x.r.description)}<br>Owner: ${esc(x.r.owner)}` })}</div>` : ""}
    ${gapParts ? `<div class="card"><h3>Sponsor questions by status</h3>${stackBar(gapParts)}
      <h3>WBS by level</h3>${hbars(Object.entries(d.wbs_levels).map(([l, v]) => ({ label: "Level " + l, value: v })))}</div>` : ""}
    <div class="card"><h3>Report versions by status</h3>${hbars(repOrder.filter((s) => rep[s] !== undefined).map((s) => ({ label: s, value: rep[s] })), { cls: (x) => x.label === "critic_stopped" || x.label === "stale" ? "s-stop" : x.label === "released" ? "s-ok" : "" })}
      ${d.pm_status ? `<h3>PM board items by status</h3>${hbars(Object.entries(d.pm_status).map(([s, v]) => ({ label: s, value: v })))}` : ""}</div>
    ${d.audit ? `<div class="card"><h3>Approvals per checkpoint</h3>${approvalsChart(d.approvals_by)}
      ${d.denied.length ? `<h3>Access denied (RBAC) by account</h3>${hbars(d.denied.map((x) => ({ label: x.actor, value: x.c })), { cls: () => "s-stop" })}` : ""}</div>
    <div class="card wide"><h3>Audit activity over time</h3>${activityChart(d.audit)}</div>` : ""}
    ${d.milestones ? `<div class="card wide"><h3>Milestone timeline &amp; dependencies</h3><div class="flowscroll">${gantt(d.milestones)}</div></div>` : ""}
  </div>`;
  bindGo();
}

function bindGo() {
  main.querySelectorAll("[data-go]").forEach((el) => (el.onclick = () => { location.hash = el.dataset.go; }));
}

function demoPanel(steps, compact) {
  const done = steps.filter((s) => s.done).length;
  return `<h2>Admin demo walkthrough · ${done}/${steps.length} complete</h2>
  <div class="progress"><i style="width:${(done / steps.length) * 100}%"></i></div>
  <div class="steps ${compact ? "compact" : ""}">${steps.map((s, i) => `
    <div class="step ${s.done ? "done" : i === steps.findIndex((x) => !x.done) ? "next" : ""}" data-go="${s.tab}" ${tipAttr(`<b>${esc(s.title)}</b><br>Owner role: ${esc(s.owner_label)}${s.detail ? "<br>" + esc(s.detail) : ""}<br><span class='muted'>Click to open</span>`)}>
      <span class="num">${s.done ? "✓" : i + 1}</span>
      <div><b>${esc(s.title)}</b><div class="muted">${s.checkpoint ? esc(s.checkpoint) + " · " : ""}<span class="rolechip r-${s.owner}">${esc(roleLabel(s.owner))}</span></div>
      ${!compact && s.detail ? `<div class="muted small">${esc(s.detail)}</div>` : ""}</div>
    </div>`).join("")}</div>`;
}

/* ---------- Admin console ------------------------------------------------ */
function rbacDiagram(roles, checkpoints, counts) {
  const W = 900, rowH = 44, cpIds = Object.keys(checkpoints), H = cpIds.length * rowH + 12;
  const ry = (i) => 34 + i * ((H - 68) / (ROLE_ORDER.length - 1 || 1));
  const cy = (i) => 24 + i * rowH;
  let s = `<svg viewBox="0 0 ${W} ${H}" class="rbacsvg" role="img" aria-label="Roles to checkpoints">`;
  ROLE_ORDER.forEach((r, i) => roles[r].checkpoints.forEach((c) => {
    const j = cpIds.indexOf(c);
    s += `<path d="M210,${ry(i)} C380,${ry(i)} 380,${cy(j)} 520,${cy(j)}" class="rl r-${r} ${r === "admin" ? "faint" : ""}"/>`;
  }));
  ROLE_ORDER.forEach((r, i) => {
    s += `<g ${tipAttr(`<b>${esc(roles[r].label)}</b><br>${esc(roles[r].description)}<br>Views: ${roles[r].views.length} · Actions: ${roles[r].actions.length}`)}>
      <rect x="10" y="${ry(i) - 20}" width="200" height="40" rx="20" class="rn r-${r}"/><text x="110" y="${ry(i) - 1}" class="rt">${esc(roleLabel(r))}</text>
      <text x="110" y="${ry(i) + 13}" class="rs">${(counts || {})[r] || 0} account(s) · ${roles[r].checkpoints.length} checkpoint(s)</text></g>`;
  });
  cpIds.forEach((c, j) => {
    const nm = checkpoints[c].name;
    s += `<g ${tipAttr(`<b>${esc(c)}</b> ${esc(nm)}<br>${esc(checkpoints[c].gates)}`)}><rect x="520" y="${cy(j) - 16}" width="${W - 526}" height="32" rx="7" class="cn"/>
      <text x="532" y="${cy(j) + 5}" class="ct"><tspan class="cid">${c}</tspan> ${esc(nm.length > 44 ? nm.slice(0, 43) + "…" : nm)}</text></g>`;
  });
  return s + `</svg><p class="muted small">Admin (faint lines) may approve any checkpoint; every other role approves only its own. The server rejects anything else and logs it as <i>access denied</i>.</p>`;
}

const TAB_LABEL = { dashboard: "Dashboard", overview: "Overview", planning: "1 · Planning", pm: "2 · PM tool", memory: "3 · Memory", risk: "4 · Risk & what-if", reports: "5 · Reports & critic", change: "6 · Change", governance: "Governance", agents: "Agent cards", eval: "Evaluation", admin: "Admin console" };
const ACTION_LABEL = { "run.pipeline": "Run pipeline", "reset.demo": "Reset demo", "pm.write": "Write PM board", "memory.ask": "Ask memory", "memory.decide": "Record decision", "reports.generate": "Regenerate reports", "reports.plant": "Plant critic fault", "change.inject": "Inject change event", "eval.run": "Run evaluation", "audit.view": "View audit trail", "audit.export": "Export audit", "users.manage": "Manage users" };

function permMatrix(u) {
  const rows = [["Views", u.views.map((v) => [TAB_LABEL[v] || v, (r) => u.roles[r].views.includes(v)])],
    ["Actions", Object.keys(ACTION_LABEL).map((a) => [ACTION_LABEL[a], (r) => u.roles[r].actions.includes(a)])],
    ["Checkpoints", Object.keys(u.checkpoints).map((c) => [`${c} · ${u.checkpoints[c].name}`, (r) => u.roles[r].checkpoints.includes(c)])]];
  return `<div class="tablewrap"><table class="matrix"><thead><tr><th></th>${ROLE_ORDER.map((r) => `<th><span class="rolechip r-${r}">${esc(roleLabel(r))}</span></th>`).join("")}</tr></thead><tbody>
    ${rows.map(([grp, items]) => `<tr class="grp"><td colspan="${ROLE_ORDER.length + 1}">${grp}</td></tr>` + items.map(([label, f]) => `<tr><td>${esc(label)}</td>${ROLE_ORDER.map((r) => `<td class="c">${f(r) ? `<span class="yes" aria-label="allowed">●</span>` : `<span class="no" aria-label="denied">·</span>`}</td>`).join("")}</tr>`).join("")).join("")}
  </tbody></table></div>`;
}

async function vAdmin() {
  const [u, d] = await Promise.all([api("/api/admin/users"), api("/api/dashboard")]);
  const roleOpts = (sel) => ROLE_ORDER.map((r) => `<option value="${r}" ${r === sel ? "selected" : ""}>${esc(roleLabel(r))}</option>`).join("");
  main.innerHTML = `
  <h1>Admin console</h1>
  <p class="lead">System administrator view: the guided demo path across all roles, who can do what, user accounts and the access log. Every change here is written to the audit trail.</p>
  ${demoPanel(d.demo, false)}
  <div class="row muted small">Tip: open each step as admin, or sign out and log in as the owning role to show the permission isolation (for example, a Group Leader cannot approve HC2).</div>
  <h2>Role → checkpoint authority</h2>
  <div class="card"><div class="flowscroll">${rbacDiagram(u.roles, u.checkpoints, d.users_by_role)}</div></div>
  <h2>Permission matrix</h2>
  ${permMatrix(u)}
  <h2>Users (${u.users.length})</h2>
  ${table(["Username", "Name", "Role", "Status", "Last login", "Sessions", "Approvals", "Human actions", "Denied", ""], u.users.map((x) => `<tr data-user="${esc(x.username)}">
     <td class="mono">${esc(x.username)}${x.username === ME.username ? " " + chip("you", "info") : ""}</td><td><input class="u-name" value="${esc(x.display_name)}" style="width:130px"></td>
     <td><select class="u-role">${roleOpts(x.role)}</select></td><td>${x.active ? chip("active", "ok") : chip("disabled", "stop")}</td>
     <td class="mono">${esc(x.last_login || "—")}</td><td>${x.active_sessions}</td><td>${x.approvals}</td><td>${x.human_actions}</td><td>${x.denied ? chip(x.denied, "stop") : 0}</td>
     <td class="uact"><button class="ghost u-save">Save</button> <button class="${x.active ? "danger" : "ghost"} u-act" data-active="${x.active}">${x.active ? "Disable" : "Enable"}</button></td></tr>`))}
  <div class="card"><h3>Create user</h3><div class="row">
    <input id="nu-user" placeholder="username" autocomplete="off"><input id="nu-name" placeholder="Display name"><select id="nu-role">${roleOpts("project_manager")}</select>
    <button id="nu-go">Create</button></div></div>
  <h2>Access log (logins, denied requests, user changes)</h2>
  ${table(["#", "Time", "Account", "Event", "Target", "Outcome"], u.access_log.map((a) => `<tr><td>${a.id}</td><td class="mono">${esc(a.ts)}</td><td>${esc(a.actor)}</td><td>${esc(a.action)}</td><td class="mono">${esc(a.target_id)}</td><td>${statusChip(a.outcome)}</td></tr>`))}`;
  bindGo();
  const save = async (tr, extra) => {
    await api("/api/admin/users", Object.assign({ username: tr.dataset.user, role: $(".u-role", tr).value, display_name: $(".u-name", tr).value }, extra));
    toast("User updated"); vAdmin();
  };
  main.querySelectorAll("tr[data-user]").forEach((tr) => {
    $(".u-save", tr).onclick = () => save(tr, {});
    $(".u-act", tr).onclick = () => save(tr, { active: !Number($(".u-act", tr).dataset.active) });
  });
  $("#nu-go").onclick = async () => {
    await api("/api/admin/users", { create: true, username: $("#nu-user").value, display_name: $("#nu-name").value, role: $("#nu-role").value });
    toast("User created"); vAdmin();
  };
}
