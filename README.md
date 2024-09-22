# streampi
https://blog.hugozhu.site

# 使用Raspberry Pi和Streamdeck监控云原生大数据系统的稳定性

关键词：Raspberry Pi, StreamDeck, Uptime Kuma, DuckDB, Airflow, Aliyun SLS, DingTalk, Clickhouse, DataWorks, Grafana

## 引言

在云原生时代，应用的稳定性至关重要。本文将介绍如何利用树莓派和国产StreamDeck 这两个低成本的硬件来灵活监控云原生应用的稳定性，提高运维效率。

## 什么是 StreamDeck？

StreamDeck 是一款可编程的硬件设备，最初设计用于流媒体控制，但其灵活性使其成为了一个优秀的 IT 运维工具，国产妙联宝是StreamDeck的平替，价格很香。

## 什么是 Raspberry Pi？

树莓派（Raspberry Pi）是一款低成本的小型单板计算机，适合学习编程、物联网和DIY项目。它具备处理器、USB、HDMI等接口，常用于教育、家居自动化和机器人开发。

## 为什么选择 StreamDeck 监控系统稳定性？

- 快速访问：一键即可查看关键指标
- 可视化：通过 LED 按钮直观显示状态
- 自定义：可根据需求设置不同的监控项
- 提高效率：减少在多个监控界面间切换的时间
- 低成本低功耗：可24*7运行， 结合钉钉机器人还可以实现远程交互

## 运行环境配置

```bash
conda create -n streampi
conda install pip
pip -r reqirements.txt
```