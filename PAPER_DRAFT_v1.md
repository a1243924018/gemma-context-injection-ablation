# Context Injection Is Not Monotonic: Measuring Critical-Intent Violations in a Small Gemma Agent

**Subtitle:** A reproducible pilot showing that on Gemma 4 E4B, *retrieval-scoped* governance rules beat *full* rule injection — measured by violation rate, not average helpfulness.

---

## Abstract

Agent builders add rules to system prompts by intuition: more rules, more safety. We test that intuition on a small model. Using Gemma 4 E4B locally and eight diagnostic cases designed to trigger operational failure modes (object drift, unresolved anaphora, unrequested action, unverified completion claims), we compare three arms that differ **only** in what is injected: (A) nothing, (B) the one or two governance rules whose keywords match the incoming request, (C) all five rules.

Judged by a pre-registered lexicon rubric applied to stored model outputs, critical-intent violation rates were **87.5% (A), 12.5% (B), and 37.5% (C)**. Full injection—the common production default—was *three times worse* than scoped retrieval on the same model with the same budget. Mean latency rose monotonically (15.2 s → 25.7 s → 31.7 s), so the worse arm was also the slower one. A second, blind judging pass reproduced the verdicts exactly (24/24), which validates our judge *implementation*, not the rubric's semantics; we report both and disclose a rubric revision made by inspecting case semantics, not arm outcomes.

We claim little and quantify everything: n = 8 cases × 3 arms = 24 runs, one model, one machine. The contribution is the **measurement frame** — violation rate with an auditable per-case rule set — and the observation that context is not a monotonic good at small parameter counts.

---

## 1. Introduction

Operational agents fail in ways that benchmark scores do not capture. They answer the *previous* question, act on the wrong object, offer generic troubleshooting where a specific diagnosis was required, or declare work complete without evidence. These are not knowledge failures; they are **intent failures**, and they are precisely what a system prompt is supposed to prevent.

Practitioners typically respond by accumulating rules. Every incident adds a line: don't guess the referent, verify before claiming, ask one question when ambiguous. On large models this usually works, because the model has capacity to attend to many constraints at once. On small models—the ones you can actually run on a laptop GPU, and the ones we deploy as local fallbacks—the same practice may backfire: five rules in a 4-billion-parameter effective model compete for the same limited attention as the user's actual request.

This paper asks one question:

> **RQ:** For a small Gemma model acting under governance rules, does injecting *all* rules outperform injecting only the rules relevant to the current request?

We answer it with a controlled comparison on eight cases, scored by an explicit rubric that ships with the data.

Two design decisions matter more than the result.

**First, we measure violations rather than quality.** A single average score hides exactly the failures we care about: an answer can be helpful, fluent, and still act on the wrong object. We therefore score each case PASS/FAIL against its own written rule, and report the fraction of FAILs as the **critical-intent violation rate**. This mirrors an earlier frozen protocol in our own operations (a 2026-11-03 ablation contract that explicitly forbade a single averaged score), and we keep that constraint here.

**Second, the judge is a file, not a model.** No LLM grades these outputs. A JSON rubric lists, per case, required term groups, forbidden term groups, and question-mark limits. Anyone can re-run the scorer against the released raw outputs and get identical verdicts. We did exactly that with an independent blind pass (Section 5.4).

---

## 2. Related Work

Prompt-level guardrails and "constitution"-style instruction sets are now standard in agent stacks, and instruction-following benchmarks (e.g., IFEval-style suites) measure compliance with *explicit* constraints. Our setting differs in that constraints are **operational and conditional**: which rule applies depends on what the user just said, and the penalty for applying the wrong one is a real-world action on a real object.

Retrieval-augmented prompting is usually discussed as a way to extend knowledge. We use the same mechanism for a different purpose—**routing rules, not facts**—and measure its effect on intent fidelity rather than answer accuracy. Work on long-context degradation and "lost in the middle" effects is consistent with our finding that added context can hurt; our contribution is a small, fully auditable instance in the agent-policy setting, with per-case failure attribution.

---

## 3. Method

### 3.1 Model and host

- Model: **Gemma 4 E4B** (`gemma-e4b-agent`), served locally by Ollama; ~5.3 GB on disk.
- Decoding: temperature 0.2, `num_predict` 700, single stream, no tools.
- Host: one laptop (RTX 3070 Ti Laptop, 8 GB VRAM), WSL2; all runs serial.
- No network calls during inference. Total cost: **$0** (local weights, local compute).

### 3.2 Cases

