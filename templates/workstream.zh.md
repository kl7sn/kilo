---
title: "{{title}}"
type: workstream
parent: "{{parent}}"
project: "{{project}}"
status: active
blocked: false
next: "[[tasks]]"
summary: ""
repos: []
lang: "zh"
updated: "{{date}}"
tags:
  - workstream
---

# {{title}}

> 父项目：[[../project]]

## 入口

- [[context]]
- [[spec]]
- [[tasks]]

## $run

1. `$run` 推进 · `$run bind` 切换 · `$run lang en|zh` · `$run auto` 无人值守
2. `doing→done` 须在 `context.md` 留下验证证据
3. 暂停前刷新 **Handoff**；长期约束写入 **Gotchas**
4. 关线须过集成闸（人工冒烟 + worktree 处置）
