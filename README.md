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

| 层 | 技术 |
|---|---|
| 后端 | FastAPI · uvicorn · Netmiko · openpyxl |
| 前端 | Vue 3 · Vite · Ant Design Vue · axios · dayjs |
| 打包 | PyInstaller |

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

> 前端改动**不需要**重启后端（静态文件每次请求都从磁盘读取）；后端改动需要重启进程。

**前端开发模式（可选）**

```bash
cd frontend && npm run dev     # http://localhost:5173，/api 已自动代理到 8000
```

## 打包成 exe

```bash
pyinstaller NetPatrol.spec
```

产物在 `dist/NetPatrol/`。（PyInstaller 采用 GPL + "打包例外"条款，用它打包自有/闭源项目是被允许的。）

## 使用说明

### 添加设备

在界面右上角点「添加设备」，填写以下信息：

| 字段 | 必填 | 说明 |
|---|---|---|
| 设备名称 | 是 | 如 `Core-SW-01` |
| 设备类型 | 是 | `huawei` / `h3c` / `cisco` / `ruijie` / `zte`，或自定义 Netmiko 驱动名 |
| IP地址 | 是 | 管理地址 |
| 端口号 | 否 | 默认 SSH `22` / Telnet `23` |
| 连接类型 | 否 | `ssh`（默认）/ `telnet` |
| 用户名 | 是 | |
| 密码 | 是 | |
| 提权密码 | 否 | enable 密码 |

设备列表保存在浏览器本地（localStorage），下次打开自动载入。

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
