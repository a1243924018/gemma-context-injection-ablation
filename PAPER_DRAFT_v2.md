# Auditing the Judge: How an Independent Review Overturned a Threefold Effect in a Small-Model Agent Ablation

**Subtitle:** On a 4B-scale Gemma agent, injection of governance rules cuts critical-intent violations from 50% to 12.5% — while the "scoped beats full" effect we first reported turned out to be three defects in our own scoring rubric.

---

## Abstract

We ran a controlled ablation on a small Gemma agent: eight diagnostic cases, three arms differing only in what governance rules are injected (none / only rules whose keywords match the request / all rules), scored by a lexicon rubric rather than an LLM judge.

Our first analysis reported that **scoped retrieval beat full injection threefold** (12.5% vs 37.5% violation rate). An independent reviewer, given only the raw generations and the rubric files, broke that claim. Three defects in our scoring oracle — a term list that echoed the probe text, an `any_of_groups` predicate that the engine evaluated as AND instead of OR, and a forbidden noun that penalised a *correct* clarifying question — each moved the numbers in our favour.

After repairing the rubric by semantics (not by outcome) and re-scoring the same 24 stored generations, the defensible result is:

| Arm | Violation rate |
|---|---|
| A — no rules injected | **50.0%** |
| B — scoped injection (1–2 rules) | **12.5%** |
| C — full injection (5 rules) | **12.5%** |

**Injection helps; the scoped-versus-full distinction does not survive.** Both injection arms reach 7/8, and the difference between them is one case, which is indistinguishable at n = 8.

We keep the dead claim in the paper on purpose. The methodological contribution is the **oracle audit**: four rubric versions, each defect documented with a counterexample, a counterfactual test showing which arm each defect moved, and every intermediate number published. An evaluation rubric that nobody attacks is an unexamined instrument — and in our case it was wrong in the direction of the result we wanted.

---

## 1. Introduction

Agents fail in ways that benchmark accuracy does not capture: they answer the previous question, act on the wrong object, offer generic troubleshooting where a specific diagnosis was required, or claim completion without evidence. Builders respond by stacking rules into the system prompt. On large models this usually works. On the small models we actually run locally — 4B scale, laptop GPU, no network — the same practice may not.

We asked a simple question: **for a small Gemma model under governance rules, does injecting all rules beat injecting only the relevant ones?**

We built an ablation to answer it, and then made a mistake worth reporting: we graded the answers with a word list we wrote ourselves, and we wrote the word list while looking at the failure modes we expected. The rubric was not neutral. When an independent reviewer re-derived the scores from the shipped files, three defects surfaced, all of them flattering our hypothesis.

This paper therefore reports two things: a small, reproducible measurement about rule injection on a 4B model, and an audit trail of the instrument that measured it.

---

## 2. Method

### 2.1 Model and host

- **Gemma 4 E4B** (`gemma-e4b-agent`), served locally by Ollama, ~5.3 GB on disk.
- Decoding: temperature 0.2, `num_predict` 700, no tools, single stream.
- One laptop (8 GB VRAM, WSL2), all runs serial, no network at inference. Cost: $0.

### 2.2 Cases

Eight cases (`C01`–`C08`), each carrying a *goal*, a *trap* (the wrong behaviour), an *expected object*, and a *metrics hint* stating what counts as failure:

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

Each case has up to three setup turns (identical across arms) plus a probe. The only manipulated variable is the injected rule set.

### 2.3 Arms

Five rules (G1–G5): resolve ambiguous referents by asking; verify before claiming completion; treat "why/how" as questions not commands; don't carry old topics into a new referent; don't volunteer credentials.

- **A — none.** System prompt is one sentence: "You are a Chinese assistant. Answer briefly and directly."
- **B — scoped.** Only rules with a keyword hit against the probe (typically 1–2), same base sentence.
- **C — full.** All five rules as a bulleted list.

Keyword matching is deliberately crude (substring, no embeddings). The question is whether *scoping at all* beats *not scoping*, not whether we can build a good router.

### 2.4 Scoring, and why it is the object of study

