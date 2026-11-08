"""DeepSeek client (OpenAI-compatible chat completions) using only the standard library.
The LLM is an optional helper: every agent has a deterministic path, and every LLM
output is checked (citations must exist, numbers must trace to facts) before use.
Each agent's Role and Context are fixed system prompts (see agents.AGENT_CARDS)."""
import hashlib
import json
import time
import urllib.error
import urllib.request

from . import audit, config, db


def available():
    return bool(config.DEEPSEEK_API_KEY) and not config.LLM_DISABLED


def generation_enabled(use_llm=True):
    """True when agents should GENERATE their core outputs with the LLM (default whenever
    DeepSeek is configured). HCH_GENERATION=baseline forces the curated baseline."""
    return bool(use_llm) and available() and config.GENERATION_MODE != "baseline"


def cached_json(agent, system, user, max_tokens=4000, fresh=False):
    """chat_json with a persistent cache keyed on (model, prompt). Temperature is 0 and the
    cache makes a re-run on the same inputs return the same output, so plan hashes (HC2),
    risk hashes (HC4) and PM-board content stay stable. fresh=True forces a new call."""
    key = "llmcache:" + agent + ":" + hashlib.sha256(
        (config.DEEPSEEK_MODEL + "\x00" + system + "\x00" + user).encode()).hexdigest()[:32]
    if not (fresh or config.LLM_FRESH):
        hit = db.kv_get(key)
        if hit is not None:
            audit.log(agent, "llm cache hit", "llm", key[-12:])
            return hit, {"cached": True}
    data, usage = chat_json(agent, system, user, max_tokens=max_tokens)
    if data is not None:
        db.kv_set(key, data)
    return data, usage


def cached_chat(agent, system, user, max_tokens=1200, fresh=False):
    """Plain-text chat with the same persistent cache as cached_json (stable re-runs)."""
    key = "llmcache:" + agent + ":txt:" + hashlib.sha256(
        (config.DEEPSEEK_MODEL + "\x00" + system + "\x00" + user).encode()).hexdigest()[:32]
    if not (fresh or config.LLM_FRESH):
        hit = db.kv_get(key)
        if hit is not None:
            audit.log(agent, "llm cache hit", "llm", key[-12:])
            return hit, {"cached": True}
    text, usage = chat(agent, system, user, max_tokens=max_tokens)
    if text is not None:
        db.kv_set(key, text)
    return text, usage


def chat(agent, system, user, temperature=0.0, max_tokens=1200, json_mode=False):
    """Returns (text, usage) or (None, {'error': ...}). Never raises to callers."""
    if not available():
        return None, {"error": "LLM not configured"}
    body = {"model": config.DEEPSEEK_MODEL, "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        config.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + config.DEEPSEEK_API_KEY})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=max(90, max_tokens // 20)) as r:
            data = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        audit.log(agent, "llm call", "llm", config.DEEPSEEK_MODEL, outcome="error",
                  detail={"error": audit.redact(str(e))})
        return None, {"error": str(e)}
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    tin, tout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    cost = tin / 1e6 * config.PRICE_IN_PER_M + tout / 1e6 * config.PRICE_OUT_PER_M
    run = audit.CURRENT_RUN.get()
    if run is not None:
        run["tokens_in"] += tin
        run["tokens_out"] += tout
        run["cost_usd"] += cost
        run["llm_calls"] += 1
    audit.log(agent, "llm call", "llm", config.DEEPSEEK_MODEL,
              detail={"tokens_in": tin, "tokens_out": tout, "seconds": round(time.time() - t0, 2)})
    return text, {"tokens_in": tin, "tokens_out": tout, "cost_usd": cost}


def chat_json(agent, system, user, **kw):
    text, usage = chat(agent, system, user, json_mode=True, **kw)
    if text is None:
        return None, usage
    try:
        return json.loads(text), usage
    except ValueError:
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e + 1]), usage
            except ValueError:
                pass
        audit.log(agent, "llm json parse", "llm", "", outcome="error", detail={"raw": text[:300]})
        return None, {"error": "unparseable JSON"}
