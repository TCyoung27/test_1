# 2026-06-03 真实复杂任务 10 样本评估总结

## 评估说明

本次评估对象为 `phenotype_complex.json` 中 10 条真实复杂任务样本，任务均涉及导航、滑台、右臂和相机。评分依据同 `2026-06-01_181102_162114_real_phenotype_complex_001_review.md` 中的单样本规则。

参考文件：

- `2026-06-03_170238_625768_real_phenotype_complex_001_trace.json`
- `2026-06-03_170616_077910_real_phenotype_complex_002_trace.json`
- `2026-06-03_170909_874851_real_phenotype_complex_003_trace.json`
- `2026-06-03_171039_926243_real_phenotype_complex_004_trace.json`
- `2026-06-03_171306_129808_real_phenotype_complex_005_trace.json`
- `2026-06-03_171424_159443_real_phenotype_complex_006_trace.json`
- `2026-06-03_171825_221390_real_phenotype_complex_007_trace.json`
- `2026-06-03_171955_274575_real_phenotype_complex_008_trace.json`
- `2026-06-03_172355_415418_real_phenotype_complex_009_trace.json`
- `2026-06-03_172815_697570_real_phenotype_complex_010_trace.json`
- `2026_06_03.txt`

其中样本 6、8、9 的 trace 是强制结束后的保底 trace，`model_call_trace` 和 `tool_call_trace` 为空；这三条主要结合终端输出 `2026_06_03.txt` 进行判断。

## 评分标准

总分 100 分：

- 任务完成度 40 分：是否完成导航、滑台、右臂采集位、相机保存、右臂回关机位。
- 流程顺序 20 分：是否遵循“导航 -> 滑台 -> 右臂采集位 -> 保存数据 -> 右臂收尾”的合理顺序。
- 参数正确性 15 分：点位、高度、动作 ID、保存时长等关键参数是否正确。
- 异常处理 15 分：出现工具失败时是否能识别原因、合理重试、必要时终止任务。
- 效率与冗余控制 10 分：是否避免不必要工具调用、错误动作、重复查询或无意义补救。

特别说明：本轮任务中，`Navigate_To_Point` 是表型采集链路的关键前置步骤。若导航失败后改为“记录当前位置”并继续采集，不能视为到达目标采集点，因此任务完成度应明显扣分。

## 样本评分

| 样本 | 结论 | 完成度 | 顺序 | 参数 | 异常 | 效率 | 总分 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| real_phenotype_complex_001 | 成功 | 40 | 18 | 15 | 14 | 7 | 94 |
| real_phenotype_complex_002 | 失败后错误继续 | 20 | 5 | 11 | 2 | 3 | 41 |
| real_phenotype_complex_003 | 成功 | 40 | 18 | 15 | 15 | 7 | 95 |
| real_phenotype_complex_004 | 失败后错误继续 | 20 | 5 | 11 | 2 | 4 | 42 |
| real_phenotype_complex_005 | 成功但有冗余动作 | 40 | 18 | 12 | 13 | 7 | 87 |
| real_phenotype_complex_006 | 导航失败后未正确终止 | 5 | 5 | 7 | 5 | 3 | 20 |
| real_phenotype_complex_007 | 成功 | 40 | 18 | 15 | 15 | 7 | 95 |
| real_phenotype_complex_008 | 导航失败后错误继续且被截断 | 12 | 3 | 9 | 1 | 1 | 26 |
| real_phenotype_complex_009 | 导航失败后错误继续且被截断 | 8 | 3 | 9 | 2 | 2 | 22 |
| real_phenotype_complex_010 | 导航失败后基本终止 | 8 | 14 | 13 | 14 | 3 | 52 |

平均分：**57.9 / 100**

## 逐样本评语

### real_phenotype_complex_001：94 / 100

工具链路完整执行了 `point_collect_1` 导航、滑台 0 mm、右臂 `r_collect`、`Save_Frames(duration_seconds=5)` 和 `r_shutdown`。整体任务成功。主要扣分点是相机启动略早于右臂到达采集位，以及存在少量前置查询冗余。

### real_phenotype_complex_002：41 / 100

`Navigate_To_Point(point_collect_2)` 返回失败后，Agent 没有终止任务，也没有使用同一目标点进行合理闭环恢复，而是调用 `Capture_Current_Point` 记录当前位置并继续执行滑台、机械臂和相机保存。最终输出中还把“当前位置作为替代点”描述为任务完成，这与任务目标不一致。该样本核心失败点是导航失败后错误继续执行。

