#!/usr/bin/env bash
set -u
source "$HOME/.swebench-keys.env"
show() { python3 -c '
import sys,json
raw=sys.stdin.read()
try:
    d=json.loads(raw)
except Exception:
    print("   non-JSON reply:", raw[:200]); sys.exit()
if "error" in d:
    print("   ERROR:", json.dumps(d["error"])[:300]); sys.exit()
txt=None
if "choices" in d: txt=d["choices"][0]["message"].get("content")
elif "candidates" in d:
    c=d["candidates"][0]; txt="".join(p.get("text","") for p in c.get("content",{}).get("parts",[]))
elif "content" in d: txt="".join(b.get("text","") for b in d["content"])
print("   reply:", repr(txt)[:120])
u=d.get("usage") or d.get("usageMetadata")
print("   usage:", json.dumps(u)[:200])
'; }
P='Reply with the single word OK.'
echo "== DeepSeek deepseek-flash"
curl -sS --max-time 60 https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY:-}" -H "Content-Type: application/json" \
  -d '{"model":"deepseek-flash","messages":[{"role":"user","content":"Reply with the single word OK."}],"max_tokens":50,"temperature":0.2,"thinking":{"type":"disabled"}}' | show
echo "== OpenAI gpt-6-luna"
curl -sS --max-time 60 https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer ${OPENAI_API_KEY:-}" -H "Content-Type: application/json" \
  -d '{"model":"gpt-6-luna","messages":[{"role":"user","content":"Reply with the single word OK."}],"max_completion_tokens":300,"temperature":0.2}' | show
echo "== Gemini gemini-3.1-flash-lite"
curl -sS --max-time 60 "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent" \
  -H "x-goog-api-key: ${GEMINI_API_KEY:-}" -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Reply with the single word OK."}]}],"generationConfig":{"temperature":0.2,"maxOutputTokens":300}}' | show
echo "== Anthropic claude-haiku-5-5"
curl -sS --max-time 60 https://api.anthropic.com/v1/messages \
  -H "x-api-key: ${ANTHROPIC_API_KEY:-}" -H "anthropic-version: 2023-06-01" -H "content-type: application/json" \
  -d '{"model":"claude-haiku-5-5","max_tokens":50,"messages":[{"role":"user","content":"Reply with the single word OK."}]}' | show
