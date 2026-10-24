# Parked for discussion (owner, 2026-10-24)

Two ideas the owner queued "so we can talk later". Nothing is decided; discuss before scripting anything.
Both came as ChatGPT drafts: every fact goes through the fact-checker agent against primary sources first.

## 1. Content direction: "AI, from first principles to production"
Position: a software engineer learning the maths behind AI, implementing it, and testing whether it works
(not an AI researcher). Three strands that feed each other:
- **Understand:** the maths behind LLMs (vectors, matrices, probability, calculus, optimisation).
- **Implement:** each concept in plain Python first (NumPy), PyTorch from neural networks on; compare with libraries.
- **Engineer:** how LLMs meet real systems (tokenisation, embeddings, retrieval, inference, tool calls, context,
  coding agents).

Repeatable format per video: a question, the maths with one small worked example, the code with printed
intermediate values, then where it sits inside an LLM (and what the simple version leaves out).

Suggested phases: 1 linear algebra (vectors, dot product, cosine, matrix multiply, projections); 2 probability
(distributions, Bayes, softmax, entropy, cross-entropy); 3 calculus (derivatives, gradients, chain rule, gradient
descent, backprop); 4 transformers (embeddings + position, Q/K/V, scaled dot-product attention, feed-forward,
residuals); 5 systems (tiny network, tiny transformer, embeddings, semantic search and RAG, inference, agents).

Suggested first ten: Why LLMs need linear algebra; vectors and embeddings from scratch; dot product and similarity;
how an LLM predicts the next token (logits, softmax); cross-entropy; gradient descent in Python; backprop without the
black box; self-attention with actual numbers; a tiny transformer from scratch; how AI coding agents work.

To discuss: how this maps onto the math series already running in TOPICS.md (part 1 tokens and part 2 embeddings
are done; part 3 attention is next), whether code-on-screen fits our 60 to 90 s verticals or needs a longer format,
and which theme (card fits maths best so far).

## 2. A video about the Pi coding agent (pi.dev)
Angle: not an install tutorial; how a minimal agent harness works (the agent loop: model asks for a tool, the harness
runs it, the result goes back) and its design choice: a small core you extend with skills and extensions, instead of
built-in plan mode, sub-agents or permission popups. Claims to verify on pi.dev/docs (how-pi-works, extensions).
Fits next to ai-harness-01 and the orchestration series. To decide: short (one idea) or long (a 6-minute walkthrough
with a live demo on a disposable branch), and the theme.
