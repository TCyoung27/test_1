# 真实评测数据集数量记录

本文档记录当前真实评测数据集的已构建样本数量，后续扩展数据集时同步更新。

## 1. 当前已构建数据集

### phenotype_simple.json

当前版本样本总数：

```text
162 条
```

按主样本编号统计：

| 类别 | 样本编号范围 | 数量 | 说明 |
|---|---|---:|---|
| `camera` | `real_simple_camera_001` - `real_simple_camera_050` | 50 | 已基本按当前设计一次到位 |
| `arm` | `real_simple_arm_001` - `real_simple_arm_044` | 44 | 覆盖右臂、左臂和双臂关机相关动作 |
| `navigation` | `real_simple_navigation_001` - `real_simple_navigation_020` | 20 | 当前基于已有 10 个 `point_collect_*` 点位设计 |
| `lift` | `real_simple_lift_001` - `real_simple_lift_020` | 20 | 已覆盖 0-250mm 范围内多个高度和表达 |
| `safety` | `real_simple_safety_001` - `real_simple_safety_028` | 28 | 新增 safety 主样本 |
| **合计** |  | **162** |  |

按 `task_type` 标签展开统计时，部分样本会同时属于多个模块。例如 safety 样本可能同时带有 `camera`、`arm`、`navigation` 标签。

当前展开统计：

| 标签 | 数量 |
|---|---:|
| `camera` | 60 |
| `arm` | 53 |
| `navigation` | 29 |
| `safety` | 30 |
| `lift` | 20 |

说明：

- `safety` 标签总数为 30，其中 28 条是 `real_simple_safety_*` 主样本，另外 2 条来自 `real_simple_arm_021` 和 `real_simple_arm_022`。
- `camera`、`arm`、`navigation` 的标签数量大于主样本数量，是因为部分 safety 样本同时带有硬件模块标签。
- 当前 simple 已按“单模块、单目标任务”收束；原先显式多步骤或多模块停止表达已改写为单目标表达，或补充到 basic 数据集中。
- 机械臂新增 `real_simple_arm_025` - `real_simple_arm_044`，覆盖左臂配置与连接、左臂 `l_shutdown / l_initial / l_collect`、左臂动作查询，以及双臂关机动作查询和执行。

### phenotype_basic.json

当前版本样本总数：

```text
149 条
```

按主样本编号统计：

| 类别 | 样本编号范围 | 数量 | 说明 |
|---|---|---:|---|
| `camera` 单模块多步骤 | `real_basic_camera_001` - `real_basic_camera_020` | 20 | 相机状态、启动、保存、预览、停止等短链路 |
| `arm` 单模块多步骤 | `real_basic_arm_001` - `real_basic_arm_034` | 34 | 右臂、左臂和少量双臂连接、状态、动作、释放等短链路 |
| `navigation` 单模块多步骤 | `real_basic_navigation_001` - `real_basic_navigation_014` | 14 | 点位查询、导航、取消、记录当前位置 |
| `navigation + lift` | `real_basic_navigation_lift_001` - `real_basic_navigation_lift_016` | 16 | 到点后设置滑台高度 |
| `arm + camera` | `real_basic_arm_camera_001` - `real_basic_arm_camera_026` | 26 | 右臂/左臂动作、双臂关机与相机预览/保存/关闭协同 |
| `navigation + camera` | `real_basic_navigation_camera_001` - `real_basic_navigation_camera_012` | 12 | 到点后相机预览、状态查询或保存 |
| `navigation + arm` | `real_basic_navigation_arm_001` - `real_basic_navigation_arm_014` | 14 | 到点后连接或执行右臂、左臂、双臂代表性动作 |
| 其他边界组合 | `real_basic_boundary_001` - `real_basic_boundary_008` | 8 | `lift + camera`、`lift + arm` 等两模块边界组合 |
| `lift` 单模块多步骤 | `real_basic_lift_001` | 1 | 滑台两段高度调整 |
| `safety` 两模块停止 | `real_basic_safety_001` - `real_basic_safety_004` | 4 | 两个硬件模块以内的安全停止短链路 |
| **合计** |  | **149** |  |

按 `task_type` 标签展开统计：

| 标签 | 数量 |
|---|---:|
| `camera` | 65 |
| `arm` | 81 |
| `navigation` | 58 |
| `lift` | 25 |
| `safety` | 4 |

说明：

- 当前 basic 已加入左臂和双臂代表性短链路，不对右臂已有样本做机械复制。
- 当前导航样本只使用已有 `point_collect_1` 到 `point_collect_10`。
- basic 中允许一个 MCP 硬件服务内多个工具调用，例如相机的“查询状态 -> 启动 -> 保存”，机械臂的“连接 -> 查询状态 -> 执行动作”。
- basic 新增少量滑台单模块多步骤和两模块安全停止样本，用于承接从 simple 中收束出的显式多步骤能力。

## 2. 当前设计限制

当前 `phenotype_simple.json` 和 `phenotype_basic.json` 未强行补满 README 中的规划数量，主要原因如下：

1. **机械臂**
   - 当前 simple 已包含右臂、左臂和双臂关机相关样本。
   - 右臂动作主要包括 `r_shutdown`、`r_initial`、`r_collect`、`r_wave`。
   - 左臂动作主要包括 `l_shutdown`、`l_initial`、`l_collect`。
   - 双臂当前只设计关机动作样本，不区分同时或顺序关机。

2. **导航**
   - 当前 `waypoints.json` 中已有 10 个真实采集点：`point_collect_1` 到 `point_collect_10`。
   - 后续点位扩展后，可继续补充更多导航语义和点位组合样本。

3. **写入类任务**
   - `Capture_Current_Point` 会写入 `waypoints.json`，当前只保留少量样本。
   - `Capture_Current_Joint_Point` 会写入机械臂关节点库，且重复运行可能与已有 `point_id` 冲突，当前 simple 数据集暂未纳入。

## 3. 后续扩展方向

后续若硬件和配置完善，可按以下方向扩展：

| 数据集 | 当前数量 | 规划目标 | 后续重点 |
|---|---:|---:|---|
| `phenotype_simple.json` | 162 | 200 左右 | 扩展更多导航点、更多写入类任务和机械臂动作语义 |
| `phenotype_basic.json` | 149 | 180 左右 | 继续扩展更多导航点组合、写入类短链路和少量两模块边界组合 |
| `phenotype_complex.json` | 待整理 | 160 左右 | 完整表型采集、多点采集、状态复用 |
| `exception_handling.json` | 0 | 80 左右 | 失败重试、失败终止、安全中断 |

当前阶段建议先基于 `phenotype_simple.json` 和 `phenotype_basic.json` 跑通基础真实评测流程，再继续整理 `phenotype_complex.json`。
