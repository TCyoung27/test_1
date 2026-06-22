# 2026-06-18 真实复杂任务 10 样本评估总结

## 评估说明

本次评估对象为优化 `skill load` 与 `crop_phenotype_collection` 技能内容后的 10 条真实复杂任务样本。任务均涉及导航、滑台、右臂和相机，评估方式沿用 2026-06-03 第一轮复杂任务评估中的 100 分制。

参考文件：

- `2026-06-18_201708_025772_real_phenotype_complex_001_trace.json`
- `2026-06-18_201802_000863_real_phenotype_complex_002_trace.json`
- `2026-06-18_201930_276647_real_phenotype_complex_003_trace.json`
- `2026-06-18_202043_272269_real_phenotype_complex_004_trace.json`
- `2026-06-18_202156_145297_real_phenotype_complex_005_trace.json`
- `2026-06-18_202754_308969_real_phenotype_complex_006_trace.json`
- `2026-06-18_202925_486083_real_phenotype_complex_007_trace.json`
- `2026-06-18_203236_659855_real_phenotype_complex_008_trace.json`
- `2026-06-18_203429_412005_real_phenotype_complex_009_trace.json`
- `2026-06-18_203542_577533_real_phenotype_complex_010_trace.json`

与第一轮不同，本轮 10 条样本均生成了完整 trace 文件，没有出现强制截断后的空 `model_call_trace` / `tool_call_trace` 保底 trace。

## 评分标准

总分 100 分：

- 任务完成度 40 分：是否完成导航、滑台、右臂采集位、相机保存、右臂回关机位。
- 流程顺序 20 分：是否遵循“导航 -> 滑台 -> 右臂采集位 -> 保存数据 -> 右臂收尾”的合理顺序。
- 参数正确性 15 分：点位、高度、动作 ID、保存时长等关键参数是否正确。
- 异常处理 15 分：出现工具失败时是否能识别原因、合理重试、必要时终止任务。
- 效率与冗余控制 10 分：是否避免不必要工具调用、错误动作、重复查询或无意义补救。

特别说明：本轮仍将 `Navigate_To_Point` 视为完整表型采集链路的关键前置步骤。若导航失败后重试仍失败，应终止当前采集链路，不继续滑台、机械臂和相机保存等依赖步骤。

## 样本评分

| 样本 | 结论 | 完成度 | 顺序 | 参数 | 异常 | 效率 | 总分 | 第一轮分数 | 变化 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| real_phenotype_complex_001 | 成功，流程更规范 | 40 | 20 | 15 | 14 | 8 | 97 | 94 | +3 |
| real_phenotype_complex_002 | 成功 | 40 | 19 | 15 | 14 | 7 | 95 | 41 | +54 |
| real_phenotype_complex_003 | 成功，流程更规范 | 40 | 20 | 15 | 15 | 7 | 97 | 95 | +2 |
| real_phenotype_complex_004 | 成功 | 40 | 19 | 15 | 14 | 6 | 94 | 42 | +52 |
| real_phenotype_complex_005 | 成功，失败重试正确 | 40 | 19 | 15 | 15 | 5 | 94 | 87 | +7 |
| real_phenotype_complex_006 | 成功 | 40 | 19 | 15 | 14 | 7 | 95 | 20 | +75 |
| real_phenotype_complex_007 | 导航失败后正确终止 | 8 | 17 | 14 | 15 | 7 | 61 | 95 | -34 |
| real_phenotype_complex_008 | 成功 | 40 | 19 | 15 | 15 | 7 | 96 | 26 | +70 |
| real_phenotype_complex_009 | 成功 | 40 | 20 | 15 | 15 | 7 | 97 | 22 | +75 |
| real_phenotype_complex_010 | 成功 | 40 | 19 | 15 | 14 | 7 | 95 | 52 | +43 |

平均分：**92.1 / 100**

第一轮平均分：**57.9 / 100**

平均分提升：**+34.2 分**

完整成功样本数：**9 / 10**

正确异常终止样本数：**1 / 10**

## 逐样本评语

### real_phenotype_complex_001：97 / 100

