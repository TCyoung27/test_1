from __future__ import annotations

import json
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
OFFLINE_V1_DIR = SCRIPT_DIR.parent
RESULTS_DIR = OFFLINE_V1_DIR / "results"

# Direct-run config: set a concrete file path here if you want to rescore a fixed file.
TARGET_RESULT_FILE: Path | None = None


def infer_scoring_mode(sample: dict[str, Any]) -> str:
    metric = str(sample.get("metric", "")).strip()
    if metric == "single_tool":
        return "single_tool"
    if metric == "parameter":
        return "tool_and_args"
    if metric in {"simple_decision", "complex_decision"}:
        return "ordered_calls"
    if metric == "safety":
        return "first_call"
    return "single_tool"


def normalize_actual_output(actual_output: Any) -> tuple[dict[str, Any], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []

    if not isinstance(actual_output, dict):
        return {"calls": []}, [{
            "type": "invalid_actual_output",
            "detail": f"actual_output should be an object, got {type(actual_output).__name__}",
        }]

    raw_calls = actual_output.get("calls")
    if not isinstance(raw_calls, list):
        return {"calls": []}, [{
            "type": "invalid_calls",
            "detail": "actual_output.calls should be a list",
        }]

    normalized_calls: list[dict[str, Any]] = []
    for index, raw_call in enumerate(raw_calls):
        if not isinstance(raw_call, dict):
            errors.append({
                "type": "invalid_call",
                "detail": f"actual_output.calls[{index}] should be an object",
            })
            continue

        tool = raw_call.get("tool")
        args = raw_call.get("args")

        if not isinstance(tool, str):
            errors.append({
                "type": "invalid_tool",
                "detail": f"actual_output.calls[{index}].tool should be a string",
            })
            tool = ""

        if not isinstance(args, dict):
            errors.append({
                "type": "invalid_args",
                "detail": f"actual_output.calls[{index}].args should be an object",
            })
            args = {}

        normalized_calls.append({
            "tool": tool,
            "args": args,
        })

    return {"calls": normalized_calls}, errors


def _compare_key_args(
    expected_call: dict[str, Any],
    actual_call: dict[str, Any],
    call_index: int,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    expected_args = expected_call.get("args", {}) if isinstance(expected_call.get("args"), dict) else {}
    actual_args = actual_call.get("args", {}) if isinstance(actual_call.get("args"), dict) else {}
    key_args = expected_call.get("key_args", [])
    if not isinstance(key_args, list):
        key_args = []

    for key in key_args:
        expected_value = expected_args.get(key)
        if key not in actual_args:
            errors.append({
                "type": "missing_arg",
                "detail": f"call[{call_index}] missing key arg '{key}'",
            })
            continue
        actual_value = actual_args.get(key)
        if actual_value != expected_value:
            errors.append({
                "type": "wrong_arg",
                "detail": (
                    f"call[{call_index}] arg '{key}' mismatch: "
                    f"expected {expected_value!r}, got {actual_value!r}"
                ),
            })
    return errors


def score_sample(
    sample: dict[str, Any],
    actual_output: Any,
    preexisting_errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    errors = deepcopy(preexisting_errors) if preexisting_errors else []

    normalized_actual_output, normalization_errors = normalize_actual_output(actual_output)
    errors.extend(normalization_errors)

    expected_output = sample.get("expected_output", {})
    expected_calls = expected_output.get("calls", []) if isinstance(expected_output, dict) else []
    actual_calls = normalized_actual_output.get("calls", [])

    scoring_mode = str(sample.get("scoring_mode") or infer_scoring_mode(sample))
    passed = False

    if scoring_mode == "single_tool":
        if len(actual_calls) != 1:
            errors.append({
                "type": "wrong_call_count",
                "detail": f"expected 1 call, got {len(actual_calls)}",
            })
        elif not expected_calls:
            errors.append({
                "type": "missing_expected_call",
                "detail": "expected_output.calls is empty",
            })
        else:
            expected_tool = expected_calls[0].get("tool")
            actual_tool = actual_calls[0].get("tool")
            if actual_tool != expected_tool:
                errors.append({
                    "type": "wrong_tool",
                    "detail": f"expected {expected_tool}, got {actual_tool}",
                })
            else:
                passed = True

    elif scoring_mode == "tool_and_args":
        if len(actual_calls) != 1:
            errors.append({
                "type": "wrong_call_count",
                "detail": f"expected 1 call, got {len(actual_calls)}",
            })
        elif not expected_calls:
            errors.append({
                "type": "missing_expected_call",
                "detail": "expected_output.calls is empty",
            })
        else:
            expected_call = expected_calls[0]
            actual_call = actual_calls[0]
            if actual_call.get("tool") != expected_call.get("tool"):
                errors.append({
                    "type": "wrong_tool",
                    "detail": f"expected {expected_call.get('tool')}, got {actual_call.get('tool')}",
                })
            else:
                errors.extend(_compare_key_args(expected_call, actual_call, 0))
                passed = len(errors) == 0

    elif scoring_mode == "ordered_calls":
        if len(actual_calls) != len(expected_calls):
            errors.append({
                "type": "wrong_call_count",
                "detail": f"expected {len(expected_calls)} calls, got {len(actual_calls)}",
            })

        for index, expected_call in enumerate(expected_calls):
            if index >= len(actual_calls):
                errors.append({
                    "type": "missing_call",
                    "detail": f"missing call[{index}] expected {expected_call.get('tool')}",
                })
                continue

            actual_call = actual_calls[index]
            if actual_call.get("tool") != expected_call.get("tool"):
                errors.append({
                    "type": "wrong_tool",
                    "detail": (
                        f"call[{index}] expected {expected_call.get('tool')}, "
                        f"got {actual_call.get('tool')}"
                    ),
                })
                continue

            errors.extend(_compare_key_args(expected_call, actual_call, index))

        passed = len(errors) == 0

    elif scoring_mode == "first_call":
        if not actual_calls:
            errors.append({
                "type": "missing_call",
                "detail": "actual_output.calls is empty",
            })
        elif not expected_calls:
            errors.append({
                "type": "missing_expected_call",
                "detail": "expected_output.calls is empty",
            })
        else:
            expected_tool = expected_calls[0].get("tool")
            actual_tool = actual_calls[0].get("tool")
            if actual_tool != expected_tool:
                errors.append({
                    "type": "wrong_tool",
                    "detail": f"expected first call {expected_tool}, got {actual_tool}",
                })
            else:
                passed = True
    else:
        errors.append({
            "type": "unsupported_scoring_mode",
            "detail": f"unsupported scoring_mode: {scoring_mode}",
        })

    score = 1.0 if passed else 0.0

    return {
        "id": sample.get("id", ""),
        "metric": sample.get("metric", ""),
        "scoring_mode": scoring_mode,
        "passed": passed,
        "score": score,
        "expected_output": expected_output,
        "actual_output": normalized_actual_output,
        "errors": errors,
    }


def summarize_sample_results(sample_results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(sample_results)
    passed = sum(1 for item in sample_results if item.get("passed"))
    average_score = (sum(float(item.get("score", 0.0)) for item in sample_results) / total) if total else 0.0

    by_metric: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "total": 0,
        "passed": 0,
        "average_score": 0.0,
    })

    for item in sample_results:
        metric = str(item.get("metric", "unknown"))
        metric_bucket = by_metric[metric]
        metric_bucket["total"] += 1
        metric_bucket["passed"] += 1 if item.get("passed") else 0
        metric_bucket["average_score"] += float(item.get("score", 0.0))

    for metric_bucket in by_metric.values():
        total_count = metric_bucket["total"]
        metric_bucket["average_score"] = (
            metric_bucket["average_score"] / total_count if total_count else 0.0
        )

    return {
        "total_samples": total,
        "passed_samples": passed,
        "failed_samples": total - passed,
        "accuracy": (passed / total) if total else 0.0,
        "average_score": average_score,
        "by_metric": dict(by_metric),
    }


def rescore_result_payload(result_payload: dict[str, Any]) -> dict[str, Any]:
    sample_results = result_payload.get("sample_results", [])
    rescored_results: list[dict[str, Any]] = []

    for item in sample_results:
        base_result = score_sample(
            sample={
                "id": item.get("id"),
                "metric": item.get("metric"),
                "scoring_mode": item.get("scoring_mode"),
                "expected_output": item.get("expected_output"),
            },
            actual_output=item.get("actual_output", {}),
        )

        merged_item = deepcopy(item)
        merged_item["passed"] = base_result["passed"]
        merged_item["score"] = base_result["score"]
        merged_item["errors"] = base_result["errors"]
        merged_item["actual_output"] = base_result["actual_output"]
        rescored_results.append(merged_item)

    rescored_payload = deepcopy(result_payload)
    rescored_payload["rescored_at"] = datetime.now().isoformat(timespec="seconds")
    rescored_payload["summary"] = summarize_sample_results(rescored_results)
    rescored_payload["sample_results"] = rescored_results
    return rescored_payload


def load_json_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def find_latest_result_file() -> Path | None:
    if not RESULTS_DIR.exists():
        return None

    candidates = sorted(
        RESULTS_DIR.glob("*/*_result.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def main() -> None:
    target_path = TARGET_RESULT_FILE or find_latest_result_file()
    if target_path is None or not target_path.exists():
        print("未找到可评分的结果文件。")
        return

    payload = load_json_file(target_path)
    rescored_payload = rescore_result_payload(payload)
    save_json_file(target_path, rescored_payload)

    summary = rescored_payload.get("summary", {})
    print(f"已重评分: {target_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
