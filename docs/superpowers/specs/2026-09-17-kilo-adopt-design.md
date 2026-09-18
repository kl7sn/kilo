# spec: `/kilo adopt <path>`

Date: 2026-09-17  
Line: 05-run/05.05-koli-continuous-optimization  
Status: approved (design-review R2)

## Goal

给 `/kilo` 补一条正式命令：把**已经存在**的本仓 git worktree 登记成**当前线的主 worktree**。

典型现场：这条线还开着，旧树已经 merge 并删掉（`pruned` 或 `missing`），外面又开了一棵新树（例如 Orca/koli），需要挂回同一条线，而不是 `/kilo new`。

## Non-goals

- 不改成「同时多棵主树」。一条线一生可以挂过多棵树，**同一时刻只有一棵主树**。
- 不在 active / smoke_pending / ready_to_merge 时替换主树。
- 不 `git worktree add`、不创建目录、不 prune 旧路径。
- 不换会话绑定（那是 `/kilo bind`）。
- 不另做 CLI / 无 path 的交互挑选。
- 不把别的 koli 改进塞进本线。

## Command

```text
/kilo adopt <path>
```

显式子命令，在相位检测之前处理。`<path>` 必填，解析成绝对路径后再比。

## Preconditions (all required)

1. 本会话已绑定一条 open line。未绑定 → 走新会话 bind 提示，不 adopt。
2. Handoff `worktree_status` ∈ `{missing, none, pruned}`。
3. `<path>` 出现在本仓 `git worktree list --porcelain`（按 path 精确匹配解析后的绝对路径）。
4. 本仓 `.kilo-state` 里没有任何**其它** line 把该 path 当作**当前主目录**。当前主目录 = 该条目 `worktree_status` ∈ `{active, smoke_pending, ready_to_merge}` 且 `worktree_path` 解析后等于 `<path>`。`pruned` / `missing` / `none` 上留下的旧 path **不算**当前主目录，adopt 可以挂走。

## Effects (success)

Adopt 挂的是**新的主树**，上一棵树的集成状态作废，不得带着旧 smoke/disposition 去关闭这条线。

1. Handoff：
   - `worktree_path` = 绝对 path
   - `worktree_branch` = 该 worktree 当前分支（porcelain `branch`）
   - `worktree_status` = `active`
   - `worktree_git_status` = 该目录 `git status`（clean / dirty）
   - `commit_status` = uncommitted（新主树尚未作为本线交付提交；已有 commits 也不算本线已 merge）
   - `smoke_status` = pending
   - `integration_next` = none
   - `blocker` = none（若原先是 worktree-missing）
   - `binding_decision` = continue-current
2. 仓库 `.kilo-state` 当前 `projects[]` 条目的 `worktree_path` / `worktree_branch` 与 Handoff 一致。
3. 父 `project.md` 本线一行：Worktree / Branch / State=`active`。
4. 执行日志记一行：adopt 了哪个 path@branch，旧 status 是什么，以及 smoke/integration/commit 已重置。
5. 再跑双向 worktree 核对（orphan / missing）。刚登记的 path 对本线不再是 orphan。

不改 git 对象、不 checkout、不删旧分支。

## Failures (stop, no state writes)

| 条件 | 行为 |
| --- | --- |
| 未绑定 | 新会话 bind 提示 |
| 没给 path | 用法：`/kilo adopt <path>`，停 |
| status 为 active / smoke_pending / ready_to_merge | 拒绝：已有主树。换树需先把当前主树处置到 pruned/missing/none |
| path 不在本仓 `git worktree list` | 拒绝：只登记已有 git 目录 |
| path 已是其它线的当前主目录 | 拒绝：不抢。判定见 Preconditions 第 4 条 |
| missing 时未写 adopt 就用主仓 | 仍禁止。只有用户写出 `/kilo adopt <主仓path>` 才登记主仓 |

## Prompt wiring

- **missing 提示**第 2 项改为：`/kilo adopt <path>`（用户给出的已有路径）。
- **orphan 核对**：仅当当前线 status ∈ `{missing, none, pruned}` 时，才把「认领到当前线」说成 `/kilo adopt <path>`。当前线已有 active 主树时，orphan 只能 keep / 授权后 prune / 绑到别的线，不能 adopt 到本线。
- **集成闸门**：树已 prune、线仍 open 时，下一棵树用 `/kilo adopt <path>`，不必 `/kilo new`。选项 3 仍是新 line；adopt 不是新线。
- **execute 预改代码闸**：任务要改代码且 `worktree_status` ∈ `{none, pruned, missing}` 时，**停下来要求 `/kilo adopt <path>`**（path 已在 `git worktree list`）。禁止把「同一条线接下棵树」做成 `/kilo new`，也禁止 missing 时悄悄用主仓。`/kilo new` 只用于新 line。

## Files to change (product)

Primary worktree: `.worktrees/05.05-koli-continuous-optimization`

| File | Change |
| --- | --- |
| `skills/kilo/SKILL.md` | 命令表加 `/kilo adopt <path>`；必要时在 startup 第 2 步点名子命令 |
| `skills/kilo/protocols/workspace.md` | 新增 `/kilo adopt` 节（前置、效果、失败） |
| `skills/kilo/protocols/recover.md` | missing/orphan 指向该命令 |
| `skills/kilo/protocols/reference.md` | missing 标准提示第 2 项；命令相关 hard block 如需 |
| `skills/kilo/protocols/execute.md` | 集成闸门：pruned + 线仍 open → adopt 下一棵树。预改代码闸：none/pruned/missing 时先 `/kilo adopt`，不要 `/kilo new`、不要回退主仓 |
| `README.md` / `README_CN.md` | 命令列表各加一行 |

不改模板字段名和 Handoff 枚举（不增加「多主树」列表）。

## Pass bar

人工冒烟（测试全绿不算通过；本仓也没有测试套件）：

1. 命令表和 missing 提示都能看到 `/kilo adopt <path>`。
2. 协议写明：active 主树时拒绝 adopt。
3. 在 `pruned` 或 `missing` 下，对已出现在 `git worktree list` 的 path 执行 adopt 后：Handoff、`.kilo-state`、`project.md` 三处主树一致，`worktree_status=active`。
4. 对未在 `git worktree list` 的 path、以及已有 active 主树时执行 adopt，状态文档不被改写。
5. adopt 成功后 `smoke_status=pending` 且 `integration_next=none`，不得沿用上一棵树的 smoke/disposition。

## Invariants kept

- 一会话 ↔ 一线 ↔ **一棵主树**
- 代码改动只在主 worktree
- missing 时禁止悄悄回退主仓
