"""Talking to the AI service. You bring your own key, and choose the service and model in the dashboard
(Settings, AI) or in .env. What is saved from the dashboard is kept in ai.json in the data folder and wins.

    PEAKCUT_AI_PROVIDER   gemini | openai | xai | groq | openrouter | anthropic | ollama | custom
    PEAKCUT_AI_MODELS     one or more model ids, comma separated, tried in this order
    PEAKCUT_AI_KEY        your key (or PEAKCUT_AI_KEY_FILE, a file holding it)
    PEAKCUT_AI_BASE_URL   only for "custom" (any service that speaks the OpenAI chat format), or to override

Every service is asked for the same thing: JSON that follows a small schema. Gemini takes the schema directly.
The others are told the schema in the prompt and asked for a JSON object, which works with any chat model.

One picture can also be shown (`see`), which is how the webcam is looked for on a gaming stream. A model that
cannot look at pictures answers with something else, and that is simply taken as "it did not look"."""
import base64
import json
import os
import re
import threading
import time

import httpx

from . import config

# name -> (label shown on the pages, address, how it is spoken to, where to get a key, an example model id)
PROVIDERS = {
    "gemini": ("Gemini", "https://generativelanguage.googleapis.com/v1beta/models", "gemini", "https://aistudio.google.com/apikey", "gemini-2.5-flash"),
    "openai": ("OpenAI", "https://api.openai.com/v1", "openai", "https://platform.openai.com/api-keys", "gpt-4o-mini"),
    "xai": ("Grok", "https://api.x.ai/v1", "openai", "https://console.x.ai", "grok-4"),
    "groq": ("Groq", "https://api.groq.com/openai/v1", "openai", "https://console.groq.com/keys", "llama-3.3-70b-versatile"),
    "openrouter": ("OpenRouter", "https://openrouter.ai/api/v1", "openai", "https://openrouter.ai/keys", "google/gemini-2.5-flash"),
    "anthropic": ("Claude", "https://api.anthropic.com/v1", "anthropic", "https://console.anthropic.com", ""),
    "ollama": ("Ollama (on this machine)", "http://127.0.0.1:11434/v1", "openai", "https://ollama.com", "llama3.1"),
    "custom": ("Custom (OpenAI-compatible)", "", "openai", "", ""),
}
ALIASES = {"google": "gemini", "grok": "xai", "claude": "anthropic", "local": "ollama"}
NO_KEY = {"ollama", "custom"}       # a model running on your own machine needs no key

# ---------------------------------------------------------------- the settings in use
_lock = threading.Lock()
_saved = {"at": None, "data": {}}


def _file():
    return config.DATA_DIR / "ai.json"


def _from_dashboard() -> dict:
    """What was saved from the dashboard, read again only when the file changes."""
    f = _file()
    try:
        at = f.stat().st_mtime_ns
    except OSError:
        at = 0
    if _saved["at"] != at:
        try:
            data = json.loads(f.read_text(encoding="utf-8")) if at else {}
        except (OSError, ValueError):
            data = {}
        _saved.update(at=at, data=data if isinstance(data, dict) else {})
    return _saved["data"]


_active = threading.local()          # the service being used by this thread right now (see `using`)
MAX_BACKUPS = 5
COOLDOWN_SEC = 15 * 60                # a service that hit its limit is skipped this long, so work goes straight to the next
_cooling: dict = {}                   # service fingerprint -> time it may be tried again


def current() -> dict:
    """Provider, models, address and key of the service in use: a backup while `using` one, else the main one."""
    cfg = getattr(_active, "cfg", None)
    return dict(cfg) if cfg else primary()


def primary() -> dict:
    """The main service: what the dashboard saved, or else what .env says."""
    d = _from_dashboard()
    p = str(d.get("provider") or config.AI_PROVIDER or "").strip().lower()
    return {"provider": ALIASES.get(p, p),
            "models": list(d["models"]) if d.get("provider") else list(config.AI_MODELS),
            "base_url": (str(d.get("base_url") or "") if d.get("provider") else config.AI_BASE_URL).rstrip("/"),
            "key": str(d["key"]) if d.get("provider") and "key" in d else config.ai_key()}


def provider() -> str:
    return current()["provider"]


def models() -> list:
    return current()["models"]


def key() -> str:
    return current()["key"]


def label() -> str:
    return PROVIDERS.get(provider(), ("",))[0]


