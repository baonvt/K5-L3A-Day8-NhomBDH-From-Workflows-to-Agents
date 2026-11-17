"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
import math

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge labels must have equal length")
    if not human:
        raise ValueError("at least one label is required")
    if any(x not in ("PASS", "FAIL") for x in (*human, *judge)):
        raise ValueError("labels must be 'PASS' or 'FAIL'")
    tp = sum(h == POS and j == POS for h, j in zip(human, judge))
    fp = sum(h != POS and j == POS for h, j in zip(human, judge))
    fn = sum(h == POS and j != POS for h, j in zip(human, judge))
    tn = sum(h != POS and j != POS for h, j in zip(human, judge))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    p_den = cm["tp"] + cm["fp"]
    r_den = cm["tp"] + cm["fn"]
    return (cm["tp"] / p_den if p_den else 0.0,
            cm["tp"] / r_den if r_den else 0.0)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = sum(cm.values())
    observed = (cm["tp"] + cm["tn"]) / n
    human_fail = cm["tp"] + cm["fn"]
    human_pass = cm["fp"] + cm["tn"]
    judge_fail = cm["tp"] + cm["fp"]
    judge_pass = cm["fn"] + cm["tn"]
    expected = (human_fail * judge_fail + human_pass * judge_pass) / (n * n)
    if math.isclose(1.0 - expected, 0.0, abs_tol=1e-15):
        raise ValueError("Cohen's kappa is undefined when expected agreement is 1")
    return (observed - expected) / (1.0 - expected)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    values = (observed_rate, sensitivity, specificity)
    if any(not math.isfinite(v) or not 0.0 <= v <= 1.0 for v in values):
        raise ValueError("rates must be finite values in [0, 1]")
    denominator = sensitivity + specificity - 1.0
    if math.isclose(denominator, 0.0, abs_tol=1e-15):
        raise ValueError("Rogan-Gladen correction is undefined when sensitivity + specificity = 1")
    return min(1.0, max(0.0, (observed_rate + specificity - 1.0) / denominator))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    if len(a) != len(b) or not a:
        raise ValueError("paired samples must have the same non-zero length")
    if n_resamples < 1 or not 0.0 < confidence < 1.0:
        raise ValueError("n_resamples must be positive and confidence must be in (0, 1)")
    if any(not math.isfinite(float(v)) for v in (*a, *b)):
        raise ValueError("paired samples must contain only finite numbers")
    delta = sum(a) / len(a) - sum(b) / len(b)
    if all(x == y for x, y in zip(a, b)):
        return (0.0, 0.0, 0.0)

    import numpy as np
    from scipy.stats import bootstrap

    result = bootstrap(
        (np.asarray(a, dtype=float), np.asarray(b, dtype=float)),
        lambda x, y, axis=-1: np.mean(x, axis=axis) - np.mean(y, axis=axis),
        paired=True,
        vectorized=True,
        n_resamples=n_resamples,
        confidence_level=confidence,
        method="percentile",
        rng=np.random.default_rng(rng),
    )
    return (float(delta), float(result.confidence_interval.low),
            float(result.confidence_interval.high))


def _validate_pass_k(n: int, c: int, k: int) -> None:
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (n, c, k)):
        raise ValueError("n, c, and k must be integers")
    if n < 1 or c < 0 or c > n or k < 1 or k > n:
        raise ValueError("require n >= 1, 0 <= c <= n, and 1 <= k <= n")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_pass_k(n, c, k)
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_pass_k(n, c, k)
    return math.comb(c, k) / math.comb(n, k) if c >= k else 0.0
