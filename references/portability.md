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

各工具共用一套主要维护记录，主纲与交接可以在项目外的笔记库。项目 `AGENTS.md` 可以只作入口，注明主机、主纲及交接的绝对位置、维护者和可访问工具；其他工具入口指向它，不维护第二套主线。允许入口带少量安全硬约束摘要（如已有的不推送、不改服务器限制），注明“完整版见主纲”、来源及核验时间。摘要不能产生新授权；来源不可读时保留已知限制，依赖缺失信息的工作先核实。

`scripts/init_project.py --project-dir ... --entrypoints-only --entrypoint claude` 只补 `AGENTS.md` 和 `CLAUDE.md`，不建文献库或科研骨架；`--entrypoint gemini` 可补 `GEMINI.md`。`--main-record`、`--handoff-record` 接入已有外部记录，`--maintainer` 指定维护者，重复 `--constraint` 保存用户已约定的硬约束摘要。脚本不修改已有入口；已有入口需要接入时，agent 先读原文再局部更新，脚本输出 kept-existing 不代表映射已经接入。

建入口前核查 Git 忽略规则；脚本在 Git 可用时报告 `ignored-local-only`／`not-ignored`／`unverified`，后者需要 agent 如实核查，非忽略不代表已被跟踪或已提交。被忽略则标记仅本地，不自动改 `.gitignore` 或强制添加。识别到第三方代码仓库、上游 checkout 或 fork 时，先与用户确定科研记录放在仓库外、仅本地还是纳入 fork；已有明确约定直接复用。创建入口不包含提交、推送或发布科研笔记的授权。

这些入口是让代理读取总纲的明确指示，不声称所有版本都把普通Markdown链接作为内容导入。用对应工具首次进入项目时，核实代理实际读过总纲和交接；未自动加载时在当前对话明确指定。

## 云端会话的持久性与发现

临时云端容器中的个人目录安装可能随容器回收消失；目录存在也不等于已注册。安装后实际调用一次 skill，并确认 agent 能读取其主文件与本次相关参考。出现 Unknown skill 时检查安装范围、工具的发现入口及重载／新会话方式；不能仅因等待了一段时间就声称加载成功，也不反复安装多个副本。

持久接入应按当前产品支持方式选择：允许加载仓库技能的环境可将完整包纳入项目指定目录；支持账号自定义技能的产品可上传并启用其接受的包。这两条都取决于产品和会话类型，不能保证项目内目录在所有云端会话都能加载。Claude Code 文档明确区分本地个人目录、仓库技能与账号技能，见 [加载范围](https://code.claude.com/docs/en/skills)；Claude 账号官方说明使用包含技能文件夹的 ZIP 并在账号中启用，见 [创建自定义技能](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)。不要把改扩展名为 `.skill` 当作已完成持久化，须按该产品要求打包、上传、启用并在新会话核实；本 skill 不自动操作账号或创建新的服务。

## 链接与跨设备证据

- Obsidian 库内优先使用带库内路径的 `[[目录/笔记]]`，符合本项目既有约定时可用其支持的 Markdown 内链；依据见 [Obsidian 内链文档](https://help.obsidian.md/links)。未实测的点击能力不标为已验证。
- 同一代码仓库内部使用相对 Markdown 链接。笔记库外、仓库外或跨主机位置使用“主机标识＋完整路径”的代码文本，同时说明需要何种工具和权限，不依赖本地绝对路径能被点击。
- 换机器时优先通过仓库标识、提交与相对路径、笔记库标识和库内路径恢复对应；本地路径由新环境重新解析。保留实际存放位置、可访问工具与核验时间；无法访问的证据标记尚未复核，不以文件同步推断服务器访问也已可用。

## 按真实能力执行

- **文件与执行**：能读写文件和运行脚本时直接完成已授权任务；只能读文本时给出相应内容或可执行步骤，不能声称已经落盘、训练或归档。
- **检索与下载**：使用当前工具提供的检索、浏览、下载或终端能力。缺网络或权限时明确哪些资料尚未取得，不把本地已有摘要写成最新检索结果。
- **子agent**：工具与授权允许时委派专门的头脑风暴职责；否则当前对话分别完成主线改进与方向审视，说明没有独立agent参与，不伪造多代理审查。
- **提问与展示**：有专门提问界面则使用；否则用普通文字提问。图表、笔记和结论保持Markdown等通用格式，不要求专有界面指令。
- **跨设备交接**：记录可核实的仓库、资料位置、原始结果和运行身份；另一设备的路径、访问权和服务连接须据实确认，不因文件同步而假定全部可用。

遇到不支持的能力，只调整执行方式并保留缺项；研究目标、既定协议、用户决策边界和证据要求保持原意。当前任务无需要时不额外检查所有工具或配置。