Eight cases (`C01`–`C08`), inherited verbatim from an operational test set frozen earlier in our system, each carrying: a *goal*, a *trap* (the wrong behavior), an *expected object*, and a *metrics hint* that states what counts as failure. They cover:

| ID | Failure mode probed |
|---|---|
| C01 | Short instruction dragged by the previous topic |
| C02 | Unresolved pronoun ("it") |
| C03 | Screenshot context: which account is on screen |
| C04 | Error dialog: name the failing component, not generic advice |
| C05 | Underspecified request: ask once, don't act |
| C06 | Noise from an unrelated unfinished task list |
| C07 | Explicit constraint: explain only, change nothing |
| C08 | Claiming completion without verification |

Each case provides up to three setup turns (a short prior exchange) followed by a probe. Setup turns are identical across arms, so the only manipulated variable is the injected rules.

### 3.3 Arms

Five governance rules (G1–G5) cover: (G1) resolve ambiguous referents by asking, don't bind to the first pending item; (G2) verify before claiming completion; (G3) treat "why/how/why can't I see it" as questions, not commands; (G4) don't carry old topics into a new referent; (G5) don't volunteer credentials or personal data.

- **Arm A — none.** System prompt is a single sentence: "You are a Chinese assistant. Answer briefly and directly."
- **Arm B — retrieval.** Inject only rules with a keyword hit against the probe text (typically 1–2 rules). Same base sentence, same formatting.
- **Arm C — full.** Inject all five rules as a bulleted list.

Keyword matching is deliberately crude (substring, no embeddings). The point is not to build a good retriever; it is to test whether *scoping at all* beats *not scoping*.

### 3.4 Scoring

For each case, a rubric entry specifies:

- `must_any`: at least one term must appear (e.g., C01 requires one of 浏览器/页面/网页/Edge/Chrome);
- `must_all_groups` / `any_of_groups`: every group, or at least one group, must be satisfied (C03 requires an Edge/account term *and* a login/sync term);
- `forbid_any`: any hit is an automatic FAIL — this encodes the trap (e.g., C01 forbids 余额/API/额度; C06 forbids unrelated task names);
- `max_question_marks`: caps clarifying questions (C05 allows at most one).

PASS requires all constraints. Verdicts are deterministic and reproducible from `raw.jsonl` + `rubric_v2.json`.

### 3.5 Rubric revision (disclosed)

The first rubric (v1) produced A 1/8, B 6/8, C 4/8. We then read the case semantics and found two entries mis-specified **independently of the results**:

- **C04** required "login component / WAM / credential" phrasing but not the specific error code `0x80190001`, which *is* the Windows account (WAM) error; and it did not penalize generic advice ("clear cache", "check network"), although the case's metrics hint says squarely that generic troubleshooting is a failure.
- **C08** expected "clarify first; if you act, verify after"; v1 accepted only verification vocabulary and therefore scored a *correct* clarifying reply as FAIL.

v2 fixes both. The direction of the effect is unchanged (B > C > A); magnitudes shift (B 6→7, C 4→5 PASS). We report v1 and v2 rather than only the winner, and both rubric files ship with the data.

---

## 4. Results

### 4.1 Violation rate (primary metric)

| Arm | Injection | PASS | Pass rate | **Violation rate** |
|---|---|---|---|---|
| A | none | 1/8 | 12.5% | **87.5%** |
| B | retrieval (1–2 rules) | 7/8 | 87.5% | **12.5%** |
| C | full (5 rules) | 5/8 | 62.5% | **37.5%** |

Under rubric v1 the ordering was identical with lower magnitudes (A 12.5% / B 75% / C 50% pass).

### 4.2 Cost side

| Arm | Mean latency | Median | Mean answer length |
|---|---|---|---|
| A | 15.2 s | 14.6 s | 64 chars |
| B | 25.7 s | 25.1 s | 81 chars |
| C | 31.7 s | 28.1 s | 53 chars |

Arm C is both the slowest and the least accurate: five rules cost ~108% more wall-clock than no rules while *reducing* pass rate versus the two-rule arm. Rule injection is not free, and paying more did not buy fidelity.

### 4.3 Failure attribution (what actually went wrong)

