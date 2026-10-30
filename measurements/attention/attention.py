"""Toy attention for part 3 (hand-picked numbers, 4 per word, to show the math; not from a trained model).
Formula: Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V  (Vaswani et al. 2017, "Attention Is All You Need",
section 3.2.1; d_k = 64 in the base model).  Sentence: "The cat ate because it was hungry."  Query word: "it"."""
import json, math, pathlib
q_it = [1, 2, 0, 1]
keys = {"cat": [2, 2, 0, 0], "ate": [1, 0, 1, 0], "hungry": [0, 0, 1, 2]}
d = len(q_it)
score = {w: sum(a * b for a, b in zip(q_it, k)) for w, k in keys.items()}
scaled = {w: s / math.sqrt(d) for w, s in score.items()}
z = sum(math.exp(v) for v in scaled.values())
share = {w: math.exp(v) / z for w, v in scaled.items()}
out = {"q_it": q_it, "keys": keys, "d": d, "score": score, "scaled": scaled, "share": {w: round(s, 4) for w, s in share.items()}}
print(json.dumps(out, indent=1))
(pathlib.Path(__file__).parent / "results.json").write_text(json.dumps(out, indent=1) + "\n")
