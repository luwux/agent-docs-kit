# DSH Agent Docs Kit

这是一个可复制到不同代码仓库的 Agent 文档骨架。它保留 DeepSeek Harness Agent Notes 的通用核心：给 agent 的常驻规则、当前架构与测试文档、路径编码的提案/决策生命周期、证据驱动的简化与文案 skill，以及可执行的最小格式检查。

套件以 DeepSeek Harness [固定提交 `b150a551b8d465e31e418e1b2eaf5e79bbb7d28e`](https://github.com/deepseek-ai/deepseek-harness/tree/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e) 为原文快照，并在 2026-08-29 复核至 [`cd5ef8148158c3a752a658978873241fdf8e2bbc`](https://github.com/deepseek-ai/deepseek-harness/tree/cd5ef8148158c3a752a658978873241fdf8e2bbc)。给 agent 的指令文件优先保留固定快照的英文原句和结构，删除 Cordis、DSH 仓库布局、命令、发布与双语配套等目标项目不存在的专属内容；后续复核只吸收了“操作说明的事实核对”和“读者起点、结果、失败与恢复路径”两条通用澄清。少量 Agent 协作措辞修订见 [UPSTREAM.md](UPSTREAM.md)。本机重审可选使用同级路径 `../deepseek-harness`；普通使用不依赖该 clone。

套件不复制上游项目专属的产品架构、包结构、命令、发布流程、双语文件、sidecar、逐文件 hash、归档 manifest，也不建立每 task/run 一份记录的第二套系统。

## 初始化

先预览，不写文件：

```bash
python3 init.py /absolute/path/to/project
```

确认目标后显式应用：

```bash
python3 init.py /absolute/path/to/project --apply
```

初始化器只复制代码中显式列出的 12 个模板文件，忽略 Finder 的 `.DS_Store`，并在写入前拒绝缺失或其他未经复核的模板文件。它会一次性检查所有目标；只要任何同名文件或请求的 `CLAUDE.md` 链接已经存在，整个操作就拒绝且不写入。Agent Note 的 lifecycle/class 目录在首个 Note 出现时按需创建，不预建 Git 无法保存的空目录。已有文档系统的项目应以 [`template/`](template/) 为对照进行人工合并，不应绕过冲突保护。

Unix 仓库若明确使用 Claude Code，可选择创建与 DSH 相同用途的兼容链接：

```bash
python3 init.py /absolute/path/to/project --apply --claude-symlinks
```

## 验证

初始化器或校验器变更时，可在套件根目录运行：

```bash
python3 -m unittest discover -s tests -v
```

目标仓库的文档检查命令：

```bash
python3 scripts/verify_agent_notes.py
git diff --check
```

格式检查只证明 Agent Note 树、路径、真实日历日期、header、lifecycle 与必需 section 一致；它不证明文档事实、产品行为、测试、数据安全或发布产物正确。

## 使用边界

普通使用不需要阅读整个 DeepSeek Harness 仓库。要改变 lifecycle、class、Note skeleton、supersession/删除、冻结归档、简化证据或工程文案规则时，先从 [`UPSTREAM.md`](UPSTREAM.md) 定位固定 commit 的 owner，并完整阅读所选原文件。

初始化后的 `docs/architecture.md` 会诚实标记“尚未记录目标仓库架构”。在完成目标仓库的代码、配置审计并写入当前事实前，不得把文档系统汇报为适配完成。适配本身属于非平凡 process decision；完成后在 `implemented/process/` 中记录采用的子集、主动省略的机制、替代方案与实际检查。

模板中的上游衍生文本依照 [DeepSeek Harness MIT 许可证](template/.agents/LICENSE.deepseek-harness) 使用。
