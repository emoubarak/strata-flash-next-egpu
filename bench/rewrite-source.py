"""Bench Strata via son API OpenAI : tg (prompt ai-bench, 200 tokens) et pp (long prompt).
Les vitesses viennent du journal du moteur (lignes « prompt N tokens ... read in X ms (Y tok/s), M generated in Z ms (W tok/s) »)."""
import json, re, sys, time, urllib.request
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18090
LOG = sys.argv[2] if len(sys.argv) > 2 else "~/repos/other/strata/strata-q2_0.log"
LABEL = sys.argv[3] if len(sys.argv) > 3 else "q2_0"

def ask(prompt, max_tokens, effort="none"):
    body = {"model": "x", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
            "temperature": 0, "reasoning_effort": effort}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    n0 = sum(1 for _ in open(LOG, errors="ignore"))
    t = time.time(); r = json.load(urllib.request.urlopen(req, timeout=3600)); dt = time.time() - t
    time.sleep(1)
    lines = open(LOG, errors="ignore").read().splitlines()[n0:]
    st = [l for l in lines if re.search(r"prompt \d+ tokens", l)]
    m = re.search(r"prompt (\d+) tokens.*?read in (\d+) ms \(([\d.]+) tok/s\), (\d+) generated in (\d+) ms \(([\d.]+) tok/s\)", st[-1]) if st else None
    acc = re.search(r"drafts accepted (\d+) of (\d+)", st[-1]) if st else None
    u = r.get("usage", {})
    return dict(wall=round(dt, 1), finish=r["choices"][0]["finish_reason"], usage=u,
                pp_tok=int(m[1]) if m else None, pp=float(m[3]) if m else None,
                tg_tok=int(m[4]) if m else None, tg=float(m[6]) if m else None,
                drafts=f"{acc[1]}/{acc[2]}" if acc else None, text=r["choices"][0]["message"]["content"][:120])

res = {"label": LABEL, "runs": []}
for i in range(3):
    x = ask("Write a short poem about GPU programming.", 200); x["test"] = "ai-bench tg200"; res["runs"].append(x); print(x, flush=True)
# même texte que les mesures du 2026-10-09/10 (DETAILS.md de Strata v0.1.41, commit fb58e0d), figé ici
doc = open("~/repos/emoubarak/local-inference/benchmarks/strata/prompt-DETAILS-fb58e0d.md", errors="ignore").read()
for n_chars, name in [(24000, "long ~6k")]:
    p = "Summarize the following document in three sentences.\n\n" + doc[:n_chars]
    x = ask(p, 100); x["test"] = name; res["runs"].append(x); print({k: v for k, v in x.items() if k != "text"}, flush=True)
json.dump(res, open(f"~/repos/emoubarak/local-inference/benchmarks/strata/{LABEL}-{time.strftime('%Y%m%d-%H%M')}.json", "w"), indent=1)
