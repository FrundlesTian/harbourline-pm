/* Harbourline AI PM - single-page UI (vanilla JS, no build step). */
const $ = (s, el = document) => el.querySelector(s);
const main = $("#main");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let current = "dashboard";
let ME = null;          // logged-in account (from /api/me); the server enforces every permission
let ROLES_META = {};
const can = (perm) => !!ME && (perm.startsWith("view.") ? ME.views.includes(perm.slice(5)) : perm.startsWith("HC") ? ME.checkpoints.includes(perm) : ME.actions.includes(perm));

async function api(path, body) {
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch(path, opt);
  const j = await r.json().catch(() => ({ error: "bad response" }));
  if (r.status === 401) { showLogin(); throw new Error(j.error || "Please log in"); }
  if (!r.ok) { toast(j.error || `HTTP ${r.status}`); throw new Error(j.error); }
  return j;
}
async function displayText(text) {
  if (window.HCH_I18N.language !== "zh" || !text) return text;
  try { return (await api("/api/translate", { text })).text; } catch (_) { return text; }
}
async function translateExtra(values) {
  if (window.HCH_I18N.language !== "zh") return;
  const texts = [...new Set(values.flat(Infinity).filter((x) => typeof x === "string" &&
    x.length > 12 && /[A-Za-z]/.test(x) && window.HCH_I18N.translate(x) === x))];
  if (!texts.length) return;
  try {
    const result = await api("/api/translate-batch", { texts });
    window.HCH_I18N.addTranslations(Object.fromEntries(texts.map((source, i) => [source, result.texts[i]])));
  } catch (_) {}
}
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => (t.hidden = true), 4200); }
/* The approver is always the logged-in account; the server signs approvals with it. */
function approver() { return ME ? ME.name : null; }

/* Permission gating: any element with data-perm is disabled (or hidden with data-perm-hide)
   when the role lacks it. This is cosmetic - the server returns 403 regardless. */
function applyPerms(root) {
  if (!ME || !root.querySelectorAll) return;
  const els = root.matches && root.matches("[data-perm]") ? [root, ...root.querySelectorAll("[data-perm]")] : root.querySelectorAll("[data-perm]");
  els.forEach((el) => {
    if (can(el.dataset.perm)) return;
    if (el.hasAttribute("data-perm-hide")) { el.hidden = true; return; }
    el.disabled = true; el.classList.add("noperm");
    el.title = `Not permitted for ${ME.role_label}: ${el.dataset.perm}`;
  });
}
new MutationObserver((recs) => recs.forEach((r) => r.addedNodes.forEach((n) => n.nodeType === 1 && applyPerms(n))))
  .observe(document.getElementById("main"), { childList: true, subtree: true });

const chip = (txt, cls = "") => `<span class="chip ${cls}">${esc(txt)}</span>`;
function statusChip(s) {
  s = String(s || "");
  const cls = /^Answered|passed|released|signed|applied|ok|approved|PASS|verified/i.test(s) ? "ok"
    : /stop|blocked|reject|stale|REOPENED|FAIL|Open$/i.test(s) ? "stop"
    : /Partial|pending|awaiting|Proposed|risk/i.test(s) ? "warn" : "info";
  return chip(s, cls);
}
function cites(list) {
  return (list || []).map((c) => {
    const id = typeof c === "string" ? c : c.id;
    const label = typeof c === "string" ? c : (c.label || c.id);
    return `<span class="cite" data-src="${esc(id)}" title="${esc(label)}">${esc(id)}</span>`;
  }).join("");
}
document.addEventListener("click", async (e) => {
  const c = e.target.closest(".cite");
  if (!c) return;
  const id = c.dataset.src;
  if (id.startsWith("RISK:")) { openModal(`<h3>${esc(id)}</h3><p>Risk register row - see tab 4.</p>`); return; }
  const s = await api(`/api/source/${encodeURIComponent(id)}`).catch(() => null);
  if (s) openModal(`<h3>${esc(s.cite.label)}</h3><pre>${esc(s.text)}</pre>`);
});
function openModal(html) { $("#modal-body").innerHTML = html; $("#modal").hidden = false; }
$("#modal-x").onclick = () => ($("#modal").hidden = true);
$("#modal").onclick = (e) => { if (e.target.id === "modal") $("#modal").hidden = true; };

$("#nav").addEventListener("click", (e) => {
  const a = e.target.closest("a[data-tab]");
  if (!a) return;
  document.querySelectorAll("#nav a").forEach((x) => x.classList.toggle("on", x === a));
  location.hash = a.dataset.tab;
});
async function render() {
  main.innerHTML = `<p class="muted">Loading…</p>`;
  try { await VIEWS[current](); } catch (e) { main.innerHTML = `<div class="card">${chip("error", "stop")} ${esc(e.message)}</div>`; }
}
function table(cols, rows) {
  return `<div class="tablewrap"><table><thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${rows.join("") || `<tr><td colspan="${cols.length}" class="muted">Nothing yet.</td></tr>`}</tbody></table></div>`;
}
function approvalLine(a) { return a ? `${statusChip(a.decision)} by <b>${esc(a.approver)}</b> (${esc(a.role)}) · ${esc(a.ts)}` : chip("not approved", "warn"); }