def base_url() -> str:
    c = current()
    return c["base_url"] or PROVIDERS.get(c["provider"], ("", ""))[1]


def _usable(c) -> bool:
    return bool(c.get("provider") in PROVIDERS and c.get("models")
                and (c.get("base_url") or PROVIDERS[c["provider"]][1]) and (c.get("key") or c["provider"] in NO_KEY))


def ready() -> bool:
    """Can any AI be asked: the main service, or one of the backups?"""
    return any(_usable(c) for c in chain(include_cooling=True))


def backups() -> list:
    """The backup services saved in the dashboard, in the order they are tried."""
    out = []
    for b in _from_dashboard().get("backups") or []:
        if isinstance(b, dict):
            p = ALIASES.get(str(b.get("provider") or "").lower(), str(b.get("provider") or "").lower())
            out.append({"id": str(b.get("id") or ""), "provider": p, "models": [str(m) for m in b.get("models") or []],
                        "base_url": str(b.get("base_url") or "").rstrip("/"), "key": str(b.get("key") or "")})
    return out


def _fingerprint(c) -> str:
    return f"{c.get('provider')}|{c.get('base_url')}|{str(c.get('key'))[-8:]}"


def cooling(c) -> bool:
    return _cooling.get(_fingerprint(c), 0) > time.time()


def cool_down(c):
    """This service hit its limit: skip it for a while, so the next one takes over at once."""
    _cooling[_fingerprint(c)] = time.time() + COOLDOWN_SEC


def chain(include_cooling=False) -> list:
    """Every usable service in the order to try: the main one, then the backups. Services resting after hitting their
    limit go last (they are still tried if nothing else is left)."""
    all_ = [c for c in [primary(), *backups()] if _usable(c)]
    if include_cooling:
        return all_
    return [c for c in all_ if not cooling(c)] + [c for c in all_ if cooling(c)]


class using:
    """`with ai.using(service):` every call in this thread goes to that service."""
    def __init__(self, cfg):
        self.cfg = cfg

    def __enter__(self):
        self.prev = getattr(_active, "cfg", None)
        _active.cfg = self.cfg
        return self.cfg

    def __exit__(self, *exc):
        _active.cfg = self.prev
        return False


def name_of(c) -> str:
    return PROVIDERS.get(c.get("provider"), (c.get("provider") or "?",))[0]


def public() -> dict:
    """What the settings page may see. The key itself never leaves the server: only whether there is one, and
    its last four characters so the owner can tell which key it is."""
    c = primary()
    with using(c):
        lab = label()
    hint = lambda k: k[-4:] if len(k) >= 12 else ""                     # noqa: E731
    return {"provider": c["provider"], "models": c["models"], "base_url": c["base_url"], "has_key": bool(c["key"]),
            "key_hint": hint(c["key"]), "ready": ready(), "label": lab,
            "saved_here": bool(_from_dashboard().get("provider")),
            "backups": [{"id": b["id"], "provider": b["provider"], "label": name_of(b), "models": b["models"],
                         "base_url": b["base_url"], "has_key": bool(b["key"]), "key_hint": hint(b["key"]),
                         "resting": cooling(b)} for b in backups()],
            "providers": [{"id": k, "label": v[0], "address": v[1], "needs_key": k not in NO_KEY, "key_url": v[3], "example": v[4]}
                          for k, v in PROVIDERS.items()]}


def _write_file(data: dict):
    with _lock:
        f = _file()
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)        # the keys are only for whoever runs the server
        except OSError:
            pass
        tmp.replace(f)
        _saved["at"] = None


def _clean_models(model_ids) -> list:
    if isinstance(model_ids, str):
        model_ids = model_ids.split(",")
    ms = [str(m).strip()[:120] for m in (model_ids or []) if str(m).strip()][:5]
    if not ms:
        raise ValueError("Enter the model to use.")
    if any(not re.fullmatch(r"[\w.\-:/@]+", m) for m in ms):
        raise ValueError("A model id has letters, digits and . - : / only.")
    return ms


