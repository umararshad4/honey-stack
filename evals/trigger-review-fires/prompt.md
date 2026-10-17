---
max_turns: 3
tags: [trigger, review]
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this diff before I merge it:
```diff
-def total(xs):
-    return sum(xs)
+def total(xs):
+    t = 0
+    for i in range(len(xs)):
+        t = t + xs[i]
+    return t
```