/* ------------------------------------------------------------ Overview */
async function vOverview() {
  const s = await api("/api/status");
  $("#mode").textContent = `${s.generation === "llm" ? "LLM: DeepSeek" : "LLM off · deterministic"} · PM: ${s.pm_backend}`;
  const c = s.counts;
  const og = s.origins || {};
  const originRow = [["planning", "Planning"], ["risk", "Risk register"], ["reporting", "Reports"], ["change", "Change analysis"]].map(([k, label]) => {
    const o = og[k];
    if (!o) return `<span>${label} ${chip("not run")}</span>`;
    const tip = o.mode === "llm" ? `Generated by ${o.model}, validated` : `Curated baseline${o.reason ? " — " + o.reason : ""}`;
    return `<span title="${esc(tip)}">${label} ${o.mode === "llm" ? chip("LLM-generated, validated", "ok") : chip("baseline fallback", o.reason && o.reason !== "LLM not configured" && o.reason !== "baseline mode requested" ? "warn" : "info")}</span>`;
  }).join(" &nbsp; ");
  const cp = s.checkpoints;
  main.innerHTML = `
  <h1>Harbourline Community Hub Refurbishment</h1>
  <p class="lead">Six agent modules and a governance layer working as one system. Facts come only from the brief, Sponsor Answers Round 1 and the data pack; anything else is reported as NOT FOUND. Agents draft; named humans approve at the checkpoints marked in amber.</p>
  <div class="row"><a href="#dashboard">Open the visual dashboard and full process flowchart →</a></div>
  <div class="card"><div class="flow">
    <span class="node">Sources → fact store (${c.facts} verified facts)</span><span class="arrow">→</span>
    <span class="node">1 Planning</span><span class="hc node">HC1 · HC2</span><span class="arrow">→</span>
    <span class="node">2 PM tool</span><span class="hc node">HC3</span><span class="arrow">·</span>
    <span class="node">4 Risk &amp; what-if</span><span class="hc node">HC4</span><span class="arrow">→</span>
    <span class="node">5 Reporting → Critic</span><span class="hc node">HC5</span><span class="arrow">·</span>
    <span class="node">6 Change</span><span class="hc node">HC6</span><span class="arrow">·</span>
    <span class="node">Bias check</span><span class="hc node">HC7</span>
  </div></div>
  <div class="row"><button id="run" data-perm="run.pipeline">Run full pipeline</button><button class="ghost" id="reset" data-perm="reset.demo">Reset demo outputs</button>
    <span class="muted">Re-running with the same inputs creates no new versions and no PM duplicates.</span></div>
  <div class="grid">
    ${[["Source chunks", c.sources], ["Sponsor Questions / gaps", c.gaps], ["Conflicts", c.conflicts], ["WBS elements", c.wbs], ["Milestones", c.milestones],
       ["Risks", c.risks], ["What-ifs", c.whatifs], ["Report versions", c.reports], ["PM issues", c.pm_issues], ["Change events", c.change_events],
       ["Pending HC6 actions", c.pending_actions], ["Audit rows", c.audit]].map(([k, v]) => `<div class="stat"><b>${v}</b><span>${k}</span></div>`).join("")}
  </div>
  <h2>Who produced the outputs</h2>
  <div class="row">${originRow}</div>
  <p class="muted">LLM-generated outputs are checked before use: unknown sources, WBS codes and tags are dropped, dates must appear in a cited source, every report number is traced by the Critic (up to 3 revision rounds). The curated baseline is used only when the LLM is off or its output fails these checks. Responses are cached, so re-runs on the same inputs are identical.</p>
  <h2>Human checkpoints</h2>
  <div class="row">${["HC1", "HC2", "HC4"].map((k) => `${k} ${cp[k] ? chip("approved (current version)", "ok") : chip("awaiting", "warn")}`).join(" &nbsp; ")} &nbsp; HC7 ${statusChip(cp.HC7 || "not run")}</div>
  <h2>Machine hand-offs (no copy-paste)</h2>
  ${table(["Time", "From", "To", "Payload", "Items"], s.handoffs.map((h) => `<tr><td class="mono">${esc(h.ts)}</td><td>${esc(h.from_agent)}</td><td>${esc(h.to_agent)}</td><td>${esc(h.payload_ref)}</td><td>${h.items}</td></tr>`))}
  <h2>Runs · cost and time</h2>
  ${table(["Run", "Kind", "Seconds", "Tokens in/out", "Cost (US$)", "LLM calls"], s.runs.map((r) => `<tr><td class="mono">${esc(r.id)}</td><td>${esc(r.kind)}</td><td>${r.seconds ?? ""}</td><td>${r.tokens_in}/${r.tokens_out}</td><td>${r.cost_usd}</td><td>${r.llm_calls}</td></tr>`))}`;
  $("#run").onclick = async () => { $("#run").disabled = true; const r = await api("/api/run", { use_llm: true }); toast(`Run ${r.run_id}: ${r.seconds}s, ${r.tokens_in + r.tokens_out} tokens`); render(); };
  $("#reset").onclick = async () => { await api("/api/reset", {}); toast("Outputs cleared. Audit log and approvals kept."); render(); };
}

/* ------------------------------------------------------------ Planning */
async function vPlanning() {
  const p = await api("/api/planning");
  if (!p.scope) { main.innerHTML = `<div class="card">No plan yet. Run the pipeline from Overview.</div>`; return; }
  main.innerHTML = `
  <h1>1 · Planning</h1>
  <p class="lead">Scope statement, Sponsor Questions with an assumption register, the brief's contradictions, a Level-3 WBS with dictionary and traceability, and a milestone plan in relative time (dates only where the sponsor or pack gives them).</p>
  <div class="card"><h3>${esc(p.scope.title)}</h3>
    <p><b>Objective.</b> ${esc(p.scope.objective.text)} ${cites([p.scope.objective.source])}</p>
    ${table(["ID", "Scope line", "Kind", "Source"], p.scope.lines.map((l) => `<tr><td>${l.id}</td><td>${esc(l.text)}</td><td>${statusChip(l.kind)}</td><td>${cites([l.cite])}</td></tr>`))}
    <p><b>Success.</b> ${esc(p.scope.success.text)} ${cites([p.scope.success.source])}</p></div>
  <h2>Sponsor Questions &amp; assumption register (${p.gaps.length})</h2>
  <div class="row">HC1: ${approvalLine(p.hc1)} <button id="hc1" data-perm="HC1">Approve register (HC1)</button></div>
  ${table(["ID", "Topic", "Question", "Why (brief evidence)", "Status", "Answer / assumption"], p.gaps.map((g) => `<tr>
     <td>${g.id}</td><td>${esc(g.category)}${g.sponsor_only ? "<br>" + chip("sponsor only", "info") : ""}</td><td>${esc(g.question)}</td>
     <td>${esc(g.why)} ${cites(g.sources)}</td><td>${statusChip(g.status)}</td>
     <td>${esc(g.answer)} ${cites(g.answer_sources)}${g.assumption ? `<div class="muted">${esc(g.assumption)}</div>` : ""}</td></tr>`))}
  <h2>Conflicts between sources (${p.conflicts.length})</h2>
  ${table(["ID", "Topic", "What disagrees", "Sources (all named)"], p.conflicts.map((c) => `<tr><td>${c.id}</td><td>${esc(c.topic)}</td><td>${esc(c.detail)}</td><td>${cites(c.sources)}</td></tr>`))}
  <h2>WBS to Level 3 with dictionary (${p.wbs.length})</h2>
  <div class="row">HC2 (plan version <span class="mono">${p.plan_hash}</span>): ${approvalLine(p.hc2)} <button id="hc2" data-perm="HC2">Approve plan baseline (HC2)</button></div>
  ${table(["Code", "Element", "Traces to", "Deliverables", "Owner", "Dictionary"], p.wbs.map((w) => `<tr>
     <td class="mono">${w.code}</td><td class="lvl${w.level}">${esc(w.name)}</td><td>${w.scope_refs.map((s) => chip(s)).join(" ")}</td>
     <td>${w.deliverable_refs.join(", ")}</td><td>${w.owner.startsWith("UNASSIGNED") ? chip(w.owner, "stop") : esc(w.owner)}</td>
     <td>${w.level === 3 ? `<details><summary>dictionary</summary>${esc(w.description)} ${cites(w.sources)}</details>` : ""}</td></tr>`))}
  <h3>Flagged, not kept (no traceable scope line)</h3>
  ${table(["Candidate element", "Reason", "Sources"], p.flagged.map((f) => `<tr><td>${esc(f.name)}</td><td>${esc(f.reason)}</td><td>${cites(f.sources)}</td></tr>`))}
  <h2>Milestone plan with dependencies</h2>
  <p class="muted">Dependency check: ${p.dependency_issues.length ? p.dependency_issues.map(esc).join("; ") : "no ordering violations"}.</p>
  ${table(["ID", "Milestone", "WBS", "Relative", "Date", "Depends on", "Note", "Sources"], p.milestones.map((m) => `<tr>
     <td>${m.id}</td><td>${esc(m.name)}</td><td class="mono">${m.wbs_code}</td><td>${esc(m.rel_month)}</td>
     <td>${m.date ? esc(m.date) : chip("TBD", "warn")}</td><td>${m.depends_on.join(", ")}</td><td>${/CONFLICT|NOT FOUND|AT RISK/.test(m.note) ? `<span style="color:var(--stop)">${esc(m.note)}</span>` : esc(m.note)}</td><td>${cites(m.sources)}</td></tr>`))}`;
  $("#hc1").onclick = () => approve("HC1");
  $("#hc2").onclick = () => approve("HC2");
  void translateExtra([p.scope.title, p.scope.objective.text, p.scope.success.text,
    p.scope.lines.map((x) => x.text), p.gaps.flatMap((x) => [x.question, x.why, x.answer, x.assumption]),
    p.conflicts.map((x) => x.detail), p.wbs.flatMap((x) => [x.description, x.acceptance]),
    p.flagged.flatMap((x) => [x.name, x.reason]), p.milestones.map((x) => x.note)]);
}
async function approve(cp, item_id, decision = "approved", comment = "") {
  const who = approver(); if (!who) return;
  const r = await api("/api/approve", { checkpoint: cp, item_id, approver: who, decision, comment });
  toast(`${cp} ${decision} by ${who}`);
  render();
  return r;
}

