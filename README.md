# DSH Agent Docs Kit

可复制到不同代码仓库的 Agent 文档骨架，源自 DeepSeek Harness 的 Agent Notes 体系（固定提交与改动见 [UPSTREAM.md](UPSTREAM.md)）。套件不复制上游的产品架构、命令、发布流程与双语机制。本仓库自身不套用模板里的文档规则，只维护这份 README。

## 两个 profile

| | `full`（默认） | `lite` |
|---|---|---|
| 适合 | 需要长期保留决策记录与格式校验的项目（如 luwux.log） | 单人加 agent 的小项目、新仓库 |
| 文档结构 | `docs/architecture.md`、`docs/testing.md`，外加 `.agents/notes/` 的 proposed/implemented/rejected/archived 生命周期 | `docs/specs/`（当前状态）、`docs/decisions/`（ADR）、`docs/tasks/`（任务简报） |
| 记录义务 | 只为代码、测试和文档解释不了的长期决策理由写 Agent Note | 只在未来 agent 很可能推翻某个决定时才写 ADR；只在跨会话的工作中才写任务简报 |
| 篇幅约束 | 无 | 任务简报约 60 行（含结果），ADR 约 50 行 |
| 校验 | `scripts/verify_agent_notes.py`（只查结构与格式） | 无；质量靠判断 |
| Skills | 完整版 prose / simplification | 精简版，不涉及 Agent Notes |
| 文件数 | 12 | 8 |

两者都保留“一个事实只有一个归属”和“规格只写当前状态”两条规则，并附带 MIT 许可证副本。

## 初始化

先预览，不写文件：

```bash
python3 init.py /absolute/path/to/project --profile lite
```

确认后应用：

```bash
python3 init.py /absolute/path/to/project --profile lite --apply
```

不加 `--profile` 时等同于 `full`。`--claude-symlinks` 会额外创建指向 `AGENTS.md` 的 `CLAUDE.md` 链接。

初始化器只复制每个 profile 在代码中显式列出的文件，忽略平台垃圾文件（`.DS_Store`、`Thumbs.db`、`*.pyc`、`__pycache__/`）；遇到其他未列入清单的模板文件、同名目标文件或被符号链接替换的目录，就拒绝整个操作，一个文件也不写。已有文档体系的项目请以 [`template/`](template/) 或 [`template-lite/`](template-lite/) 为参照手工合并。

初始化后，架构文档会如实标明“尚未记录目标仓库架构”。在审计目标仓库并写入当前事实之前，不要宣称适配已经完成。

## 验证

修改初始化器或模板后，在套件根目录运行：

```bash
python3 -m unittest discover -s tests -v
```

`full` 目标仓库的文档检查：

```bash
python3 scripts/verify_agent_notes.py
```

该脚本只能证明 Agent Note 的目录、文件名、header、状态与必需 section 一致；即使没有任何 Note 也会通过。它不检查链接、supersession 或内容真实性。

## 变更记录

- 2026-09-27：`full` 同步 DeepSeek Harness `21638c5` 的文档流程变更：放宽写 Note 的门槛，新增“小改动 Note 直接删除”规则，重写 simplification skill（详见 [UPSTREAM.md](UPSTREAM.md)）。已安装的项目（如 luwux.log）需手动同步。
- 2026-09-27：新增 `lite` profile（`template-lite/`、`--profile`）；删除模板中误入的 `.DS_Store`；初始化器改为忽略 `.DS_Store`、`Thumbs.db`、`*.pyc` 与 `__pycache__/`，原先只忽略 `.DS_Store`，遇到其他平台文件会中止。

模板中源自上游的文本依照 [DeepSeek Harness MIT 许可证](template/.agents/LICENSE.deepseek-harness) 使用。
