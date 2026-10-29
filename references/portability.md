# 跨工具接入与能力差异

## 兼容目标

同一套科研目录、Markdown规则、模板和交接可在不同工具间复用。核心只要求理解文件内容；初始化脚本需要可用的 Python 3.10+，仅用标准库。不硬编码特定模型、MCP服务、函数名、终端shell或当前机器路径。

“兼容各工具”指可移植核心、相应工具的接入及有限能力下的替代方式，不保证所有工具版本都会自动发现skill或拥有同样能力。文档核对和脚本测试分别记为相应验证，不冒充已经在每个产品实机测试。

## 核心包与接入位置

保留整个 `yanflow/` 文件夹，包括 `SKILL.md`、`references/`、`assets/` 和 `scripts/`；只复制主文件会丢失参考与模板。`agents/openai.yaml` 是可选的界面元数据，不是核心工作流依赖，其他工具无需执行它。

下列是2026-10-29核对官方文档得到的本地位置。README 优先提供个人安装的一条命令，供多个项目复用；也可选择项目内安装。实际安装时按使用者工具版本和官方要求确认，不自动改写多个工具的个人配置，也不把本地可读等同云端已同步。

| 工具 | 项目级skill位置示例 | 项目上下文接入 |
| --- | --- | --- |
| Codex | `.agents/skills/yanflow/` | `AGENTS.md`；见 [OpenAI skills](https://learn.chatgpt.com/docs/build-skills) 和 [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) |
| Claude Code | `.claude/skills/yanflow/` | 按当前版本的项目记忆规则读取；需要时使用短 `CLAUDE.md` 入口，见 [skills](https://code.claude.com/docs/en/skills) 和 [项目记忆](https://code.claude.com/docs/en/memory) |
| Cursor | `.agents/skills/yanflow/` 或 `.cursor/skills/yanflow/` | 支持 `AGENTS.md`；见 [skills](https://cursor.com/docs/skills) 和 [规则](https://cursor.com/docs/rules) |
| Gemini CLI | `.agents/skills/yanflow/` 或 `.gemini/skills/yanflow/` | 需要时使用短 `GEMINI.md` 入口，见 [skills](https://geminicli.com/docs/cli/skills/) 和 [项目上下文](https://geminicli.com/docs/cli/gemini-md/) |
| 其他支持Agent Skills的工具 | 使用该工具官方指定目录 | 核查其项目规则入口，不猜配置语法 |
| 无原生skill加载能力的工具 | 手动提供 `SKILL.md` 及本次相关参考文件 | 请求其先读项目总纲和交接，再按当前目标工作 |

不在同一个扫描范围无差别安装多个同名副本；有些工具会同时扫描兼容目录。若保留多个已安装副本，应明确主要维护版本及更新方式，避免不同工具使用不同规则。

个人安装：Codex 使用 `$HOME/.agents/skills/yanflow/`，Claude Code 使用 `$HOME/.claude/skills/yanflow/`，Cursor 使用 `$HOME/.cursor/skills/yanflow/`，依据为上表各工具官方文档。`$HOME` 是使用者主目录，PowerShell 和常见 Unix shell 均可展开；cmd 需改用 PowerShell 或其自身路径语法。

Gemini CLI 官方支持 `gemini skills install https://github.com/unno11/yanflow.git`，默认 scope 为 user，按提示确认安装即可；无需另写安装器或跳过其交互确认。个人安装面向本机工具，不自动同步到云端会话。

使用者要求 agent 安装时，先识别当前工具和已有安装，使用该工具可用的安装能力或克隆到对应目录；保留完整包并检查 `SKILL.md`。已有目录先确认来源和本地修改，适合时采用保留本地修改的更新方式，不覆盖它或顺带安装到其他工具。安装后让工具重新发现，再核实能否调用；仅文件存在不代表当前会话已经加载。

## 项目记录保持一份

各工具共用 `AGENTS.md`、`handoff.md`、`brainstorm.md`、文献索引、实验和数据记录。工具入口文件只告诉工具先读哪里，不成为另一套主纲。

`scripts/init_project.py --entrypoint claude` 可在指定项目中补 `CLAUDE.md`，`--entrypoint gemini` 可补 `GEMINI.md`；参数可重复。先由实际任务确定需要哪些入口，不默认全部创建。脚本不修改已有入口；已有入口需接入时先读原文再局部补链接。

这些入口是让代理读取总纲的明确指示，不声称所有版本都把普通Markdown链接作为内容导入。用对应工具首次进入项目时，核实代理实际读过总纲和交接；未自动加载时在当前对话明确指定。

## 按真实能力执行

- **文件与执行**：能读写文件和运行脚本时直接完成已授权任务；只能读文本时给出相应内容或可执行步骤，不能声称已经落盘、训练或归档。
- **检索与下载**：使用当前工具提供的检索、浏览、下载或终端能力。缺网络或权限时明确哪些资料尚未取得，不把本地已有摘要写成最新检索结果。
- **子agent**：工具与授权允许时委派专门的头脑风暴职责；否则当前对话分别完成主线改进与方向审视，说明没有独立agent参与，不伪造多代理审查。
- **提问与展示**：有专门提问界面则使用；否则用普通文字提问。图表、笔记和结论保持Markdown等通用格式，不要求专有界面指令。
- **跨设备交接**：记录可核实的仓库、资料位置、原始结果和运行身份；另一设备的路径、访问权和服务连接须据实确认，不因文件同步而假定全部可用。

遇到不支持的能力，只调整执行方式并保留缺项；研究目标、既定协议、用户决策边界和证据要求保持原意。当前任务无需要时不额外检查所有工具或配置。