/* ------------------------------------------------------------ PM tool */
async function vPM() {
  const b = await api("/api/pm/board");
  const jira = b.backend === "jira";
  main.innerHTML = `
  <h1>2 · PM tool integration</h1>
  ${jiraPanel(b)}
  <p class="lead">Backend: <b>${esc(b.backend)}</b> (project <b data-no-translate>${esc(b.project)}</b>). Writes need the plan approved (HC2) and the exact diff approved (HC3). Stable external keys (<span class="mono">ext-HCH-…</span> labels) make a second run update rather than duplicate. Agents may create, update and comment; Done, close and delete are human acts.</p>
  <div class="row"><button id="prev" data-perm="pm.write">1. Preview diff (read-only)</button><span id="previnfo" class="muted"></span></div>
  <div id="prevbox"></div>
  <h2>Board (${b.issues.length} items)</h2>
  <div class="row"><button class="ghost" id="rb">Read back &amp; verify</button><span id="rbinfo"></span></div>
  <div class="row"><span class="muted">Guardrail demo - the agent tries to:</span>
    <button class="danger" data-op="done" data-perm="pm.write">move to Done</button><button class="danger" data-op="close" data-perm="pm.write">close</button><button class="danger" data-op="delete" data-perm="pm.write">delete</button></div>
  ${table(["Key", "Type", "Summary", "Labels", "Due", "Status", "Links", "Comments", "Human"], b.issues.map((i) => `<tr>
    <td class="mono">${i.url ? `<a href="${esc(i.url)}" target="_blank" rel="noopener">${esc(i.key)} ↗</a>` : esc(i.key)}</td><td>${esc(i.issue_type)}</td><td>${esc(i.summary)}${i.parent_key ? `<div class="muted">parent ${esc(i.parent_key)}</div>` : ""}</td>
    <td>${i.labels.map((l) => chip(l, l === "ai-generated" ? "info" : l.startsWith("change-") ? "warn" : "")).join(" ")}</td>
    <td>${esc(i.due_date || "")}</td><td>${statusChip(i.status)}</td><td>${i.links.map((l) => esc(l.type + " " + l.key)).join("<br>")}</td>
    <td>${(i.comments || []).map((c) => `<div class="muted">${esc(c.body)}</div>`).join("")}</td>
    <td>${b.backend === "mock" && i.status !== "Done" ? `<button class="ghost" data-human="${esc(i.key)}" data-perm="pm.write">Done</button>` : i.url ? `<a href="${esc(i.url)}" target="_blank" rel="noopener" class="muted">Open in Jira</a>` : ""}</td></tr>`))}`;
  bindJiraPanel();
  $("#prev").onclick = async () => {
    const p = await api("/api/pm/preview");
    if (!p.ok) { $("#previnfo").innerHTML = chip(p.reason, "stop"); return; }
    $("#previnfo").innerHTML = `preview <span class="mono">${p.preview_id}</span>: ${Object.entries(p.counts).map(([k, v]) => chip(`${k} ${v}`, k === "unchanged" ? "ok" : "warn")).join(" ")}`;
    $("#prevbox").innerHTML = `<div class="row"><button id="hc3" data-perm="HC3">2. Approve this diff (HC3) and write</button></div>` +
      `<details><summary>${p.items.length} items</summary>${table(["External key", "Summary", "Action", "Remote"], p.items.map((i) => `<tr><td class="mono">${esc(i.ext_key)}</td><td>${esc(i.summary)}</td><td>${statusChip(i.action)}</td><td>${esc(i.remote_key || "")}</td></tr>`))}</details>`;
    $("#hc3").onclick = async () => {
      const who = approver(); if (!who) return;
      await api("/api/approve", { checkpoint: "HC3", item_id: p.preview_id, approver: who, decision: "approved" });
      const r = await api("/api/pm/apply", { preview_id: p.preview_id });
      toast(r.ok ? `Created ${r.created}, updated ${r.updated}, unchanged ${r.unchanged}; read-back ${r.readback.verified ? "verified" : "has issues"}` : r.reason);
      render();
    };
  };
  $("#rb").onclick = async () => {
    const r = await api("/api/pm/readback");
    $("#rbinfo").innerHTML = `${statusChip(r.verified ? "verified" : "not verified")} board ${r.board_items} / plan ${r.plan_items}; missing ${r.missing.length}; mismatched ${r.mismatched.length}; duplicates ${Object.keys(r.duplicates).length}; human-Done ${r.human_done.length}`;
  };
  main.querySelectorAll("[data-op]").forEach((btn) => btn.onclick = async () => {
    const key = (b.issues[0] || {}).key || "HCH-1";
    const r = await api("/api/pm/agent_attempt", { op: btn.dataset.op, key });
    toast(r.blocked ? r.message : "not blocked?!");
  });
  main.querySelectorAll("[data-human]").forEach((btn) => btn.onclick = async () => {
    const who = approver(); if (!who) return;
    await api("/api/pm/human", { key: btn.dataset.human, status: "Done", human: who }); render();
  });
  void translateExtra(b.issues.flatMap((x) => [x.summary, x.description, ...(x.comments || []).map((c) => c.body)]));
}

