#!/usr/bin/env python3
"""PreToolUse Hook: 拦截 git commit，验证测试和质量检查通行证"""

import json
import re
import sys
from pathlib import Path


ARTIFACTS_DIR = ".claude/artifacts"
QUALITY_THRESHOLD = 75


def get_git_head():
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def check_test_cert(base: Path, head: str) -> list[str]:
    errors = []
    cert = base / ARTIFACTS_DIR / "test-result.json"

    if not cert.exists():
        errors.append("  - 缺少测试通行证 (test-result.json)")
        return errors

    try:
        data = json.loads(cert.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        errors.append("  - 测试通行证损坏，无法读取")
        return errors

    if not data.get("passed"):
        errors.append(
            f"  - 测试未通过 ({data.get('tests_passed', 0)}/{data.get('tests_total', 0)} 通过)"
        )

    if data.get("git_head") != head:
        errors.append("  - 测试通行证过期（代码已变更，请重新运行 @gitcommit-agent）")

    return errors


def check_quality_cert(base: Path, head: str) -> list[str]:
    errors = []
    cert = base / ARTIFACTS_DIR / "quality-result.json"

    if not cert.exists():
        errors.append("  - 缺少质量通行证 (quality-result.json)")
        return errors

    try:
        data = json.loads(cert.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        errors.append("  - 质量通行证损坏，无法读取")
        return errors

    score = data.get("overall_score", 0)
    if not data.get("passed"):
        errors.append(
            f"  - 质量评分不足 ({score}/100, 需要 ≥ {QUALITY_THRESHOLD})"
        )

    if data.get("git_head") != head:
        errors.append("  - 质量通行证过期（代码已变更，请重新运行 @gitcommit-agent）")

    return errors


def has_git_commit(command: str) -> bool:
    """检测命令中是否包含 git commit，包括复合命令（&& ; || 换行）"""
    segments = re.split(r'&&|;|\|\||\n', command)
    for seg in segments:
        seg = seg.strip()
        # 匹配 "git commit" 开头，排除 git commit-tree/graph 等子命令
        if re.search(r'^git\s+commit\b', seg) and not re.search(r'^git\s+commit-(?:tree|graph)', seg):
            return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "").strip()

    # Intercept git commit in plain or compound commands (but not commit-tree/graph)
    if not has_git_commit(command):
        sys.exit(0)

    base = Path.cwd()
    head = get_git_head()

    if not head:
        # No commits yet — allow first commit without checks
        sys.exit(0)

    errors = check_test_cert(base, head) + check_quality_cert(base, head)

    if errors:
        msg = (
            "\n"
            "⛔  [提交拦截] 以下检查未通过:\n"
            + "\n".join(errors)
            + "\n\n"
            "请运行 @gitcommit-agent 完成测试和质量检查后再提交。\n"
        )
        print(msg, file=sys.stderr)
        sys.exit(2)

    # Read certificate data for display before cleanup
    try:
        test_data = json.loads(
            (base / ARTIFACTS_DIR / "test-result.json").read_text(encoding="utf-8")
        )
        quality_data = json.loads(
            (base / ARTIFACTS_DIR / "quality-result.json").read_text(encoding="utf-8")
        )
        test_passed = f"{test_data.get('tests_passed', '?')}/{test_data.get('tests_total', '?')}"
        quality_score = quality_data.get("overall_score", "?")
    except Exception:
        test_passed = "?"
        quality_score = "?"

    # Clean up certificates so next commit needs fresh checks
    try:
        (base / ARTIFACTS_DIR / "test-result.json").unlink(missing_ok=True)
        (base / ARTIFACTS_DIR / "quality-result.json").unlink(missing_ok=True)
    except OSError:
        pass

    print(
        f"\n✅  [提交检查] 全部通过 — 测试 {test_passed}, 质量 {quality_score}/100\n",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
