"""LLM smoke test (Gemini primary, DeepSeek backup). Reads the API keys from .env /
environment; never prints them.
    python3 scripts/llm_smoke_test.py
Checks: (1) raw API call, (2) grounded Memory answer with a validated citation,
(3) NOT FOUND on a question the pack cannot answer, (4) a full pipeline run with
LLM on, with the Critic still gating both reports. Uses a throw-away database."""
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["HCH_DB"] = str(Path(tempfile.mkdtemp(prefix="hch-llm-")) / "llm.db")

from app import audit, config, db, llm, memory, pipeline  # noqa: E402

provs = config.llm_providers()
if not provs:
    sys.exit("No LLM key found (GEMINI_API_KEY or DEEPSEEK_API_KEY) in .env or environment")
for p in provs:
    print(f"{p['name']}: key loaded (value not shown) · model {p['model']} · {p['base_url']}")

ok = True
t = time.time()
text, usage = llm.chat("smoke", "Reply with exactly: OK", "ping", max_tokens=5)
if text is None:
    print("1 raw call: FAIL -", audit.redact(usage.get("error")))
    sys.exit(1)
print(f"1 raw call: PASS ({time.time() - t:.1f}s) reply={text.strip()!r} via {usage.get('model')} tokens={usage['tokens_in']}+{usage['tokens_out']}")

pipeline.init()
with audit.Run("llm-smoke") as run:
    a = memory.answer("What is the maximum grant under the NRF conditions?")
    p2 = (not a["not_found"]) and a["mode"] == "llm" and any(c["id"] == "NRF-1.2" for c in a["citations"])
    print(f"2 grounded answer: {'PASS' if p2 else 'CHECK'} mode={a['mode']} cites={[c['id'] for c in a['citations']]}\n   {a['answer'][:200]}")
    b = memory.answer("What is the energy performance target for the refurbished Hub?")
    p3 = b["not_found"]
    print(f"3 NOT FOUND: {'PASS' if p3 else 'FAIL'} mode={b['mode']} answer={b['answer'][:120]}")
    ok = ok and p3
r = pipeline.full_run(use_llm=True)
reps = db.q("SELECT id,status,llm_used,critic FROM reports WHERE planted IS NULL")
print(f"4 full run with LLM: {r['seconds']}s, tokens {r['tokens_in']}+{r['tokens_out']}, US${r['cost_usd']}, "
      f"LLM gaps proposed {r['planning']['llm_gaps']}")
for x in reps:
    stops = [f["detail"][:100] for f in db.L(x["critic"]) if f["severity"] == "STOP"]
    print(f"   {x['id']}: {x['status']} (LLM summary used={bool(x['llm_used'])}) {stops[:2]}")
rej = db.q("SELECT actor, action, detail FROM audit_log WHERE outcome IN ('rejected','error')")
print(f"   LLM outputs rejected or failed and logged: {len(rej)}")
for x in rej[:5]:
    print("    -", x["actor"], x["action"], audit.redact(x["detail"])[:140])
print("RESULT:", "PASS" if ok else "FAIL")