/* Jira connection panel (PM tool page). The token is never sent to the browser. */
function jiraPanel(b) {
  const jira = b.backend === "jira";
  let body;
  if (jira) {
    body = `<div class="row">${chip("Jira Cloud", "info")} <span>Site <a href="${esc(b.site)}" target="_blank" rel="noopener">${esc(b.site)}</a> · project <b>${esc(b.project)}</b></span>
      ${b.error ? chip("connection error", "stop") : chip(`${b.issues.length} AI items on Jira`, "ok")}
      <button class="ghost" id="jcheck">Test Jira connection</button></div>
      ${b.error ? `<div class="finding STOP">${esc(b.error)}</div>` : ""}`;
  } else if (b.jira_token_set && b.jira_missing.length) {
    body = `<div class="row">${chip("Mock board (SQLite)", "warn")} <span>A Jira API token was found, but Jira stays off until these are set in <span class="mono">.env</span>:</span>
      ${b.jira_missing.map((m) => chip(m, "stop")).join(" ")}<button class="ghost" id="jcheck">Check configuration</button></div>
      <p class="muted small">Add <span class="mono">JIRA_BASE_URL=https://&lt;site&gt;.atlassian.net</span>, <span class="mono">JIRA_EMAIL</span> (the Atlassian account that owns the token) and <span class="mono">JIRA_PROJECT_KEY</span>, then restart the server.</p>`;
  } else {
    body = `<div class="row">${chip("Mock board (SQLite)", "info")} <span class="muted">Same data contract as Jira. Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env to write to Jira Cloud.</span>
      <button class="ghost" id="jcheck">Check configuration</button></div>`;
  }
  return `<div class="card jira">${body}<div id="jres"></div></div>`;
}
function bindJiraPanel() {
  const btn = $("#jcheck");
  if (!btn) return;
  btn.onclick = async () => {
    btn.disabled = true; $("#jres").innerHTML = `<span class="muted">Checking…</span>`;
    try {
      const h = await api("/api/pm/health");
      $("#jres").innerHTML = h.ok ? `<div class="jgrid">
        <div><span class="muted">Account</span><b>${esc(h.account)}</b></div>
        <div><span class="muted">Project</span><b>${h.project.url ? `<a href="${esc(h.project.url)}" target="_blank" rel="noopener">${esc(h.project.key)} · ${esc(h.project.name)}</a>` : esc(h.project.key + " · " + h.project.name)}</b>${h.project.style ? `<small class="muted">${esc(h.project.style)}-managed</small>` : ""}</div>
        <div><span class="muted">Issue type mapping</span>${Object.entries(h.type_mapping).map(([k, v]) => `<div>${esc(k)} → ${/^MISSING/.test(v) ? chip(v, "stop") : `<b>${esc(v)}</b>`}</div>`).join("")}</div>
        <div><span class="muted">"Blocks" link type</span>${h.blocks_link_type ? chip("available", "ok") : chip("missing", "stop")}</div>
        <div><span class="muted">Synced items</span><b>${h.synced_items}</b><small class="muted">${esc(h.last_sync || "never")}</small></div></div>`
        : `<div class="finding STOP">${esc(h.error)}</div>`;
    } finally { btn.disabled = false; }
  };
}

/* ------------------------------------------------------------ Memory */
const SAMPLE_Q = ["What is the maximum grant?", "When is practical completion?", "Who appoints the active ageing centre operator?",
  "How much is the asbestos removal estimate?", "What is the energy performance target?", "How much will the rooftop garden cost?",
  "How long does childcare licensing take?", "What does Tranche 2 require?"];
async function vMemory() {
  const log = await api("/api/qa");
  main.innerHTML = `
  <h1>3 · Memory &amp; retrieval</h1>
  <p class="lead">Ask about the brief, sponsor answers or data pack. Answers cite document, section and lines; the agent says NOT FOUND when the pack is silent, and names both sides when sources conflict. Human decisions recorded below are carried into later sessions.</p>
  <div class="row"><input id="q" style="flex:1;min-width:260px" placeholder="Ask a question…"><button id="ask" data-perm="memory.ask">Ask</button></div>
  <div class="row">${SAMPLE_Q.map((q) => `<span class="chip" style="cursor:pointer" data-q="${esc(q)}">${esc(q)}</span>`).join("")}</div>
  <div id="ans"></div>
  <h2>Decision log (carried forward)</h2>
  <div class="row"><input id="dec" style="flex:1;min-width:260px" placeholder="e.g. Sponsor decided on 2027-04-08: east core closure accepted with temporary lift"><button class="ghost" id="adddec" data-perm="memory.decide">Record decision</button></div>
  ${table(["ID", "Decision", "By", "When"], log.decisions.map((d) => `<tr><td>${d.id}</td><td>${esc(d.text)}</td><td>${esc(d.made_by)}</td><td class="mono">${esc(d.date)}</td></tr>`))}
  <h2>Recent questions</h2>
  ${table(["Time", "Question", "Answer", "Mode"], log.log.map((r) => `<tr><td class="mono">${esc(r.ts)}</td><td>${esc(r.question)}</td><td>${r.not_found ? chip("NOT FOUND", "warn") : esc(r.answer.slice(0, 160))}</td><td>${esc(r.mode)}</td></tr>`))}`;
  const ask = async (q) => {
    const query = SAMPLE_Q.find((sample) => window.HCH_I18N.translate(sample) === q) || q;
    $("#q").value = window.HCH_I18N.language === "zh" ? window.HCH_I18N.translate(query) : query;
    const a = await api("/api/ask", { question: query, use_llm: true });
    if (!a.not_found) a.answer = await displayText(a.answer);
    $("#ans").innerHTML = `<div class="answer ${a.not_found ? "nf" : ""}">
      ${a.not_found ? `<b>NOT FOUND</b> <span class="muted">— ${esc(a.reason || "")}</span>` : esc(a.answer).replace(/\[([A-Z0-9\-.]+)\]/g, (m, id) => `<span class="cite" data-src="${id}">${id}</span>`)}
      <div class="row">${cites(a.citations)} ${chip(a.mode)}</div>
      ${a.conflicts.length ? `<div>${chip("sources conflict", "stop")} ${a.conflicts.map((c) => `${c.id} ${esc(c.topic)}`).join("; ")}</div>` : ""}
      <details><summary>retrieved passages</summary>${a.retrieved.map((r) => `<div>${cites([r])} <span class="muted">${esc(r.label)} · score ${r.score}</span></div>`).join("")}</details></div>`;
  };
  $("#ask").onclick = () => $("#q").value.trim() && ask($("#q").value.trim());
  $("#q").onkeydown = (e) => { if (e.key === "Enter") $("#ask").click(); };
  main.querySelectorAll("[data-q]").forEach((c) => (c.onclick = () => ask(c.dataset.q)));
  $("#adddec").onclick = async () => { const who = approver(); if (!who || !$("#dec").value.trim()) return; await api("/api/decision", { text: $("#dec").value.trim() }); render(); };
}

