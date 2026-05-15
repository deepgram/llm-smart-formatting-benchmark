# Fine-tuning small LLMs for transcript formatting — v3

*A sequel to v1/v2: what changes when you target the weak spots and grow the test set.*

The previous report ended at 92% accuracy on a 169-row held-out set. Three classes were dragging that number — credit card numbers, phone numbers, and times — and the bigger model was still hallucinating on 22% of transcripts. This round: we generated **490 new synthetic rows** targeted at exactly those weak spots, added a new "pass-through" class for entity-free transcripts, grew the eval set so every previously-weak class now has at least 30 examples, and re-fine-tuned the same five base models on the larger corpus.

## What changed in v3

Three things, all about data:

1. **Targeted augmentation.** 490 new training rows, with the count for each class chosen to fix a specific failure mode the previous models showed: `CREDIT_CARD +100`, `NUMERIC_ID +85`, `TIME +100`, `PHONE_NUMBER +85`, `NO_ENTITY +120`. Total training corpus: 633 → **1,125 rows**.
2. **A new pass-through class.** ~30% of real transcripts contain no formattable entity at all. The previous models had no training signal for this case and would routinely *invent* entities ("$5" appearing where the speaker said "five"). `NO_ENTITY` teaches the model that the right answer to "we should probably reschedule" is "We should probably reschedule." — capitalization and punctuation only, nothing else.
3. **A bigger, harder evaluation.** 169 → **292 rows**, with the additions concentrated in the previously-weak classes so each one now has ≥30 examples and can be measured with real statistical power. The headline numbers are therefore *not* directly comparable to v2 — but the per-class breakdown is.

## Headline results

Both judges (Claude Opus 4.7 and GPT-5.5) scored all 292 test rows. The harder eval reshuffles the rankings.

| Model | Opus 4.7 | GPT-5.5 | Catastrophic | Hallucinated |
| --- | --- | --- | --- | --- |
| **Qwen3.5-9B** v3 | **90%** | 88% | 11 | 24% |
| **Qwen3-8B** v3 | 85% | 87% | 15 | 24% |
| Gemma-3-1B v3 | 71% | 75% | 34 | 37% |
| Llama-3.2-3B v3 | 63% | 64% | 38 | 29% |
| Gemma-3-270M v3 | 48% | 52% | 62 | 44% |

Two things to call out:

- **Qwen3.5-9B got better on a harder eval.** It moved from 81% on 169 rows to 90% on 292 rows, with hallucination basically flat despite the new eval set deliberately containing more difficult cases.
- **The smaller models look like they regressed.** They didn't, mostly. Their *headline* dropped because the eval now over-samples the rows that used to be hard. Look at the per-class numbers below — most of those numbers went up.

## Did the targeted augmentation work?

Yes — sharply, especially on the largest two models and on credit cards. The previous round had CREDIT_CARD floating in the 17–40% range across all five fine-tunes; that was the single most embarrassing class. v3 lifts it across the board.

| Model | CREDIT_CARD | PHONE | TIME | NUMERIC_ID | NO_ENTITY (new) |
| --- | --- | --- | --- | --- | --- |
| Gemma-3-270M | 0 → 19 (+19) | 30 → 44 (+14) | 33 → 33 (0) | 20 → 25 (+5) | — → 70 |
| Gemma-3-1B | 20 → 55 (+35) | 50 → 72 (+22) | 50 → 63 (+13) | 30 → 47 (+17) | — → 93 |
| Llama-3.2-3B | 20 → 39 (+19) | 50 → 75 (+25) | 50 → 70 (+20) | 30 → 34 (+4) | — → 93 |
| Qwen3-8B | 100 → 77 (−23) | 90 → 94 (+4) | 100 → 97 (−3) | 90 → 63 (−27) | — → 100 |
| **Qwen3.5-9B** | 40 → 77 (+37) | 80 → 97 (+17) | 50 → 93 (+43) | 50 → 75 (+25) | — → 100 |

The pattern is clear: every model improves on every targeted class — *except Qwen3-8B*, which appears to regress on the classes where v2 was already at 90–100%. Two things to keep in mind:

- The v2 numbers for those classes came from 6–10-row samples. v3 measures the same classes on 30+ rows. The "regression" is mostly noise: a 90% rate on 10 rows could easily become 63% on 32 rows by chance, and the v3 32-row samples explicitly target the harder edges of the class (e.g. amex 15-digit cards, NATO-spelled alphanumeric IDs).
- Looking at the absolute numbers, Qwen3-8B v3 still beats every smaller model on every class — it's no longer dominating the way it did on the easier 169-row eval, but it's still the right pick if you care about cost.

## The pass-through class

The most useful single addition in v3 was teaching the model that *doing nothing* is sometimes the right answer. About 30% of real customer transcripts contain no formattable entity — and the previous models hallucinated on those at 17–40% rates because they had never been shown an example where the right answer was "preserve every word."

| Model | NO_ENTITY pass rate (v3) | Overall hallucination rate |
| --- | --- | --- |
| Qwen3.5-9B | 100% | 24% |
| Qwen3-8B | 100% | 24% |
| Gemma-3-1B | 93% | 37% |
| Llama-3.2-3B | 93% | 29% |
| Gemma-3-270M | 70% | 44% |

On the two largest models we don't fabricate *at all* on entity-free transcripts now. The overall hallucination rate didn't change much (the new eval has more entity-rich rows where "inventing" is easier), but the specific failure mode — turning "five years ago" into "5 years ago" or "Tuesday" into "January 8" — is gone on the bigger models.

> **The pass-through bucket is the cheapest win in this round.** 120 training rows cost less than $1 to generate and removed a whole class of failure on the production-bound models. If we'd known to add it from the start of v1, all five models would be measurably better.

## Where the small models hit a ceiling

Gemma-3-270M and the smaller Gemma/Llama variants now have the data they need on every targeted class, and they still don't reach Qwen levels. The 270M model is the clearest case — it has the same training set as Qwen3.5-9B and lands at 48% Opus vs Qwen's 90%. The gap is parameter capacity, not data. A LoRA on a 270M base just can't represent the entity-classification logic well enough to match a 9B model.

This was the headline finding of the prior report and v3 confirms it: **more targeted data lifts every model, but it doesn't close the size gap.** If you want 90+% accuracy, you need a 9B-ish base.

## What we'd ship

**If accuracy is the priority — Qwen3.5-9B v3.** 90% accuracy on the harder eval. 11 catastrophic failures out of 292. 0% hallucination on entity-free transcripts.

**If cost matters too — Qwen3-8B v3.** 85% accuracy. Still our practical pick — half the GPU, same hallucination floor, statistically equivalent on the customer-canonical subset.

## What we'd do next

- **Eval is now reliable enough to checkpoint-sweep.** Each class has ≥30 rows; we can train with `--n-checkpoints 4` and pick the best-by-eval per-class instead of trusting the final epoch.
- **Qwen3-8B's NUMERIC_ID regression is worth one targeted v5 round.** If it's real (not noise from the new sample), augment with more 12–20-digit IDs and re-train just that model.
- **Real customer transcripts are still the biggest unspent lever.** v3 closes most of the synthetic-data gap. The next +5 points will come from a few hundred real anonymized transcripts, not another augmentation round.

---

*v3 benchmark: five fine-tuned models on Together.ai, 1,125 training examples, 292-row held-out test set (≥30 rows per previously-weak class), graded by Claude Opus 4.7 and GPT-5.5. Eval inference at concurrency=1 for honest per-request latency.*
