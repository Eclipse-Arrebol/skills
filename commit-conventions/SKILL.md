---
name: commit-conventions
description: >-
  Write and review Git commit messages using the user's type(scope): description convention,
  choose the type and scope from the actual changes, and apply the rule during authorized
  commits or pushes. Use for 提交规范、commit消息、feat/fix格式、规范提交、修改提交信息;
  formatting requests alone do not authorize Git mutations.
---

# Git 提交规范

将真实变更概括为`type(scope): description`。本技能规定提交信息，不自行扩展暂存、提交、推送或历史改写的权限；用户和当前仓库的明确规则优先。

## 格式

```text
type(scope): description
```

- 使用英文半角`(`、`)`、`:`，冒号后空一格；不使用`feat（模块）：描述`这样的全角格式。
- type用小写；scope用实际技能名、组件名或改动模块，如`algorithm-animation`、`commit-conventions`、`readme`。不要用无意义的`all`、`misc`代替可识别模块。
- 描述简短、具体，默认使用英文动词短语，也可按用户／仓库要求使用中文，保持同一仓库语言一致。避免仅写`update files`、`fix bug`，不虚构修复内容或任务编号。
- 一次提交表达一个相对完整的目的；相关说明随功能一起提交，无关修改拆开。不要为了套格式制造空提交。

## 类型选择

| type | 使用情形 |
|---|---|
| feat | 新增功能、能力或独立技能 |
| fix | 修复已存在的错误行为 |
| docs | 仅修改文档、说明或示例文字 |
| refactor | 调整结构，保持既有行为 |
| perf | 性能改进 |
| test | 测试或验证用例变更 |
| build | 依赖、构建系统或打包方式变更 |
| ci | 持续集成配置变更 |
| chore | 不属于以上类型的维护事项 |

选择类型依据实际影响，不仅看文件扩展名。例如新增技能即使主要文件是Markdown，也属于feat；新增技能时同时更新目录README，整体仍可作为一个feat提交。破坏兼容时才使用仓库要求的`!`或BREAKING CHANGE，不凭猜测添加。

```text
feat(commit-conventions): add scoped commit message rules
feat(algorithm-animation): add silent teaching animation skill
fix(algorithm-animation): preserve saved edge weights
docs(readme): update skill descriptions
```

## 实际提交时

用户只要求拟定／检查／讨论格式时，给出合适消息，不据此修改索引、创建提交或推送。用户已经要求提交或推送时，沿用该授权完成工作，不额外设置格式批准关卡。

先查看工作区、暂存差异和相关提交，按本次实际变更选择type与scope；只暂存本次应包含的路径，不把用户其他改动一并带入。提交后核对实际subject与提交SHA；推送时确认目标仓库／分支，并核验远端结果。报告实际完成状态，不把“生成了消息”说成“已经提交／推送”。

## 修改现有提交

先区分“今后采用规范”和“改写某条现有提交”，不要把格式偏好自动解释为改写已发布历史。

- 用户明确要求修改最新、尚未推送的提交时，可以amend；只改消息时保持文件树不变。
- 用户已明确要求修改已推送的提交并推送时，不重复索要相同授权。先核对目标提交及远端HEAD，保护用户未提交改动；仅改消息时核验新旧文件树相同。
- 必须更新已发布历史时，使用带精确预期旧SHA的`--force-with-lease`或等价比较更新；不使用裸`--force`。远端有新变化时重新检查，不覆盖未知新提交。
- 在授权或目标含糊时，先给出具体改写方案再澄清；不为普通新提交或已有明确授权制造额外确认。
