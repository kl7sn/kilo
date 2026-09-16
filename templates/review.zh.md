## Acceptance

- status: missing
- version: 1
- supersedes: -
- updated: "{{date}}"
- user_prompt: |
  <用户验收原话；首次 execute 改动前必须冻结>
- spec_anchors:
  - path: "spec.md"
    note: "<sheet / 章节>"
- constraints: []
- pass_bar: -

## ReviewIndex

| Finding | 严重度 | 任务 | Commit | 状态 | 回合 |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Claims

- id: C01
  task: T01
  claim: "<可证伪的一句话>"
  must_trace: []
  disproof_hint: "<如何证伪>"

## ReviewThread

- status: open
- cycle: 1
- updated: "{{date}}"

### R1 · reviewer

- at: "{{date}}"
- commit: -
- acceptance_version: 1
- acceptance_result: partial
- summary: "<一句话结论>"
- findings:
  - id: F1
    severity: high
    title: "<问题简述>"
    evidence: []
    status: open

### R1b · implementer

- at: "{{date}}"
- commit: -
- summary: "<一句话说明>"
- responses:
  - finding: F1
    disposition: fixed
    task: T01
    note: "<简述>"
- open_risks: []
- ask_user: []
