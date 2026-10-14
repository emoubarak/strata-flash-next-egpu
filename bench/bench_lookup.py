"""Strata rewrite bench (the agent-edits-a-file case, same prompt as the Qwen ngram bench):
rename one function across a ~900-token source file. Speeds from the engine log.

Usage: bench_lookup.py [PORT] [ENGINE_LOG] [LABEL] [SOURCE_FILE]
Writes LABEL-lookup-DATE.json next to this script (distinct from bench_strata.py's files).
"""
import json, os, re, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18090
LOG = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/repos/other/strata/strata-q2_0.log")
LABEL = sys.argv[3] if len(sys.argv) > 3 else "lookup"
SRC = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "rewrite-source.py")

def ask(prompt, max_tokens):
    body = {"model": "x", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens,
            "temperature": 0, "reasoning_effort": "none"}
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    n0 = sum(1 for _ in open(LOG, errors="ignore"))
    t = time.time(); r = json.load(urllib.request.urlopen(req, timeout=1800)); dt = time.time() - t
    time.sleep(1)
    lines = open(LOG, errors="ignore").read().splitlines()[n0:]
    st = [l for l in lines if re.search(r"prompt \d+ tokens", l)]
    m = re.search(r"prompt (\d+) tokens.*?read in (\d+) ms \(([\d.]+) tok/s\), (\d+) generated in (\d+) ms \(([\d.]+) tok/s\)", st[-1]) if st else None
    acc = re.search(r"drafts accepted (\d+) of (\d+)", st[-1]) if st else None
    return dict(wall=round(dt, 1), pp_tok=int(m[1]) if m else None, pp=float(m[3]) if m else None,
                tg_tok=int(m[4]) if m else None, tg=float(m[6]) if m else None,
                drafts=f"{acc[1]}/{acc[2]}" if acc else None, text=r["choices"][0]["message"]["content"])

code = open(SRC, encoding="utf-8").read()
edit = ("Rewrite the whole file below, unchanged except for one thing: rename the function `ask` to "
        "`ask_strata` everywhere. Output only the complete file in one ```python block.\n\n```python\n"
        + code + "```")
res = {"label": LABEL, "runs": []}
x = ask(edit, 2500); x["test"] = "reecriture"
x["fidele"] = x["text"].count("ask_strata(") >= 2 and "def ask(" not in x["text"]
res["runs"].append(x)
print({k: v for k, v in x.items() if k != "text"}, "FAITHFUL" if x["fidele"] else "UNFAITHFUL", flush=True)
json.dump(res, open(os.path.join(HERE, f"{LABEL}-lookup-{time.strftime('%Y%m%d-%H%M')}.json"), "w"), indent=1)
