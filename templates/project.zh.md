---
title: "{{title}}"
type: project
parent: ""
project: "{{project}}"
status: active
blocked: false
summary: ""
repos: []
lang: "zh"
updated: "{{date}}"
tags:
  - project
---

# {{title}}

`/kilo` 项目容器。用 `/kilo init` 创建。

## 下属任务包

| 任务包 | 备注 | Worktree | 分支 | 状态 |
| --- | --- | --- | --- | --- |
| | | | | |

> 链接示例：`[[01.01-hello/workstream]]`
> `状态` 用 Handoff 枚举：`none|active|missing|smoke_pending|ready_to_merge|pruned`

## 仓库

| ID | path |
| --- | --- |
| | |

## 稳定事实

<!-- 长期有效、可验证，且每条任务包都需要的事实：构建/运行命令、目录约定、
     外部系统的怪癖。每条一行，可选 `check:` 校验命令。
     只记当前为真：后续任务包推翻某条时原地替换，改动原因写进那条线的
     ## 关键决策 —— 这里不堆变更历史。
     临时的坑不进这里，留在任务包 context.md。 -->

## 坑位索引

<!-- 只做指路，不复制原文。每个主题一行：
     - <主题>：<一句话结论> → [[01.03-slug/context]]
     只有无法变成 test/lint/类型约束的坑才值得加一条。
     结论被推翻时，当轮就改写或删掉该行。 -->
