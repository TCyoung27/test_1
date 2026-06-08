# SkillMiddleware 机制说明

## 1. 现有机制

`SkillMiddleware` 用于实现 Agent 的技能加载与工具动态暴露机制。当前框架中，技能不是一开始全部塞进提示词，而是先在系统提示词中提供可用技能目录，再由模型根据任务需要调用 `load_skill` 读取具体技能内容。

当前机制分为三层：

1. **技能发现**
   - `SkillLoader.scan_skills()` 扫描 `agent/skills/<skill_name>/` 目录。
   - 主技能文件优先使用 `SKILL.md`，同时兼容旧的 `skill.md`。
   - 通过 YAML frontmatter 解析 `name` 和 `description`，用于生成技能目录提示。

2. **主技能加载**
   - 模型调用 `load_skill(skill_name)`。
   - 读取该技能的 `SKILL.md / skill.md` 主说明。
   - `load_skill` 会更新 LangGraph 状态中的 `skills_loaded`。
   - `SkillMiddleware` 根据最新的 `skills_loaded` 判断当前技能，并在下一轮模型调用中暴露该技能对应的 MCP 工具。

3. **参考文件按需读取**
   - 模型可以调用 `load_skill(skill_name, file_path="references/xxx.md")`。
   - 该模式只读取技能目录内的 Markdown 参考文件，不更新 `skills_loaded`，也不切换当前技能。
   - 适合将复杂流程、失败处理、工具边界、示例等内容放入 `references/`，由模型在需要时主动读取。

当前推荐的技能目录结构：

```text
skill-name/
├── SKILL.md
└── references/
    ├── workflow.md
    ├── failure_policy.md
    ├── tool_usage.md
    └── examples.md
```

`SkillMiddleware` 目前采用单技能模式：如果历史上加载过多个技能，只取 `skills_loaded` 中最后一个作为当前技能。这样可以避免多技能工具同时暴露导致工具空间过大，也更符合当前作物表型采集智能体的主要使用场景。

## 2. 工具暴露逻辑

`SkillMiddleware` 初始化时始终保留基础工具：

```python
self.base_tools = [load_skill]
```

模型未加载技能时，只能看到基础工具和技能目录说明。加载某个主技能后：

- `expose_skill_tools=True`：在线运行、真实评估、UI 对话默认模式。中间件会把当前技能映射到的 MCP 工具暴露给模型。
- `expose_skill_tools=False`：离线评估隔离模式。模型可以读取主技能和 references，但不会真实暴露业务 MCP 工具，避免离线评估时查询本地配置或误调用硬件工具。

因此，离线评估中模型只能把业务工具写入最终 JSON 结果；真实运行中模型才会实际调用 MCP 工具。

## 3. 相比旧机制的优化

旧机制主要是“只加载一个主 `skill.md` 文件”。这种方式简单，但在作物表型采集这类复杂任务中存在几个问题：

1. **主文件过于臃肿**
   - 导航、滑台、机械臂、相机、失败处理、工具参数、示例都写在一个文件里，容易让主说明变得很长。
   - 模型读取后重点不够突出，复杂任务中容易忽略关键约束。

2. **细节和主流程混在一起**
   - 主流程、工具边界、异常策略、示例都放在同一层，后续维护成本高。
   - 修改某个局部策略时容易影响整体说明。

3. **不利于离线评估和真实任务共用**
   - 离线评估更关注“是否按规则规划工具链”。
   - 真实任务更关注“是否根据现场状态执行、失败时如何处理”。
   - 单文件很难同时兼顾两类场景的上下文粒度。

优化后的机制保留一个 `load_skill`，但通过 `file_path` 参数将它泛化为“读取技能目录内 Markdown 文件”的能力。这样既不增加新的工具名，也能支持主说明和参考材料分层。

改进效果：

- `SKILL.md` 可以保持精简，主要写触发条件、最高优先级规则、reference 索引。
- `references/workflow.md` 专门写完整采集流程。
- `references/failure_policy.md` 专门写失败处理和终止策略。
- `references/tool_usage.md` 专门写工具边界、参数来源和默认值原则。
- `references/examples.md` 专门写少量典型链路示例。

这种结构更接近成熟 Agent 的技能设计方式，同时仍然适配当前 MCP 工具调用框架。

## 4. 当前适用边界

当前机制只支持读取技能目录内的 Markdown 文件，不支持执行 `scripts/` 下的脚本。这样做是为了保持机制轻量，并避免真实硬件任务中引入额外执行风险。

如果后续需要进一步扩展，可以考虑：

- 支持 `references/` 下更多细分文档；
- 支持对 reference 文件列表进行显式索引；
- 在任务开始前根据用户输入自动建议模型读取某些 references；
- 视需要再评估是否支持 `scripts/`，但不建议在当前真实硬件评估阶段引入。

## 5. 总结

当前 `SkillMiddleware` 的核心思想是：让模型先知道有哪些技能，再按需读取主技能和参考文档，最后由中间件根据当前技能动态开放工具。

相比之前只加载一个主文件的机制，现在的设计更适合复杂智能体任务：主说明更清晰，细节可拆分，离线评估和真实运行可以共用同一套技能内容，同时通过 `expose_skill_tools` 控制是否真实暴露业务工具。
﻿
