import json, glob, sys, os
PRICES = {"openai": (0.05, 0.25), "gemini": (0.25, 1.50), "anthropic": (0.10, 0.50)}  # USD per 1M tokens (in, out)
def find_usage(o):
    if isinstance(o, dict):
        if "prompt_tokens" in o and "completion_tokens" in o:
            return o
        for v in o.values():
            r = find_usage(v)
            if r: return r
    elif isinstance(o, list):
        for v in o:
            r = find_usage(v)
            if r: return r
    return None
out = sys.argv[1]
prov = sys.argv[2] if len(sys.argv) > 2 else ""
paths = sorted(glob.glob(os.path.join(out, "**", "*.traj.json"), recursive=True))
if not paths:
    print("no trajectories found under", out)
for p in paths:
    d = json.load(open(p)); msgs = d.get("messages", []); info = d.get("info", {})
    pin = pout = calls = 0
    for m in msgs:
        if m.get("role") != "assistant": continue
        u = find_usage(m)
        if u:
            calls += 1; pin += u.get("prompt_tokens") or 0; pout += u.get("completion_tokens") or 0
    print("trajectory:", os.path.basename(p))
    print("  exit_status:", info.get("exit_status"), "| messages:", len(msgs), "| calls with usage:", calls)
    print("  prompt_tokens: %d | completion_tokens: %d" % (pin, pout))
    if prov in PRICES and calls:
        a, b = PRICES[prov]
        print("  est. cost at list price: $%.4f" % (pin * a / 1e6 + pout * b / 1e6))
    if calls == 0:
        a = [m for m in msgs if m.get("role") == "assistant"]
        if a: print("  no usage found; assistant keys:", list(a[0].keys()), "extra keys:", list((a[0].get("extra") or {}).keys()))
for pj in glob.glob(os.path.join(out, "preds.json")):
    preds = json.load(open(pj))
    for iid, v in preds.items():
        print("patch length for", iid, ":", len((v or {}).get("model_patch") or ""))
