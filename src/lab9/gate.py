"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from numbers import Real
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item


def _threshold_problems(current: dict, previous: dict, label: str) -> list[str]:
    """Check that a metric/slice threshold was not weakened on the same eval set."""
    problems = []
    now, before = current.get("threshold") or {}, previous.get("threshold") or {}
    for direction in ("min", "max"):
        if direction in before and direction not in now:
            problems.append(f"{label}: removed {direction} threshold")
        elif direction in before and direction in now:
            loosened = now[direction] < before[direction] if direction == "min" else now[direction] > before[direction]
            if loosened:
                problems.append(f"{label}: loosened {direction} threshold {before[direction]} -> {now[direction]}")
    if any(k in now for k in ("min", "max")) != any(k in before for k in ("min", "max")):
        problems.append(f"{label}: changed threshold direction")
    if previous.get("blocking") and not current.get("blocking"):
        problems.append(f"{label}: blocking was disabled")
    if before.get("no_significant_drop") and not now.get("no_significant_drop"):
        problems.append(f"{label}: removed no_significant_drop")
    if "max_increase" in before:
        if "max_increase" not in now:
            problems.append(f"{label}: removed max_increase threshold")
        elif now["max_increase"] > before["max_increase"]:
            problems.append(f"{label}: loosened max_increase threshold {before['max_increase']} -> {now['max_increase']}")
    return problems


def _ratchet_problems(spec: dict, base_spec: dict) -> list[str]:
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []  # a new eval-set version gets its own reviewed baseline
    problems = []
    now_metrics = {m["id"]: m for m in spec.get("metrics", [])}
    old_metrics = {m["id"]: m for m in base_spec.get("metrics", [])}
    for mid, old in old_metrics.items():
        if mid not in now_metrics:
            problems.append(f"metric:{mid}: removed from spec")
        else:
            problems.extend(_threshold_problems(now_metrics[mid], old, f"metric:{mid}"))
    now_slices = {(s.get("name"), s.get("metric")): s for s in spec.get("slices", [])}
    old_slices = {(s.get("name"), s.get("metric")): s for s in base_spec.get("slices", [])}
    for key, old in old_slices.items():
        label = f"slice:{key[0]}/{key[1]}"
        if key not in now_slices:
            problems.append(f"{label}: removed from spec")
        else:
            current = now_slices[key]
            # Slice thresholds use top-level min/max rather than a nested threshold map.
            problems.extend(_threshold_problems({**current, "threshold": current},
                                                {**old, "threshold": old}, label))
    return problems


