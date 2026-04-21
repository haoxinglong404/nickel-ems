# Claude Code 项目备忘录 · Nickel Plant EMS

> **⚠️ AI 助理：每次会话开始时请完整阅读此文件，不要跳过任何"重要约定"。**

---

## 🎯 项目本质

**这是什么项目**：印尼某湿法冶镍车间的设备管理 Web 应用（单页面 + 云数据库）。

**谁在用**：1 位设备管理员（非技术人员）+ 4-6 位工人。移动端为主，宽屏次之。

**关键属性**：
- 🏭 **生产环境** — 代码直接影响实际车间运作，不是玩具项目
- 👥 **多人协作** — 数据通过 Firebase 实时同步，一人改全团队秒同步
- 📱 **移动优先** — 按钮 ≥44px、输入框 ≥52px、字号不小于 13px
- 🔒 **数据不能丢** — 删除都要"撤销/硬删除"双轨制

---

## 🏗️ 技术架构（**一句话原则：不引入框架**）

```
单文件 index.html  →  Firebase Firestore  →  GitHub Pages
（HTML+CSS+JS）      （实时数据库）          （静态托管）
```

**Firebase 项目**：`nickel-ems` · 区域 `asia-southeast1`（新加坡）
- 认证：无（工号登录 + 客户端密码校验）
- 数据库：Firestore（测试模式规则，将于 **2026-05-19** 左右到期）
- 存储：暂未使用

**Firestore 集合**（每个文档的 id 字段要和 Firestore doc id 一致）：
- `users` · 用户账号（id = 工号字符串）
- `equipments` · 设备台账（id = `eq_seed_XXXX`）
- `workorders` · 工单（id = `wo_时间戳_随机`）
- `lubepoints` · 润滑点（id = `lp_XXXX`）
- `lubehistory` · 润滑执行记录
- `spareparts` · 备件（id = `sp_XXXXX`）
- `spareparthistory` · 备件出入库记录（id = `ph_时间戳_随机`）

---

## 🚨 绝对不要做的事（血泪教训）

### ❌ 禁止引入任何构建工具

不要用 webpack、vite、npm install 任何东西。项目就是一个 `index.html`，直接浏览器打开就能用。

### ❌ 禁止分拆文件

不要把 CSS/JS 拆出去。用户直接在 GitHub 网页上传 `index.html` 就是部署 —— 这是**用户的核心工作流**，不能破坏。

### ❌ 禁止修改字段命名

下面这些字段名绝不能改（Firestore 已有历史数据）：

| 集合 | 字段 | 说明 |
|---|---|---|
| workorders | `contactName` / `contactPhone` | 现场联系人（不是 siteContact） |
| workorders | `status` | `pending-approval` / `approved` / `rejected` / `in-progress` / `pending-confirm` / `done` / `reopened` |
| workorders | `equipmentId === 'other'` | 非设备工作的特殊值 |
| spareparts | `source` | `long`（长周期）或 `random`（随机） |
| spareparthistory | `type` | `in`（入库）或 `out`（领用） |
| spareparthistory | `reverted` / `isCounter` | 撤销标记，别用其他字段名 |

### ❌ 禁止用 localStorage 存业务数据

只能用来记：
- 当前会话 token（`SESSION_KEY`）
- 用户偏好（如上次联系方式自动填充）

所有业务数据必须在 Firestore。

### ❌ 禁止删除"首次启动种子数据"逻辑

`seedIfEmpty()`、`seedLubeIfEmpty()`、`seedPartsIfEmpty()`、`seedImportedWorkordersIfNeeded()` 这些函数**保留不删**。它们只在云端对应集合为空时才写入，幂等安全。

---

## ✅ 必须遵守的命名和约定

### 位号命名规则

格式：`{区域}-{专业}-{类型}-{序号}{分支}`

示例：
- `201-PE-AG-001A` · 201 区域 · 工艺设备 · 搅拌器 · 001 · A 分支
- `316-1-MT-PP-003` · 316-1 区域 · 金属设备 · 泵 · 003

**绝对不要**生成不符合这个格式的位号。如果需要给设备加位号，先参考 Firestore `equipments` 集合里现有的格式。

### 工单号规则

格式：`WO{YYYYMMDD}{序号3位}`

示例：`WO20260419001`

### 文件改动必须满足

1. **每次修改 `index.html` 都要**：
   - 用 `node --check` 验证 JS 语法（提取 `<script type="module">` 内容）
   - 修改后文件大小不能异常变化（正常 950KB ~ 1.2MB）
   - 验证所有 `onclick` 调用的函数都通过 `window.fn = fn` 暴露

2. **改 HTML 结构时必须**：
   - 如果加新 module（section），要同步更新 `switchModule()` 的所有相关逻辑
   - 如果加新顶栏，要在 `switchModule()` 里控制显隐

3. **改样式时必须**：
   - 用现有的 CSS 变量（`var(--ink)`、`var(--g-deep)` 等）
   - 不要加内联 `style="color: green"`，没意义且难维护

---

## 🎨 设计系统（不要偏离）

**色板**（这些变量已定义在 `:root`）：
```css
--paper:   #FAFAF7  /* 米白背景 */
--ink:     #1A2A1A  /* 墨绿·正文 */
--g-deep:  #3A5424  /* 镍钴绿·深 */
--g-forest:#27500A  /* 镍钴绿·森林 */
--g-mist:  #F0F5E8  /* 镍钴绿·雾 */
--g-primary:#97C459 /* 镍钴绿·亮 */
--muted:   #6B6A66  /* 次级文字 */
--subtle:  #9B9A96  /* 辅助文字 */
--line:    #E4E0D8  /* 分隔线 */
```

