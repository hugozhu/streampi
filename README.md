# StreamPi - 低成本快速响应系统监控工具
> The Low-Cost Fast Response System Monitoring Tool

![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-0.1.1-orange.svg)

**项目主页**: https://blog.hugozhu.site

## 项目简介

StreamPi 是一款基于 Raspberry Pi 和 StreamDeck 的智能运维监控系统，旨在为 DevOps 和 SRE 团队提供低成本、高效能的监控解决方案。通过可编程的物理按键和可视化界面，实现对云原生应用和基础设施的实时监控与快速响应。

### 核心特性

- **快速响应**：物理按键一键查看关键指标，无需切换多个监控界面
- **可视化直观**：通过 LED 按钮实时显示系统状态和告警
- **高度可扩展**：插件化架构，支持自定义监控项和集成
- **低成本部署**：基于树莓派和国产 StreamDeck（妙控宝），24x7 运行低功耗
- **远程协作**：集成钉钉机器人，支持远程交互和告警通知
- **REST API**：提供完整的 HTTP API，支持外部系统集成

### 支持的监控场景

- 云原生应用监控（Kubernetes、Docker）
- 数据库性能监控（ClickHouse、DuckDB）
- 大数据平台监控（Airflow、DataWorks）
- 日志分析（Aliyun SLS）
- 服务可用性监控（Uptime Kuma）
- 自定义指标展示（加密货币价格、金价等）

### 技术栈

- **后端框架**: FastAPI + Uvicorn
- **异步编程**: asyncio + uvloop
- **硬件驱动**: StreamDock SDK
- **消息集成**: 钉钉 Stream API
- **数据处理**: Pandas + DuckDB
- **图形渲染**: Cairo + CairoSVG

## 什么是 StreamDeck？

StreamDeck 是一款可编程的硬件设备，配备多个可自定义的 LCD 按键，最初设计用于流媒体控制。其灵活性使其成为优秀的 IT 运维工具。国产**妙控宝（MiraBox）**是 StreamDeck 的高性价比替代品。

## 什么是 Raspberry Pi？

树莓派（Raspberry Pi）是一款低成本的单板计算机，具备完整的 Linux 系统支持，适合物联网、自动化和边缘计算场景。其低功耗特性使其成为 24x7 运行监控系统的理想选择。

## 为什么选择 StreamPi？

| 优势 | 说明 |
|------|------|
| **即时响应** | 物理按键点击，毫秒级响应，无需打开浏览器或切换窗口 |
| **视觉直观** | LED 背光和图标实时反映系统状态，一眼识别异常 |
| **灵活定制** | 插件化架构，轻松添加新的监控项和集成 |
| **成本低廉** | 硬件成本仅需几百元，开源软件免费使用 |
| **移动友好** | 集成钉钉机器人，随时随地接收告警和远程操作 |
| **低功耗** | 24x7 运行，年耗电成本不足 50 元 |

## 快速开始

### 硬件要求

- Raspberry Pi 3B+ 或更高版本（推荐 4B/5）
- StreamDeck 设备（Elgato StreamDeck 或妙控宝 MiraBox）
- 4GB+ SD 卡（推荐 16GB+）
- 稳定的网络连接

### 软件要求

- Python 3.12+
- Raspberry Pi OS (Debian-based) 或 Ubuntu
- uv 包管理器（推荐）或 pip

### 安装步骤

#### 1. 安装系统依赖

```bash
# 安装 USB 和图形库依赖
sudo apt update
sudo apt install -y libudev-dev libusb-1.0-0-dev libhidapi-libusb0
sudo apt install -y libcairo2 libcairo2-dev

# 安装 Python 依赖工具
pip install pyudev
```

#### 2. 配置 USB 设备权限

为 StreamDeck 设备添加 udev 规则，允许非 root 用户访问：

```bash
# Elgato StreamDeck 设备
sudo tee /etc/udev/rules.d/10-streamdeck.rules << EOF
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0fd9", GROUP="users", TAG+="uaccess"
EOF

# 妙控宝 StreamDock 设备
sudo tee /etc/udev/rules.d/20-streamdock.rules << EOF
SUBSYSTEMS=="usb", ATTRS{idVendor}=="5500", GROUP="users", TAG+="uaccess", ATTR{idProduct}=="1001", MODE="0666"
EOF

# 重载 udev 规则
sudo udevadm control --reload-rules
sudo udevadm trigger
```

#### 3. 安装 StreamPi

**方法 A：使用 uv（推荐）**

```bash
# 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/hugozhu/streampi.git
cd streampi

# 安装依赖
uv sync
```

**方法 B：使用 pip**

```bash
# 克隆项目
git clone https://github.com/hugozhu/streampi.git
cd streampi

# 创建虚拟环境（可选）
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .
```

#### 4. 配置文件

复制示例配置并根据需求修改：

```bash
cp config_sample.json config.json
```

编辑 `config.json`，配置端口、设备型号、代理和插件：

```json
{
  "server_port": 8001,
  "device_model": "streamdock",
  "proxy": "socks5://localhost:11081",
  "dingtalk": {
    "token": "your-dingtalk-token"
  },
  "plugins": [
    {
      "type": "DingtalkPlugin",
      "access_token": "your-token",
      "access_key": "your-key",
      "access_secret": "your-secret"
    }
  ]
}
```

#### 5. 启动服务

```bash
# 使用 FastAPI CLI（开发模式，支持热重载）
fastapi dev main.py --port 8000

# 或者使用生产模式
fastapi run main.py --port 8000

# 或者直接运行
python main.py --port 8000 --log info
```

服务启动后，访问 http://localhost:8000/docs 查看 API 文档。

### 故障排除

#### USB 设备无响应

如果按键失灵，可以重置 USB 设备：

```bash
# 查找设备
lsusb

# 重置指定设备
sudo usbreset <bus-id>:<device-number>
# 例如: sudo usbreset 001:015
```

#### 权限问题

确保当前用户在 `users` 组中：

```bash
sudo usermod -aG users $USER
# 重新登录以使组权限生效
```

#### 依赖安装失败

如果 Cairo 相关依赖安装失败：

```bash
sudo apt install -y pkg-config python3-dev
```