工具链路完整执行了 `point_collect_1` 导航、滑台 0 mm、右臂 `r_collect`、相机启动、`Save_Frames(duration_seconds=5)` 和右臂 `r_shutdown`。与第一轮相比，本轮在右臂到达采集位后才启动相机并保存数据，流程顺序更符合标准采集链路。轻微扣分点是仍有少量必要性不强的查询与连接准备。

### real_phenotype_complex_002：95 / 100

第一轮中该样本因 `Navigate_To_Point(point_collect_2)` 失败后调用 `Capture_Current_Point` 并继续采集，被判为“失败后错误继续”。本轮成功导航到 `point_collect_2`，随后完成滑台 25 mm、右臂 `r_collect`、5 秒 RGB-D 保存和 `r_shutdown`。核心提升是没有再出现“当前位置替代目标点”的错误策略。

### real_phenotype_complex_003：97 / 100

成功完成 `point_collect_3` 导航、滑台 50 mm、右臂采集位、6 秒 RGB-D 保存和右臂关机位。与第一轮相比，采集顺序更干净，未出现相机过早启动的问题。该样本展示了优化后标准完整链路的稳定性。

### real_phenotype_complex_004：94 / 100

第一轮中该样本导航失败后继续采集，并把当前位置作为替代点，导致任务目标不成立。本轮成功到达 `point_collect_4`，滑台升至 75 mm，右臂执行 `r_collect`，保存 5 秒 RGB-D 后执行 `r_shutdown`。主要扣分点是额外调用 `Get_Arm_Profile`，以及相机已运行时仍调用 `Start_Camera`，属于轻微冗余。

### real_phenotype_complex_005：94 / 100

该样本是本轮最能体现失败策略优化的例子。第一次 `Navigate_To_Point(point_collect_5)` 返回失败后，Agent 对同一 `waypoint_id` 重试一次并成功；随后 `Set_Lift_Height(height_mm=100)` 第一次失败，Agent 主动加载 `references/failure_policy.md`，再使用相同高度重试并成功。之后正确执行 `r_collect`、启动相机、保存 8 秒 RGB-D 和 `r_shutdown`。

相比第一轮，该样本不再尝试错误动作 `collect_position_right`，而是通过 `Get_Arm_Actions` 使用真实动作 ID `r_collect`。扣分点是最后额外执行了 `Stop_Camera` 和 `Disconnect_Arms`，用户未明确要求释放设备，效率分略降。

### real_phenotype_complex_006：95 / 100

第一轮中样本 6 两次导航失败后仍继续查询相机状态、连接机械臂，并最终被截断。本轮成功导航到 `point_collect_6`，滑台设置为 125 mm，右臂进入采集位，保存 5 秒 RGB-D 后回到关机位。该样本从低分失败样本转为完整成功样本，说明新一轮测试中正常链路稳定性明显提升。

### real_phenotype_complex_007：61 / 100

本轮两次 `Navigate_To_Point(point_collect_7)` 均返回失败。Agent 在重试失败后直接终止采集链路，并在最终回复中说明不能继续执行滑台、机械臂动作和数据采集步骤。虽然原始采集任务没有完成，因此完成度得分较低，但异常处理完全符合当前技能策略。

该样本与第一轮评分相比下降，是因为第一轮该样本真实导航成功并完成了采集；本轮真实环境中导航失败。不过从策略角度看，本轮表现更安全：没有继续执行任何依赖目标点位的后续动作。

### real_phenotype_complex_008：96 / 100

第一轮中样本 8 两次导航失败后仍调用 `Capture_Current_Point`、设置滑台、连接机械臂并启动相机，属于严重流程错误。本轮成功导航到 `point_collect_8`，完成滑台 175 mm、右臂 `r_collect`、5 秒 RGB-D 保存和 `r_shutdown`。该样本从“失败后错误继续且被截断”提升为完整成功。

### real_phenotype_complex_009：97 / 100

第一轮中样本 9 导航失败后仍继续执行后续设备准备动作。本轮成功导航到 `point_collect_9`，滑台设置为 200 mm，右臂执行 `r_collect`，启动相机保存 8 秒 RGB-D，并执行 `r_shutdown`。流程顺序和参数均正确，是本轮提升最明显的样本之一。

