# 1 机械臂 MCP 工具
- `Get_Arm_Status`
  获取当前机械臂状态，供 LLM、UI 等参考。
  返回内容通常为 JSON 文本，包含连接状态、IP、当前动作和忙碌状态。
- `Get_Arm_Profile`
  获取机械臂连接配置与型号信息。
  返回内容通常为 JSON 文本，包含 `arm_model`、`right_ip`、`left_ip`、`description`。
- `Connect_Arms`
  连接机械臂，支持连接单臂或双臂。
  参数：
  - `right_ip: Optional[str]`
    右臂 IP 地址；如果需要连接右臂，可传此参数。
  - `left_ip: Optional[str]`
    左臂 IP 地址；如果需要连接左臂，可传此参数。
  - `arm_model: Optional[int]`
    机械臂型号，当前支持 `65` 和 `75`，不传时默认按 `65` 连接。
  返回内容通常为普通文本，描述左右臂连接成功、失败或跳过情况。
- `Disconnect_Arms`
  断开所有已连接的机械臂，并安全释放资源。
  无参数。
  返回内容通常为普通文本，描述左右臂断开状态。
- `Capture_Current_Joint_Point`
  读取当前机械臂关节值，并保存到点位库。
  参数：
  - `point_id: str`
    点位唯一 ID。
  - `name: str`
    点位名称。
  - `arm_side: str`
    机械臂侧别，仅支持 `left` 或 `right`，默认 `right`。
  返回内容通常为 JSON 文本，包含保存结果和点位内容。
- `Get_Arm_Actions`
  获取当前动作库中的机械臂动作，其中 `action_id` 对应每个动作，可用于执行动作。
  无参数。
  返回内容通常为 JSON 文本，包含动作库版本、描述以及可执行动作列表。
- `Execute_Action`
  执行机械臂动作库中的预定义动作，同步执行并带互斥保护。
  参数：
  - `action_id: str`
    动作 ID，用于匹配动作并执行，应与动作库中的定义一致。
  返回内容通常为普通文本，表示动作执行成功、失败或机械臂正忙。
- `Emergency_Stop`
  机械臂急停，属于最高优先级中断操作。
  无参数。
  可在任何时刻调用，不受动作锁影响，会中断正在执行的动作，并强制停止所有已连接的机械臂。
  返回内容通常为普通文本，表示急停结果。

# 2 相机 MCP 工具
- `Get_Camera_Status`
  返回相机当前运行状态。
  无参数。
  返回内容通常为普通文本，典型值为 `RUNNING` 或 `STOPPED`。
- `Start_Camera`
  启动 RealSense D435i 摄像头线程。
  无参数。
  返回内容通常为普通文本，表示启动成功、已在运行或未检测到设备。
- `Stop_Camera`
  停止 RealSense D435i 摄像头线程。
  无参数。
  返回内容通常为普通文本，表示停止成功或当前无需停止。
- `Get_Latest_Frame`
  获取最新一帧 RGB 和 Depth 伪彩色图像。
  参数：
  - `quality: int`
    JPEG 编码质量，默认 `30`。
  返回内容通常为两个文本块，分别是 RGB JPEG 的 Base64 和 Depth 伪彩色 JPEG 的 Base64；若无帧，可能返回 `NO_FRAME`。
- `Save_Frames`
  启动 RealSense 相机并在后台保存指定时长的帧数据（RGB/Depth），线程内部自动计时结束。
  参数：
  - `save_dir: str`
    保存目录，默认 `./capture`。
  - `frame_interval: int`
    每隔多少帧保存一次，默认 `5`。
  - `save_color: bool`
    是否保存彩色图像，默认 `True`。
  - `save_depth: bool`
    是否保存深度图，默认 `True`。
  - `duration_seconds: int`
    保存持续时间，单位秒，默认 `60`。
  返回内容通常为普通文本，表示保存线程已启动。

# 3 底盘与滑台 MCP 工具
- `Get_Local_Waypoints`
  查询本地 `waypoints.json` 中已保存的 `waypoint_id` 和 `waypoint_name`。
  无参数。
  返回内容通常为 JSON 文本，包含点位数量和点位列表。
- `Navigate_To_Point`
  从本地点位文件读取 waypoint，并直传位姿发起导航。
  参数：
  - `waypoint_id: str`
    本地 `waypoints.json` 中已存在的点位 ID。
  - `task_id: Optional[str]`
    可选任务 ID；不传自动生成。
  - `recv_timeout_sec: float`
    等待终态消息超时，单位秒。
  返回内容通常为 JSON 文本，包含 `request`、`ack`、`final_message`、`feedback_count` 等。
- `Cancel_Navigation`
  取消当前正在执行的导航任务。
  参数：
  - `task_id: Optional[str]`
    可选任务 ID；不传自动生成。
  - `recv_timeout_sec: float`
    等待终态消息超时，单位秒。
  返回内容通常为 JSON 文本，终态消息类型一般为 `cancel_result` 或 `error`。
- `Capture_Current_Point`
  抓取当前位姿并返回 waypoint，同时同步保存到本地 `waypoints.json`。
  参数：
  - `waypoint_id: str`
    必填点位 ID，由客户端提供。
  - `waypoint_name: Optional[str]`
    可选点位名称。
  - `read_timeout_sec: float`
    读取位姿超时，默认 `2.0` 秒。
  - `waypoint_timeout_sec: float`
    返回点位默认导航超时，默认 `60.0` 秒。
  - `task_id: Optional[str]`
    可选任务 ID；不传自动生成。
  - `recv_timeout_sec: float`
    等待终态消息超时，单位秒。
  返回内容通常为 JSON 文本；成功时 `final_message.type` 为 `waypoint_captured`。
- `Set_Lift_Height`
  设置滑台绝对高度，单位 mm。
  参数：
  - `height_mm: int`
    目标高度，当前静态范围为 `0 ~ 250`。
  - `task_id: Optional[str]`
    可选任务 ID；不传自动生成。
  - `recv_timeout_sec: float`
    等待终态消息超时，单位秒，默认 `60.0`。
  返回内容通常为 JSON 文本，终态消息类型一般为 `lift_result` 或 `error`。
