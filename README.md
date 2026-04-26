# 湿法冶镍设备管理系统（Nickel Plant EMS）

> 印尼某湿法冶镍项目现场设备管理系统 · 移动端优先 · 云端协作

[![Live](https://img.shields.io/badge/live-online-brightgreen)](https://haoxinglong404.github.io/nickel-ems/)
[![Version](https://img.shields.io/badge/version-v0.9-blue)](./CHANGELOG.md)

---

## 🌿 这是什么

一个为**湿法冶镍车间**设计的设备管理移动 Web 应用，运行在印尼生产现场。核心解决六件事：

1. **设备台账** — 420 台设备 · 7 个区域（201/202/203/218/316-1/546/923）· 位号命名规范严格
2. **工单流程** — 8 种角色协作（生产/检修各 3 层级 + 经理 + 管理员），从提报到关单全链路
3. **润滑管理** — 620 个润滑点（208 脂润滑 + 256 油润滑 + 156 待补充油号）· 真实历史 194 条 · 426 个未初始润滑标记
4. **备件库存** — 1861 条备件（含长周期 + 随机 + 84 协议待清点）· 领用/入库/撤销/硬删除
5. **工器具管理** — 251 件工器具 · 借用 vs 领用双轨 · 购物车批量出入库
6. **用户权限** — 8 角色 + 自我保护 + 最后一管理员保护

## 🎨 设计风格

米白 + 镍钴绿的 Apple 极简杂志风格。不是工业风、不是 SaaS 风。
- **主色** `#3A5424`（镍钴绿·深）
- **纸色** `#FAFAF7`（米白）
- **字体** Cormorant Garamond（衬线大字）+ Inter（无衬线正文）+ JetBrains Mono（等宽标签）

## 🚀 快速开始

### 在线使用

直接访问：https://haoxinglong404.github.io/nickel-ems/

### 本地预览

本项目是**单文件应用**（`index.html`），没有构建步骤。

**最快方式 · 双击 preview.bat**：

```bash
# 双击 preview.bat 即可，会自动开浏览器
# 或命令行
py preview.py
```

会在 `http://localhost:8000/?preview=1` 起本地服务器。

**或手动启动**：

```bash
git clone https://github.com/haoxinglong404/nickel-ems.git
cd nickel-ems
python -m http.server 8000
```

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

## 📋 角色说明（v0.9 重构）

按"生产线 + 检修线 + 管理"分层：

| 角色 | 主要职责 |
|---|---|
| **管理员** | 全权限：系统配置、用户管理、设备台账、硬删除 |
| **经理** | 决策层：审批跨班组工单、数据导出 |
| **检修主任** | 部门主管：审批工单、批量入库、数据导出 |
| **检修班长** | 现场主管：派单、本班组接修、批量入库 |
| **检修员工** | 一线：接单去修设备 |
| **生产主任** | 部门主管：跨班组验收、数据导出 |
| **生产班长** | 现场主管：本班组验收 + 提报 |
| **生产员工** | 一线：提报故障 + 验收修后效果 |

详细权限矩阵见 [CLAUDE.md](./CLAUDE.md#-角色矩阵)。

## 🗂️ 文件结构

```
nickel-ems/
├── index.html              # 主应用（所有代码都在这里）
├── README.md               # 本文件
├── CLAUDE.md               # AI 助理的项目备忘录
├── ARCHITECTURE.md         # 架构设计文档
├── CHANGELOG.md            # 版本演变历史
├── DEPLOY.md               # 部署指南
├── GETTING_STARTED.md      # 给项目发起人的 Claude Code 入门
├── preview.bat             # 一键启动本地预览（Windows）
├── preview.py              # 本地预览服务器
├── .gitignore
└── .claudeignore
```

## ❓ 常见问题

### 为什么 `index.html` 这么大（1.5 MB+）？

因为所有种子数据（420 设备 + 620 润滑点 + 1861 备件 + 251 工器具）都内联在 HTML 里，首次启动时上传到 Firestore。部署一次即可，之后不再加载这些数据。GitHub Pages 自动 gzip 压缩后约 350 KB，4G 网络 1-2 秒就能打开。

### 数据会丢吗？

不会。所有数据都存在 Firebase 云端。即使删除本地浏览器数据，重新打开还能从云端同步回来。

### 离线可用吗？

部分支持。Firestore 启用了 `enableIndexedDbPersistence`，断网后仍能查看缓存数据，但不能写入。完全离线写入需要 PWA + 离线队列（roadmap 里）。

## 📞 项目发起人

**郝兴龙**（工号 6725102247）· 高压酸浸车间设备管理员 · 印尼项目现场

---

*本项目由 AI 协作开发。见 [CLAUDE.md](./CLAUDE.md) 了解如何用 Claude Code 接手此项目，[GETTING_STARTED.md](./GETTING_STARTED.md) 了解从 0 上手的完整流程。*
