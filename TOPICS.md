# Topics

The list of videos to make, in order of priority inside each series. Update the status when a
video is scripted, rendered or posted. Posted videos are listed in `videos/INDEX.md`.

Rules for a topic to be on this list:
- One idea, one surprising fact or number, explainable in 45 to 90 seconds.
- Prefer topics we can measure on this laptop (Ollama, a toy script). Real numbers beat borrowed ones.
- Math is shown as one small worked example with real numbers, never as a wall of formulas.

Status: `idea`, `next`, `scripted`, `rendered`, `posted`.

## Series 1: The math behind LLMs

Each part takes one formula and works it with real numbers. The order builds up: each part ends by
pointing to the next one.

| # | Topic | Hook | The math, in one line | Measure locally | Status |
|---|---|---|---|---|---|
| 1 | Tokens | Why AI cannot count the r's in "strawberry" | Text becomes pieces of words, then numbers | Yes: run a tokenizer on real words | rendered (tokens-01) |
| 2 | Embeddings | How AI knows "king" is close to "queen" | Words are points; closeness is the angle between them (cosine) | Yes: embed words, print similarities | idea |
| 3 | Attention | How each word looks at every other word | Score = query dot key, divided by the square root of the size | Partly: tiny example by hand | idea |
| 4 | Softmax and temperature | Why "creative" mode makes things up | Scores become chances: divide by temperature, then softmax | Yes: same prompt at 0, 0.7, 1.5 | idea |
| 5 | Context cost | Why 2x context costs about 4x in attention | Every token looks at every token: n times n | Yes: time prefill at 1k, 2k, 4k tokens | idea |
| 6 | Model size to memory | Why a 7B model needs about 14 GB | Parameters times bytes each: 7B x 2 bytes (FP16) | Yes: load and read memory use | idea |
| 7 | Quantization | Same model, a quarter of the memory | 16 bits to 4 bits per weight: 14 GB to about 4 GB | Yes: compare two Ollama builds | idea |
| 8 | KV cache memory | Why long chats eat GPU memory | 2 x layers x heads x size x tokens x bytes | Yes: compute for a real model | idea |
| 9 | Decode speed limit | Why tokens per second has a ceiling | Speed is about memory bandwidth divided by model size | Yes: measured tokens/s vs the formula | idea |
| 10 | Loss and perplexity | How a model learns from being wrong | Loss = how surprised it was; perplexity = e to the loss | Yes: perplexity of two texts | idea |
| 11 | Gradient descent | Learning is walking downhill | Step = minus learning rate times slope | Yes: a 10-line toy fit | idea |
| 12 | LoRA | Fine-tune 0.1% of the weights | One big matrix change = two thin matrices multiplied | Partly: count parameters | idea |
| 13 | Mixture of experts | A big model that runs like a small one | Total parameters vs active parameters per token | No: use published model cards | idea |
| 14 | Scaling laws | How much data a model needs | About 20 training tokens per parameter (Chinchilla) | No: published paper | idea |

## Series 2: Inference (how the answer gets made)

| # | Topic | Hook | Status |
|---|---|---|---|
| 1 | Prefill, decode, KV cache, temperature | One word at a time | posted (inference-01) |
| 2 | Batching | How one GPU serves a thousand users | idea |
| 3 | Speculative decoding | A small model guesses, the big model checks | idea |
| 4 | Prompt caching | Why the second call is cheaper | idea |
| 5 | Running a model locally | What your laptop can really run | idea |

## Series 3: Harnesses and agents

| # | Topic | Hook | Status |
|---|---|---|---|
| 1 | The AI harness | The model is not the product | posted (ai-harness-01) |
| 2 | Orchestration, parts 1 to 3 | One agent keeps the plan | posted |
| 3 | Prompt injection | "It only reads your email." | posted-ready (v2 chosen: line people, 2x, clean cover) |
| 4 | Tool calling | How a model "uses" a tool it cannot touch | idea |
| 5 | The agent loop | Think, act, look, repeat | idea |
| 6 | MCP | One plug for every tool | idea |
| 7 | RAG | Open-book exam for AI | idea |
| 8 | Context engineering | What goes into the window, and what stays out | idea |
| 9 | Evals | How you know your agent got better | idea |

## Trend shorts

News as it happens, 30 to 45 seconds, in the punchline look. Add here when a story breaks.

## Parked for discussion (owner, 2026-10-24)

Not decided yet; talk before scripting. Details: `ideas/2026-10-24-content-direction.md`.
- Content direction "AI, from first principles to production": maths, then code, then real systems, as one series.
- A video about the Pi coding agent (pi.dev): how a minimal agent harness works and why it keeps the core small.

