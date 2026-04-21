# 湿法冶镍设备管理系统（Nickel Plant EMS）

> 印尼某湿法冶镍项目现场设备管理系统 · 移动端优先 · 云端协作

[![Live](https://img.shields.io/badge/live-online-brightgreen)](https://haoxinglong404.github.io/nickel-ems/)
[![Version](https://img.shields.io/badge/version-v0.8-blue)](./CHANGELOG.md)

---

## 🌿 这是什么

一个为**湿法冶镍车间**设计的设备管理移动 Web 应用，运行在印尼生产现场。核心解决五件事：

1. **设备台账** — 361 台设备，4 个安装区域（201/202/203/316-1），位号命名规范严格
2. **工单流程** — 5 种角色（管理员/提报人/审批人/维修人/只读人）协作，从提报到关单全链路
3. **润滑管理** — 511 个润滑点（283 加脂 + 228 换油），逾期提醒、执行登记
4. **备件库存** — 1777 条备件（1410 长周期 + 367 随机），领用/入库/撤销/硬删除
5. **用户权限** — 5 角色 + 自我保护 + 最后一管理员保护

## 🎨 设计风格

米白 + 镍钴绿的 Apple 极简杂志风格。不是工业风、不是 SaaS 风。
- **主色** `#3A5424`（镍钴绿·深）
- **纸色** `#FAFAF7`（米白）
- **字体** Cormorant Garamond（衬线大字）+ Inter（无衬线正文）+ JetBrains Mono（等宽标签）

## 🚀 快速开始

### 在线使用

直接访问：https://haoxinglong404.github.io/nickel-ems/

### 本地开发

本项目是**单文件应用**（`index.html`），没有构建步骤。

```bash
# 克隆仓库
git clone https://github.com/haoxinglong404/nickel-ems.git
cd nickel-ems

# 用任何本地服务器打开（推荐，因为涉及 ES Module）
python3 -m http.server 8000
# 或
npx serve
```

浏览器打开 `http://localhost:8000`，即可访问。

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| 前端 | 纯原生 HTML/CSS/JS（ES Module）· 无框架 |
| 数据库 | Firebase Firestore（asia-southeast1 新加坡节点） |
| 托管 | GitHub Pages |
| 资源 | gstatic.com CDN（Firebase SDK 12.x）· Google Fonts |

**故意不用框架**：这是一个中等规模的单车间系统，不需要 React/Vue 的复杂度。一个 HTML 文件 + 云数据库已经足够。

## 📱 部署

详见 [DEPLOY.md](./DEPLOY.md)

简要流程：
1. 修改 `index.html`
2. `git commit && git push origin main`
3. GitHub Pages 自动部署（约 1-2 分钟）
4. 用户端清缓存刷新

## 📋 角色说明

| 角色 | 工号示例 | 能做什么 |
|---|---|---|
| **Admin** 管理员 | 6725102247 | 全部操作 + 用户管理 + 硬删除 |
| **Reporter** 提报人 | — | 提报工单、查设备 |
| **Approver** 审批人 | — | 审批工单（李主任/王主任） |
| **Technician** 维修人 | — | 接单、登记完工（张师傅/赵师傅） |
| **Reader** 只读/报修 | — | 查看为主 |

## 🗂️ 文件结构

```
nickel-ems/
├── index.html          # 主应用（所有代码都在这里）
├── README.md           # 本文件
├── CLAUDE.md           # AI 助理的项目备忘录
├── ARCHITECTURE.md     # 架构设计文档
├── CHANGELOG.md        # 版本演变历史
├── DEPLOY.md           # 部署指南
├── .gitignore
└── .claudeignore
```

## ❓ 常见问题

### 为什么 `index.html` 这么大（1 MB+）？

因为所有种子数据（361 设备 + 511 润滑点 + 1777 备件）都内联在 HTML 里，首次启动时上传到 Firestore。部署一次即可，之后不再加载这些数据。

### 数据会丢吗？

不会。所有数据都存在 Firebase 云端。即使删除本地浏览器数据，重新打开还能从云端同步回来。

### 离线可用吗？

目前不可用。需要网络连接。未来计划用 PWA + Firestore 离线持久化实现。

## 📞 项目发起人

**郝兴龙**（工号 6725102247）· 高压酸浸车间设备管理员 · 印尼项目现场

---

*本项目由 AI 协作开发。见 [CLAUDE.md](./CLAUDE.md) 了解如何用 Claude Code 接手此项目。*
