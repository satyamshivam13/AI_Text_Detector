# Fairness: false-positive rate by population

A detector can score 95%+ on a balanced benchmark and still be **unusable for a
group of people**. The number that matters ethically is not overall accuracy — it
is the false-positive rate *per population*: how often real humans in each group
are accused of using AI.

Every sample in this evaluation is **human-authored**, so any AI verdict is a
false positive by construction. Reproduce it:

```bash
python scripts/prepare_fairness_set.py          # 785 human samples, 10 populations
python scripts/fpr_by_population.py --analyzer binoculars
python scripts/fpr_by_population.py --analyzer gpt2
python scripts/fpr_by_population.py --analyzer ensemble
```

Populations: TOEFL essays by **non-native English writers** and native-speaker
student/college/technical essays (Liang et al., 2023,
[ChatGPT-Detector-Bias](https://github.com/Weixin-Liang/ChatGPT-Detector-Bias)),
plus real human answers across five HC3 domains. Neither corpus is redistributed.

## Results (n=785 human samples; % = real people falsely flagged as AI)

The **Ensemble** column below is the **old GPT-2-weighted blend**, kept as the
cautionary baseline. The *current* default ensemble is Binoculars-weighted, so its
numbers equal the Binoculars column (re-measured: overall 1.0%, non-native 5.5%,
every native population 0.0%). See "What this means", point 2.

| Population | n | **Binoculars** (= current default ensemble) | GPT-2 | Ensemble (old GPT-2-weighted) |
|-----------|--:|---------------:|------:|---------:|
| **Non-native writers (TOEFL)** | 91 | **5.5%** | 26.4% | **71.4%** |
| US 8th-grade students | 88 | 0.0% | 1.1% | 17.1% |
| College admission essays | 70 | 0.0% | 0.0% | 24.3% |
| CS224N technical essays | 145 | 0.0% | 1.4% | 9.7% |
| HC3 reddit_eli5 | 60 | 0.0% | 3.3% | 5.0% |
| HC3 open_qa | 60 | 3.3% | 83.3% | 38.3% |
| HC3 finance | 60 | 0.0% | 6.7% | 25.0% |
| HC3 medicine | 60 | 0.0% | 8.3% | 3.3% |
| HC3 wiki_csai | 60 | 0.0% | 10.0% | 56.7% |
| **Overall** | **694** | **1.0%** | **13.5%** | **27.1%** |
| Overall Wilson 95% CI | | [0.5%, 2.1%] | [11.2%, 16.3%] | [23.9%, 30.5%] |

(`toefl_gpt4_polished` — the same TOEFL essays polished by GPT-4 — is excluded
from the overall: it is human-authored but machine-edited, genuinely ambiguous.
For the record: Binoculars 0.0%, GPT-2 39.6%, Ensemble 51.6%.)

## What this means

**1. Use Binoculars.** It is both the most accurate (on HC3) and by far the
fairest: 1.0% overall, and 5.5% [2.4%, 12.2%] on the hardest population. The
cross-perplexity *ratio* cancels the "simple, predictable text looks AI-generated"
effect that drives the bias — which is the entire reason the method exists.

**2. A GPT-2-weighted ensemble is the WORST for fairness.** 27% of real humans
overall, and **71% of non-native English writers**, were flagged. Its strong
aggregate HC3 accuracy (0.95) *masked* this — the essay populations are harder
than HC3's mixed answers.

**This is why the default ensemble verdict is now Binoculars-driven**
(`weight_binoculars=1.0`, GPT-2/NLTK weight 0). Re-measured with that default,
the ensemble collapses onto Binoculars' numbers: **overall 1.0% [0.5%, 2.1%],
non-native 5.5%, every native-speaker population 0.0%.** The Ensemble column in
the table above is the *old GPT-2-weighted blend*, kept as the cautionary
baseline. GPT-2/NLTK sub-scores still display for transparency but no longer
drive the verdict.

**3. GPT-2 reproduces Liang et al. (2023).** 26% of non-native writers vs ~1% of
native writers. Non-native English is simpler and more predictable, so it has low
GPT-2 perplexity, so single-model perplexity flags it. This is a known, published
failure mode, confirmed here.

**4. Even Binoculars is not perfectly fair.** Non-native writers still see 5.5%
vs 0% for native-speaker essays. The confidence interval is wide (n=91), but the
disparity is real and is stated, not hidden. A 1-in-18 false-accusation rate is
not "safe" for a high-stakes decision about a non-native writer.

## Do not use any of these for consequential decisions

None of these analyzers should be the basis for accusing a specific person of
academic dishonesty or fraud. Treat every result as weak probabilistic evidence,
never proof, and weight it toward *not* flagging when the writer may be a
non-native speaker, a child, or writing in a simple/formulaic register — the
groups these detectors are most likely to wrong.

## Caveats

- Essay `n` per population is 70–145; the Wilson intervals reflect the resulting
  uncertainty. Larger samples would tighten them.
- Populations are English-only and mostly academic. Other registers and languages
  are unmeasured.
- Numbers are analyzer verdicts at each analyzer's default threshold. Binoculars'
  threshold is the HC3-calibrated 0.7625; the ensemble uses `ThresholdConfig` /
  `EnsembleConfig` defaults.