def save_backups(items) -> dict:
    """Save the list of backup services. Each item: provider, models, base_url, and key (left out or empty keeps the
    key already saved for that backup's id, since the page never has it)."""
    import secrets
    if not isinstance(items, list):
        raise ValueError("The backups must be a list.")
    old = {b["id"]: b for b in backups() if b["id"]}
    out = []
    for i, it in enumerate(items[:MAX_BACKUPS], 1):
        if not isinstance(it, dict):
            continue
        p = ALIASES.get(str(it.get("provider") or "").strip().lower(), str(it.get("provider") or "").strip().lower())
        if p not in PROVIDERS:
            raise ValueError(f"Backup {i}: choose one of the AI services in the list.")
        try:
            ms = _clean_models(it.get("models"))
        except ValueError as e:
            raise ValueError(f"Backup {i}: {e}")
        address = str(it.get("base_url") or "").strip().rstrip("/")[:300]
        if address and not re.fullmatch(r"https?://[^\s]+", address):
            raise ValueError(f"Backup {i}: the address has to start with http:// or https://")
        if p == "custom" and not address:
            raise ValueError(f"Backup {i}: a custom service needs its address.")
        bid = str(it.get("id") or "")
        prev = old.get(bid)
        k = str(it.get("key") or "").strip()[:400] or (prev["key"] if prev and prev["provider"] == p else "")
        if not k and p not in NO_KEY:
            raise ValueError(f"Backup {i} ({PROVIDERS[p][0]}): paste its key.")
        out.append({"id": bid if prev else secrets.token_hex(4), "provider": p, "models": ms, "base_url": address, "key": k})
    data = dict(_from_dashboard())
    data["backups"] = out
    _write_file(data)
    return public()


def save(provider_id: str, model_ids, address: str = "", new_key=None) -> dict:
    """Save the choice made in the dashboard. `new_key` None keeps the key that is already there (the page never
    has it to send back); an empty string removes it."""
    p = ALIASES.get(str(provider_id or "").strip().lower(), str(provider_id or "").strip().lower())
    if p not in PROVIDERS:
        raise ValueError("Choose one of the AI services in the list.")
    ms = _clean_models(model_ids)
    address = str(address or "").strip().rstrip("/")[:300]
    if address and not re.fullmatch(r"https?://[^\s]+", address):
        raise ValueError("The address has to start with http:// or https://")
    if p == "custom" and not address:
        raise ValueError("A custom service needs its address, for example http://127.0.0.1:1234/v1")
    old = primary()
    k = old["key"] if new_key is None and old["provider"] == p else str(new_key or "").strip()[:400]
    if not k and p not in NO_KEY:
        raise ValueError("Paste the key for this service.")
    data = {"provider": p, "models": ms, "base_url": address, "key": k,
            "backups": _from_dashboard().get("backups") or []}         # saving the main service keeps the backups
    _write_file(data)
    return public()


def make_main(backup_id: str) -> dict:
    """Swap: this backup becomes the main AI, and the main AI takes its place in the backup list. Keys, models and
    addresses all move with them, so nothing has to be typed again."""
    d = dict(_from_dashboard())
    bs = [dict(b) for b in d.get("backups") or [] if isinstance(b, dict)]
    i = next((n for n, b in enumerate(bs) if str(b.get("id")) == str(backup_id)), None)
    if i is None:
        raise ValueError("That backup isn't there any more. Reload the page.")
    new_main, old = bs[i], primary()
    if _usable(old):
        bs[i] = {"id": new_main.get("id") or "", "provider": old["provider"], "models": old["models"],
                 "base_url": old["base_url"], "key": old["key"]}
    else:
        bs.pop(i)                                                   # no main to keep: the backup simply moves up
    d.update(provider=new_main["provider"], models=new_main["models"], base_url=new_main.get("base_url") or "",
             key=new_main.get("key") or "", backups=bs)
    _cooling.pop(_fingerprint({**new_main, "base_url": (new_main.get("base_url") or "").rstrip("/")}), None)
    _write_file(d)
    return public()


def move_backup(backup_id: str, step: int) -> dict:
    """Move a backup up (-1) or down (+1) in the order they are tried."""
    d = dict(_from_dashboard())
    bs = [b for b in d.get("backups") or [] if isinstance(b, dict)]
    i = next((n for n, b in enumerate(bs) if str(b.get("id")) == str(backup_id)), None)
    if i is None:
        raise ValueError("That backup isn't there any more. Reload the page.")
    j = max(0, min(len(bs) - 1, i + (1 if int(step) > 0 else -1)))
    bs[i], bs[j] = bs[j], bs[i]
    d["backups"] = bs
    _write_file(d)
    return public()


