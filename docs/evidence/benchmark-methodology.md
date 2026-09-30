# AuraGuard Evidence: Benchmark Methodology & Audit

## 1. Overview
AuraGuard's benchmark methodology enforces scientific rigor:
1. **Zero Hallucination / No Mock Numbers**: All reported metrics are collected by running real automated scripts.
2. **Warm-up Iterations**: Every benchmark runs at least 1 warm-up iteration prior to statistical capture to eliminate cold-start cache distortions.
3. **Distribution Statistics**: Measures mean, median, 95th percentile, minimum, and maximum.
4. **Hardware Grounding**: Benchmark outputs include exact CPU models, memory sizes, execution providers, and timestamps in JSON format (`benchmarks/results/`).

---

## 2. TTFT Methodology Revision (Phase 6 vs Phase 7)
* **Phase 6 Flaw**: Measured prompt tokenization time into a tensor (`inputs = tokenizer(...)`), reporting `3.74 ms`.
* **Phase 7 Correction**: Implemented `TTFTStreamer` inheriting from Hugging Face's `BaseStreamer`. Accurately records $t_{\text{first\_token}} - t_{\text{request\_start}}$, capturing the entire prompt prefill computation across all transformer attention layers.
* **Empirical Measured Difference**: On the 12th Gen Intel Core i5-1235U CPU, true TTFT is **14,278.46 ms** (~14.28s) for full prompt prefill (~250 tokens), and **510.4 ms** for single-sentence prompts.
