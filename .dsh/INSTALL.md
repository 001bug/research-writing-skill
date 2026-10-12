# Research Writing Skill for DeepSeek Harness

适配基于本机 DSH `0.1.5-rc.2` 的文件系统技能加载器；无需改 DSH 源码。
完整保留仓库，19 个子技能分别注册到用户级目录，不能只复制一个 SKILL.md。

## Linux 安装

需要 Python 3.11+、bash、realpath、rg 和支持 `skill` 的 DSH 预设（例如 standard）。
将下面第一行改为完整仓库的实际路径：

```bash
RESEARCH_WRITING_ROOT='/绝对路径/research-writing-skill'
RESEARCH_WRITING_DSH_HOME="${DSH_HOME:-$HOME/.dsh}"
python3 -m venv "$RESEARCH_WRITING_DSH_HOME/research-writing/.venv"
RESEARCH_WRITING_PYTHON="$RESEARCH_WRITING_DSH_HOME/research-writing/.venv/bin/python"
"$RESEARCH_WRITING_PYTHON" -m pip install -r "$RESEARCH_WRITING_ROOT/requirements-dsh.lock.txt"
"$RESEARCH_WRITING_PYTHON" "$RESEARCH_WRITING_ROOT/scripts/check_skill_integrity.py" --root "$RESEARCH_WRITING_ROOT"
"$RESEARCH_WRITING_PYTHON" "$RESEARCH_WRITING_ROOT/scripts/install_dsh.py"
```

`requirements-dsh.lock.txt` 固定本次 Linux / Python 3.11 验证版本；其他系统若需重新解析依赖，使用 `requirements-dsh.txt`，运行全部测试后记录新的 freeze。
安装器也接受 `--dsh-home /自定义目录`。使用非默认位置时，启动 DSH 和运行后续命令必须使用同一 `DSH_HOME`。
不需要重启电脑；安装后在 DSH 打开新会话即可。已经运行的会话是否实时刷新取决于技能 watcher 设置。

安装会先检查所有名称冲突：遇到未由安装清单管理的文件、目录或符号链接时停止，保留现状。
安装清单位于 `$DSH_HOME/research-writing/installation.json`。重复执行安装是幂等的。
项目级 `.dsh/skills` / `.agents/skills` 的同名技能优先于用户级，发现行为仍以 DSH 当前预设为准。
不要把完整 `skills/` 作为单个技能链接，也不要把技能安装进 Codex 的全局目录。

## 开始使用

在 DSH 中选择一个独立的论文工作区，不要选择技能仓库，也不要在 Java 项目根目录写论文。
确认 DSH 的文件工具和 shell 都处于该论文工作区。可用如下提示词开始：

> 请用 skill 工具加载 using-research-writing 和 writing-humanities，协助我规划一篇中文本科毕业论文。先收集学校格式、导师要求、已有文献和研究问题，再创建 plan；每章写完让我确认，不编造文献。

若当前预设没有 `skill` 工具，切换到 standard 等支持技能的预设。
目录中的技能不会作为启动 hook 自动执行；模型按技能描述和明确请求加载。整篇写作使用 `paper-orchestration` 的原生子代理流程。
资源路径、脚本调用、章节角色与能力缺口处理详见 [RUNTIME.md](RUNTIME.md)。

## 更新与卸载

更新仓库后运行完整性检查和隔离测试，再重复安装命令。
仓库搬迁后在新位置重新执行安装，安装器只更新自身管理的链接。
不要删除技能仓库，否则注册链接失效。

```bash
python3 "$RESEARCH_WRITING_ROOT/scripts/install_dsh.py" --uninstall
```

卸载只移除清单管理且目标未被改动的链接；不会删除论文、其他技能、仓库或虚拟环境。
如果有人替换过受管理链接，卸载会先报告冲突并停止，避免部分卸载。

## 离线验收

```bash
"$RESEARCH_WRITING_PYTHON" -m unittest discover -s "$RESEARCH_WRITING_ROOT/tests" -p 'test_*.py' -v
"$RESEARCH_WRITING_PYTHON" "$RESEARCH_WRITING_ROOT/scripts/research_quality_gate.py" --self-test
node --import /本机/deepseek-harness/node_modules/tsx/dist/loader.mjs "$RESEARCH_WRITING_ROOT/tests/dsh-loader.mjs" --dsh-root /本机/deepseek-harness --source "$RESEARCH_WRITING_ROOT"
```

最后一项使用本机 DSH 的实际加载器，临时注册技能并核对 19 项发现、加载和项目级覆盖优先级；不修改 DSH 源码或配置。
如要只读核对已安装的用户级技能，在最后一项追加 `--installed-home "$RESEARCH_WRITING_DSH_HOME"`。
测试不调用收费模型，也不执行真实知识库业务操作。成功只代表加载、路径、依赖和脚本通过，模型写作效果仍需人工演练。
TeX 编译器和 Word 排版导出不包含在本次安装中。
