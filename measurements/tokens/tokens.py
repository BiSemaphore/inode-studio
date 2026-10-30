"""Why AI can't count letters, measured on this laptop (local, no network at run time).

1. The tested model's own tokenizer (Qwen2.5-Coder, from Hugging Face) shows that it never sees
   letters: "strawberry" is three tokens, three numbers.
2. The same model (Ollama) is asked to count the r's in strawberry, N times, with its default
   sampling, so each run is a fresh answer. We record how often it is right (the answer is 3).

  python3 run/tokens.py [model] [runs]        -> run/results.json
"""
import json, re, sys, pathlib, urllib.request
from tokenizers import Tokenizer

HERE = pathlib.Path(__file__).resolve().parent
MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-coder:7b"
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 10

tok = Tokenizer.from_pretrained("Qwen/Qwen2.5-Coder-7B-Instruct")
WORDS = ["strawberry", "the", "understanding", "tokenization", "lollapalooza"]
ids = lambda w: tok.encode(w, add_special_tokens=False).ids
splits = {w: {"ids": ids(w), "pieces": [tok.decode([i]) for i in ids(w)]} for w in WORDS}

def ask(prompt):
    req = urllib.request.Request("http://localhost:11434/api/chat",
        data=json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                         "stream": False}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())["message"]["content"]

def first_int(s):
    m = re.search(r"\b(\d+)\b", s)
    return int(m.group(1)) if m else None

def main():
    q = "How many times does the letter r appear in the word strawberry? Answer with just the number."
    answers, right = [], 0
    for _ in range(RUNS):
        a = first_int(ask(q))
        answers.append(a)
        right += (a == 3)
    results = {"model": MODEL, "runs": RUNS, "tokenizer": "Qwen/Qwen2.5-Coder-7B-Instruct", "sampling": "model default",
               "splits": splits,
               "question": q, "correct": 3,
               "answers": answers, "times_right": right}
    (HERE / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps({k: results[k] for k in ("model", "splits", "answers", "times_right")}, indent=2))

if __name__ == "__main__":
    main()