No LLM grades the outputs. A JSON rubric lists, per case: required term groups (`must_any`, `must_all_groups`, `any_of_groups`), forbidden terms (`forbid_any`, encoding the trap), and a cap on question marks. A single Python function applies it; verdicts are deterministic and recomputable from the shipped JSONL.

This design is auditable — and brittle, in ways Section 4 documents.

---

## 3. Results

### 3.1 Final numbers (rubric v4)

| Arm | PASS | **Violation rate** | Mean latency | Median |
|---|---|---|---|---|
| A — none | 4/8 | **50.0%** | 15.2 s | 14.6 s |
| B — scoped | 7/8 | **12.5%** | 25.7 s | 25.1 s |
| C — full | 7/8 | **12.5%** | 31.7 s | 28.1 s |

Two findings, one that survives and one that does not:

1. **Injection is protective.** Dropping from 50% to 12.5% violations is a four-case swing; the failures that disappear are exactly the ones the rules address (anaphora resolution, unsupported completion claims, generic troubleshooting).
2. **Scoping is not distinguishable from full injection at this scale.** The two arms tie at 7/8. Our earlier "threefold" difference was an artifact (Section 4).

Cost note: full injection is ~2.1× slower than no injection for no measurable accuracy gain over the scoped arm — a practical argument for scoping on latency grounds alone, but not on correctness grounds.

### 3.2 What actually changed in the answers

Behavioural observations we can defend from the raw text:

- **Arm A** drifts to generic remedies: on C04 ("login error dialog") it returns "clear cache / check network" instead of naming the failing component; on C05 it starts acting ("马上…") instead of asking.
- **Arms B and C** both ask a single clarifying question when the referent is missing (C02, C05, C08) and both identify the error code on C04 without attributing it to a component.
- The single remaining failure in both B and C is C04: neither names the credential/login-component layer.

### 3.3 A claim we are retracting

Our first draft stated: *"on C01, Arm C returned to the previous topic and answered about 余额 — five rules did not prevent topic bleed."* That is **false**. The stored answer is a clarifying question — *"请问您是在哪个页面（例如：用量页或余额充值页）刷新不到？"* — and it was scored FAIL solely because the page name contains the forbidden noun 余额. The narrative was a rubric artifact dressed up as a mechanism. It is removed, and Section 4 explains how it happened.

---

## 4. The instrument audit

An independent reviewer received only `raw.jsonl`, the rubric files, and the judge script, and was asked to break the result rather than confirm it. It returned **FAIL** with six findings. We reproduced all of them.

### 4.1 Defects found, each with a counterexample