/* ------------------------------------------------------------ Risk */
async function vRisk() {
  const r = await api("/api/risk");
  const grid = {};
  r.register.forEach((x) => { const k = `${x.likelihood}-${x.impact}`; grid[k] = (grid[k] || []).concat(x.id); });
  let heat = `<div class="heat"><div></div>${[1, 2, 3, 4, 5].map((i) => `<div class="muted">I${i}</div>`).join("")}`;
  for (let l = 5; l >= 1; l--) {
    heat += `<div class="muted">L${l}</div>`;
    for (let i = 1; i <= 5; i++) {
      const s = l * i, ids = grid[`${l}-${i}`] || [];
      const bg = s >= 20 ? "#f3c7c2" : s >= 12 ? "#f8e1bf" : s >= 6 ? "#f4f0d8" : "#e7f2ea";
      heat += `<div style="background:${bg}" title="${ids.join(", ")}">${ids.length || ""}</div>`;
    }
  }
  heat += "</div>";
  main.innerHTML = `
  <h1>4 · Risk register &amp; what-if</h1>
  <p class="lead">Scored L×I with owner, trigger and linked WBS; every row cites its evidence. The 2025 seed register was checked rather than trusted. Re-scoring after a change event is proposed by the agent and applied only after HC6.</p>
  <div class="row">HC4 (register version <span class="mono">${r.risk_hash}</span>): ${approvalLine(r.hc4)} <button id="hc4" data-perm="HC4">Approve register (HC4)</button></div>
  <div class="card" style="display:flex;gap:24px;flex-wrap:wrap"><div>${heat}</div>
    <div style="flex:1;min-width:260px"><h3>Seed register QA (computed)</h3>${r.seed_qa.map((f) => `<div class="finding STOP">${esc(f.risk)}: ${esc(f.issue)} ${cites([f.source])}</div>`).join("")}</div></div>
  ${table(["ID", "Risk", "Owner", "L", "I", "Score", "Trigger", "Mitigation", "WBS", "Status", "Sources"], r.register.map((x) => `<tr>
    <td>${x.id}${x.stale ? "<br>" + chip("stale", "stop") : ""}${r.top5.includes(x.id) ? "<br>" + chip("top 5", "warn") : ""}</td><td>${esc(x.description)}${x.note ? `<div class="muted">${esc(x.note)}</div>` : ""}</td>
    <td>${esc(x.owner)}</td><td>${x.likelihood}</td><td>${x.impact}</td><td><b>${x.score}</b></td><td>${esc(x.trigger_cond)}</td><td>${esc(x.mitigation)}</td>
    <td class="mono">${x.wbs_links.join(" ")}</td><td>${statusChip(x.status)}<div class="muted">v${x.version} · ${esc(x.origin)}</div></td><td>${cites(x.sources)}</td></tr>`))}
  <h2>What-if scenarios</h2>
  ${r.whatifs.map((w) => `<div class="card"><h3>${w.id} · ${esc(w.name)} ${w.stale ? chip("stale", "stop") : ""} ${chip("v" + w.version)} ${w.event_id ? chip(w.event_id, "warn") : ""}</h3>
    <b>Assumptions</b><ul>${w.assumptions.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>
    <b>Result</b><pre class="mono" style="white-space:pre-wrap">${esc(JSON.stringify(w.result, null, 1))}</pre>${cites(w.sources)}</div>`).join("")}`;
  $("#hc4").onclick = () => approve("HC4");
  void translateExtra([r.seed_qa.map((x) => x.issue),
    r.register.flatMap((x) => [x.trigger_cond, x.mitigation, x.note]),
    r.whatifs.flatMap((x) => [x.assumptions, Object.values(x.result || {})])]);
}

/* ------------------------------------------------------------ Reports */
function md(text) {
  return esc(text).split("\n").map((l) => {
    if (l.startsWith("# ")) return `<h1>${l.slice(2)}</h1>`;
    if (l.startsWith("## ")) return `<h2>${l.slice(3)}</h2>`;
    if (l.startsWith("&gt; ")) return `<blockquote class="muted">${l.slice(5)}</blockquote>`;
    if (l.startsWith("- ")) return `<li>${l.slice(2)}</li>`;
    return l ? `<p>${l}</p>` : "";
  }).join("").replace(/\[([A-Za-z0-9:\-., ]+)\]/g, (m, ids) => ids.split(/,\s*/).map((id) => `<span class="cite" data-src="${id.trim()}">${id.trim()}</span>`).join(""));
}
let selReport = null;
async function vReports() {
  const { reports } = await api("/api/reports");
  if (!selReport || !reports.find((r) => r.id === selReport)) selReport = (reports.find((r) => r.status !== "stale") || reports[0] || {}).id;
  main.innerHTML = `
  <h1>5 · Reporting with a critic</h1>
  <p class="lead">One fact sheet feeds two audiences: a one-page EDC exception update and the NRF monthly report (clause 3.2 contents). The Critic traces every number and date to a cited source, checks required sections, the top five risks, conflicts and change events, and STOPs the draft on any fault. Only Critic-passed drafts can be released (HC5).</p>
  <div class="row"><button class="ghost" id="genE" data-perm="reports.generate">Regenerate EDC draft</button><button class="ghost" id="genN" data-perm="reports.generate">Regenerate NRF draft</button><label class="muted"><input type="checkbox" id="usellm" checked> use LLM summary</label>
   <span class="muted">Plant a fault:</span><select id="fault">${["wrong_number", "invented_figure", "missing_citation", "drop_section", "wrong_top5", "status_spin", "remove_conflicts", "wrong_date", "invented_person", "hidden_gap", "bad_calc"].map((f) => `<option value="${f}">${f}</option>`).join("")}</select>
   <select id="fkind"><option value="nrf">NRF</option><option value="edc">EDC</option></select><button class="danger" id="plant" data-perm="reports.plant">Plant &amp; run Critic</button></div>
  <div class="split"><div class="list card">${reports.map((r) => `<a data-r="${r.id}" class="${r.id === selReport ? "on" : ""}">${esc(r.id)}<br>${statusChip(r.status)} ${r.event_id ? chip(r.event_id, "warn") : ""}</a>`).join("") || "No reports"}</div><div id="rview"></div></div>`;
  main.querySelectorAll("[data-r]").forEach((a) => (a.onclick = () => { selReport = a.dataset.r; vReports(); }));
  $("#genE").onclick = async () => { await api("/api/reports/generate", { kind: "edc", use_llm: $("#usellm").checked }); vReports(); };
  $("#genN").onclick = async () => { await api("/api/reports/generate", { kind: "nrf", use_llm: $("#usellm").checked }); vReports(); };
  $("#plant").onclick = async () => {
    const r = await api("/api/reports/plant", { kind: $("#fkind").value, fault: $("#fault").value });
    openModal(`<h3>Planted fault: ${esc($("#fault").value)} → ${statusChip(r.status)}</h3>${r.critic.map((f) => `<div class="finding ${f.severity}"><b>${esc(f.rule)}</b> ${esc(f.detail)}</div>`).join("")}`);
  };
  if (!selReport) return;
  const r = await api(`/api/report/${encodeURIComponent(selReport)}`);
  let content = r.content;
  const summary = content.match(/## Summary\n([\s\S]*?)(?=\n## |$)/);
  if (summary && window.HCH_I18N.language === "zh") {
    const original = summary[1].trim();
    content = content.replace(original, await displayText(original));
  }
  if (current !== "reports" || !$("#rview")) return;
  $("#rview").innerHTML = `
   <div class="row">${statusChip(r.status)} ${r.llm_used === 2 ? chip("LLM-generated, Critic-checked", "ok") : r.llm_used ? chip("LLM summary (checked)", "info") : chip("deterministic")}
     <button id="rel" data-perm="HC5" ${r.status === "critic_passed" ? "" : "disabled"}>Release to readers (HC5)</button>
     <span>${r.approval ? approvalLine(r.approval) : ""}</span></div>
   <div class="card"><b>Critic findings</b>${r.critic.map((f) => `<div class="finding ${f.severity}"><b>${esc(f.rule)}</b> ${esc(f.detail)}</div>`).join("")}</div>
   <div class="report">${md(content)}</div>`;
  $("#rel").onclick = async () => { await approve("HC5", r.id); };
}

/* ------------------------------------------------------------ Change */
async function vChange() {
  const c = await api("/api/change");
  if (window.HCH_I18N.language === "zh") {
    await Promise.all(c.events.map(async (e) => {
      if (e.impact?.narrative?.text) e.impact.narrative.display = await displayText(e.impact.narrative.text);
    }));
  }
  const pending = c.actions.filter((a) => a.status === "pending");
  main.innerHTML = `
  <h1>6 · Change handling</h1>
  <p class="lead">The Week 12 event is injected as a dated, numbered input; the data pack is never edited. The Change Agent finds affected WBS, deliverables, milestones and risks, marks stale outputs, refreshes what-ifs and report drafts automatically, and drafts actions that wait for HC6. It never edits the baseline, closes or deletes.</p>
  <div class="row">${c.available.map((id) => `<button data-ce="${id}" data-perm="change.inject" ${c.events.find((e) => e.id === id) ? "class='ghost'" : ""}>Inject ${id}</button>`).join("")}
    <details data-perm="change.inject" data-perm-hide><summary>Custom event</summary><div class="card"><div class="row"><input id="cid" placeholder="CE-03"><input id="cdate" placeholder="2027-04-06"><input id="ctitle" placeholder="Title"></div><textarea id="ctext" rows="3" placeholder="Event text"></textarea><button id="cgo">Inject custom</button></div></details></div>
  ${c.events.map((e) => {
    const i = e.impact || {};
    return `<div class="card"><h2 style="margin-top:0">${esc(e.id)} · ${esc(e.title)} <span class="muted">(${esc(e.date)})</span></h2>
    <p><i>${esc(e.text)}</i></p><div>${(e.tags || []).map((t) => chip(t)).join(" ")}</div>
    <h3>Affected</h3><p>WBS ${(i.affected_wbs || []).map((w) => chip(w.code)).join(" ")}<br>Deliverables ${(i.affected_deliverables || []).join(", ")}<br>
      Milestones ${(i.affected_milestones || []).map((m) => chip(m.id, "warn")).join(" ")} → downstream ${(i.downstream_milestones || []).map((m) => chip(m)).join(" ")}<br>
      Risks ${(i.affected_risks || []).map((r) => chip(r.id + " (" + r.score + ")", "stop")).join(" ")}</p>
    <h3>Now stale</h3>${(i.stale || []).map((s) => `<div class="finding STOP">${esc(s.type)} ${esc(s.id)} — ${esc(s.reason)}</div>`).join("")}
    <h3>Regenerated automatically</h3><p>${(i.regenerated || []).map((x) => chip(x, "ok")).join(" ")}</p>
    <h3>Cost and time impact</h3><ul>${(i.cost_time || []).map((x) => `<li>${esc(x.text)} ${cites(x.cites)} ${x.trace === "ok" ? chip("traced", "ok") : chip("untraced", "stop")}</li>`).join("")}</ul>
    ${i.narrative && i.narrative.text ? `<p><b>LLM summary (Critic-checked):</b> ${esc(i.narrative.display || i.narrative.text)}</p>` : ""}
    <h3>Sponsor decisions needed</h3>${table(["What", "Who", "When", "Sources"], (i.decisions || []).map((d) => `<tr><td>${esc(d.what)}</td><td>${esc(d.who)}</td><td>${esc(d.when)}</td><td>${cites(d.sources)}</td></tr>`))}
    <h3>UNRESOLVED</h3><ul>${(i.unresolved || []).map((u) => `<li>${esc(u.item)} ${cites(u.sources)}</li>`).join("")}</ul>
    <button class="ghost" data-note="${esc(e.id)}">View Change Impact Note</button></div>`;
  }).join("")}
  <h2>Actions awaiting HC6 (${pending.length})</h2>
  <div class="row"><button id="appall" data-perm="HC6" ${pending.length ? "" : "disabled"}>Approve all pending (each logged)</button></div>
  ${table(["ID", "Kind", "Target", "Proposal", "Status", ""], c.actions.map((a) => `<tr><td class="mono">${a.id}</td><td>${esc(a.kind)}</td><td class="mono">${esc(a.target)}</td>
    <td>${esc(a.rationale)}${a.kind === "risk_rescore" ? `<div class="muted">${a.payload.from.join("×").replace(/×(\d+)$/, " = $1")} → ${a.payload.to.join("×").replace(/×(\d+)$/, " = $1")}</div>` : ""}</td>
    <td>${statusChip(a.status)}</td><td>${a.status === "pending" ? `<button data-ok="${a.id}" data-perm="HC6">Approve</button> <button class="danger" data-no="${a.id}" data-perm="HC6">Reject</button>` : ""}</td></tr>`))}`;
  main.querySelectorAll("[data-ce]").forEach((b) => (b.onclick = async () => { b.disabled = true; await api("/api/change/inject", { id: b.dataset.ce }); toast(`${b.dataset.ce} analysed`); vChange(); }));
  main.querySelectorAll("[data-ok]").forEach((b) => (b.onclick = () => approve("HC6", b.dataset.ok)));
  main.querySelectorAll("[data-no]").forEach((b) => (b.onclick = () => approve("HC6", b.dataset.no, "rejected")));
  main.querySelectorAll("[data-note]").forEach((b) => (b.onclick = async () => { const n = await api(`/api/change/note/${b.dataset.note}`); openModal(`<div class="report">${md(n.markdown)}</div>`); }));
  $("#appall").onclick = async () => {
    const who = approver(); if (!who) return;
    for (const a of pending) await api("/api/approve", { checkpoint: "HC6", item_id: a.id, approver: who, decision: "approved" });
    toast(`${pending.length} actions approved by ${who}`); vChange();
  };
  const cg = $("#cgo");
  if (cg) cg.onclick = async () => {
    const ev = { id: $("#cid").value.trim(), date: $("#cdate").value.trim(), title: $("#ctitle").value.trim(), text: $("#ctext").value.trim(), source: "Custom input" };
    await api("/api/change/inject", { custom: ev }); vChange();
  };
  void translateExtra(c.events.filter((e) => /^CE-0[12]$/.test(e.id)).flatMap((e) => {
    const i = e.impact || {};
    return [e.title, e.text, (i.stale || []).map((x) => x.reason), (i.cost_time || []).map((x) => x.text),
      (i.decisions || []).flatMap((x) => [x.what, x.when]), (i.unresolved || []).map((x) => x.item)];
  }));
}

/* ------------------------------------------------------------ Governance */
async function vGov() {
  const g = await api("/api/governance");
  const b = g.bias && g.bias.result;
  const bars = (obj) => { const max = Math.max(...Object.values(obj)); return `<table class="bars">${Object.entries(obj).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<tr><td>${esc(k)}</td><td style="width:55%"><div class="bar" style="width:${(v / max) * 100}%"></div></td><td>${typeof v === "number" && v < 1 ? v.toFixed(3) : v}</td></tr>`).join("")}</table>`; };
  main.innerHTML = `
  <h1>Governance layer</h1>
  <p class="lead">Named human checkpoints, a complete audit trail of every agent write and human decision, blocked guardrail attempts, and the bias &amp; fairness check on the resident consultation.</p>
  <div class="row" data-perm="audit.export" data-perm-hide><a href="/api/export/audit.csv"><button class="ghost">Export audit (CSV)</button></a><a href="/api/export/approvals.csv"><button class="ghost">Export approvals (CSV)</button></a><a href="/api/export/governance.json"><button class="ghost">Export governance pack (JSON)</button></a></div>
  <h2>Checkpoint map</h2>
  ${table(["ID", "Checkpoint", "Approver role", "Gates", "Approvals"], g.checkpoints.map((c) => `<tr><td>${c.id}</td><td>${esc(c.name)}</td><td>${esc(c.role)}</td><td>${esc(c.gates)}</td><td>${c.approvals}</td></tr>`))}
  <h2>Bias &amp; fairness check — resident consultation</h2>
  ${b ? `<div class="row">HC7: ${statusChip(g.bias.status)} ${g.hc7 ? approvalLine(g.hc7) : ""} <button id="hc7" data-perm="HC7">Sign off (HC7)</button></div>
  <div class="card">${b.findings.map((f) => `<div class="finding ${f.severity === "high" ? "STOP" : ""}"><b>${f.id}</b> ${esc(f.text)} ${cites(f.sources.filter((s) => !s.includes("computed")))}</div>`).join("")}
   <h3>Actions</h3><ul>${b.actions.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></div>
  <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
    <div class="card"><h3>Responses by age band</h3>${bars(b.age)}</div>
    <div class="card"><h3>By channel</h3>${bars(b.channel)}<h3>By language</h3>${bars(b.language)}</div>
    <div class="card"><h3>Themes — raw count</h3>${bars(b.themes_raw)}</div>
    <div class="card"><h3>Themes — each age band weighted equally</h3>${bars(b.themes_reweighted)}</div>
  </div>
  <details><summary>Non-English comment glosses</summary>${table(["Original", "Gloss"], Object.entries(b.translations).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`))}</details>` : "<p>Run the pipeline first.</p>"}
  <h2>Approvals</h2>
  ${table(["Time", "Checkpoint", "Item", "Approver", "Role", "Decision", "Comment"], g.approvals.map((a) => `<tr><td class="mono">${esc(a.ts)}</td><td>${a.checkpoint}</td><td class="mono">${esc(a.item_type)} ${esc(a.item_id)}</td><td>${esc(a.approver)}</td><td>${esc(a.role)}</td><td>${statusChip(a.decision)}</td><td>${esc(a.comment)}</td></tr>`))}
  <h2>Blocked or rejected attempts (${g.blocked.length})</h2>
  ${table(["Time", "Actor", "Action", "Target", "Detail"], g.blocked.map((a) => `<tr><td class="mono">${esc(a.ts)}</td><td>${esc(a.actor)}</td><td>${statusChip(a.action)}</td><td class="mono">${esc(a.target_id)}</td><td class="mono">${esc(a.detail).slice(0, 160)}</td></tr>`))}
  <h2>Audit log (latest ${g.audit.length} of ${g.audit_total})</h2>
  <div class="row"><input id="af" placeholder="Filter (actor, action, target)…" style="min-width:260px"></div>
  <div id="audit">${auditTable(g.audit)}</div>`;
  if ($("#hc7")) $("#hc7").onclick = () => approve("HC7", "BIAS-1");
  $("#af").oninput = () => { const f = $("#af").value.toLowerCase(); $("#audit").innerHTML = auditTable(g.audit.filter((a) => JSON.stringify(a).toLowerCase().includes(f))); };
  if (b) void translateExtra([b.findings.map((x) => x.text), b.actions]);
}
function auditTable(rows) {
  return table(["#", "Time", "Run", "Actor", "Type", "Action", "Target", "Outcome", "Detail"], rows.map((a) => `<tr><td>${a.id}</td><td class="mono">${esc(a.ts)}</td><td class="mono">${esc((a.run_id || "").slice(-11))}</td><td>${esc(a.actor)}</td><td>${esc(a.actor_type)}</td><td>${esc(a.action)}</td><td class="mono">${esc(a.target_type)} ${esc(a.target_id)}</td><td>${statusChip(a.outcome)}</td><td class="mono">${esc(a.detail).slice(0, 140)}</td></tr>`));
}

