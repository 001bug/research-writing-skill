# DSH 适配验收记录

日期：2026-10-11。范围：本机 Linux 用户级技能适配。

## 开工水位

- Nexus HEAD：`90e34ee670e65dc0384f470e738aa4b5af6b5e27`。
- 预存工作区：`vue/src/views/admin/AdminLayoutView.vue` 已修改；`research-writing-skill/` 未跟踪。前端文件未改动。
- DSH：`0.1.5-rc.2`，本机源码 `fb2c4b9`。
- `CODE_CONFIRMED`：用户级技能目录扫描为单层；原门禁的数字引用漏检、`06_` 文件名误判已冻结为 characterization 用例。
- 文档差异：上游没有 DSH 安装指引，默认示例依赖仓库 cwd 和 PowerShell；现已补充 DSH 资源契约及 Python 入口。
- 证据不足：没有调用模型，因此不能证明模型能可靠遵循整篇流程或生成合格论文。
- 原完整性门禁主要断言字符串存在，无法证明运行行为；保留其内容契约，同时新增行为测试。

## 实际修改

- 19 个技能加入 DSH 资源定位契约；入口、章节编排、验证、环境和图表技能补充 DSH 流程。
- 用户级安装器：所有冲突先检查、所有权清单、幂等安装、搬迁更新、卸载保护与失败回滚。
- 两个质量/完整性门禁的唯一逻辑迁移至 Python；PowerShell 仅保留参数转发。
- 引用标记新增数字格式；章节角色与可配置阈值取代文件名推断。
- 增加独立依赖清单和 freeze、Linux 中文字体发现、安装/运行/卸载文档。
- 未修改 Java RAG、Python rag-tools 或 Vue；没有模型调用、真实聊天、解析、索引、数据库写入、提交或推送。

## 验证证据

| 检查 | 结果 |
| --- | --- |
| 初始目标测试 | 新安装器/门禁模块不存在，退出 1；随后实现 |
| Python 隔离测试 | 40 tests，OK，退出 0 |
| 实际 DSH 文件系统 provider + registry | 2 个临时工作区各发现/加载 19 个技能；项目覆盖优先级和资源根目录通过，退出 0 |
| 正式用户目录只读核对 | 实际加载器从 `/home/ohmygoda/.dsh/skills` 加载 19 个技能，通过，退出 0 |
| 安装器正式执行两次 | 两次均注册 19 个技能，退出 0 |
| 完整性门禁 | 通过，退出 0 |
| 论文质量门禁 self-test | 通过，退出 0 |
| pip check | No broken requirements found，退出 0 |
| Python compileall / bash -n | 通过，退出 0 |
| git diff --check | 通过，退出 0；技能仓库为未跟踪目录，另用完整性检查和编译/测试覆盖新增文件 |

测试覆盖中文/空格路径、源仓库搬迁、冲突与回滚、卸载保护、初始化保留旧文件、角色/引用/占位/证据映射、PDF CLI、离线图表/统计和 CrossRef 模拟响应。
文献检索测试没有真实 API 请求。PowerShell 包装器已静态核对，因本机未安装 PowerShell，没有执行其运行测试。

## 本机安装结果

- 完整资源仓库：`/home/ohmygoda/project/nexus-agent-pro-academy/research-writing-skill`。
- 技能目录：`/home/ohmygoda/.dsh/skills/<技能名>/`，19 个目录链接。
- 所有权清单：`/home/ohmygoda/.dsh/research-writing/installation.json`。
- 独立解释器：`/home/ohmygoda/.dsh/research-writing/.venv/bin/python`，Python 3.11.17。
- 精确依赖：`requirements-dsh.lock.txt`。
- 运行时未修改 DSH 源码、预设或模型设置。新建支持 skill 的会话后使用。

## 实际能力边界

`DATA_CONFIRMED`：技能加载、资源定位、依赖与脚本已验证。
模型执行效果尚未演练；子代理章节流程为适配说明，未消费模型额度验证。
没有安装 TeX 编译器或 Word 导出；没有接入知识库 MCP。
质量门禁仅提供机械结构检查，不证明文献真实性、学术质量或学校最终合规。
