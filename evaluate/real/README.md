## 部署与启动

```bash

cd nav\\\_control
./start\\\_gateway.sh
```

## 请求类型总览

1. `navigate\\\_to\\\_point`：客户端直传 waypoint 导航
2. `capture\\\_current\\\_point`：抓取当前位置并返回 waypoint（服务端不落盘）
3. `cancel\\\_navigation`：取消当前导航
4. `set\\\_lift\\\_height`：设置滑台绝对高度（单位 mm）