/* ------------------------------------------------------------ Agents */
async function vAgents() {
  const a = await api("/api/agents");
  main.innerHTML = `<h1>Agent cards</h1><p class="lead">Role and context are fixed per agent. Every card names its inputs, outputs, tools and stop condition.</p>
  <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(320px,1fr))">${a.agents.map((x) => `<div class="card">
   <h3 style="margin-top:0">${esc(x.name)} ${chip(x.module, "info")}</h3>
   <p><b>Role.</b> ${esc(x.role)}<br><b>Context.</b> ${esc(x.context)}</p>
   <p><b>Inputs.</b> ${x.inputs.map(esc).join("; ")}<br><b>Outputs.</b> ${x.outputs.map(esc).join("; ")}<br><b>Tools.</b> ${x.tools.map(esc).join("; ")}</p>
   <p><b>Stop condition.</b> ${esc(x.stop)}<br><b>Checkpoint.</b> ${esc(x.checkpoint)}</p>
   <details><summary>System prompt</summary><pre class="mono" style="white-space:pre-wrap">${esc(x.system_prompt)}</pre></details></div>`).join("")}</div>`;
  void translateExtra(a.agents.flatMap((x) => [x.name, x.role, x.context, x.inputs, x.outputs, x.tools, x.stop]));
}

