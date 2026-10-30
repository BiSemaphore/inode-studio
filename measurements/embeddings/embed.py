"""Embeddings, measured on this laptop: nomic-embed-text through Ollama, with the "clustering: " task prefix
(the model card requires a task prefix; clustering fits "how similar are these words"; fact-checked 2026-10-24).
Each word becomes a list of numbers (a vector). Closeness = the angle between two vectors
(cosine similarity). Usage: .venv/bin/python -I run/embed.py  -> prints and writes run/results.json"""
import json, math, os, urllib.request

MODEL = "nomic-embed-text"
PREFIX = "clustering: "
WORDS = ["king", "queen", "banana", "man", "woman", "apple"]

def embed(texts):
    req = urllib.request.Request("http://127.0.0.1:11434/api/embed", method="POST",
                                 data=json.dumps({"model": MODEL, "input": [PREFIX + x for x in texts]}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))["embeddings"]

def cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

V = dict(zip(WORDS, embed(WORDS)))
pairs = [("king", "queen"), ("king", "banana"), ("queen", "banana"), ("man", "woman"), ("banana", "apple"), ("king", "apple")]
out = {"model": MODEL, "prefix": PREFIX, "dims": len(V["king"]), "first_numbers": {w: [round(x, 3) for x in V[w][:4]] for w in ("king", "queen")}, "pairs": {}}
for a, b in pairs:
    c = cos(V[a], V[b]); out["pairs"][f"{a}-{b}"] = {"cosine": round(c, 3), "angle_deg": round(math.degrees(math.acos(c)), 1)}
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(os.path.dirname(__file__), "results.json"), "w"), indent=1)
