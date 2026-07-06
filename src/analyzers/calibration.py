"""
Perplexity Calibration
======================

Turns a raw perplexity into a **calibrated AI-probability** in ``[0, 1]`` via a
logistic (sigmoid) transform.

Why this exists
---------------
The previous ensemble mapped *both* GPT-2 and NLTK perplexity to an AI-score
with the single formula ``max(0, min(1, 1 - perplexity / 500))``. That is wrong
for two independent reasons:

1. **It conflates incommensurable scales.** GPT-2 perplexity on ordinary English
   is ~40-100; the Brown-corpus n-gram model produces perplexities in the
   hundreds-to-thousands. One linear map cannot fit both.
2. **It has no calibrated decision boundary.** Human GPT-2 perplexity ~58 maps
   to ``1 - 58/500 = 0.88`` — i.e. human text scored 88% AI. This is the
   systematic AI-bias flagged in the audit (finding C2).

A logistic with an explicit midpoint (the perplexity at which AI-probability is
0.5) and slope fixes both: each analyzer gets its own midpoint/slope, and the
midpoint *is* the decision boundary.

The ``direction`` argument encodes the empirical relationship for each analyzer:

* GPT-2 — lower perplexity means *more* predictable, hence more AI-like
  (``direction="lower_is_ai"``).
* Brown-corpus NLTK — formal/modern text is atypical of the 1961 corpus and so
  scores *higher* perplexity while also being more likely AI in practice
  (``direction="higher_is_ai"``). This signal is weaker and mainly reflects
  stylistic typicality; it is weighted accordingly in the ensemble.
"""

from __future__ import annotations

import math


def logistic_ai_probability(
    perplexity: float,
    midpoint: float,
    slope: float,
    direction: str = "lower_is_ai",
) -> float:
    """Map a perplexity to a calibrated AI-probability in ``[0, 1]``.

    Args:
        perplexity: Raw perplexity value (>= 0).
        midpoint: Perplexity at which the AI-probability is 0.5 (the decision
            boundary).
        slope: Logistic steepness (> 0). Larger => sharper transition.
        direction: ``"lower_is_ai"`` (default) or ``"higher_is_ai"``.

    Returns:
        AI-probability in ``[0, 1]``.
    """
    if slope <= 0:
        raise ValueError("slope must be positive")
    if direction not in ("lower_is_ai", "higher_is_ai"):
        raise ValueError("direction must be 'lower_is_ai' or 'higher_is_ai'")

    # sign chosen so that the AI side of the midpoint maps above 0.5.
    sign = 1.0 if direction == "lower_is_ai" else -1.0
    z = sign * slope * (midpoint - perplexity)
    # Numerically stable logistic.
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)