### real_phenotype_complex_010：95 / 100

第一轮中样本 10 两次导航失败后基本能终止任务，但仍额外查询机械臂状态、相机状态和动作库。本轮成功导航到 `point_collect_10`，滑台升到 250 mm，右臂进入采集位，保存 10 秒 RGB-D 到 `./capture_point10`，最后右臂回关机位。扣分点是相机已运行时仍调用 `Start_Camera`，属于轻微冗余。

## 提升示例分析

### 示例 1：导航失败后的依赖链路保护

第一轮主要问题是导航失败后仍继续执行依赖步骤，典型样本包括 2、4、6、8、9。优化后，样本 7 清楚展示了新的失败处理策略：

```text
Navigate_To_Point(point_collect_7) -> ok=false
Navigate_To_Point(point_collect_7) -> ok=false
终止任务，不继续 Set_Lift_Height / Execute_Action / Save_Frames
```

这说明 skill 中关于“导航失败后最多同点重试一次，仍失败则终止采集链路”的规则已经被 Agent 正确采用。

### 示例 2：工具失败后按 failure_policy 重试

样本 5 中同时出现导航失败和滑台失败：

```text
Navigate_To_Point(point_collect_5) -> ok=false
Navigate_To_Point(point_collect_5) -> ok=true
Set_Lift_Height(height_mm=100) -> ok=false
load_skill(... references/failure_policy.md)
Set_Lift_Height(height_mm=100) -> ok=true
```

这个链路比第一轮更好，因为 Agent 没有换点、没有记录当前位置作为替代点，也没有忽略滑台失败继续采集，而是读取失败处理策略后对相同参数进行一次合理重试。

### 示例 3：动作 ID 使用更稳定

第一轮样本 5 曾尝试不存在或不合适的动作 `collect_position_right`，随后才改为 `r_collect`。本轮复杂任务中，Agent 普遍通过 `Get_Arm_Actions` 获取动作库后使用真实存在的 `r_collect` 和 `r_shutdown`，未再出现错误动作 ID 造成的明显扣分。

### 示例 4：标准采集顺序更符合任务语义

第一轮多个成功样本存在相机启动早于右臂采集位动作的问题。本轮样本 1、3、9 等更符合以下顺序：

```text
Get_Local_Waypoints
Navigate_To_Point
Set_Lift_Height
Connect_Arms / Get_Arm_Actions
Execute_Action(r_collect)
Start_Camera 或确认相机运行
Save_Frames
Execute_Action(r_shutdown)
```

这更贴合作物表型采集的真实语义：先到位、调整高度、机械臂到采集姿态，再保存 RGB-D 数据。

## 总体结论

本轮 10 个复杂真实任务中，完整成功样本为 **9 条**，异常正确终止样本为 **1 条**。与第一轮相比，最关键的提升不是单个工具调用成功率，而是任务控制策略变得稳定：

- 导航失败后不再调用 `Capture_Current_Point` 作为错误补救。
- 导航失败后不再继续执行滑台、机械臂和相机保存等依赖步骤。
- 工具返回 `ok=false` 后，Agent 能在部分样本中加载 `failure_policy.md` 并按策略重试。
- 机械臂动作 ID 使用更稳定，主要使用动作库中的 `r_collect` 与 `r_shutdown`。
- 标准采集链路顺序更接近“导航 -> 滑台 -> 右臂采集位 -> 相机保存 -> 右臂收尾”。

仍需优化的点：

- 相机已运行时，部分样本仍重复调用 `Start_Camera`。
- 少数样本在用户未明确要求时执行 `Stop_Camera` 或 `Disconnect_Arms`，属于收尾冗余。
- 若要进一步提升效率分，可在技能中更明确“只在用户要求释放设备或任务策略要求时才停止相机/断开机械臂”。

整体来看，优化后的 skill load 与技能内容显著改善了复杂任务中的失败处理和流程稳定性，尤其修复了第一轮中最严重的“导航失败后错误继续采集”问题。
