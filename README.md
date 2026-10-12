# NetPatrol · 网络设备自动化巡检系统

一键批量登录网络设备、执行巡检命令、生成 HTML / TXT 报告，支持定时巡检与实时日志。

支持华为、华三、思科、锐捷、中兴等主流厂商设备，基于 [Netmiko](https://github.com/ktbyers/netmiko)。

---

## 功能

- **批量巡检** — 录入设备清单后多线程并发执行
- **多厂商** — 华为 / H3C / 思科 / 锐捷 / 中兴，支持 SSH、Telnet，可自定义 Netmiko 驱动
- **命令可配** — 按厂商自定义巡检命令（`config/commands.txt`）
- **报告输出** — 每台设备生成 HTML 或 TXT 报告，可在线预览、下载、批量清理
- **定时巡检** — 每日定时 / 指定日期，支持多轮次与失败自动重试
- **实时日志** — WebSocket 推送执行日志与进度
- **网络测试** — 内置 Ping 持续探测（含延迟曲线）与 Tracert 路由追踪
- **单机部署** — 前后端打包为一个 exe，双击即用

## 技术栈

后端基于 FastAPI 与 uvicorn 构建，网络设备连接由 Netmiko 完成；前端采用 Vue 3 + Vite，界面组件使用 Ant Design Vue；应用最终通过 PyInstaller 打包为免安装的单机程序。

## 快速开始

**环境**：Python 3.11+；Node.js 18+（仅前端开发/构建时需要）

```bash
# 1. 后端依赖
pip install -r requirements.txt

# 2. 前端依赖 + 构建
cd frontend && npm install && npm run build && cd ..

# 3. 启动（浏览器会自动打开 http://127.0.0.1:8000）
python run_app.py
```

前端资源由后端在每次请求时从磁盘读取，因此调整 `frontend/` 后，只需重新执行 `npm run build` 并刷新浏览器即可，无需重启服务；而后端代码（`backend/`、`modules/`）在进程启动时载入，修改后必须重启进程才会生效。

需要注意，服务仅在启动阶段检查 `frontend/dist` 是否存在。若启动时前端尚未构建，之后即使补上构建，也需要重启一次才能正常访问。

如需单独调整界面，可另起前端开发服务器，它已配置将 `/api` 代理至后端：

```bash
cd frontend && npm run dev
```

随后访问 http://localhost:5173 即可，页面改动支持热更新。

## 打包为可执行文件

```bash
pyinstaller NetPatrol.spec
```

打包完成后，可执行文件位于 `dist/NetPatrol/` 目录，可整体拷贝到未安装 Python 的机器上直接运行。

## 使用说明

### 添加设备

在界面右上角点击「添加设备」即可录入设备。其中**设备名称、设备类型、IP 地址、用户名、密码**为必填项；端口号与连接类型可以留空，此时按连接方式自动取默认值（SSH 为 `22`，Telnet 为 `23`）；若设备需要进入特权模式执行命令，请一并填写「提权密码」。

设备类型支持 `huawei`、`h3c`、`cisco`、`ruijie`、`zte` 五种常见厂商，也可以直接填写 Netmiko 的驱动名称，以便对接其它品牌设备。

录入的设备会保存在浏览器本地，下次打开页面时自动载入。

### 巡检命令（`config/commands.txt`）

按厂商分组，`[厂商]` 后跟命令列表：

```
[huawei]
display version
display ip interface brief

[cisco]
show version
show running-config
```

### 系统设置（`config/config.json`）

首次运行会自动生成。也可从示例复制后修改：

```bash
cp config/config.example.json config/config.json
```

## 目录结构

```
NetPatrol/
├─ run_app.py          启动入口
├─ backend/            FastAPI 后端（路由 / WebSocket / 定时调度 / 历史）
├─ modules/            巡检引擎（Netmiko 连接、设备解析、报告生成）
├─ config/             commands.txt（巡检命令）· config.json（系统设置）
├─ frontend/           Vue 3 前端
└─ reports/            巡检报告输出目录（运行时生成）
```

## 免责声明 / Disclaimer

本项目仅供网络运维人员在**已获授权**的网络环境中使用。

- 本工具会用你提供的凭据登录网络设备并执行命令（含读取运行配置）。请仅在你有权管理的设备上使用，并自行确认符合所属组织的安全与合规要求。
- 设备密码默认以**明文**保存在浏览器 `localStorage` 与 `config/config.json` 中。请勿在共享或不受信任的环境中使用，也不要将含真实设备的配置文件或 `reports/` 提交到公开仓库。
- 本软件按"现状"提供，不提供任何明示或暗示的担保。作者不对因使用本软件造成的网络中断、配置变更、数据丢失或其它任何损失承担责任。**在生产环境使用前请务必充分测试。**

## License

[MIT](LICENSE)
