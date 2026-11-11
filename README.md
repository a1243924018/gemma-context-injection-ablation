# Auditing the Judge — artifact bundle

Gemma 4 E4B, 8 diagnostic cases x 3 injection arms (none / scoped / full), 24 generations.
Scored by a shipped lexicon rubric — and the rubric is part of what this paper studies.

## Files
- `raw.jsonl` — 24 generations (verbatim answers, per-run latency)
- `rubric_v1..v4.json` — every rubric version, each with `_changes_vN` explaining the edit
- `rescore_rubric.py` — the only judge implementation
- `summary_v1..v4.json` — arm-level results per rubric version
- `blind_for_zhixing.jsonl` / `blind_verdicts_pass2.jsonl` / `blind_key.json` — blind second pass
- `zhixing_paper_verdict.json` — the independent reviewer's FAIL verdict, verbatim
- `PAPER_DRAFT_v1.md` (retracted claim) / `PAPER_DRAFT_v2.md` (final)

## Headline
Final (rubric v4): A 4/8 = 50% violations, B 7/8 = 12.5%, C 7/8 = 12.5%.
The earlier "scoped beats full threefold" claim was an artifact of three rubric defects
(probe-echo terms, an any_of_groups predicate evaluated as AND, a forbidden noun that
penalised a correct clarifying question). Repairs are documented per version.

## Reproduce
```
python3 rescore_rubric.py --rubric=rubric_v4.json   # final numbers
python3 rescore_rubric.py --rubric=rubric_v1.json   # the retracted ones
python3 gemma_ablation_e4b.py --arms A,B,C          # re-run generations (ollama, gemma-e4b-agent)
```