/* ------------------------------------------------------------ Evaluation */
async function vEval() {
  const e = await api("/api/eval");
  const m = e.measures || {};
  main.innerHTML = `<h1>Evaluation</h1><p class="lead">The harness runs on a throw-away database: ${e.total || "33"} test cases including the brief's gaps and both Week 12 change events, and the five comparable measures.</p>
  <div class="row"><button id="ev" data-perm="eval.run">Run evaluation (deterministic)</button><button class="ghost" id="evl" data-perm="eval.run">Run with LLM</button><span class="muted">${e.generated ? "Last run " + esc(e.generated) : "Not run yet"}</span></div>
  ${e.missing ? "" : `<div class="grid">
    <div class="stat"><b>${(m.gap_recall.value * 100).toFixed(0)}%</b><span>Gap recall (${m.gap_recall.hits}/${m.gap_recall.total})</span></div>
    <div class="stat"><b>${(m.invention_rate.value * 100).toFixed(1)}%</b><span>Invention rate (${m.invention_rate.untraceable}/${m.invention_rate.claims_sampled} claims)</span></div>
    <div class="stat"><b>${Object.values(m.rerun_stability.fresh_db_identical || {}).every(Boolean) ? "identical" : "differs"}</b><span>Re-run stability · PM 2nd sync created ${m.rerun_pm ? m.rerun_pm.second.created : "?"}</span></div>
    <div class="stat"><b>${(m.critic_catch.value * 100).toFixed(0)}%</b><span>Critic catch rate (${m.critic_catch.caught}/${m.critic_catch.total})</span></div>
    <div class="stat"><b>${m.cost_time.mean_seconds}s</b><span>Per full run · ${m.cost_time.mean_tokens} tokens · US$${m.cost_time.mean_cost_usd}</span></div>
    <div class="stat"><b>${e.passed}/${e.total}</b><span>Test cases passed</span></div></div>
  <p class="muted">Missed gaps: ${(m.gap_recall.missed || []).map(esc).join("; ") || "none"}</p>
  ${table(["ID", "Category", "Test", "Result", "Detail"], e.cases.map((c) => `<tr><td>${c.id}</td><td>${esc(c.category)}</td><td>${esc(c.description)}</td><td>${statusChip(c.pass ? "PASS" : "FAIL")}</td><td class="mono">${esc(String(c.detail)).slice(0, 220)}</td></tr>`))}`}`;
  $("#ev").onclick = async () => { $("#ev").disabled = true; toast("Running evaluation…"); await api("/api/eval/run", { use_llm: false }); vEval(); };
  $("#evl").onclick = async () => { $("#evl").disabled = true; toast("Running evaluation with LLM…"); await api("/api/eval/run", { use_llm: true }); vEval(); };
  if (!e.missing) void translateExtra([e.cases.map((x) => x.description), m.gap_recall.missed || []]);
}

