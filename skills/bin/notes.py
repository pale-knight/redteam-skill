#!/usr/bin/env python3
"""Init ./notes.md in the engagement cwd. Never writes into the skill pack.

  python ~/.claude/skills/bin/notes.py init      # 已有则不动
  python ~/.claude/skills/bin/notes.py validate  # 收尾可选
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

TEMPLATE = """## 目标
- 范围/授权:
- 入口: IP/域名/云账号

## 已拿下
- 主机 / 权限 / 怎么拿到的 / 会话（webshell URL | rev 口 | RDP）
- 当前模块:

## 凭据
- user:pass|NT|token （来源:） ⚠️未校验 / ✅已校验

## 攻击机
- 监听: 端口/工具 （你开的）
- 代理:

## 攻击面
-

## RESTORE
-

## 待跟进
-
"""

USAGE = """usage:
  notes.py init       # cwd = 作战目录，已有 notes.md 不覆盖
  notes.py validate
必须在靶场目录跑，不要在 ~/.claude/skills 里跑。"""

PLACEHOLDER = re.compile(
    r"^(?:-?\s*)(?:主机 / 权限.*|当前模块:?|user:pass.*|范围/授权:?|入口:.*)?\s*$"
)


def _section(text: str, heading: str) -> str:
    pat = re.compile(rf"^## {re.escape(heading)}\s*$", re.M)
    m = pat.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def _has_fact(section: str) -> bool:
    for line in section.splitlines():
        s = line.strip()
        if not s or s == "-":
            continue
        if PLACEHOLDER.match(s):
            continue
        return True
    return False


def main() -> int:
    notes = Path.cwd() / "notes.md"
    cmd = sys.argv[1] if len(sys.argv) > 1 else "init"
    if cmd in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    if cmd == "init":
        if notes.exists():
            print(f"exists, not overwritten: {notes}")
            return 0
        notes.write_text(TEMPLATE, encoding="utf-8")
        print(f"created {notes}")
        return 0
    if cmd == "validate":
        if not notes.is_file():
            print("missing ./notes.md", file=sys.stderr)
            return 1
        t = notes.read_text(encoding="utf-8")
        bad = False
        if "## 已拿下" not in t:
            print("missing ## 已拿下", file=sys.stderr)
            bad = True
        elif not _has_fact(_section(t, "已拿下")):
            print("## 已拿下 is empty (template only)", file=sys.stderr)
            bad = True
        if re.search(r"\bCOMPLETE\b", t) and "## RESTORE" not in t:
            print("COMPLETE without ## RESTORE", file=sys.stderr)
            bad = True
        if bad:
            return 1
        print("ok")
        return 0
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