- **Arm A (no rules).** C04: generic troubleshooting ("clear cache, check network") instead of naming the failing component. C06: drifted to unrelated task names (`Gemma`, `任务`). C05: started acting ("马上…") instead of asking. C08: no verification vocabulary. This is the expected baseline: without rules, the model optimizes for plausible helpfulness.
- **Arm B (retrieval).** Six of eight cases anchored correctly; the single miss was C04 under v1, fixed under v2 (7/8). C02 resolved the pronoun by asking *one* question rather than guessing.
- **Arm C (full).** The interesting failure: on C01 it returned to the *previous* topic and answered about 余额 (balance) — the exact trap. Five rules in the prompt did not prevent topic bleed; they displaced attention from the current referent. C07/C08 also failed. This is the empirical core of the paper: **at 4B scale, rule volume is not protective, and can be actively harmful.**

### 4.4 Judge agreement

A second pass re-judged all 24 outputs with arm labels removed and order shuffled, using the same rubric v1. It reproduced 24/24 verdicts. We emphasize what this does and does not show: it validates that our scorer implementation is faithful to the written rules (no hidden leniency, no off-by-one in matching), and it rules out arm-label leakage. It does **not** validate the rules themselves—both passes share the same lexicon. Rubric validity remains the study's main external threat (Section 6).

---

## 5. Discussion

If the effect is real, the practical rule for small-model agents is: **route rules, don't stack them.** Retrieve the one or two policies that bear on the current request and leave the rest out of the prompt. This is cheap (no training), inspectable (the injected set is logged per turn), and—by our measurement—more reliable than the "comprehensive system prompt" default.

The mechanism we find most plausible is attention competition rather than instruction conflict: the rules do not contradict each other, yet adding them degrades the model's grip on the *user's* referent. A 4B-scale model spending prompt capacity on five abstract prohibitions has less to spend on "which page is the user pointing at". Larger models may absorb this cost; we did not test them, and we decline to extrapolate.

There is a second, methodological claim: **violation rate with a shipped rubric is a better unit of progress than average answer quality.** It is auditable, it does not require a judge model, and it makes regressions visible (our A arm's 87.5% is not a "quality dip"; it is seven specific, named failures).

---

## 6. Limitations

1. **n is tiny.** 8 cases × 3 arms = 24 generations. We report rates, not confidence intervals as if they were stable estimates; a single case flips 12.5 points.
2. **One model.** Gemma 4 E4B only. The monotonicity claim, if any, is about *this* scale.
3. **Lexicon judging.** Term matching cannot see paraphrase; C04's v1 error is a concrete example of the rubric punishing a valid answer. We mitigated by disclosure and revision, not by an LLM judge (which would reintroduce the very opacity we are avoiding).
4. **Single machine, no repetition.** Temperature 0.2 and one sample per cell; sampling variance is unmeasured.
5. **Retrieval is naive.** Substring keyword matching; a learned router would likely raise arm B further, which strengthens—not weakens—the practical recommendation, but we did not test it.
6. **Task set provenance.** Cases come from our own operational incident patterns, so they are biased toward the failures we happen to have experienced.

---

## 7. Reproducibility

Everything needed is in one directory; no API keys, no network at inference.

```
gemma_ablation_oe_20261111/
  raw.jsonl                  # 24 generations + per-run elapsed, verbatim answers, sha256 1e429f33…
  rubric_v1.json             # original judge rules
  rubric_v2.json             # revised rules + _changes_v2 (reasons)
  rescore_rubric.py          # the only judge implementation
  summary_v1.json / summary_v2.json
  blind_for_zhixing.jsonl    # 24 answers, arm labels stripped, shuffled (seed 20261111)
  blind_verdicts_pass2.jsonl # independent judging pass
  blind_key.json             # id → arm mapping (kept for audit)
```

Re-run the judge (fast, deterministic):

```bash
python3 rescore_rubric.py --rubric=rubric_v2.json
```

Re-run the experiment (≈7 min on the reference laptop):

```bash
python3 gemma_ablation_e4b.py --arms A,B,C
```

The harness writes one JSONL line per run and flushes immediately, so an interrupted run resumes without regenerating completed cells.

---

## 8. Conclusion

On a small Gemma model, injecting a full rule set made the agent **worse** than injecting one or two contextually matched rules—37.5% versus 12.5% critical-intent violations—while also being slower. Both beat injecting nothing (87.5%). The rule we take away is not "use retrieval"; it is that **context is a budget, and budgeting it is part of the policy**. We publish the rubric, the raw generations, and the judge so that this claim can be checked, and revised, by someone who did not run it.

---

*Appendix A — per-case verdicts for both rubrics and both judging passes are in `rescore_v1.jsonl`, `rescore_v2.jsonl`, `blind_verdicts_pass2.jsonl`. Full system prompt text per arm is reconstructible from `gemma_ablation_e4b.py::system_prompt()` and the five rules G1–G5 listed in Section 3.3.*
