#!/usr/bin/env python3
"""Stop Hook: 交付验收 — 修改代码后必须完成验证才能结束会话"""

import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    messages = data.get("messages", [])

    files_modified = False
    all_assistant_text = ""
    all_tool_result_text = ""

    modify_tools = {"Edit", "Write", "NotebookEdit"}

    verify_keywords = [
        # 中文
        "测试", "验证", "检查", "lint", "typecheck", "类型检查",
        "todo", "TODO", "功能验证",
        # 英文 / 工具名
        "pytest", "npm test", "npm run test", "go test", "cargo test",
        "eslint", "prettier", "mypy", "tsc", "ruff", "flake8",
        "jest", "vitest", "playwright",
        "build", "构建成功", "pass", "passed", "通过",
        "确认无误", "验证通过", "检查通过", "全部通过",
        # 明确声明
        "已完成验证", "验证完成", "verified", "verification",
    ]

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        # Collect assistant text responses
        if role == "assistant":
            if isinstance(content, str):
                all_assistant_text += content + " "
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        all_assistant_text += block.get("text", "") + " "
                    elif isinstance(block, dict) and block.get("type") == "tool_use":
                        if block.get("name") in modify_tools:
                            files_modified = True

        # Collect tool result text (test output, etc.)
        if role == "user" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    result_content = block.get("content", "")
                    if isinstance(result_content, str):
                        all_tool_result_text += result_content + " "
                    elif isinstance(result_content, list):
                        for rc in result_content:
                            if isinstance(rc, dict) and rc.get("type") == "text":
                                all_tool_result_text += rc.get("text", "") + " "

    combined_text = (all_assistant_text + " " + all_tool_result_text).lower()

    # Check if verification was done (keywords appear together with tool result
    # indicating actual execution, not just mention)
    verification_done = False
    for kw in verify_keywords:
        if kw.lower() in combined_text:
            verification_done = True
            break

    if files_modified and not verification_done:
        print(
            "\n"
            "⚠️  [交付验收] "
            "本轮修改了代码/配置/文件，"
            "但未检测到验证结果！\n"
            "\n"
            "请继续完成以下验证后再结束：\n"
            "  1. 测试 (test/pytest/npm test/...)\n"
            "  2. 代码检查 (lint/typecheck/eslint/mypy/...)\n"
            "  3. 功能验证或 TODO 检查\n"
            "\n"
            "完成验证后告知结果，再次尝试结束。\n",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