| # | Defect | Where | Effect on the numbers | How it was caught |
|---|---|---|---|---|
| D1 | `must_any` contained terms that appear **verbatim in the probe** (`0x80190001`, 错误码) ⇒ copying the screen counts as diagnosis | C04, rubric v2 | B and C flip FAIL→PASS (the entire 6→7 and 4→5 gain) | Counterfactual: remove only those two terms, keep everything else ⇒ B, C revert to FAIL |
| D2 | `any_of_groups` was implemented as **all groups must match** (AND) instead of any (OR) | judge code, v2 | The C08 fix had *zero* effect; numbers unchanged from v1 | Reviewer read the loop: `for grp in any_of_groups: if not any(...)` — fails the case if *any* group misses |
| D3 | `forbid_any` contained a **bare noun** (余额) that a correct answer legitimately uses when naming the page | C01, v1–v2 | Arm C's correct clarifying question scored as a trap-hit | Reviewer diffed the answer against the forbidden list |
| D4 | Lexicon scoring is **not paraphrase-robust**: C02 answers in arms A and C are semantically near-identical to B but miss the literal keyword 哪个 | C02, v1–v3 | Split near-identical answers across PASS/FAIL | Side-by-side reading of the three stored answers |
| D5 | A correct **explanation-only** answer was penalised for lacking the literal words 解释/说明 | C07, v1–v3 | Arm A lost a case it should have kept | Reading the stored answer |
| D6 | `run.log` recorded 23 of 24 cells (the 24th came from an earlier smoke run and was resumed by the harness's idempotent skip) | packaging | None on results; but it undermined the "one command reproduces everything" claim | Reviewer counted lines against `raw.jsonl` |

Net direction of D1–D5: **every one of them made arm C look worse and/or arm B look better.** That is not a coincidence to be shrugged at; a rubric authored by the experimenter inherits the experimenter's expectations.

### 4.2 The repair, and the risk of repairing

We introduced rubric v3 (fix D1, D2, D3) and v4 (fix D4, D5), and re-scored the *same* 24 stored generations — no model was re-run, no answer was edited.

| Rubric | A | B | C | Headline claim it would support |
|---|---|---|---|---|
| v1 (original) | 1/8 | 6/8 | 4/8 | scoped ≫ full, both ≫ none |
| v2 (after first self-review) | 1/8 | 7/8 | 5/8 | scoped ≫ full |
| v3 (after reviewer, D1–D3) | 2/8 | 7/8 | 6/8 | scoped > full |
| **v4 (after reviewer, D4–D5)** | **4/8** | **7/8** | **7/8** | **injection ≫ none; scoped ≈ full** |

We are aware that revising a rubric after seeing a critique is exactly the shape of p-hacking. Three things keep it honest, and readers should judge whether they are enough:

1. **Every version ships**, with `_changes_vN` recording the reason for each edit and the case's `metrics_hint` that justifies it.
2. **The trend is against our own hypothesis.** Repairing the instrument destroyed our favourite claim; a tuned rubric would have moved the other way.
3. **The repairs are semantic, not per-arm.** Each edit is justified by the case's own metrics hint (e.g. "unrelated actions = 查余额/查API/调用额度" is an *action-phrase* rule, so the noun alone must not trigger it).

### 4.3 What the audit implies for small-model evaluation

Lexicon rubrics are cheap, deterministic and inspectable — and they are also a hypothesis about language. On 24 samples, ours produced at least five misjudgements, all biased toward the result we expected. Any paper reporting a rubric-scored agent difference without publishing the rubric *and* an adversarial pass over it is reporting, at best, a measurement of its own word list.

---

## 5. Limitations

1. **n = 8 cases × 3 arms = 24 generations.** One case moves a rate by 12.5 points. The surviving claim (injection vs none) rests on a four-case difference; the retracted claim rested on one.
2. **One model, one machine, one sample per cell** (temperature 0.2). Sampling variance is unmeasured.
3. **The rubric remains a lexicon.** v4 fixes the specific defects found; it does not make term matching paraphrase-robust. A second reviewer would likely find more.
4. **The task set is ours**, drawn from our own operational incidents, so it is biased toward failure modes we happen to have met.
5. **Latency includes prompt overhead only**, not any downstream agent cost.

---

## 6. Reproducibility

One directory, no keys, no network at scoring time:

```
raw.jsonl           24 generations, verbatim answers + latency (sha256 1e429f33…)
rubric_v1..v4.json  every version, with _changes_vN and the reasoning
rescore_rubric.py   the only judge implementation
summary_v1..v4.json arm-level results per version
blind_*             second judging pass, arm labels stripped (seed 20261111), key kept for audit
zhixing_paper_verdict.json   the independent reviewer's FAIL verdict, verbatim
```

```
python3 rescore_rubric.py --rubric=rubric_v4.json     # final numbers
python3 rescore_rubric.py --rubric=rubric_v1.json     # the retracted ones
```

Re-running the generations takes ≈7 minutes and is resumable cell-by-cell.

---

## 7. Conclusion

On a 4B-scale Gemma agent, injecting governance rules cut critical-intent violations from 50% to 12.5%. Whether you inject one or five rules made no measurable difference in our data — a claim we could not make in our first draft, because our scoring rubric had three defects and each one pointed the same way. We publish the dead claim, the failing verdict that killed it, and all four rubric versions, because the audit is the part we would want to read.

---

*Appendix A — per-case verdicts for all four rubrics and both judging passes are in `rescore_v*.jsonl` and `blind_verdicts_pass2.jsonl`. The five governance rules G1–G5 are listed in §2.3; the system prompt for each arm is reconstructible from `gemma_ablation_e4b.py::system_prompt()`.*
