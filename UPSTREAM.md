# DeepSeek Harness 原文入口

通用骨架固定参考 DeepSeek Harness commit [`b150a551b8d465e31e418e1b2eaf5e79bbb7d28e`](https://github.com/deepseek-ai/deepseek-harness/tree/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e)。只阅读当前机制需要的 owner，但每个选中的文件都应完整阅读。

2026-08-29 又复核了 [`cd5ef8148158c3a752a658978873241fdf8e2bbc`](https://github.com/deepseek-ai/deepseek-harness/tree/cd5ef8148158c3a752a658978873241fdf8e2bbc)。Agent Note lifecycle、class、格式与归档 owner 没有改变；本套件没有升级或复制最新 DSH 文档系统，只从最新 `dsh-doc` 工作流中吸收两条与产品无关的澄清：操作说明的事实核对，以及教程写作前定义读者起点、可观察结果、可能失败、恢复路径和下一层深度。

为减少额外输入要求和重复工作，本地适配参考 [Astra 行为指南](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra#prompting-best-practices)，删除文案 skill 的显式 `scope` 前置要求，明确不引入或改变持久决策的机械性及局部小改动可豁免 Note，测试由 Agent 自行选择最少且必要的项目，允许不必要时不测；取消固定 Git 检查、操作说明的强制实测及验证责任方要求，并去除重复指令；必要的局部契约仍按文案 skill 保留。lifecycle、class、Note 格式、决策维护与归档机制保持原样。

`lite` profile（`template-lite/`）的两个 skill 是上述同名 skill 的精简改写：删除 Agent Note 生命周期相关内容，把决策与任务记录改为 ADR 和短任务简报；其来源仍为下表同名文件。

2026-09-27 复核至 [`21638c56315ae6a2b552d6091945d3144c9af32e`](https://github.com/deepseek-ai/deepseek-harness/tree/21638c56315ae6a2b552d6091945d3144c9af32e)，`full` profile 同步了其中与项目无关的文档流程变更：Agent Note 只为代码、测试和现有文档无法承载的长期决策理由而写，局部 UI 改动豁免；只记录小 UI 调整或纯机械改动的 implemented Note 直接删除，其余在仍有历史决策价值时才归档；归档不因既有标题标点或空行布局受阻；测试变更理由写在变更说明里；`docs/AGENTS.md` 的当前状态规则、slop checklist 与引用规则精简为上游新措辞；`dsh-find-simplifications` 按上游新结构重写为“追问可删除的维护义务”，删去 DSH 专属约束，并把 `references/historical-patterns.md` 的通用结论并入追问清单（该文件链接的都是 DSH 自有 Note，因此不复制）。lifecycle、class、Note 格式与 `dsh-prose-standard` 在该区间内没有变化；`archived-agent-notes.ts` 的变更只涉及 DSH 的封存例外，校验脚本保持不变。

若本机另有完整 clone，可将它以 detached HEAD 检出到同一固定提交，并放在可选同级路径 `../deepseek-harness` 以便搜索与逐文件比较。该本机路径不是便携包依赖；其他机器使用下表的固定提交 URL。

| 机制 | 原文 |
| --- | --- |
| 仓库级 agent 指令与验证原则 | [`AGENTS.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/AGENTS.md) |
| 文档层级、one-home 与文案规则 | [`docs/AGENTS.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/AGENTS.md) |
| Agent Note lifecycle、class、格式、supersession、合并删除与归档 | [`.agents/notes/README.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/.agents/notes/README.md)；写作门槛与删除规则见 [`21638c5` 版](https://github.com/deepseek-ai/deepseek-harness/blob/21638c56315ae6a2b552d6091945d3144c9af32e/.agents/notes/README.md) |
| Notes 子树指令 | [`.agents/notes/AGENTS.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/.agents/notes/AGENTS.md) |
| 已实施决策的同步维护 | [`.agents/notes/implemented/AGENTS.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/.agents/notes/implemented/AGENTS.md) |
| 冻结归档 | [`.agents/notes/archived/AGENTS.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/.agents/notes/archived/AGENTS.md) |
| 可执行 lifecycle/class 集合 | [`scripts/agent-note-tree.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/scripts/agent-note-tree.ts) |
| 可执行 Note 格式 | [`scripts/verify-agent-note-format.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/scripts/verify-agent-note-format.ts) |
| 归档路径、header 与上游完整冻结验证 | [`scripts/verify-archived-agent-notes.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/scripts/verify-archived-agent-notes.ts) 与 [`scripts/archived-agent-notes.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/scripts/archived-agent-notes.ts) |
| 相关检查、实际结果与 pending/failure 报告 | [`.agents/skills/dsh-pre-push-checks/SKILL.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/.agents/skills/dsh-pre-push-checks/SKILL.md) |
| 简化与死代码的消费者证据 | [`.agents/skills/dsh-find-simplifications/SKILL.md`](https://github.com/deepseek-ai/deepseek-harness/blob/21638c56315ae6a2b552d6091945d3144c9af32e/.agents/skills/dsh-find-simplifications/SKILL.md) 与 [`references/historical-patterns.md`](https://github.com/deepseek-ai/deepseek-harness/blob/21638c56315ae6a2b552d6091945d3144c9af32e/.agents/skills/dsh-find-simplifications/references/historical-patterns.md) |
| 完整命题与文案覆盖 | [`.agents/skills/dsh-prose-standard/SKILL.md`](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/.agents/skills/dsh-prose-standard/SKILL.md) |
| 后续复核的通用操作事实与读者路径原则 | [`.agents/skills/dsh-doc/SKILL.md`](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/.agents/skills/dsh-doc/SKILL.md)；只采用 workflow 第 4、7 步与 fact-check 原则，不复制 kind、Cordis、双语、网站或 DSH gates |

不要把原文中的产品名、包名、运行时结构、命令、发布阶段、双语机制或托管平台流程移入目标项目，除非目标项目存在独立消费者并把选择记录为自己的决策。
