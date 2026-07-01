from __future__ import annotations

from typing import Any


def empty_standard_metrics() -> dict[str, Any]:
    return {
        "throughput_tok_s": None,
        "ttft_ms": None,
        "p99_latency_ms": None,
        "memory_peak_mb": None,
        "gpu_util_avg_pct": None,
        "cost_per_1m_tokens_usd": None,
        "quality_delta_pct": None,
    }


def merge_metrics(standard: dict[str, Any], plugin: dict[str, Any]) -> dict[str, Any]:
    base = empty_standard_metrics()
    base.update({k: v for k, v in standard.items() if k in base})
    return {"standard": base, "plugin": plugin}


def flatten_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in metrics.get("standard", {}).items():
        flat[key] = value
        flat[f"standard.{key}"] = value
    for key, value in metrics.get("plugin", {}).items():
        flat[f"plugin.{key}"] = value
    return flat


def evaluate_thresholds(
    metrics: dict[str, Any],
    thresholds: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    flat = flatten_metrics(metrics)
    checks: dict[str, Any] = {}
    all_pass = True

    for name, rule in thresholds.items():
        op = rule["op"]
        expected = rule.get("value")
        actual = flat.get(name)

        if op == "exists":
            passed = actual is not None
        elif actual is None:
            passed = False
        elif op == "gte":
            passed = actual >= expected
        elif op == "lte":
            passed = actual <= expected
        elif op == "eq":
            passed = actual == expected
        elif op == "neq":
            passed = actual != expected
        else:
            passed = False

        checks[name] = {
            "op": op,
            "expected": expected,
            "actual": actual,
            "passed": passed,
        }
        if not passed:
            all_pass = False

    return {"passed": all_pass, "checks": checks}
