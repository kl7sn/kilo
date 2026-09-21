# spec: `/kilo up`

Date: 2026-09-21  
Line: 05-run/05.06-kilo-up  
Status: settled

## Goal

给 `/kilo` 增加显式命令 `/kilo up`：识别当前对话里可沉淀的操作经验，分到三层，**先列出再写入**（skill 默认不新建）。

## Non-goals

- 不把 05.04 拿掉的 bundled `up` skill 装回 kilo 安装包。
- 不把长命令写进 `spec.md`（spec 仍是设计合同）。
- 不默认用 `kilo-` 前缀建 skill。
- 不把密钥、token、具体 AK/SK 写入任何状态文档。
- 不自动关 05.05。

## Command

```text
/kilo up
```

相位检测之前处理。必须已绑定 open line。

## Classification (highest matching level, then stop)

1. **Line / project（单 project）**  
   绑环境：集群、context、pod、端口、alias、桶名、本仓路径。  
   长步骤 → 该 line 可选 `ops.md`（没有就不建）。  
   `context.md` `## Gotchas` 只留一行指针。  
   `project.md`：能验证的短句进 `## Stable Facts`；坑进 `## Gotcha Index`，指针指向 `ops.md` 或 `context.md`，**不指向 spec.md**。

2. **Workspace（所有 project）**  
   不绑仓库、不绑集群的短规矩。  
   写入 `Projects/_facts.md`（与 project 相同的两节）。没有该文件则创建空两节再追加。  
   含环境名的不得升到这一层。

3. **Skill**  
   有独立触发、跨会话、现有 skill 加一节会变糊。  
   先吸收进最近的现有 skill。默认新建数为 0。  
   新建须用户确认。前缀沿用现有规则（`shimo-*` / `st-*` / 无前缀），**不要默认 `kilo-`**。  
   与现有 skill 相反的做法标冲突，不合并。

## Interaction

1. 列出本轮可写入的 1 / 2 / 3 项（可空）。  
2. 等人选范围后再改文件。  
3. `/kilo auto` 不得新建 skill；最多拟 1/2 的补丁仍须可回滚的短写入。本线实现里 auto 对 3 硬停。

## Layout

```text
<workspace>/Projects/
├── _facts.md                 # optional; Stable Facts + Gotcha Index
└── NN-project/
    ├── project.md            # existing two sections; no extra experience file
    └── NN.MM-line/
        ├── spec.md           # design contract only
        ├── ops.md            # optional runbook; create only when this line has recipes
        └── context.md        # Handoff stays short; Gotchas are one-liners or pointers
```

## Recover

Read order: `Projects/_facts.md`（若存在）→ `project.md` 两节 → 当前 line。Follow Gotcha Index only when the topic touches this line.

## Pass bar

- 命令表有 `/kilo up`。
- 协议写明三层落点、先列后写、skill 默认不建、`kilo-` 不是默认前缀。
- `ops.md` 为可选；Gotcha Index 示例指向 ops/context，不指向 spec。
- `Projects/_facts.md` 出现在 layout 与 recover。
- README 中英各有一行命令说明。
