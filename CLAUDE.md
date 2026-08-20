# pale0knight

半自动、人工选题。只打当前 `/模块` 直到成功条件。不是 agent。不能替你输密码、开监听、点确认。
Attack 打到对应权限。无稳定公开 PoC 不编命令。

本目录：`CLAUDE.md` + `./notes.md`。助手只写 `./notes.md`。

```text
全局 ~/.claude/skills/<模块>/SKILL.md
     ~/.claude/skills/shared/modules.yaml
     ~/.claude/skills/bin/modules.py
     ~/.claude/skills/bin/notes.py
```

禁止：`./modules.yaml`、`python ../bin/...`（相对的是本靶场上一级，不是 skill）。

```text
开局  Read ./notes.md
      没有 → python ~/.claude/skills/bin/notes.py init
打    走到分支才 Read 当前 skill 的 references/ 一份
      要人动手 → 立刻停，说明等你做什么，等回报。不要假装已成功。
      半路别的面只记 notes，不跳模块
收尾  追加 ./notes.md
      python ~/.claude/skills/bin/modules.py tail <当前模块名>
      优先 default_next；never_default 不当默认（你点名除外）
      名册外的名字不许建议 → 停
你    选 /模块 或 /clear
```

`/edr-bypass`：回原模块。不要 `/clear`，不要 `tail`。

- 不自动切模块；不读 notes 不许当新目标开打
- SYSTEM → 默认 `/ad-recon`，不要默认 `/ad-attack`
- 云身份 → 默认 `/cloud-recon`
- 「命令已写出」≠ 已拿下；没监听不弹 shell
- recon 不 exploit；Kerberoast 要票+砸+用留 `/ad-attack`
