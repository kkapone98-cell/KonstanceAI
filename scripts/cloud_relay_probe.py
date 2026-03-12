import os, json, time, pathlib
from urllib import request
from dotenv import load_dotenv

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
OUT = ROOT / "data" / "cloud_status.json"


def save(obj):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _relay_http_url():
    url = (os.getenv("OPENCLAW_RELAY_URL") or "").strip()
    if not url:
        return ""
    if url.startswith("ws://"):
        return "http://" + url[5:]
    if url.startswith("wss://"):
        return "https://" + url[6:]
    return url


def probe():
    load_dotenv()
    raw_url = (os.getenv("OPENCLAW_RELAY_URL") or "").strip()
    url = _relay_http_url() or raw_url
    token = (os.getenv("OPENCLAW_RELAY_TOKEN") or "").strip()

    res = {
        "ts": int(time.time()),
        "configured": bool(raw_url),
        "url": raw_url,
        "ok": False,
        "status": None,
        "latency_ms": None,
        "error": ""
    }

    if not url:
        res["error"] = "OPENCLAW_RELAY_URL missing"
        save(res)
        return res

    payload = {
        "message": "healthcheck: reply with short ok",
        "context": {"assistant": "konstance", "probe": True}
    }
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    t0 = time.time()
    try:
        req = request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", errors="ignore")
            dt = int((time.time() - t0) * 1000)
            res["status"] = int(getattr(r, "status", 200))
            res["latency_ms"] = dt
            if 200 <= res["status"] < 300 and body:
                res["ok"] = True
            else:
                res["error"] = f"non-2xx or empty body: status={res['status']}"
    except Exception as e:
        res["error"] = str(e)

    save(res)
    return res


if __name__ == "__main__":
    out = probe()
    print(json.dumps(out, indent=2))
    raise SystemExit(0 if out.get("ok") else 2)