def list_models(provider_id=None, address=None, with_key=None) -> list:
    """The model ids a service offers, so the settings page can show a list to pick from."""
    c = current()
    p = ALIASES.get(str(provider_id or c["provider"]).lower(), str(provider_id or c["provider"]).lower())
    if p not in PROVIDERS:
        raise ValueError("Choose one of the AI services in the list.")
    k = str(with_key or "").strip() or (c["key"] if c["provider"] == p else "")
    base = str(address or "").strip().rstrip("/") or (c["base_url"] if c["provider"] == p else "") or PROVIDERS[p][1]
    if not base:
        raise ValueError("Enter the service's address first.")
    how = PROVIDERS[p][2]
    if how == "gemini":
        r = httpx.get(base, params={"pageSize": 200}, headers={"x-goog-api-key": k}, timeout=20)
    elif how == "anthropic":
        r = httpx.get(f"{base}/models", params={"limit": 200}, headers={"x-api-key": k, "anthropic-version": "2023-06-01"}, timeout=20)
    else:
        r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {k}"} if k else {}, timeout=20)
    if r.status_code != 200:
        raise AIError(f"HTTP {r.status_code} {r.text[:200].replace(k or chr(0), '<key>')}")
    data = r.json()
    if how == "gemini":
        found = [m.get("name", "").split("/")[-1] for m in data.get("models", [])
                 if "generateContent" in (m.get("supportedGenerationMethods") or [])]
    else:
        found = [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
    return sorted({m for m in found if m})[:400]


def test() -> dict:
    """One tiny request with the settings in use, to prove the key, the address and the model all work."""
    ms = models()
    if not ready():
        raise ValueError("Save a service, a model and a key first.")
    out, sent, wrote = call(ms[0], 'Answer with a JSON array that holds the single string "ok".', {"type": "ARRAY", "items": {"type": "STRING"}})
    return {"ok": True, "model": ms[0], "tokens": sent + wrote, "answer": str(out)[:80]}


class AIError(RuntimeError):
    pass


problem = {"text": "", "at": 0.0}       # why the AI last failed, for the dashboard; cleared when it answers again


def explain(e) -> str:
    """What went wrong with an AI call, in words the owner can act on."""
    text, low = str(e), str(e).lower()
    name = (models() or ["?"])[0]
    if "404" in text or "not found" in low or "does not exist" in low or "unknown model" in low or "not_found" in low:
        return f"{label()} doesn't know the model \"{name}\". Open Settings, AI, press Find models and pick one from the list."
    if "401" in text or "403" in text or "api key" in low or "api_key" in low or "unauthorized" in low or "permission" in low:
        return f"{label()} refused the key. Paste a working key under Settings, AI."
    if "429" in text or "quota" in low or "rate limit" in low or "exhausted" in low:
        return f"{label()} says the key has hit its limit or has no credit left. Check the account with {label()}, or try again later."
    if "connect" in low or "timed out" in low or "timeout" in low or "getaddrinfo" in low or "refused" in low or "nodename" in low or "servname" in low or "nameresolutionerror" in low or "name resolution" in low:
        return f"ClipNova couldn't reach {label()}. Check the internet connection" + (" and that Ollama is running." if provider() == "ollama" else ".")
    return ""


def note_problem(e):
    why = explain(e)
    if why:
        problem.update(text=why, at=time.time())


def clear_problem():
    problem.update(text="", at=0.0)


def _fail(r, model):
    text = r.text[:300].replace(key() or "\0", "<key>")
    raise AIError(f"HTTP {r.status_code} {text}")


# ---------------------------------------------------------------- the schema, said in words for chat models
def _json_schema(s):
    """Gemini's schema spelling (ARRAY, OBJECT...) as ordinary JSON Schema."""
    if isinstance(s, dict):
        return {k: (v.lower() if k == "type" and isinstance(v, str) else _json_schema(v)) for k, v in s.items()}
    if isinstance(s, list):
        return [_json_schema(x) for x in s]
    return s


def _wrapped(prompt, schema):
    return (prompt + "\n\nAnswer with JSON only, no other text and no code fences: one object with a single key "
            "\"items\", whose value follows this JSON Schema:\n" + json.dumps(_json_schema(schema)))


def _json_chunks(text: str):
    """Every balanced {...} or [...] in the text, in the order they appear."""
    out, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            if depth == 0:
                start = i
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0 and start is not None:
                out.append(text[start:i + 1])
                start = None
            elif depth < 0:
                depth = 0
    return out


def _parse(text):
    """The JSON in an answer, even if the model wrapped it in a code fence or a sentence.

    A model that is not careful sometimes puts a sentence in front of the JSON,
    or a second object after it, or forgets a comma. The JSON is looked for
    inside the answer rather than demanded of it."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    out = None
    try:
        out = json.loads(text)
    except ValueError:
        for chunk in _json_chunks(text):
            try:
                out = json.loads(chunk)
                break
            except ValueError:
                continue
        if out is None:
            m = re.search(r"[\[{].*[\]}]", text, re.S)
            if not m:
                raise AIError("The AI did not answer with JSON.")
            try:
                out = json.loads(m.group(0))
            except ValueError:
                raise AIError("The AI did not answer with JSON.")
    if isinstance(out, dict) and "items" in out:
        out = out["items"]
    return out


# ---------------------------------------------------------------- one call
def call(model: str, prompt: str, schema: dict, timeout: float | None = None):
    """Ask one model. Returns (the parsed JSON answer, tokens sent, tokens written back).

    `timeout` is how long one answer may take. A live stream passes a short one, because a slow
    answer must not stop the recording."""
    how = PROVIDERS[provider()][2]
    return {"gemini": _gemini, "openai": _openai, "anthropic": _anthropic}[how](model, prompt, schema, timeout)


def see(prompt: str, image: bytes, timeout: float | None = None) -> tuple[str, int, int]:
    """Ask about one picture, moving on to the next service when one fails (see `_see_one`)."""
    last = None
    for cfg in chain():
        with using(cfg):
            try:
                return _see_one(prompt, image, timeout)
            except Exception as e:  # noqa: BLE001
                last = e
                if is_limit(e):
                    cool_down(cfg)
    if last:
        raise last
    return "", 0, 0


def is_limit(e) -> bool:
    """Did the service say this key is out of quota, credit or rate? Then the next service should take over."""
    low = str(e).lower()
    return ("429" in low or "quota" in low or "rate limit" in low or "exhausted" in low or "insufficient" in low
            or "credit" in low or "billing" in low or "402" in low)


def test_backups() -> list:
    """One tiny request to each backup, so the owner knows every one of them works before it is needed."""
    out = []
    for b in backups():
        if not _usable(b):
            out.append({"label": name_of(b), "ok": False, "error": "Not complete: needs a model and a key."})
            continue
        with using(b):
            try:
                call(b["models"][0], 'Answer with a JSON array that holds the single string "ok".', {"type": "ARRAY", "items": {"type": "STRING"}}, 40)
                out.append({"label": name_of(b), "model": b["models"][0], "ok": True})
            except Exception as e:  # noqa: BLE001
                out.append({"label": name_of(b), "model": b["models"][0], "ok": False,
                            "error": (explain(e) or str(e))[:200].replace(b["key"] or "\0", "<key>")})
    return out


def _see_one(prompt: str, image: bytes, timeout: float | None = None) -> tuple[str, int, int]:
    """Ask one model about one picture: (the answer as text, tokens in, tokens out).

    Nothing is broken by a service that cannot look at pictures, or a model that is only text: the answer
    comes back empty, or says something the caller does not understand, and the caller carries on without
    it. The picture is a JPEG, passed as base64 inside the ordinary message."""
    if not ready() or not image or not models():
        return "", 0, 0
    model = models()[0]
    b64 = base64.b64encode(image).decode()
    how = PROVIDERS[provider()][2]
    if how == "gemini":
        body = {"contents": [{"role": "user", "parts": [
            {"text": prompt},
            {"inline_data": {"mimeType": "image/jpeg", "data": b64}}]}]}
        r = httpx.post(f"{base_url()}/{model}:generateContent", json=body,
                       headers={"x-goog-api-key": key()}, timeout=timeout or 120)
        if r.status_code != 200:
            _fail(r, model)
        data = r.json()
        text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        u = data.get("usageMetadata", {})
        sent = int(u.get("promptTokenCount") or 0)
        return text, sent, max(0, int(u.get("totalTokenCount") or 0) - sent)
    if how == "anthropic":
        body = {"model": model, "max_tokens": 300, "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
            {"type": "text", "text": prompt}]}]}
        r = httpx.post(f"{base_url()}/messages", json=body, timeout=timeout or 120,
                       headers={"x-api-key": key(), "anthropic-version": "2023-06-01"})
        if r.status_code != 200:
            _fail(r, model)
        data = r.json()
        text = "".join(p.get("text", "") for p in data.get("content") or [] if p.get("type") == "text")
        u = data.get("usage") or {}
        return text, int(u.get("input_tokens") or 0), int(u.get("output_tokens") or 0)
    headers = {"Authorization": f"Bearer {key()}"} if key() else {}
    body = {"model": model, "stream": False, "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]}
    r = httpx.post(f"{base_url()}/chat/completions", json=body, headers=headers, timeout=timeout or 120)
    if r.status_code != 200:
        _fail(r, model)
    data = _openai_body(r)
    text = (data["choices"][0]["message"].get("content") or "")
    u = data.get("usage") or {}
    return text, int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)


def _gemini(model, prompt, schema, timeout=None):
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json", "responseSchema": schema}}
    r = httpx.post(f"{base_url()}/{model}:generateContent", json=body, headers={"x-goog-api-key": key()}, timeout=timeout or 120)
    if r.status_code != 200:
        _fail(r, model)
    data = r.json()
    text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    u = data.get("usageMetadata", {})
    sent = int(u.get("promptTokenCount") or 0)
    return json.loads(text), sent, max(0, int(u.get("totalTokenCount") or 0) - sent)   # the answer, and any thinking billed with it


def _openai_body(r):
    """The answer, whether the service sent plain JSON or an event stream.

    Some OpenAI-compatible servers answer with a stream of events unless the
    request says otherwise, so the answer is read from whichever shape arrived.
    A model that answers with a tool call instead of a message leaves the JSON in
    the call's arguments, so that is used too."""
    try:
        data = r.json()
    except ValueError:
        data = _from_events(r.text)
    for ch in data.get("choices") or []:
        msg = ch.get("message") or {}
        if (msg.get("content") or "").strip():
            continue
        for call in msg.get("tool_calls") or []:
            args = (call.get("function") or {}).get("arguments")
            if args:
                msg["content"] = args
                break
    return data


def _from_events(text: str) -> dict:
    """Read an answer out of a server-sent event stream."""
    parts, usage, calls = [], {}, {}
    for line in (text or "").splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            d = json.loads(chunk)
        except ValueError:
            continue
        usage = d.get("usage") or usage
        for ch in d.get("choices") or []:
            for piece in ((ch.get("message") or {}), (ch.get("delta") or {})):
                if piece.get("content"):
                    parts.append(piece["content"])
                for call in piece.get("tool_calls") or []:
                    i = call.get("index", 0)
                    calls[i] = calls.get(i, "") + ((call.get("function") or {}).get("arguments") or "")
    message = {"content": "".join(parts)}
    if not message["content"] and calls:
        message["content"] = "".join(calls.values())
    return {"choices": [{"message": message}], "usage": usage}


def _openai(model, prompt, schema, timeout=None):
    headers = {"Authorization": f"Bearer {key()}"} if key() else {}
    body = {"model": model, "messages": [{"role": "user", "content": _wrapped(prompt, schema)}], "stream": False}
    # Most services accept these two extras; a few models refuse one of them, so they are dropped on a refusal.
    extras = [{"temperature": 0.4, "response_format": {"type": "json_object"}}, {"response_format": {"type": "json_object"}}, {}]
    r = None
    for extra in extras:
        r = httpx.post(f"{base_url()}/chat/completions", json={**body, **extra}, headers=headers, timeout=timeout or 180)
        if r.status_code not in (400, 422):
            break
    if r.status_code != 200:
        _fail(r, model)
    data = _openai_body(r)
    u = data.get("usage") or {}
    return _parse(data["choices"][0]["message"].get("content")), int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)


def _anthropic(model, prompt, schema, timeout=None):
    body = {"model": model, "max_tokens": 8192, "messages": [{"role": "user", "content": _wrapped(prompt, schema)}]}
    r = httpx.post(f"{base_url()}/messages", json=body, timeout=timeout or 180,
                   headers={"x-api-key": key(), "anthropic-version": "2023-06-01"})
    if r.status_code != 200:
        _fail(r, model)
    data = r.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    u = data.get("usage") or {}
    return _parse(text), int(u.get("input_tokens") or 0), int(u.get("output_tokens") or 0)