window.addEventListener("hashchange", () => selectTab(location.hash.slice(1)));
window.addEventListener("hch-languagechange", () => { if (ME) render(); });
function selectTab(t) {
  if (!VIEWS[t]) return;
  if (!ME) return;
  if (!can("view." + t)) { toast(`Your role (${ME.role_label}) cannot open this page.`); t = "dashboard"; history.replaceState(null, "", "#dashboard"); }
  current = t;
  document.querySelectorAll("#nav a").forEach((x) => x.classList.toggle("on", x.dataset.tab === t));
  render();
}
const VIEWS = { dashboard: vDashboard, overview: vOverview, planning: vPlanning, pm: vPM, memory: vMemory, risk: vRisk, reports: vReports, change: vChange, governance: vGov, agents: vAgents, eval: vEval, admin: vAdmin };

/* ------------------------------------------------------------ Login / session */
function showLogin() {
  ME = null;
  $("#login").hidden = false; $("#userbox").hidden = true;
  document.body.classList.add("locked");
  setTimeout(() => $("#l-user").focus(), 0);
}
function enterApp(user) {
  ME = user;
  $("#login").hidden = true; $("#userbox").hidden = false;
  document.body.classList.remove("locked");
  document.body.dataset.role = user.role;
  $("#u-name").textContent = user.name;
  $("#u-role").textContent = user.role_label;
  $("#u-avatar").textContent = user.name.slice(0, 1).toUpperCase();
  $("#u-avatar").className = `avatar r-${user.role}`;
  document.querySelectorAll("#nav a[data-tab]").forEach((a) => (a.hidden = !user.views.includes(a.dataset.tab)));
  api("/api/status").then((s) => { $("#mode").textContent = `${s.generation === "llm" ? "LLM: DeepSeek" : "LLM off · deterministic"} · PM: ${s.pm_backend}`; }).catch(() => {});
  const t = location.hash.slice(1);
  selectTab(VIEWS[t] && user.views.includes(t) ? t : "dashboard");
}
$("#login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#l-err").hidden = true;
  const r = await fetch("/api/login", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: $("#l-user").value, password: $("#l-pw").value }) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) { $("#l-err").textContent = j.error || "Sign-in failed"; $("#l-err").hidden = false; return; }
  $("#l-pw").value = "";
  const m = await api("/api/me"); ROLES_META = m.roles;
  enterApp(j.user);
});
document.querySelectorAll("#login .acct").forEach((b) => (b.onclick = () => { $("#l-user").value = b.dataset.u; $("#l-pw").value = b.dataset.p; $("#l-pw").focus(); }));
$("#logout").onclick = async () => { await fetch("/api/logout", { method: "POST" }); main.innerHTML = ""; showLogin(); };
fetch("/api/me").then((r) => (r.ok ? r.json() : null)).then((m) => { if (m && m.user) { ROLES_META = m.roles; enterApp(m.user); } else showLogin(); })
  .catch(() => showLogin());