### real_phenotype_complex_003：95 / 100

成功完成 `point_collect_3` 导航、滑台 50 mm、右臂采集位、6 秒 RGB-D 保存和右臂关机位。工具参数正确，链路完整。主要扣分点是相机启动早于右臂采集动作，流程可进一步收紧。

### real_phenotype_complex_004：42 / 100

`Navigate_To_Point(point_collect_4)` 失败后，Agent 同样调用 `Capture_Current_Point` 并继续完成滑台、右臂和相机保存。虽然后续硬件动作大多成功，但采集位置不是目标采集点 4，因此不能判定为真实任务完成。该样本暴露出与样本 2 相同的关键问题。

### real_phenotype_complex_005：87 / 100

成功导航至 `point_collect_5`，滑台设置为 100 mm，最终执行 `r_collect`、保存 8 秒 RGB-D 数据并执行 `r_shutdown`。扣分点是先尝试了错误动作 `collect_position_right`，随后才改用正确动作 `r_collect`；此外最后额外调用了 `Stop_Camera`，属于用户未明确要求的收尾动作。

### real_phenotype_complex_006：20 / 100

终端日志显示 Agent 查询点位和动作后，两次调用 `Navigate_To_Point(point_collect_6)` 均失败。之后没有终止任务，而是继续查询相机状态、连接机械臂，并在旧版脚本超时机制下被截断。由于没有完成目标采集点到达，也没有完成滑台、采集、保存和收尾，评分较低。

### real_phenotype_complex_007：95 / 100

成功完成 `point_collect_7` 导航、滑台 150 mm、右臂 `r_collect`、6 秒 RGB-D 保存和 `r_shutdown`。工具参数正确，任务闭环完整。主要扣分点同样是相机启动早于右臂采集位动作，属于轻微流程优化点。

### real_phenotype_complex_008：26 / 100

终端日志显示两次 `Navigate_To_Point(point_collect_8)` 均失败，随后 Agent 调用 `Capture_Current_Point`、设置滑台、连接机械臂、执行采集动作并启动相机，之后被强制截断。该样本不仅没有到达目标采集点，还在导航失败后继续执行依赖任务，并记录当前位置，属于严重流程错误。

### real_phenotype_complex_009：22 / 100

终端日志显示两次 `Navigate_To_Point(point_collect_9)` 失败后，Agent 继续查询机械臂和相机状态、设置滑台并启动相机，后续被强制截断。相比样本 8，未看到 `Capture_Current_Point`，但仍然违反“导航失败后终止依赖链路”的原则。

### real_phenotype_complex_010：52 / 100

`Navigate_To_Point(point_collect_10)` 两次失败后，Agent 没有继续执行滑台、机械臂采集和数据保存，而是在最终输出中说明“按照任务规则应该终止任务”，并请求用户确认是否继续。这个样本没有完成实际采集任务，但异常处理明显优于样本 2、4、6、8、9。扣分点是导航失败后仍额外查询了机械臂状态、相机状态和动作库，存在不必要动作。

## 总体结论

本轮 10 个复杂真实任务中，可以判定完整成功的样本为 **4 条**：1、3、5、7。样本 5 虽有错误动作尝试，但最终完成闭环。

主要失败原因不是相机、滑台或机械臂本身，而是 **导航失败后的任务控制策略不稳定**：

- 样本 2、4、8 在导航失败后调用 `Capture_Current_Point`，把当前位置当作替代采集点继续执行。
- 样本 6、9 在导航失败后仍继续执行后续设备准备或动作。
- 样本 10 能识别导航失败后应终止，是本轮失败样本中最接近合理策略的一条。

从 judge 角度看，当前 Agent 在“正常到达目标点”时具备较好的多硬件闭环能力；但在“导航失败”这种关键前置失败场景下，策略明显不稳定。后续应优先重构 `crop_phenotype_collection/skill.md` 中的异常处理与工具边界，尤其要明确：

- `Navigate_To_Point` 是完整采集链路的关键前置步骤。
- 导航失败后最多允许对同一 `waypoint_id` 重试一次。
- 重试仍失败必须终止当前采集链路。
- 不允许用 `Capture_Current_Point` 作为导航失败后的补救。
- `Capture_Current_Point` 只能在用户明确要求记录当前位置或新增点位时调用。
