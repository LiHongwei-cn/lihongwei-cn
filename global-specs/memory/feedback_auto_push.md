---
name: auto-push-to-github
description: 项目代码改动必须同步推送 GitHub
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1e82ae41-815b-4069-8908-fd3ebed6420a
---

对 C:\Users\HP\Desktop\1 项目的任何文件改动，完成后必须 commit 并 push 到 GitHub，确保 GitHub Pages 网站同步更新。

**Why:** 网站部署在 GitHub Pages，本地改动不推送则线上不会生效。
**How to apply:** 每次改完代码后，git add → git commit → git push。如果 commit 信息不明显，用中文描述改动内容。