def _basic_report_problems(report: dict, spec: dict, label: str) -> list[str]:
    problems = []
    manifest = report.get("manifest") or {}
    rows = report.get("rows")
    if not isinstance(rows, list):
        return [f"{label}: rows is not a list"]
    seeds = manifest.get("seeds")
    item_count = manifest.get("items")
    if not isinstance(seeds, list) or not seeds or len(seeds) != len(set(seeds)):
        problems.append(f"{label}: invalid or duplicate manifest seeds")
        seeds = []
    if not isinstance(item_count, int) or item_count < 1:
        problems.append(f"{label}: invalid manifest item count")
        item_count = 0
    if len(rows) != item_count * len(seeds):
        problems.append(f"{label}: row count {len(rows)} != items × seeds ({item_count * len(seeds)})")
    keys = [(r.get("item_id"), r.get("seed")) for r in rows]
    if len(set(keys)) != len(keys):
        problems.append(f"{label}: duplicate (item_id, seed) row")
    item_ids = {r.get("item_id") for r in rows}
    if len(item_ids) != item_count:
        problems.append(f"{label}: row item count {len(item_ids)} != manifest items {item_count}")
    expected = {(item_id, seed) for item_id in item_ids for seed in seeds}
    if set(keys) != expected:
        problems.append(f"{label}: row seeds/items do not match the manifest")
    if not isinstance(report.get("evaluator_failures"), list):
        problems.append(f"{label}: evaluator_failures is missing or invalid")
    elif report["evaluator_failures"]:
        problems.append(f"{label}: evaluator_failures is not empty")
    if manifest.get("metric_spec_version") != spec.get("metric_spec_version"):
        problems.append(f"{label}: metric spec version does not match the supplied spec")
    if manifest.get("eval_set_version") not in (None, spec.get("eval_set_version")):
        problems.append(f"{label}: eval-set version does not match the supplied spec")
    eval_path = Path(spec.get("eval_set", ""))
    if eval_path.is_file():
        from lab9.evalset import sha12
        if manifest.get("eval_set_sha") != sha12(eval_path):
            problems.append(f"{label}: eval_set_sha does not match the current eval-set file")

    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        problems.append(f"{label}: metrics is not an object")
        metrics = {}
    for mid, val in metrics.items():
        if not isinstance(val, Real) or isinstance(val, bool) or not math.isfinite(float(val)):
            problems.append(f"{label}: metric {mid} is not a finite number")
    for metric in spec.get("metrics", []):
        mid = metric["id"]
        if mid not in metrics:
            problems.append(f"{label}: missing summary metric {mid}")
        derived = metric.get("grader") in {"lab8.metrics.summarize", "lab9.stats.pass_hat_k"}
        for i, row in enumerate(rows):
            if mid not in row:
                if not derived:
                    problems.append(f"{label}: row {i} is missing graded metric {mid}")
                    break
                continue
            if row[mid] is None:
                problems.append(f"{label}: row {i} has None graded metric {mid}")
                break
            if isinstance(row[mid], float) and not math.isfinite(row[mid]):
                problems.append(f"{label}: row {i} has non-finite metric {mid}")
                break
        vals = [r.get(mid) for r in rows]
        valid_vals = (bool(rows) and all(
            (type(v) is bool) or (isinstance(v, Real) and not isinstance(v, bool) and math.isfinite(float(v)))
            for v in vals
        ))
        if rows and mid in metrics and mid in rows[0] and valid_vals:
            observed = (sum(bool(v) for v in vals) if metric.get("kind") == "safety"
                        else sum(float(v) for v in vals) / len(vals))
            if not math.isclose(float(metrics[mid]), observed, abs_tol=1e-4):
                problems.append(f"{label}: summary metric {mid} does not match its rows")
    if rows and all("reply_observed" in row for row in rows):
        if any(type(row["reply_observed"]) is not bool for row in rows):
            problems.append(f"{label}: reply_observed must be boolean on every row")
        observed_replies = sum(row["reply_observed"] is True for row in rows)
        if manifest.get("reply_trials_observed") != observed_replies:
            problems.append(f"{label}: reply_trials_observed does not match rows")
        if report.get("shape") != "swarm" and any(m["id"] == "reply_amount_matches_ledger" for m in spec.get("metrics", [])) and not observed_replies:
            problems.append(f"{label}: reply grader has no observed reply events")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = _basic_report_problems(pr, spec, "PR")
    problems += _basic_report_problems(base, spec, "baseline")
    if pr.get("manifest", {}).get("eval_set_sha") != base.get("manifest", {}).get("eval_set_sha"):
        problems.append("PR and baseline eval_set_sha differ")
    if pr.get("manifest", {}).get("eval_set_version") != base.get("manifest", {}).get("eval_set_version"):
        problems.append("PR and baseline eval_set_version differ")

    pr_rows, base_rows = pr.get("rows") or [], base.get("rows") or []
    pr_keys = {(r.get("item_id"), r.get("seed")) for r in pr_rows}
    base_keys = {(r.get("item_id"), r.get("seed")) for r in base_rows}
    if pr_keys != base_keys:
        problems.append("PR (item_id, seed) rows differ from baseline")
    base_by_item = {r.get("item_id"): r.get("slices") or [] for r in base_rows}
    for row in pr_rows:
        if (row.get("slices") or []) != base_by_item.get(row.get("item_id"), []):
            problems.append(f"item {row.get('item_id')}: slice tags differ from baseline")
            break

    if base_spec is not None:
        problems += _ratchet_problems(spec, base_spec)

    # Reports are evidence, not a place to edit a score by hand. Where the summary
    # is derived directly from row values, verify it against those rows.
    try:
        metric_ids = [m["id"] for m in spec.get("metrics", []) if pr_rows and m["id"] in pr_rows[0]]
        recomputed = (aggregate(pr_rows, metric_ids, k_values=spec.get("pass_k", []))
                      if pr_rows and all("cost" in row for row in pr_rows) else {})
        for mid, val in recomputed.items():
            if mid in (pr.get("metrics") or {}) and val is not None:
                if not math.isclose(float(pr["metrics"][mid]), float(val), abs_tol=1e-4):
                    problems.append(f"PR: summary metric {mid} does not match rows")
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        problems.append("PR: could not recompute report metrics from rows")
    return sorted(set(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        current, previous = per_item(pr, metric, name), per_item(base, metric, name)
        keys = sorted(set(current) & set(previous))
        verdicts = []
        mean = sum(current.values()) / len(current) if current else None
        note = ""
        if not keys:
            verdicts.append("missing slice data")
        if mean is not None and "min" in rule and mean < rule["min"]:
            verdicts.append(f"mean {mean:.3f} < min {rule['min']}")
        if rule.get("no_significant_drop") and keys:
            d, lo, hi = stats.paired_bootstrap(
                [current[k] for k in keys], [previous[k] for k in keys],
                n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
            )
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdicts.append("significant drop")
        label = f"slice:{name}/{metric}"
        if verdicts and rule.get("blocking"):
            blocked.append(label)
        status = "BLOCK" if verdicts and rule.get("blocking") else "warn" if verdicts else "ok"
        lines.append(f"  {label:<36} {mean!s:<8} {note:<28} {status}" +
                     (f" ({'; '.join(verdicts)})" if verdicts else ""))
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
