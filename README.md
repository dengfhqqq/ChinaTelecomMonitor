# ChinaTelecomMonitor（多账号自用版）

> 本项目 **Fork 自 [Cp0204/ChinaTelecomMonitor](https://github.com/Cp0204/ChinaTelecomMonitor)**，基于原项目进行微小修改，仅作个人使用，充分尊重原作者的开发成果。


## 原项目介绍
中国电信 话费、通话、流量 套餐用量监控工具，支持青龙面板部署、本地保存登录 Token、多通知渠道推送，原项目特性如下：
- ✅ 支持青龙面板定时监控
- ✅ 本地保存登录 Token，有效期内不重复登录
- ✅ 支持 Docker 独立部署 API 服务
- ✅ 多通知渠道配置（原项目支持 Bark、WxPusher 等）


## 本版本修改点（与原项目差异）
1. **核心功能**：新增「多账号监控」支持，通过 `TELECOM_USER` 环境变量用 `&` 分隔多个账号（格式：`手机号1密码1&手机号2密码2`）；
2. **适配调整**：微调 `telecom_monitor.py` 代码，支持按账号独立记录登录状态、失败次数，避免多账号互相干扰；
3. **声明**：本版本所有代码修改由 AI 辅助完成，仅作个人学习和自用，不用于商业用途。


## 部署说明（自用版）
### 青龙面板拉库命令ql repo https://github.com/dengfhqqq/ChinaTelecomMonitor.git "telecom_monitor" "" "telecom_class|notify"
### 环境变量配置
| 环境变量         | 示例                          | 备注                                  |
|------------------|-------------------------------|---------------------------------------|
| `TELECOM_USER`   | `17388852667123456&19195519970654321` | 多账号用 `&` 分隔，每个账号为「11位手机号+6位服务密码」 |
| `TELECOM_FLUX_PACKAGE` | `true`（默认）              | 是否推送流量包明细，`false` 仅推送基础信息 |


## 致谢（完全保留原项目致谢）
- 原项目作者 [Cp0204](https://github.com/Cp0204)：感谢开发核心监控功能；
- 参考项目：[ChinaTelecomMonitor（Go 语言实现）](https://github.com/xxx/ChinaTelecomMonitor)（原项目标注的参考）；
- 接口支持：[boxjs](https://github.com/xxx/boxjs)（原项目标注的接口来源）。


## 免责声明
1. 本项目仅作个人学习使用，请勿用于商业或非法用途；
2. 使用过程中请遵守中国电信相关服务条款，切勿频繁请求接口，避免账号风控；
3. 账号密码等敏感信息仅本地保存，请勿泄露给他人，风险自负。
