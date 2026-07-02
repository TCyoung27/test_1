from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

SCRIPT_DIR = Path(__file__).resolve().parent
OFFLINE_V1_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = OFFLINE_V1_DIR.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.assistant import SmartAssistant  # noqa: E402
from scorer import score_sample, summarize_sample_results  # noqa: E402


DATASETS_DIR = OFFLINE_V1_DIR / "datasets"
PROMPTS_DIR = OFFLINE_V1_DIR / "prompts"
RESULTS_DIR = OFFLINE_V1_DIR / "results"

# Direct-run config.
# DATASET_NAME = "single_tool"
# DATASET_NAME = "parameter"
# DATASET_NAME = "safety"
# DATASET_NAME = "simple_decision"
DATASET_NAME = "complex_decision"
BASE_PROMPT_FILE = PROMPTS_DIR / "base_prompt.txt"
MODE_PROMPT_FILE = PROMPTS_DIR / f"{DATASET_NAME}_prompt.txt"
DATASET_FILE = DATASETS_DIR / f"{DATASET_NAME}.json"
USER_MESSAGE_SUFFIX = (
    "请根据以上信息完成离线规划。\n"
    "如果你需要先确认真实工具名，必须先调用 load_skill。\n"
    "最后一条回复必须只包含最终工具调用计划 JSON。"
)


@contextmanager
def project_root_workdir():
    """
    临时切换到项目根目录，确保 MCP 相对路径按项目本体启动。
    """
    original_cwd = Path.cwd()
    os.chdir(PROJECT_ROOT)
    try:
        yield
    finally:
        os.chdir(original_cwd)


def load_text_file(path: Path) -> str:
    """读取 UTF-8 文本文件，并兼容 BOM。"""
    return path.read_text(encoding="utf-8").lstrip("\ufeff").strip()


