## Acceptance

- status: missing
- version: 1
- supersedes: -
- updated: "{{date}}"
- user_prompt: |
  <verbatim acceptance from the user; freeze before the first execute mutation>
- spec_anchors:
  - path: "spec.md"
    note: "<sheet / section>"
- constraints: []
- pass_bar: -

## ReviewIndex

| Finding | Severity | Task | Commit | Status | Round |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Claims

- id: C01
  task: T01
  claim: "<falsifiable sentence>"
  must_trace: []
  disproof_hint: "<how to refute>"

## ReviewThread

- status: open
- cycle: 1
- updated: "{{date}}"

### R1 · reviewer

- at: "{{date}}"
- commit: -
- acceptance_version: 1
- acceptance_result: partial
- summary: "<one line>"
- findings:
  - id: F1
    severity: high
    title: "<short>"
    evidence: []
    status: open

### R1b · implementer

- at: "{{date}}"
- commit: -
- summary: "<one line>"
- responses:
  - finding: F1
    disposition: fixed
    task: T01
    note: "<short>"
- open_risks: []
- ask_user: []
