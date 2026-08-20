#!/usr/bin/env python3
"""List/check module names. Does not choose the next module.

  python ~/.claude/skills/bin/modules.py list
  python ~/.claude/skills/bin/modules.py show privesc-win
  python ~/.claude/skills/bin/modules.py tail privesc-win
  python ~/.claude/skills/bin/modules.py check ad-recon
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YAML = ROOT / "shared" / "modules.yaml"

USAGE = """usage:
  modules.py list
  modules.py show <模块>
  modules.py tail <模块>
  modules.py check <模块> [模块...]
不要把子命令用 | 连在一起。"""


def parse(text: str) -> dict:
    modules: dict[str, dict] = {}
    cur = None
    in_mod = False
    for raw in text.splitlines():
        if raw.startswith("modules:"):
            in_mod = True
            continue
        if not in_mod:
            continue
        m = re.match(r"^  ([a-z0-9-]+):\s*$", raw)
        if m:
            cur = m.group(1)
            modules[cur] = {}
            continue
        if cur is None:
            continue
        kv = re.match(r"^    (success|kind):\s*(.+)$", raw)
        if kv:
            modules[cur][kv.group(1)] = kv.group(2).strip()
            continue
        lst = re.match(r"^    (default_next|never_default):\s*\[(.*)\]\s*$", raw)
        if lst:
            inner = lst.group(2).strip()
            modules[cur][lst.group(1)] = [
                x.strip() for x in inner.split(",") if x.strip()
            ]
    return modules


def main() -> int:
    if not YAML.is_file():
        print(f"missing {YAML}", file=sys.stderr)
        return 2
    mods = parse(YAML.read_text())
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0 if args else 2
    cmd = args[0]
    if cmd in ("list", "-l"):
        for name, d in mods.items():
            print(f"/{name}\t{d.get('success', '')}")
        return 0
    if cmd == "show" and len(args) == 2:
        name = args[1].lstrip("/")
        if name not in mods:
            print(f"unknown module: {name}", file=sys.stderr)
            return 1
        d = mods[name]
        print(f"/{name}")
        print(f"success: {d.get('success', '')}")
        print("default_next: " + ", ".join("/" + x for x in d.get("default_next", [])))
        print("never_default: " + (", ".join("/" + x for x in d.get("never_default", [])) or "(none)"))
        return 0
    if cmd == "check":
        if len(args) < 2:
            print(USAGE, file=sys.stderr)
            return 2
        bad = False
        for n in args[1:]:
            n = n.lstrip("/")
            if n not in mods:
                print(f"FAIL {n}", file=sys.stderr)
                bad = True
            else:
                print(f"OK /{n}")
        return 1 if bad else 0
    if cmd == "tail" and len(args) == 2:
        name = args[1].lstrip("/")
        if name not in mods:
            print(f"unknown module: {name}", file=sys.stderr)
            return 1
        if name == "edr-bypass":
            print("edr-bypass: 回原模块把链打完。不要 /clear。不要建议新模块。")
            return 0
        d = mods[name]
        nxt = d.get("default_next") or []
        never = d.get("never_default") or []
        print(f"优先候选（/{name} default_next，已去掉 never_default）：")
        shown = False
        for x in nxt:
            if x not in never:
                print(f"- /{x}")
                shown = True
        if not shown:
            print("- （无优先候选，凭 notes 从名册里建议）")
        if never:
            print("never_default（不当默认；操作者点名除外）： " + ", ".join("/" + x for x in never))
        print("名册外的名字不许建议。停。等操作者选 /模块 或 /clear。")
        return 0
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