def load_json_file(path: Path) -> dict[str, Any]:
    """读取 JSON 文件。"""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json_file(path: Path, payload: dict[str, Any]) -> None:
    """将结果 JSON 原子性较强地写回到目标路径。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def build_result_payload(
    dataset_payload: dict[str, Any],
    run_id: str,
    run_timestamp: datetime,
    sample_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """组装当前评估运行的完整结果结构。"""
    return {
        "schema_version": dataset_payload.get("schema_version", "v1"),
        "dataset_name": dataset_payload.get("dataset_name", DATASET_NAME),
        "description": dataset_payload.get("description", ""),
        "run_id": run_id,
        "generated_at": run_timestamp.isoformat(timespec="seconds"),
        "dataset_file": str(DATASET_FILE),
        "base_prompt_file": str(BASE_PROMPT_FILE),
        "mode_prompt_file": str(MODE_PROMPT_FILE),
        "summary": summarize_sample_results(sample_results),
        "sample_results": sample_results,
    }


def persist_result_file(
    result_file: Path,
    dataset_payload: dict[str, Any],
    run_id: str,
    run_timestamp: datetime,
    sample_results: list[dict[str, Any]],
) -> None:
    """将当前进度落盘，支持中途终止后保留已完成样本。"""
    save_json_file(
        result_file,
        build_result_payload(
            dataset_payload=dataset_payload,
            run_id=run_id,
            run_timestamp=run_timestamp,
            sample_results=sample_results,
        ),
    )


def build_eval_system_prompt() -> str:
    """拼接基础 prompt 和当前指标 prompt。"""
    base_prompt = load_text_file(BASE_PROMPT_FILE)
    mode_prompt = load_text_file(MODE_PROMPT_FILE)
    return f"{base_prompt}\n\n{mode_prompt}".strip()


def build_user_message(sample: dict[str, Any]) -> str:
    """将样本转成统一的用户输入文本。"""
    user_instruction = sample.get("user_instruction", "")
    initial_state = sample.get("initial_state", {})
    initial_state_json = json.dumps(initial_state, ensure_ascii=False, indent=2)

    return (
        f"用户指令：\n{user_instruction}\n\n"
        f"初始状态：\n{initial_state_json}\n\n"
        f"{USER_MESSAGE_SUFFIX}"
    )


def message_content_to_text(content: Any) -> str:
    """将 LangChain message.content 归一化为纯文本，便于存档和解析。"""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text_part = item.get("text")
                if isinstance(text_part, str):
                    parts.append(text_part)
                    continue
            parts.append(str(item))
        return "\n".join(part for part in parts if part)

    if content is None:
        return ""

    return str(content)


def serialize_message(message: Any) -> dict[str, Any]:
    """将 LangChain message 压平成便于调试和落盘的字典结构。"""
    payload: dict[str, Any] = {
        "type": getattr(message, "type", message.__class__.__name__),
        "content": message_content_to_text(getattr(message, "content", "")),
    }

    name = getattr(message, "name", None)
    if name:
        payload["name"] = name

    tool_call_id = getattr(message, "tool_call_id", None)
    if tool_call_id:
        payload["tool_call_id"] = tool_call_id

    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        payload["tool_calls"] = tool_calls

    invalid_tool_calls = getattr(message, "invalid_tool_calls", None)
    if invalid_tool_calls:
        payload["invalid_tool_calls"] = [str(item) for item in invalid_tool_calls]

    additional_kwargs = getattr(message, "additional_kwargs", None)
    if additional_kwargs:
        payload["additional_kwargs"] = additional_kwargs

    response_metadata = getattr(message, "response_metadata", None)
    if response_metadata:
        payload["response_metadata"] = response_metadata

    return payload


def extract_json_object_from_text(text: str) -> str | None:
    """从最终 AI 文本中提取最可能的 JSON 对象片段。"""
    stripped = text.strip()
    if not stripped:
        return None

    fenced_markers = ("```json", "```JSON", "```")
    for marker in fenced_markers:
        if marker in stripped:
            parts = stripped.split(marker)
            for part in parts:
                candidate = part.strip()
                if candidate.startswith("{") and candidate.endswith("}"):
                    return candidate

    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    start = stripped.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(stripped)):
        char = stripped[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped[start:index + 1]

    return None


def sanitize_calls_payload(payload: Any) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """校验并归一化最终 `calls` JSON 结构。"""
    errors: list[dict[str, str]] = []

    if not isinstance(payload, dict):
        return {"calls": []}, [{
            "type": "invalid_json_payload",
            "detail": f"parsed payload should be an object, got {type(payload).__name__}",
        }]

    raw_calls = payload.get("calls")
    if not isinstance(raw_calls, list):
        return {"calls": []}, [{
            "type": "missing_calls",
            "detail": "parsed JSON does not contain a valid calls array",
        }]

    sanitized_calls: list[dict[str, Any]] = []
    for index, raw_call in enumerate(raw_calls):
        if not isinstance(raw_call, dict):
            errors.append({
                "type": "invalid_call",
                "detail": f"calls[{index}] should be an object",
            })
            continue

        tool = raw_call.get("tool")
        args = raw_call.get("args")

        if not isinstance(tool, str):
            errors.append({
                "type": "invalid_tool",
                "detail": f"calls[{index}].tool should be a string",
            })
            tool = ""

        if not isinstance(args, dict):
            errors.append({
                "type": "invalid_args",
                "detail": f"calls[{index}].args should be an object",
            })
            args = {}

        sanitized_calls.append({
            "tool": tool,
            "args": args,
        })

    return {"calls": sanitized_calls}, errors


def extract_final_plan_from_messages(messages: list[Any]) -> tuple[dict[str, Any], str, list[dict[str, str]]]:
    """从整轮消息中倒序提取最后一个可评分的 JSON 计划。"""
    for message in reversed(messages):
        message_type = getattr(message, "type", "")
        if message_type != "ai":
            continue

        raw_text = message_content_to_text(getattr(message, "content", ""))
        candidate = extract_json_object_from_text(raw_text)
        if not candidate:
            continue

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            return {"calls": []}, raw_text, [{
                "type": "json_decode_error",
                "detail": f"failed to parse final AI JSON: {exc}",
            }]

        sanitized_output, sanitize_errors = sanitize_calls_payload(parsed)
        return sanitized_output, raw_text, sanitize_errors

    return {"calls": []}, "", [{
        "type": "no_valid_json_output",
        "detail": "no AI message containing a valid JSON plan was found",
    }]


async def run_single_sample(
    assistant: SmartAssistant,
    system_prompt_text: str,
    sample: dict[str, Any],
) -> dict[str, Any]:
    """运行单条样本，并返回可直接写入结果文件的记录。"""
    agent = assistant.create_agent(
        system_prompt=SystemMessage(content=system_prompt_text),
        expose_skill_tools=False,
    )
    thread_id = f"{sample.get('id', 'sample')}-{uuid.uuid4()}"

    result = await agent.ainvoke(
        {
            "messages": [HumanMessage(content=build_user_message(sample))]
        },
        config={"configurable": {"thread_id": thread_id}},
    )

    messages = result.get("messages", [])
    message_trace = [serialize_message(message) for message in messages]
    actual_output, final_ai_text, parse_errors = extract_final_plan_from_messages(messages)

    scored = score_sample(sample=sample, actual_output=actual_output, preexisting_errors=parse_errors)

    return {
        "id": sample.get("id", ""),
        "metric": sample.get("metric", ""),
        "scoring_mode": sample.get("scoring_mode", ""),
        "user_instruction": sample.get("user_instruction", ""),
        "initial_state": sample.get("initial_state", {}),
        "expected_output": sample.get("expected_output", {}),
        "actual_output": scored["actual_output"],
        "passed": scored["passed"],
        "score": scored["score"],
        "errors": scored["errors"],
        "final_ai_text": final_ai_text,
        "message_trace": message_trace,
        "thread_id": thread_id,
    }


async def evaluate_dataset() -> Path:
    """执行当前数据集评估，并持续将中间进度写入结果文件。"""
    dataset_payload = load_json_file(DATASET_FILE)
    system_prompt_text = build_eval_system_prompt()
    print(system_prompt_text)
    run_timestamp = datetime.now()
    run_id = run_timestamp.strftime("%Y-%m-%d_%H%M%S")
    result_dir = RESULTS_DIR / run_id
    result_file = result_dir / f"{DATASET_NAME}_result.json"

    assistant: SmartAssistant | None = None
    sample_results: list[dict[str, Any]] = []

    persist_result_file(
        result_file,
        dataset_payload=dataset_payload,
        run_id=run_id,
        run_timestamp=run_timestamp,
        sample_results=sample_results,
    )
    print(f"结果文件初始化完成: {result_file}")

    with project_root_workdir():
        try:
            assistant = await SmartAssistant.create()
            for sample in dataset_payload.get("samples", []):
                sample_result = await run_single_sample(
                    assistant=assistant,
                    system_prompt_text=system_prompt_text,
                    sample=sample,
                )
                sample_results.append(sample_result)
                persist_result_file(
                    result_file,
                    dataset_payload=dataset_payload,
                    run_id=run_id,
                    run_timestamp=run_timestamp,
                    sample_results=sample_results,
                )
                print(
                    f"[{sample_result['id']}] "
                    f"passed={sample_result['passed']} "
                    f"score={sample_result['score']}"
                )
        finally:
            if assistant is not None:
                await assistant.shutdown()

    persist_result_file(
        result_file,
        dataset_payload=dataset_payload,
        run_id=run_id,
        run_timestamp=run_timestamp,
        sample_results=sample_results,
    )
    return result_file


def main() -> None:
    """直接运行当前配置的数据集评估。"""
    result_file = asyncio.run(evaluate_dataset())
    print(f"评估完成，结果已保存到: {result_file}")


if __name__ == "__main__":
    main()
