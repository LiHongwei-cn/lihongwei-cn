---
name: auto-sync-github-after-task
description: 每次完成任务后必须自动 git commit + push，如果涉及网页内容改动也要自动更新并推送
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a5946395-ac39-46e4-883a-20205dc63ee0
---

每次完成任务后必须自动执行 git add + commit + push。
如果任务涉及 HTML/CSS 网页内容改动，同样需要提交并推送，网址项目内容会自动同步到 GitHub Pages。
不需要用户提醒——这是默认行为。

**Why:** 用户多次提醒后才执行，浪费时间和上下文。用户明确表示"不想再打字提醒"。

**How to apply:** 任何代码或网页改动完成后，最后一步永远是 git commit + git push，不等待用户确认。
