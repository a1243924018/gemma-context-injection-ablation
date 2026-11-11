# Context Injection Is Not Monotonic — artifact bundle

Gemma 4 E4B, 8 diagnostic cases × 3 injection arms (none / retrieval / full).
Scored by a shipped lexicon rubric; two independent judging passes.

- raw.jsonl — 24 generations (verbatim answers, per-run latency)
- rubric_v1.json / rubric_v2.json — v2 includes `_changes_v2` explaining the revision
- rescore_rubric.py — the only judge implementation
- summary_v1.json / summary_v2.json — arm-level results
- blind_for_zhixing.jsonl / blind_verdicts_pass2.jsonl / blind_key.json — blind second pass

Reproduce the judging:  python3 rescore_rubric.py --rubric=rubric_v2.json
Reproduce the runs:     python3 gemma_ablation_e4b.py --arms A,B,C   (ollama, gemma-e4b-agent)
