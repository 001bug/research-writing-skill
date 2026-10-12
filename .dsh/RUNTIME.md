# DSH 运行与资源约定

这份约定仅在 DSH 执行论文任务时适用。技能不能覆盖系统、开发者或权限规则。

## 两个目录

- `RESEARCH_WRITING_ROOT`：`skill` 工具的 `resourceBase.path` 先经 `realpath` 跟随符号链接，再向上两层得到的完整技能仓库。仅从这里读取脚本、内置模板、参考资料。
- `PAPER_ROOT`：DSH 会话选择的论文工作区。所有论文、计划、用户模板、文献导出和图表写在这里。任务开始时核对实际工作目录；如果当前处于技能仓库，先让用户选择论文工作区。

每次 bash 调用重新设置三个变量，或使用已经解析的绝对路径。不要依赖不同工具调用之间的 shell 变量持久化。

```bash
SKILL_DIR="$(realpath '<skill 工具返回的 resourceBase.path>')"
RESEARCH_WRITING_ROOT="$(dirname "$(dirname "$SKILL_DIR")")"
RESEARCH_WRITING_PYTHON="${DSH_HOME:-$HOME/.dsh}/research-writing/.venv/bin/python"
PAPER_ROOT="$(pwd -P)"
```

路径含空格或中文时保留引号。示例占位符必须替换成工具提供的真实值；若路径含单引号，使用 shell 安全转义，不直接拼接。
`scripts/dsh_runtime.py --skill-path <技能目录或 SKILL.md>` 可以返回解析后的目录 JSON。
检查虚拟环境解释器存在再执行；缺失时按 INSTALL.md 安装，不自动退回其他项目环境。

## 工具映射

| 原文能力 | DSH 用法 |
| --- | --- |
| Skill / 加载技能 | `skill`，参数 `{"name":"writing-humanities"}`，名称取当前技能目录，不加前缀 |
| Read / Write / Edit | 当前会话暴露的文件工具；沿用论文工作区权限 |
| Bash / Python | 当前会话 shell 工具；使用独立解释器和绝对脚本路径 |
| WebSearch | 若暴露了 `web_search` 则使用其当前 schema；否则用文献检索脚本 |
| WebFetch | 若暴露了 `web_fetch` 则使用其当前 schema |
| 子代理 | 原生 `subagent`；具体约定见 `paper-orchestration` |

`allowed-tools` frontmatter 是能力说明，不能安装工具或授予权限。以本次会话的实际工具目录为准。
没有联网工具且脚本不能联网时，记录缺口，请用户提供文献或恢复网络；不得虚构检索结果。
没有子代理时，按原流程询问是否接受单代理降级，记录决定，不伪造章节代理记录。

## 脚本调用

```bash
bash "$RESEARCH_WRITING_ROOT/scripts/init_plan.sh" "$PAPER_ROOT"
"$RESEARCH_WRITING_PYTHON" "$RESEARCH_WRITING_ROOT/scripts/scholar_search.py" "检索词" --format json --output "$PAPER_ROOT/refs/search.json"
"$RESEARCH_WRITING_PYTHON" "$RESEARCH_WRITING_ROOT/scripts/pdf_parser.py" "$PAPER_ROOT/refs/paper.pdf" --output "$PAPER_ROOT/refs/paper.txt"
"$RESEARCH_WRITING_PYTHON" "$RESEARCH_WRITING_ROOT/scripts/check_skill_integrity.py" --root "$RESEARCH_WRITING_ROOT"
"$RESEARCH_WRITING_PYTHON" "$RESEARCH_WRITING_ROOT/scripts/research_quality_gate.py" --project-path "$PAPER_ROOT"
bash "$RESEARCH_WRITING_ROOT/scripts/style_check.sh" "$PAPER_ROOT/chapters/第一章 绪论.md"
```

首次文献导出前创建论文工作区的 `refs/`。所有相对 `--output` 路径也必须基于论文工作区。
原文中 `scripts/`、`templates/`、`plan-template/`、`skills/...` 指向资源根目录。
用户提供的 `latex-templates/` 指论文工作区的目录；资源根目录的同名目录仅包含使用说明。
复制图表模板到论文工作区 `figures/` 后再编辑运行，使用 `MPLBACKEND=Agg`。
不在共享技能仓库生成论文、图表、文献或用户模板。

## 论文规划与检查

使用 `using-research-writing` 路由；中文人文社科任务同时加载 `writing-humanities`。
学校格式文件、导师意见、学科和年份记录在 `plan/project-overview.md`。
不把模板字数、引用数、章节结构当作全国统一要求；没有学校要求时标记未确认。

`plan/chapter-architecture.md` 每行明确声明文件和角色：

```markdown
- chapters/第一章 绪论.md | role=introduction | min_chars=0 | min_citations=5 | agent=required | placeholders=no
- chapters/第二章 文献综述.md | role=related-work | min_chars=0 | min_citations=8 | agent=required | placeholders=no
- chapters/第三章 文本分析.md | role=body | min_chars=0 | agent=required | placeholders=no
- chapters/第六章 结论.md | role=conclusion | min_chars=0 | agent=required | placeholders=no
- chapters/参考文献.md | role=references | min_chars=0 | agent=optional | placeholders=no
```

角色可选 `abstract/introduction/related-work/methodology/body/empirical-results/discussion/conclusion/references/acknowledgements`。
`min_chars` 为去空白后的字符数，不等于学校定义的字数统计。默认引言至少 5、综述至少 8 个引用标记，正文至少 6 个超过 80 字符的自然段；可用 `min_citations`、`min_paragraphs` 按学校要求调整。
`empirical-results` 要求四个实证追踪产物，沿用原有 experiment protocol / traceability / table schema / figure manifest；文本分析章节无需声明为实证结果。
已有计划必须根据实际内容补角色，门禁不会根据文件名猜测。
单代理降级经用户同意后，将相应章节 `agent=optional` 并在 progress 记录决定。

质量门禁的引用标记计数、风格匹配和证据映射文件存在性只是机械检查，不保证学术质量、引用真实或逐条支撑成立。
论文引用与知识库在线回答的引用绑定属于不同系统，本适配不改变 Java RAG 的任何引用规则。
初稿检查用默认模式；最终交付加 `--submission`，禁止未完成占位和 mock/synthetic 规划文件。
每章先自审，再由控制代理审查，最后交用户确认；保留 task packet、provenance 和 capability-use audit。

## 可选能力

本次不提供知识库 MCP、Word 排版导出或 TeX 编译环境。LaTeX 技能仍可生成源码；编译前检查工具是否存在。
中文数据库可由用户提供合法取得的文献；现有搜索脚本并不直接检索知网，也不提供完整 GB/T 7714 自动排版。