**字体栈**：
- `--font-serif` = Cormorant Garamond（大标题）
- `--font-sans` = Inter（正文、按钮）
- `--font-mono` = JetBrains Mono（标签、数字、等宽）

**圆角**：主卡片 `14px`，次级 `10px`，胶囊按钮 `999px`。

**间距**：8px 网格（4/8/12/16/20/24/32）。

---

## 🔄 典型工作流：加新功能的正确姿势

用户说："给工单加个导出 Excel 的按钮"。

**正确的流程**：

1. **先读 `ARCHITECTURE.md`** 了解现有工单模块结构
2. **用 Grep 工具**搜代码里是否已有导出相关代码（避免重复）
3. **规划改动**：
   - 哪里加按钮？
   - 用什么 JS 库实现？（能不加就不加 → 先看 SheetJS 是否已经在 CDN 引入过）
   - 权限：谁能导出？
4. **提议方案**给用户确认（中文 + Markdown 格式，有结构、有取舍）
5. **动手改代码**，每一步用 str_replace / create_file 精确操作
6. **验证**：
   - `node --check` 验证 JS
   - 用 `grep -c` 确认函数被 `window.` 暴露
   - 检查相关 onclick 语法
7. **交付**：告诉用户"做了什么、怎么测试、已知限制"

---

## 📝 用户偏好（郝兴龙）

- **不要用英文解释**。必须中文为主，英文术语要配翻译。
- **不要让用户做技术决策**。我问"您想用方案 A 还是 B"之前，先给推荐。
- **不要给太多选项**。2-4 个最好，超过 5 个用户会困惑。
- **修改 UI 前先给视觉说明**（用 SVG/HTML 预览，而不是纯文字描述）。
- **严谨**：每次 str_replace 要 assert 成功，不能静默失败。
- **动手之前**告诉用户"我准备做 X、Y、Z"，让她确认。

---

## 🎭 角色矩阵（权限设计必须参考这个）

| 功能 | admin | approver | reporter | tech | reader |
|---|---|---|---|---|---|
| 查看设备 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 编辑设备 | ✓ | ✗ | ✗ | ✗ | ✗ |
| 提报工单 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 审批工单 | ✓ | ✓ | ✗ | ✗ | ✗ |
| 接单 | ✓ | ✗ | ✗ | ✓ | ✗ |
| 登记润滑 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 备件领用/入库 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 备件撤销 | 自己的 + admin全部 | 自己的 | 自己的 | 自己的 | 自己的 |
| 备件硬删除 | ✓ | ✗ | ✗ | ✗ | ✗ |
| 用户管理 | ✓ | ✗ | ✗ | ✗ | ✗ |
| 硬删历史 | ✓ | ✗ | ✗ | ✗ | ✗ |

---

## 🔑 关键常量和入口

- **管理员初始账号**：工号 `6725102247` · 密码 `15086370152hxl`
- **副管理员**（翔总）：工号 `6724013003` · 登录弹专属欢迎卡
- **VIP 配置**：在代码里搜 `VIP_WELCOMES` 常量，添加新 VIP 在这里加
- **Firebase 配置**：在 HTML 里搜 `firebaseConfig` 常量
- **SESSION_KEY**：`nickel_ems_session` （localStorage 里的会话键）

---

## 🚀 下次会话应该知道的上下文

当前版本：**v0.8**（含备件模块 + 撤销/硬删除 + 翔总欢迎卡 + 工单联系人字段 + "其他"设备选项 + 6 条历史工单导入）

**最近做的改动**（按时间倒序）：
1. 工单提报加必填字段 `contactName` + `contactPhone`
2. 设备选择器加 "其他/非设备工作" 按钮（用 `pickEquipmentOther()`）
3. 首次启动自动导入 6 条 Excel 历史工单（都是待审批状态）
4. 翔总欢迎卡去"敬"字
5. 用户管理可添加/改为"管理员"角色（有自我保护 + 最后一管理员保护）

**已知待办**（按紧急度）：
- ⚠️ Firestore 测试模式规则 ~2026-05-19 到期，需升级（高优先级）
- 📊 数据导出 Excel 功能（用户多次提过）
- 📸 图片上传（设备故障照片）
- 📬 消息通知
- 📊 数据看板

---

## 🧪 测试建议

本项目没有单元测试框架（故意为之 —— 用户是非技术人员，不需要维护测试）。

AI 助理在修改代码时的**最低质量标准**：

1. **语法正确**：`node --check` 通过
2. **函数暴露**：所有 `onclick="fn()"` 的 `fn` 都在 `window.fn = fn` 里
3. **元素齐全**：`getElementById('xxx')` 调用的 `xxx` 都在 HTML 里存在
4. **module 协同**：新 module 在 `switchModule()` 的所有分支里都处理到了
5. **字段一致**：Firestore 写入的字段名与读取的字段名一致

每次交付前必须跑一遍这 5 条。

---

## 🛡 安全规则（未实施但要知道）

目前 Firestore 是**测试模式**（任何人登录都能读写）。

升级到生产规则时要做：
1. 所有写操作必须登录（`request.auth != null`）
2. `users` 集合只有 admin 能写
3. `workorders` 只能改自己创建的（除非是审批人/管理员）
4. `equipments` 只有 admin 能写
5. 硬删除操作都要有审计字段（`deletedBy`、`deletedAt`）

---

*文件长度：本文件刻意保持在 200 行以内，Claude Code 每次会话都会读取。保持紧凑、准确、可执行。*
