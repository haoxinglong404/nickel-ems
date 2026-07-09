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
- `equipments` · 设备台账（**422** 台 · id = `eq_seed_XXXX` / `eq_new_XXX` / `eq_v6_XXX`）· 2026-07-01 加 `abcClass` 关键性等级（A/B/C，352 台已赋级 = A30/B69/C253，70 静设备未分类）
- ~~`workorders` · 工单~~ —— **2026-07-01 废弃**（工单模块整体删除，换成检修模块；云端集合用 `清空旧工单_F12脚本.js` 清空，rules 白名单暂留以便删）
- `maintenancelogs` · **检修记录**（id = `ml_时间戳_随机`）—— 2026-07-01 新增，替代工单；**2026-07-08 起选二级库备件自动扣库存**（联动 secondstock/secondstockhistory）
- `lubepoints` · 润滑点（**871** 个 · id = `lp_XXXX` / `lp_v6_001` / … / `lp_v13_NNN`(拆上下轴承) / `lp_v14_NNN`(污水泵结构统一) / `lp_v15_NNN`(浓密机减速机拆8点) / `lp_v16_NNN`(电机拆前/后轴承) / `lp_v17_NNN`(201B给料槽搅拌补齐轴承)）
- `lubehistory` · 润滑执行记录
- ~~`spareparts` · 备件~~ —— **2026-06-21 废弃删除**（前端模块已移除，云端集合用 F12 脚本清空）
- ~~`spareparthistory` · 备件出入库记录~~ —— 同上废弃
- ~~`tools` · 工器具台账~~ —— **2026-06-21 废弃删除**（前端模块 + 购物车整体移除）
- ~~`toolhistory` · 工器具出入库历史~~ —— 同上废弃
- `secondstock` · **二级库（现场库存台账）**（id = `ss_imp_NNN` 种子 / `ss_时间戳_随机` 新增）—— 2026-06-21 新增模块，替代旧备件
- `secondstockhistory` · 二级库出入库历史（id = `ssh_时间戳_随机`）—— 2026-07-08 起带 `mlId` 字段的 = 检修记录的**账本投影**（每次保存检修记录整体重写：每备件恒一笔出库=当前用量，删记录笔就消失；禁手动撤销/删除）
- `inspecttemplates` · **巡检模板**（**32 个** · id = `tpl_<key>`）—— 2026-04-29 新增；**2026-07-04 升级 v2 数值点检 + 07-05 现场核实变体**：24 个 v2 结构化模板（`v:2` + `groups[{g,pts:[{p,ms:[{n,t:'num'/'chk',u,max,min,std,mth}]}]}]`，含离心泵 5 种密封变体/搅拌器 4 变体/浓硫酸隔膜泵等）+ 8 个 v1 勾选模板（items 数组；**静设备无"设备停机未运行"项**）；每个模板带 `rev`（=`INSPECT_TPL_REV`）内容修订号，**改模板内容必须 +1 并配新迁移 marker**
- `inspecthistory` · 巡检执行记录（id = `ih_时间戳_随机`）—— v2 设备只在**有异常时**写（带 `src:'v2'` 供历史 tab 去重），v1 设备照旧每次写
- `inspectmonthly` · **月度数值点检表**（id = `im_<eqId>_<YYYYMM>`）—— 2026-07-04 新增：一台设备一月一文档，`days["日"]={at,by,byId,stopped,v:{测点key:数值或0/1},abn:[超限key],notes:{},note}`；**只订阅当月+上月**（where month in）→ 读取量恒定不随历史增长；同一天重复提交 = 覆盖当天（订正通道）
- `meta` · 一次性迁移幂等标记（id = `*_v[N]_YYYYMMDD`）

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
| spareparts | `stockStatus` | `'missing'` 表示协议待清点（仅 sp_tbd_*） |
| spareparts | `countedAt` / `countedQty` / `countDiff` | 现场清点字段（不动 quantity）|
| spareparts | `techAgreementName` / `techAgreementQty` / `techAgreementUnit` | 技术协议数据 |
| spareparthistory | `type` | `in`（入库）/ `out`（领用）/ `count`（清点） |
| spareparthistory | `reverted` / `isCounter` | 撤销标记，别用其他字段名 |
| tools | `quantity` / `totalIn` / `totalOut` | 库存 + 累计入/出（`totalConsume`/`totalReturn` 为前端按需计算，不存库）|
| toolhistory | `type` | `in`（入库）/ `out`（**借用**·要还）/ `consume`（**领用**·消耗）/ `return`（归还）|
| toolhistory | `slipId` | 同次提交的多条共享单号（如 `CN20260423-XXXX`）|
| toolhistory | `consumed: true` | V10 把历史 isImport=true 的 out 标记为消耗 |
| lubepoints | `operationType` | `'oil'` / `'grease'` —— **但显示分类按 standardOil 是否含"脂"判断**，详见 `getLubeKind()` |

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
   - 修改后文件大小不能异常变化（正常 1.85MB ~ 1.95MB，seed 常量占大头）
   - 验证所有 `onclick` 调用的函数都通过 `window.fn = fn` 暴露
   - 内联 `oninput="someVar.x = this.value"` 也要求 `someVar` 在 window 上（模块作用域 `let` 不行 — 见 woBuffer 的 Object.defineProperty 桥接）

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
- **每次代码改动 push 后**，必须更新本 CLAUDE.md 的"下次会话应该知道的上下文"段落（追加到"最近做的改动"列表，移除已完成的待办，新增/修改 marker 表如有数据迁移），保证新会话能无缝接上项目。改动小可只追一行；改动大要相应更新 Firestore 集合表 / 字段表 / 模块结构。

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

当前版本：**v0.15**（v0.14 → 润滑加「导出五定表」按钮 + SheetJS 换 xlsx-js-style 带样式分支）

**底部导航**：设备 / 巡检 / **检修** / 二级库 / 润滑 / 我的（**横滑 flex**）
> ⚠️ 注意：**工单模块已于 2026-07-01 整体删除**，换成「检修记录」（`data-nav="maintenance"`，沿用原工单骨架：list/detail/create 三页 + 复用设备选择器 + `mlBuffer` 桥接）。工器具/旧备件模块 2026-06-21 已删，`data-nav="parts"` 指向二级库。
> **检修模块**（`maintenance` module）：**2026-07-08 收紧为仅 admin 可登记/编辑/删除**（原"谁都能登记"，因联动扣库存改掉；其他人只读）。**无彻底删除**（同日移除：只可作废=软删可恢复，删除时库存自动回补）。字段 `equipmentId/Tag/Name`·`category`(fault/planned/preventive)·`repairDate`·`faultParts[]`(标签多选)·`faultCause`·`measures`·`spareParts[]`(可从二级库挑/手填，**二级库的自动扣库存·手填的不扣**)·`repairerName`·`note`·软删 `deleted`。常量 `ML_CATEGORY_MAP`/`COMMON_FAULT_PARTS`/`ABC_CLASS_MAP`。设备详情"相关记录"tab 改读 `mlCache`。
> **设备 A/B/C 分级**：`abcClass` 字段(''/A/B/C)，设备卡/检修记录/详情显示徽章(`.abc-badge`)，设备编辑页有下拉。352 台已写云端(A30/B69/C253)，70 静设备未分类。**本地 SEED 未同步 abcClass**(主 SEED id 按位置生成+位号迁移，注入易错、生产读云端不受影响，故意不动)。桌面 `设备ABC分级清单_草稿_2026-07-01.xlsx` 留档。

**模块结构**：
- 二级库（`parts` module，标题 Second Stock）：现场库存台账，**带结存的库存账**
  - 字段：`name`/`materialCode`/`sourceNo`/`unit`/`fieldLocation`(现场库位)/`location`(领出库位·只读)/`requestQty`/`inQty`/`quantity`(结存)/`usagePart`/`applicant`
  - **库位双轨**：`location`=从仓库领出时的货位（只读保留）；`fieldLocation`=车间二级库实际存放位置（管理员填，列表/筛选/卡片都用这个）
  - module：`parts`(列表)/`parts-detail`(详情)/`parts-txn`(领用/入库)/`parts-edit`(新增/编辑)/`parts-history`(出入库历史·全员可看·2026-07-08)
  - **仅 admin** 可领用/入库/编辑/删除/批量导入；其他人只读
  - 详情页按钮：－领用（出库减结存）/＋入库/✏️编辑/🗑️删除条目
  - 顶部按钮（admin）：＋新增 / 📥批量导入（粘贴 Excel）/ ↓导出
  - 历史 type：`in`(入库)/`out`(领用)，带撤销(reverted/isCounter)+硬删双轨
  - **辅助函数**：`escapeAttr`(属性转义)、`renderInfoRow`(信息行)、`ssDataSource`(预览模式云端空时回退 SEED) —— 这几个原属旧备件模块，删除时一并删了，已在二级库块重新定义
  - `ssTxnBuffer`/`ssEditBuffer` 用 `Object.defineProperty(window,...)` 桥接（同 woBuffer 套路，内联 oninput 需要）
- 润滑模块顶部 3 tab：🛢️ 脂润滑 / ⛽ 油润滑 / 📝 待补充油号（**按 standardOil 是否含"脂"分**）
  - **列表按设备分组（2026-06-30）**：一台设备(同位号+同油种)=一张卡，多点位用分组卡 `renderLubeGroupCard`(内含各点位行+「一键登记全部」按钮 `openBulkLube`/`confirmBulkLube`)、单点位沿用原 `renderLubeCard`。分组逻辑 `groupLubePointsByDevice()`，卡片徽章/筛选取「最严重点位」状态 `lubeGroupStatus()`。
  - **概览按设备统计**：4 个概览卡(逾期/即将/未初始/全部)=**设备台数**(每台归入最严重点位状态，互斥)，非点位数；列表计数「X 台设备 · Y 个点位」。
  - **一键登记全部**：弹 sheet 列出该设备各「需润滑」点位(免维护自动跳过)，按各自标准油号/量 writeBatch 各记一笔 lubehistory + 顺延 nextLubeAt。
  - **免维护电机**：`maintenanceFree:true` → `getLubeStatus()`='exempt'，排除逾期/即将/未初始统计；潜水密封电机(排泥泵/潜水搅拌/污水池+集水坑潜水泵)、刮泥机行走/升降电机、PAM·PAC加药泵/搅拌器电机均已标(共 64 个电机 mf)。**液下渣浆泵电机不算免维护**(外置电机有加注量)。
  - **电机=前/后轴承两点(2026-06-30)**：155 个需润滑电机(非免维护、有加注量)各拆「电机前轴承+电机后轴承」(`lp_v16_NNN`，前后各按原加注量)；64 免维护 + 5 无加注量电机保持单点不拆。

**已运行的一次性迁移（marker 都在 `meta/` 集合）**：
| Marker | 做的事 |
|---|---|
| `eq_seed_fix_v2_20260421` | 修 312A/B 位号冲突 + 删 201B 重复 |
| `eq_fix_v3_20260422` | 62 个位号规范化（TBD→正式 + 316-1 空格修复）|
| `eq_lube_fix_v6_20260423` | 修 10 个孤立润滑点 + 拆 002/003 设备 + 加 102B + 313B 润滑点 |
| `parts_enrich_v4_20260422` | 367 随机备件补 5 字段（材质/技术协议/设备位号等）|
| `parts_tech_agreement_v5_20260422` | 加 84 条"协议待清点"备件 + 补技术协议单位 |
| `add_motor_lp_v7_20260423` | 202-PE-PP-005 高压水泵·电机润滑点 |
| `area_lube_v8_20260423` | 218/923/546 区 107 个新润滑点 |
| `tools_v9_20260423` | 导入 251 工器具 + 410 出入库历史 |
| `tool_reclassify_v10_20260423` | 历史 410 条 out 改为 consume（领用·不算待归还）|
| `inspect_init_v11_20260429` | 上传 17 个巡检模板（按 equipment.type 关联）|
| `inspect_tpl_v2_20260704` | 巡检模板升级 v2 数值点检结构（21 个覆盖写入；**预览模式跳过**，上线后线上页面首次加载时执行）|

**最近做的改动**（按时间倒序）：
1. **设备名直观化改名 · 第二批 202 浓密预热区 44 台**（2026-07-09，用户逐台核对拍板，高压水泵 1 台不改）：「N系列-」前缀正式启用（位号数字第一位=系列），如 `202-PE-PP-101A`→1系列-剪切泵-A泵；**给料槽/给料槽搅拌 001A/B/C 经用户确认对应 1/2/3 系列**（→1系列-低温预热器给料槽-A 式）；污水泵/污水坑搅拌按归属起名（1#/2#/3#浓密机污水泵-A/B/C泵 + 低预给料槽污水泵-D泵，搅拌同款）。云端 writeBatch 308 文档 = equipments 44 + lubepoints 150 + lubehistory 74 + inspecthistory 2 + inspectmonthly 38（maintenancelogs 202 区 0 条），回读零残留；本地 SEED 同步（+1206B）。已核对 `getInspectTplKeyForEq` 分流：新名都包含原名关键词、「低预给料槽污水坑搅拌」不会误命中「给料槽搅拌」（污水坑搅拌分支在前且非连续子串）。预览验证：搜"2系列"12 台、润滑搜"浓密机污水"6 台 15 点、0 报错。**待办：203 批（约 280 台）要同步改 ML_KEY_EQ_GROUPS 两处精确匹配。**
1. **设备名直观化改名 · 第一批 201 原矿区 20 台**（2026-07-09，用户逐台核对拍板）：3 条生产线设备大量重名不直观，**按子项分批改名**。201 批：晨曦（201·FAJAR）/海湾（201B·TELUK）项目前缀 + 泵「-A泵」/非泵「-A」后缀（如 `201-PE-PP-001A`→晨曦-原矿浆输送泵-A泵）；全区公用的改「201污水泵/201污水坑搅拌」。**历史快照一并刷新**（用户要求）：云端一次 writeBatch 139 文档 = equipments 20 + lubepoints.name 55 + lubehistory.name 38 + inspecthistory.equipmentName 9 + inspectmonthly.equipmentName 17（maintenancelogs 201 区为 0 条），回读零残留；本地 SEED_EQUIPMENTS/SEED_LUBE_POINTS 同步（+387B）。**纯数据改动无代码逻辑变更**。预览真实数据验证：设备列表/润滑列表（搜"晨曦"油 8 台 8 点+脂 8 台 22 点与结构吻合）、0 报错。**后续批次规则已定**（详见 memory project-equipment-rename-scheme）：202/203 用「N系列-」前缀（约 310 台）、中/高温预热器给料泵改「高预一级泵（warman/五二五）」式；**做 203 批时必须同步改 `ML_KEY_EQ_GROUPS` 两处精确匹配**（`n==='高压釜给料泵'` 和 `/^高压釜\d隔室搅拌$/`）为包含式，且新名须包含原名连续文字以保 `getInspectTplKeyForEq` 分流不破。核对页模板：`桌面/设备改名核对_201原矿区.html`。
1. **删除 SEED_NEW_EQUIPMENTS_V2 灾备隐患**（2026-07-09，用户拍板）：`seedNewEquipmentsV2IfNeeded` 无 meta 标记、只认"eq_new_001 是否存在"判重，payload 是 2026-04 的 57 条旧占位位号（218-TBD-PAC加药泵-01 等）——极端场景（equipments 被清后由主 SEED 重种、生成 eq_seed_* 位置 id）会把旧数据重灌且 V3/V4/V5 修正迁移因 marker 已存在不会再跑。常量+函数+init 调用整块删除（-12.4KB）；主 SEED_EQUIPMENTS 快照已含这 57 台的正式数据，灾备不受影响。预览验证：启动正常、422 台/871 润滑点照常、0 报错。
1. **五定表提交改为"直接填设备室模板"**（2026-07-09 深夜，用户拍板）：设备室坚持要他们那份文件（模板里的行点位本来就是用户自己填的半成品，系统 871 点更全）→ **不做替代表，直接往模板副本里灌系统数据**：`填五定表_模板填充脚本.py`（repo 根,gitignore）+ 预览会话 Firestore eval 导数据(点+历史 JSON)。**规则**：模板公式/保护/条件格式/表头全不动、旧数据清空重填；油表 243 行扩到 306 行（第246行公式 Translator 翻译下拉+样式复制+CF `AA4:AA246→AA4:AA309`，**顺手补了模板原件被手删的 78 个标记公式格**）；脂表公式原本就预铺到 1006 行够用。**周期列关键口径**：他们的 LET 公式把**纯数字当"天"**（原件填 8000 小时被当 8000 天,永不超期）→ 填 `periodDays` 纯数字(天)，公式算出的已超期/未润滑与系统一致（Python 全表模拟 0 错误分支,超期 33+31 与系统吻合）；免维护点周期留空+部位加「（免维护）」（周期空→公式不出标记,同原件做法）。日期必须写真 datetime（字符串会触发"M4格式错误"）。成品 `Desktop/晨曦项目-高压酸浸车间-设备润滑台账_EMS填充_2026-07-09.xlsx`（**待用户核对后交设备室**）；以后每次交表让 Claude 重跑此流程（导新数据→跑脚本）。openpyxl 踩坑：改 CF 范围不能原地 `rng.sqref=`（内部 dict key 会崩）,要 `del cfl._cf_rules[cf]` 后 `cfl.add(new_sq, rule)` 重加。
1. **润滑导出加「设备室五定表」格式**（2026-07-09，**用户拍板保留按钮、文字定为「导出五定表」，已 push**——正式交表走上一条的填模板流程，此按钮作内部自助/备用格式）：设备室要求提交《设备润滑五定表》（模板 `Downloads/晨曦项目-高压酸浸车间-设备润滑台账.xlsx`，带锁定 LET/TODAY 公式+sheet 保护，用户没法填）。润滑页头加「↓导出五定表」按钮（原「↓导出」保留不动）→ `exportLubeWudingXlsx()`/`buildLubeWudingSheets()`：**完全复刻模板结构但 0 公式、无保护**——2 个 sheet（`高压酸浸车间润滑油台账` 63 列 / `润滑脂台账` 62 列，按 getLubeKind 分、unspecified 按 operationType），左五定表（序号/子项/位号/名称/部位/规定油牌号/规定用量/换油周期，油表多一列"首次换油周期"留空）+ 右润滑记录（初次+第1~8次×6列）。**数据规则**：位号加 `109-` 前缀（201B→`109B-`）、子项 201B→201、周期=periodHours 或 periodDays×24、免维护点周期列写"免维护"、记录按 lubePointId 关联时间正序（初次=最早一笔，其后超 8 笔取最近 8）、标记列直接算好写文字：填了=已润滑(绿)、最后一笔后下一空组按 getLubeStatus 标 已超期(红)/未润滑(黄)。**顺手把 SheetJS CDN 换成 xlsx-js-style@1.2.0**（0.18.5 的带样式分支，API 兼容但 bundle 不内嵌 codepage 表——loadXlsxLib 先加载同包 cpexcel.js 兜底旧 .xls 中文，失败不阻塞；XLSX.read 读回归已测），五定表带边框/宋体表头/彩色标记。**多视角审查后修掉 3 处**：①周期列只有 periodDays 的点写「N天」明示单位（不再×24 折算成假小时与 periodHours 混同列，仅 316-1 的 12 个点走此分支）；②补油/换油按 sheet 油种定（脂表恒补油/油表恒换油，不按 actualOil 猜——有"2#锂基酯"OCR 错字和空值记录）；③cpexcel 见上。已预览真实数据 E2E：306 油+565 脂=871 点无漏、表头与模板逐格一致、合并区一致、0 公式（桌面样例文件已删，被填模板正式成品取代）。纯前端，无数据迁移、无 rules 变更。**Fuchs 归类问题已修（2026-07-09 用户拍板）**：21 个高压釜搅拌「机械密封轴承」点 standardOil="Fuchs Renolit H 443 HD 88" 不含"脂"字曾被 getLubeKind 判成油 → 同 POLYREX EM 先例补「（锂基脂）」后缀（云端 writeBatch 21 条回读核验 + 本地 SEED 同步 21 处；**mobilOil 使用油号保持原文不动**，仅 21 条、无历史记录受影响），自动归位脂 tab/脂台账；修后口径 **油 285 / 脂 586**，桌面填模板成品已用新分类重新生成（油表扩行相应变 4..288，脂表 4..589）。
1. **检修联动账本改"重写投影"式**（2026-07-08 深夜，用户反馈出库历史流水乱后定的方案）：原"台账差额法"每次改动追加 out/in 流水，删除→恢复折腾一圈就留 ±6 对冲垃圾、改设备后旧笔 reason 还是旧设备名。改成：**每次保存/删除/恢复检修记录 → batch.delete 该 mlId 全部旧账本笔 → 按当前 spareParts 重开干净出库笔**（每备件保留最早出库 createdAt，reason 统一"检修：位号 设备名"跟随当前设备），结存仍按差额调整（buildMlStockPlan 校验/确认框不变，plan 加 `target`/`oldEntries`）。效果：**一条检修记录任何时刻每备件只有一笔出库=当前真实用量；删除（作废）记录则出库笔直接消失**、库存加回，不留对冲流水。`mlStockLedger` 差额算法保留（重写后台账天然=目标）。同晚顺手：①永久删除 2 条测试检修记录（106A"测试"+306B 唐仕彬手填那条，账本干净无库存影响）；②把 306A/306B 两条在用记录重新保存触发投影重写，8 笔乱流水收敛成 4 笔干净出库（单向阀 12+O型圈 12 与实际吻合）。预览+真实云端 E2E 全验证（建→改量→改设备→删→恢复→再删→清理，结存全程精确回原值）。
1. **检修/二级库账目闭环收死：检修记录去掉彻底删除 + 检修联动账本记录禁撤销/禁删除**（2026-07-08 晚，接上一条的后续加固）：用户定的规则——**检修联动的账本记录（带 mlId）唯一修改入口是改检修记录本身**。①检修记录**彻底删除功能整个移除**（`hardDeleteMaintenance` 函数+按钮+window 暴露全删，`cloudDeleteMaintenance` 保留备用）：检修记录是设备档案，只许作废（软删可恢复、库存自动回补）不许消失，否则账本孤儿对不上账；已删除状态只剩「恢复」按钮。②二级库带 `mlId` 的历史记录**撤销/删除按钮都不显示**（详情页 canRevert/canDelete 加 `!h.mlId`），`revertSecondStockHistory`/`hardDeleteSecondStockHistory` 函数层也拦截（toast 引导去检修记录改）；手工记录不受影响。已用真实云端 E2E 验证（建测试记录→按钮隐藏→函数拦截库存不动→软删回补→已删除页只剩恢复→测试数据清零、结存回原值 412）。用户要求"检修选了备件就自动从二级库扣数量"，并决定检修登记权限收紧。**①权限**：`openMlCreate`/`canEditMl`/`submitMaintenance`/FAB 显隐全部改仅 admin（原"谁都能登记、改删自己的"），其他人检修模块只读。**②台账差额法**（核心设计）：每笔自动扣减写 `secondstockhistory` 时带 `mlId` 关联字段；同步时算 `目标用量(spareParts 带 ssId 条目汇总) − 台账净扣额(mlStockLedger，剔除 reverted/isCounter)` = 差额，>0 出库 / <0 回补——天然兼容 admin 手动撤销单笔（撤销后再编辑记录会重新对齐）。**③函数**：`mlStockLedger`/`mlTargetStock`/`buildMlStockPlan`(校验结存+确认文案)/`applyMlStockPlanToBatch`(writeBatch 原子写：检修记录+结存+历史)。新建=全额扣、编辑=差额多退少补、软删=全回补、恢复=重扣(结存不足拦)、硬删不动(软删时已补)；结存不足 alert 拦截；手填备件(无 ssId)不碰库存。**④UI**：`addStockPart` prompt 显示当前结存+校验>0；出库历史 reason 自动填"检修：位号 设备名"；二级库详情页+历史页带 `mlId` 的记录显示「🔧 检修」标签(`.parts-hist-ml-tag`)，点击 `openMlFromSS` 跳检修详情(已硬删则 toast)。**⑤已实测**（预览+真实云端，测试数据已全部清理、结存回原值）：新建扣2/编辑2→3补扣1/编辑3→1回补2/99999拦截/删除回补/恢复再扣/历史页标签跳转，控制台 0 报错。无数据迁移、无 rules 变更（复用现有集合）。
1. **二级库出入库历史页 + 润滑历史页**（2026-07-08）：用户要"直接看到今天出库/润滑了什么"。两个模块各加「📋 历史」入口按钮（页头导出旁，**全员可见**）→ 整页历史视图（新 module `parts-history` / `lube-history`，各带独立顶栏，switchModule 里 hideMain + navKey 归回 parts/lube）。**结构相同**：类型 tab（二级库=出库/入库/全部，默认出库；润滑=全部/脂/油，默认全部，按 `actualOil` 含"脂"判断同 getLubeKind 口径）+ 自然日时间筛选（今天/近7天/近30天/全部，默认今天）+ 汇总条（二级库剔除已撤销/撤销对冲；润滑加脂按 g、换油按 L 分开合计）+ 按天分组卡片（今天/昨天/N月N日·周X）+「↓导出」按当前筛选导 Excel。**返回链路**：`openSecondStockDetail(id, from)` / `openLubeDetail(id, from)` 加第二参 + `ssDetailFrom`/`lubeDetailFrom`，从历史页进详情返回文字变"返回出入库历史/润滑历史"并原路返回（同 openMlDetail 套路）；两个详情顶栏返回文字 span 补了 id。订阅回调加"历史页活跃时重渲染"。CSS 复用：润滑历史页直接用二级库的 `.ss-hist-*` 类。纯前端展示，无数据迁移、无 rules 变更。预览已用真实云端数据验证（当天 4 笔出库/281 条润滑历史全对上）。
1. **巡检到期改为"自然日 + 早上 6 点"更新**（2026-07-07）：`calcNextInspectAt` 从"上次巡检时刻 + N×24h"改为"上次巡检的日历日 + N 天的 06:00"——A 类今天任何时间巡检，明天 06:00 准时回到待巡检，工人早班跑巡回不会因为"还差俩小时才满 24h"漏设备。周期本身不变（A=1/B=2/C=7 天）。**同日顺手修 `formatRelTime`**：今天/昨天/N 天前也改按自然日算（原来昨天下午的记录今天上午看不满 24h 误显示"今天"，用户发现）。
1. **巡检：静设备全部移出 + 趋势页显示勾选测点 + 等级筛选**（2026-07-06）：①**静设备不做点检**（用户定：设备太多工作量太大）：`getInspectTplKeyForEq` 对 压力容器/贮槽/非标静设备 直接 return null（70 台），巡检范围 388→**318 台**（A30/B69/C219，全部有等级）；v1 勾选模板只剩 刮泥机3+给料器1 在用，静设备模板（pv_*/tank/non_standard/ns_no_vib）SEED 里保留未删。②**趋势页全测点显示**：原来只显示 num 测点，现在 chk（正常/异常）测点也显示——`getTrendChkSeries` 读月表 0/1 值，渲染每日点条 `.ins-chk-strip`（绿=正常 红=异常，点小方块 showToast 当天判定+备注），统计"检查 N 次·异常 M 次"；hero 计数改"N 个测点（数值 X + 勾选 Y）"。③**巡检列表加等级筛选行**：`#inspect-class-row`（区域/类型行下面独立一行，全部等级/A类/B类/C类，`inspectClassFilter`，可与区域/类型/搜索叠加）。④**历史/异常卡片可点进趋势**（同日追加，用户反馈：设备巡检完就从待巡检消失、趋势入口跟着丢）：`renderInspectHistCard` 整卡 onclick=`openInspectTrend(equipmentId)` + 右侧"📈 点检数据"提示；v1 设备点了 toast 提示非数值点检；删除按钮已有 stopPropagation 不冲突。**顺手**：`window.showToast` 补暴露（chk 点条内联 onclick 需要，之前一直没在 window 上）。**注意：线上已在真实使用**——2026-07-06 已有工人（潘东旭）提交 v2 点检 35 条历史，rules 已发布、迁移已跑，v2 上线三步已完成。检修列表"全部等级"筛选条下加**重点设备条**（⭐两组，`ML_KEY_EQ_GROUPS` 按设备名匹配：给料泵 `name==='高压釜给料泵'` 6 台 / 搅拌器 `/^高压釜\d隔室搅拌$/` 21 台；每组带 `parts` 重点零件关键词配置）。**三级整页结构**（用户明确不要半屏 sheet）：检修列表 → `maintenance-keyeq`（组内设备卡=位号+ABC徽章+记录数+最近日期）→ `maintenance-eqlog`（单台检修档案：`全部记录` tab + 零件 tab）。**零件更换时间线** `renderMlPartTimeline`：归类**按故障部位标签精确匹配**（`parts[].tags`，07-05 用户反馈模糊搜文本会把"隔膜补油阀"误归隔膜后改的；`kw` 仅用于时间线上提取备件品牌）。给料泵：单向阀/隔膜/隔热组件(tags 含"隔热段"兼容旧记录)；搅拌器：机械密封/减速机/桨叶(tags 含搅拌桨/叶轮)。**登记表单联动** `mlFormFaultPartOptions`：选中重点设备时该组零件标签自动排在"故障部位"选项最前（工人直接点选，归类才准），节点=更换日期+「用了 N 天（约X周/月）后更换」（最新一条=「在用·已 N 天」）+该次备件品牌规格芯片+原因摘要，顶部显平均更换间隔；**使用时长对比条形图** `renderMlPartLifeChart`（条长∝天数、颜色=备件名、图例、在用=半透明+标注）——给采购对比供应商寿命用。**返回链路**：`openMlDetail(id, from)` 加第二参 + `mlDetailFrom`，从档案页进详情返回回档案页；`backToMlKeyEq` 按当前设备 `mlEqlogGroup()` 归组返回。switchModule 两个新 module（keyeq/eqlog）都隐藏顶栏底栏、导航高亮"检修"。`renderMlCard(ml, from)` 加参（⚠️ `renderMaintenanceList` 已改 `.map(m=>renderMlCard(m))`，不能直接 `.map(renderMlCard)` 否则 map 的 index 会被当 from）。曾做过预览演示数据 `previewMlDemoRecords()`（9 条 106A 假记录演示时间线），**用户验收后同日已删除**，线上/预览都不会出现。上一版做过又被替换的"主列表只看一台"过滤也已删干净。
1. **数值点检模板按现场实况精修 + 生产模板误升级事故**（2026-07-05，接 v2 改造）：**①用户逐台核实密封/联轴器结构**，模板拆变体（有啥看啥，没有的字段不出现）：离心泵→5 种（默认机封+密封液=中/高温预热器给料泵 warman/五二五；`cf_mech` 只机封=高压水泵/反洗泵/雨水回用泵；`cf_mech_cool` 机封+冷却水=原矿浆输送泵/絮凝剂二次稀释泵/低温预热器给料泵/闪蒸后液/洗水/洗液/冲洗水泵/浓硫酸输送泵；`cf_packing_cool` 填料+冷却水=剪切泵/底流泵；`cf_double_suction` 中开双吸=回用水泵·轴承箱两端叫联轴器端/非联轴器端）；搅拌器→4 种（默认机封+密封液=高压釜隔室搅拌 21 台；`agitator_open` 敞口无机封=给料槽搅拌+絮凝剂搅拌器；`agitator_mech` 只机封=闪蒸密封槽搅拌；`pit_agitator` 污水坑搅拌**加机架轴承**；`chem_agitator`=PAM/PAC 搅拌无机架）；地坑泵（污水泵）**删填料/机械密封组 + 删油位油质**（立式泵轴承打脂无油窗）；浓硫酸给料泵→`diaphragm_pump_acid`（法兰联轴器只看运行状态、推进液系统只有补油阀）；加药泵删吸药/下料；给料泵用空压机删联轴器组；高压釜→`pv_no_gauge`（删表计留安全阀）、闪蒸槽/预热器/接收罐/储气罐→`pv_basic`（删安全阀+表计）、尾气净化装置→`ns_no_vib`（删震动异响）；**静设备全部删"设备停机未运行"项**（静设备谈不上停机）。**②不做点检 34 台**：起重机全部 18（电动单梁/旋转吊臂/316-1/218）、潜水搅拌 2、排泥泵/潜水泵 9、絮凝剂制备系统 1、316-1 E~H 未安装外送泵 4 —— `getInspectTplKeyForEq` 返回 null 即不进巡检。**最终分流：v2 数值 314 台 / v1 勾选 74 台 / 不做 34 台**（Python 镜像规则核对过）。**③模板 `rev` 修订号机制**：`INSPECT_TPL_REV`=2 注入全部模板，`getInspectTemplateForEquipment` 云端 rev≠代码 rev 就用内置 SEED——预览/迁移间隙永远显示与代码匹配的模板。**④事故与回滚（重要）**：preview_start 首次打开 tab 是裸 localhost:8000（无 ?preview=1）→ `applyInspectTplV2IfNeeded` 在生产云端真跑了（第一版 21 个 v2 模板 + marker 写入），线上旧代码点开动设备巡检表单会因 `tpl.items.map` 报错。**已于当晚用户批准后回滚完成**（恢复 17 个 v11 模板 + 删 4 个新增 tpl 文档 + 删 marker `inspect_tpl_v2_20260704`，回读核验 0 残留）。已在迁移函数加 **localhost/127.0.0.1 一律不跑** 守卫防复发。**⑤预览演示数据**：`seedPreviewInspectDemo()` 仅 ?preview=1 且云端月表空时注入内存（6 台高压釜给料泵×2 个月每日数据，106A 曲轴箱振动爬升剧情），不写云端。
1. **巡检模块升级为数值点检 v2**（2026-07-04，**待用户预览验收后 push**）：领导要求巡检数据能支撑分析，按纸质《设备日常点检记录表》(机修二车间 xlsx，14 张 sheet)改造。**①模板 v2**：15 个 v2 结构化模板（9 张纸质表转录：离心泵/地坑泵(立式液下)/搅拌器/小型搅拌/隔膜泵(GEHO)/螺杆泵/空压机/浓密机/起重机(全目测) + 6 类自设计经用户逐条审定：柱塞泵(删压力油位)/密封液系统(删液位报警)/补液站/液压站(删电控)/加药泵(删油位压力)/风机），核心复用「轴承五件套」=水平/垂直/轴向振动(≤4.5mm/s 测振仪)+温度(<70℃ 测温枪)+异响(听针)；构建用 `_num/_chk/_vib5/_vib4/_oilChk/_mechSeal/_coupling` 辅助函数。**模板解析** `getInspectTplKeyForEq(eq)`：设备级 `inspectTplKey` 字段优先(预留) → type+设备名分流（地坑泵名含潜水泵/排泥泵→`submersible_pump` v1、隔膜泵名含加药泵→`dosing_pump`、搅拌器名含污水坑/PAM/PAC 搅拌→`pit_agitator`、密封系统名含补液站→`makeup_station`）。**分流结果：v2 数值点检 338 台 / v1 勾选 84 台**(静设备70+潜水泵9+成套4+给料器1，用户决定暂缓)。**②频率按等级**：`getInspectCycleDays` A=1天/B=2天/C=7天(`INSPECT_CYCLE_BY_CLASS`)，未分级用模板 cycleDays——用户定的方案(全员每天太重)。**③月表存储** `inspectmonthly`(见集合表)：因整集合订阅模式下"一次一条"一年 13 万条会爆免费读配额(5万/天)，仿纸质表"一台一月一张"。**④录入页**：v2 分支按部件分组卡、数值键盘 inputmode=decimal、超限实时标红+强制备注(`metricOutOfRange`)、chk 项正常/异常、停机免检；提交写月表 + 异常另写 inspecthistory。**⑤趋势页** `inspect-trend` module：**全部数值测点按部件分组卡平铺**（07-05 用户要求，弃测点下拉），每测点=标题行(最新/均值/超限次数)+紧凑 SVG 折线(高150)+上/下限虚线+**自动标注最高/最低值**+**点数据点弹当天读数**（透明大命中圈 `insTrendPtClick`，注册表 `_trendPtsReg`）；导出按钮置顶；巡检卡「📈趋势」进入。**⑥导出**：巡检页头「↓导出」=当月明细长表+异常汇总(给领导分析)；趋势页=单台纸质样式月表(行=日期列=测点)。**⑦模板版本守卫**：`getInspectTemplateForEquipment` 云端模板版本≠SEED 期望时用 SEED(防迁移间隙/预览期读到旧结构崩溃)。**⑧顺手修 2 个存量 bug**：`inspectExecBuffer`/`lubeExecBuffer` 都没桥接 window，内联 oninput 一直静默 ReferenceError(巡检异常备注写不进 buffer；润滑"≈N 下"提示不实时刷)——补 defineProperty 桥接。**上线三步(用户执行)**：① Console 发布 firestore.rules(加 `inspectmonthly`，先发布不影响旧代码) ② push 代码(线上首次加载自动跑 `inspect_tpl_v2_20260704` 迁移) ③ 真实登录提交一台点检验证。**预览局限**：预览模式迁移被跳过(模板走 SEED 守卫回退即可看 v2 表单)，但 rules 未发布前提交点检会 permission-denied。
1. **21 台高压釜搅拌器减速机油号更正为 PAO 合成油**（2026-07-03）：203-PE-AG-101/201/301 A~G「减速机」点（`lp_0114~0134`）按 Flender H2SV10B 铭牌（OIL VISCOSITY ISO VG 320 **PAO-OIL**）改 standardOil `VG320`→`ISO VG 320 PAO`、mobilOil `MOBILGEAR EP 320`→`Mobil SHC Gear 320`（全合成）。云端 Chrome MCP 逐条核验后 updateDoc+回读，本地 SEED 同步。**加注量未动**（台账 150/130L vs 铭牌 ≈119L，待用户定夺）；其他 27 个 VG320 点不变。**注意**：PAO 与矿物油不混用，换油需放净。
1. **修 6 条阀门油压站电机轴承 operationType oil→grease**（2026-07-02）：203-PE-EP-103/203/303 电机前/后轴承（2#锂基脂 17.4g，`lp_0450/0451/0452`+`lp_v16_129/130/131`）operationType 错录 oil 致 UI 单位显示 L。云端经 Chrome MCP 在 EMS 已认证会话里 updateDoc 修复+回读核验，本地 SEED 同步；确认全库再无"油号含脂但标 oil"矛盾条目。起因：做 203-3 系列换油统计（油 17 种 ≈8472L + 脂 4 种 ≈9.2kg，明细见当次会话）时发现。
1. **修复删工单误删公共时间函数致润滑/检修详情页打不开**（2026-07-02）：删工单 commit(9ad1b36) 把 `formatFullTime`/`formatShortTime` 当工单代码误删，但润滑详情页(最后/下次润滑)和检修详情页(登记行)还在用 → 渲染抛 ReferenceError、详情页整个打不开。原样补回两函数（放 `formatDate` 旁工具区）。已扫过该 commit 删掉的全部 31 个函数，无第三个漏网。**经验**：大块删模块前，对"看着像该模块专属"的小工具函数要先 grep 全文件确认没有别的调用方。
1. **检修模块加 A/B/C 等级筛选 + 备件消耗汇总**（2026-07-01）：① 列表加**等级筛选条**(`ml-class-filter-bar`,全部/A/B/C,状态 `mlClassFilter`,`setMlClassFilter`),独立于类别、可叠加(如"预防性维护+B类"),`filterMaintenanceLogs` 加 `eqClassOf(m.equipmentId)===mlClassFilter`。② 段头加「📊备件消耗」按钮 → `openMlPartsSummary()` 弹 sheet(`showSheet('mlPartsSummary')`)：`aggregateMlSpareParts()` 按 `name+unit` 合计总量+次数(**跟随当前筛选** filterMaintenanceLogs),`exportMlPartsXlsx()` 导两 sheet(汇总+明细,复用 `_exportSheets`)给采购做依据。CSS `.ml-sp-sum-row`。**目的**：统计备件消耗、给采购提供依据。
1. **删工单模块 → 建检修记录模块 + 设备 A/B/C 分级**（2026-07-01）：用户"工单设计得好但推行不动(人微言轻,审批流卡)"，要求删工单、改成事后登记的检修记录。**①删工单**：3 个 section + ~20 函数 + `woBuffer`/`WO_STATUS_MAP`/`URGENCY_MAP`/`COMMON_ISSUE_TAGS`/`generateWoCode` + `SEED_IMPORTED_WORKORDERS` 种子 + FAB + 底栏 + "我的"里工单菜单项 + assignTech sheet 全删；`workorders` 云端集合用户跑 `清空旧工单_F12脚本.js`(gitignore)清空。**②建检修模块**(复用工单骨架，Python 锚点切片改 index.html)：新集合 `maintenancelogs`，无审批(谁都能登记/改删自己的/admin 硬删+恢复)，字段见集合表；`renderDeviceRecords` 改读 `mlCache`；`pickEquipment` retarget 到 `mlBuffer`；showSheet 加 `pickMlPart`(从二级库挑备件,**不扣库存**)。**③设备 A/B/C**：`abcClass` 字段+徽章+编辑页下拉；按用户给的《晨曦高压酸浸动设备清单.xlsx》(47组/222台动设备,A/B/C列)**位号精确匹配**系统 422 台(展开 `109-`前缀+`A~C`/`101A~301A`/`103A/B~303A/B` 等范围)→219 台精确;未覆盖动设备(218全区+203密封液辅助等136台)用户选"名称推断"全判 C;静设备~130 不分。共 352 台写云端(A30/B69/C253)。**用预览会话 preview_eval 直接批量 updateDoc 写云端**(admin `?preview=1` 匿名 auth)。**经验**：① 大块删/建用 Python 锚点切片(`find(start)`→`find(end)`),但**end 锚点是否保留要想清**——常量切片误把 `return 'WO'...}` 尾巴留下致 `Illegal return statement`,靠 preview 里 blob 注入+`window.onerror` 定位到行;② 本机无 node,校验靠 preview 加载后查 `typeof window.fn` 全 `function` + 控制台 0 报错(整脚本语法错会让全部 window 暴露失败);③ **SEED 同步 abcClass 放弃**:主 SEED_EQUIPMENTS 无内嵌 id(加载按位置生成)、`eq_new_*` id 在迁移数组里重复出现,按 id/tag 注入都易错,生产读云端不受影响故不动;④ 预览设备显示是 SEED 覆盖,所以**预览里设备卡不显示 abc 徽章,但正式上线读云端就有**。**上线三步**(用户执行)：发布 firestore.rules(加 `maintenancelogs`,已发布) → push 代码 → 跑清空旧工单脚本。
1. **21 个污水泵润滑结构统一**（2026-06-30）：用户确认"污水泵电机都免维护、泵都是上下两个轴承"。审计发现 21 个污水泵(203×15+202×4+201×1+316×1)结构乱：有的只有电机点、有的只有上/下轴承、316 啥都没有。**统一成每泵=电机(免维护)+上轴承+下轴承**：新建 27 点(`lp_v14_001~027`)——17 个电机免维护标记 + 5 泵补上/下轴承(119/219/120/220/316)。轴承量按泵型：ZJLX(40/65)→上101/下55、FYUC(65/80,含316)→上26/下30(6314+NU315)。**316-1-PE-PP-002 原零润滑点**，补全 3 点(轴承 6314/NU315 同 320，但**油号普通 3#锂基脂**非浓硫酸专用)。683 点。云端 setDoc 写入。**经验**：审核 HTML 按"name·point"归组时，**"污水泵"通用名被 ZJLX(101)和 FYUC(26)共用→假阳性不一致**，看 model 才准；同型号同部位才是真比较。
1. **润滑脂加注量全面审核 + "免维护"状态 + 多处校正**（2026-06-30）：在"打的下数"基础上对**全部 368 个脂点**做一致性审核并清零异常。**①新增"免维护"状态**：润滑点加 `maintenanceFree:true` 字段 → `getLubeStatus()` 首行返回 `'exempt'`，**排除出逾期/即将/未初始统计**，只在"全部"可查、登记按钮保留（修电机时手动登记）；卡片/详情/设备 tab 都加了 exempt 显示，详情页"标准用量 N/A、润滑周期 免维护轴承，无需润滑"。应用到 **2 台空压机电机 203-PE-CM-102/302**（封脂 6309-ZZ + MOBIL POLYREX EM 聚脲基脂；油号写成`MOBIL POLYREX EM（聚脲基脂）`带"脂"字以保持 `getLubeKind` 脂 tab 分类）。**后续(同日)又把另 33 个封脂无加油口电机也设免维护**：浓硫酸给料泵·油泵电机 12(原3.9) + 污水泵·电机 4(119/219/120/220) + 污水坑搅拌·电机 17(原4.96)——**只动这些小辅助/封脂电机，主泵电机(如浓硫酸给料泵主电机51/26.25g)不动**；污水泵只有这 4 个有独立电机点，其余污水泵的点是上/下轴承座(有加油口)。共 35 个免维护点。**②"同型号电机应同加油量"一致性审核**：生成本地审核 HTML `润滑脂加注量审核.html`(gitignore，生成器 `_gen_lube_audit.py` + 待改清单 `_pending_lube_fixes.json` 均 gitignore)，按电机型号+部位归组、标红不一致。校正：污水坑搅拌(YE3-112M-4/Y4kW=Y112M-4·6206)**全统一 4.96g**(原 17/23.1/5 乱)；闪蒸密封槽搅拌(上海电气 YE3-160L-4·6309)→**12.5g**；第二隔室浓硫酸给料泵(皖南 YXVF250M-4·6314)→**26.25g**；油泵电机(皖南 YE4-90L-4·6205)→**3.9g**；BPY-355L3-6 统一 **71.5g**。共 38+6 条脂量。**③补 5 台电机 motor 字段**：闪蒸密封槽搅拌×3(上海电气 YE3-160L-4 15kW) + 空压机×2(WEG W22 Premium 160L-4 15kW 巴西)，**这 5 条原 SEED 缺 motor 且缺 id**，一并补全(eq_seed_0073/85/97/105/107)。**④剪切泵位号归位**：`lp_0268/0269`(剪切泵·电机 51g)原误挂 `202-PE-PP-303`(絮凝剂二次稀释泵)→改回 `202-PE-PP-301`(301 缺电机点、303↔301 打字错)；订正后 301 补齐(轴承箱27+电机51 同 101/201)、303 干净(轴承箱2.4+电机24)。**⑤打的下数**：`usesGreaseGun()` 对联轴器/齿圈/开式齿不显示下数。**云端全部用预览会话 preview_eval 直接写**(admin 登录 `?preview=1` 已带匿名 auth)。**经验**：① 预览只覆盖 SEED_EQUIPMENTS 显示、**润滑点读云端**，改云端才看得到(改完要硬刷清浏览器缓存，否则旧 JS)；② 同型号电机不同加油量=录错信号；③ 审核归组**主电机 vs 油泵电机别按设备 motor 型号混为一组**(按 `model+'·'+point` 分，否则 26.25 vs 3.9 误报)；④ `getLubeKind` 按"脂"字分脂/油 tab，聚脲基脂等无"脂"字油号要补"（聚脲基脂）"；⑤ 机座号→6xxx 球轴承→SKF g：80=3.29/90=3.9/112=4.96/160=12.5/180=17.4/200=20.15/250=26.25。
1. **润滑列表按设备分组 + 概览按设备统计 + 电机拆前/后轴承 + 一批免维护电机**（2026-06-30）：**①列表分组**：润滑列表从"一个点位一张卡"改成"**一台设备一张卡**"——多点位用 `renderLubeGroupCard`(卡内列各点位 + 「一键登记全部」)、单点位沿用 `renderLubeCard`。`groupLubePointsByDevice()` 按 `tag`+油种归组，卡片徽章/筛选取「最严重点位」状态 `lubeGroupStatus()`(overdue>due-soon>pending-init>ok>exempt)。**②概览改设备口径**：4 个概览卡(逾期/即将/未初始/全部)从"点位数"改成"**设备台数**"(每台归入最严重点位状态，互斥)；列表计数「X 台设备 · Y 个点位」。**③一键登记全部** `openBulkLube`/`confirmBulkLube`：弹 sheet 列出该设备各「需润滑」点位(免维护自动跳过)，按各自标准油号/量 writeBatch 各记一笔 lubehistory + 顺延 nextLubeAt；单点位仍可点行进详情单独登记(两种方式都保留)。**④浓密机减速机拆 8 点**：3 台褐铁矿浓密机(202-PE-TH-101/201/301)原"小减速机轴承 8000g"(=8 行星减速机) → 拆成「1#~8#减速机轴承」各 1000g(原点改名 1# 保留 id/历史/逾期状态，新建 7 个 `lp_v15_001~021`)。**⑤免维护电机**：潜水密封电机(排泥泵6/潜水搅拌2/污水池潜水泵2/集水坑潜水泵1)+刮泥机行走升降电机3+PAM加药泵5/PAC搅拌器2/PAM搅拌器3 共 24 个标 `maintenanceFree`(本轮)，加历史共 64 个电机 mf；**液下渣浆泵(923)电机不算免维护**(外置电机有加注量20.15g)、PAC加药泵无润滑点。**⑥电机拆前/后轴承**：155 个「需润滑」电机(非免维护、有加注量) → 各拆「电机前轴承+电机后轴承」(`lp_v16_001~155`，**前后各按原加注量**，因 SKF g 本就是单轴承量)；64 免维护 + 5 无加注量电机**不拆**保持单点。**总点位 683 → 859**。**⑦补漏**：原矿浓密机给料槽搅拌共 6 台(201-PE-AG-001A/B/C + 201B-PE-AG-002A/B/C)，但 201B 那 3 台**之前只有"减速机"一个点**(连电机点都没有，故前面机架轴承拆分/电机拆前后都没轮到它)——补齐机架上轴承780/机架下轴承601/电机前轴承51/电机后轴承51 各 3 台共 12 点(`lp_v17_001~012`，初始未初始润滑)，859→**871**。**实现**：代码改 index.html(分组/概览/一键登记 ~+200 行)；数据全程用预览会话(`?preview=1` admin 已带匿名 auth)直接 preview_eval 写云端 + Python 同步本地 SEED(字符串替换保留 key 顺序、json.dumps 默认分隔符)，逐项核对、控制台 0 报错。**经验**：① 模块作用域 `let`(lubePointsCache 等)不在 window 上，preview_eval 读不到，要么读 DOM 要么 import firebase 直查云端；② 分组后状态筛选/概览口径要统一(都按设备最严重状态)否则"逾期 25 台"点进去对不上；③ 拆点用新 marker 系列(v15/v16)，原点改名+保留 id 不丢历史。
1. **润滑"打的下数"功能 + 加油量科学化校正**（2026-06-29）：现场标定**黄油枪 10 下 ≈ 9.5g（1 下≈0.95g）**，给脂润滑用量后加"≈N 下"提示（卡片/详情页·标准用量/登记表单实时换算）。**口径**：`greasePumps(g)=Math.floor(g/0.95)`——**油量宁少不多**（电机轴承多打脂会顶坏/升温），有小数一律**向下取整**。**只对黄油枪打的脂点显示**：`usesGreaseGun(lp)` 排除部位名含`联轴器/齿圈/开式齿`的（联轴器灌满壳腔、开式齿圈刷涂，不用枪）。**借下数暴露了一批不科学的加油量并校正（按 SKF G=0.005×外径D×宽度B + 实拍轴承型号）**：① **4 台污水泵电机 500g→17.4/20.15g**（119/219=YE3-180M-4·6311→17.4；120/220=YE3-200L-4·6312→20.15，与同款 923 液下渣浆泵一致）；② **给料槽搅拌机架轴承拆上下两点**（两个加油口）：202 低温预热器(lp_0283/85/87)→**上342(29372推力)/下230(NU1076)**；201 原矿浓密机(lp_0247/48/49)→**上780(370680双列圆锥Ø650×240)/下601(23176调心Ø620×194)**（30212/30234 是减速机齿轮轴轴承走油浴 lp_0001，电机是球轴承另有 51g 脂点，故 4 个买的轴承无电机的）；③ **16 个污水泵轴承座 500g 全拆上下**：320 浓硫酸(65FYUC)→上26(6314·6314-RZ密封不补)/下30(NU315)；其余 15 台 ZJLX(40/65ZJLX)→**上101(7320AC×2)/下55(NU321)**。**8000g 小减速机轴承(202-PE-TH-101/201/301)经用户确认正确**（=8 个行星减速机×每个1000g，不动）。**实现**：本地 SEED 共改 26 点+新建 22 点(下轴承 `lp_v13_001~022`，新 marker 系列 v13)，640→656... 实际 637→656。**云端用预览会话(`?preview=1` 带匿名 auth，连真实库)直接 preview_eval 跑总脚本写入**（26 改+22 建，0 缺失，逐项 getDoc 核对）——**新路子：admin 登录预览页后可直接在已认证会话里改云端，不必非得用户手动 F12**。总脚本 `润滑加油量修正_总脚本_F12脚本.js`(gitignore)。**经验**：① 预览模式只覆盖 SEED_EQUIPMENTS 显示，**润滑点读云端**，所以本地 SEED 改完预览看不到、要先写云端；② 判断轴承上下=按功能（推力/双列圆锥=托重量定位→上；圆柱/调心+紧定套=承径向浮动→下）；③ 电机用球轴承(6xxx)不用圆锥滚子(302xx)，可据此排除。
1. **修复"未初始润滑"点打不开的 bug**（2026-06-29）：润滑模块里 status=`未初始润滑`（pending-init）的点**点不开、没法登记**。根因在 [index.html:6169](index.html:6169) `renderLubeDetail` 的 `statusMap` 只定义了 `overdue/due-soon/ok` 三态，**漏了 `pending-init`** → 取 `st.lbl` 读 `undefined` 抛错 → `openLubeDetail` 里后面的 `switchModule('lube-detail')` 执行不到 → 详情页打不开。修法：给 `statusMap` 补 `'pending-init': { lbl: '未初始润滑', color: 'var(--muted)' }` + 兜底 `|| {lbl:'—',...}`。预览验证(admin 登录走真实流程)：点开 201-PE-AG-001A → 详情页开 / 状态显"未初始润滑" / "登记润滑"按钮在 / 点击弹出登记表单 / 控制台 0 报错。**经验**：凡是 `map[key].prop` 这种取值，key 来自可扩展的状态枚举时，一定要么覆盖全部枚举值、要么加 `|| 默认对象` 兜底——否则新增一个状态就整页静默崩。**附**：写了个 `撤回二级库批量导入_F12脚本.js`(gitignore) 给用户撤回某次批量导入（按 4 段 id `ss_<ts>_<i>_<rand>` 的时间戳分组、整批删，不碰种子/手动新增）
1. **润滑标签改名 + 校正 116 点"使用油号"**（2026-06-27）：① **UI 标签**：润滑点详情页([index.html:6225/6229](index.html:6225)) + 导出 Excel 表头([index.html:7877](index.html:7877)) 的 `标准油号`→`厂家推荐油号`、`美孚牌号`→`使用油号`（纯显示文字，字段 standardOil/mobilOil 不变）。② **数据**：按用户编辑的「设备用油明细表」校正 116 个润滑点 mobilOil(=使用油号)——VG46 类(L-FC46/N46/L-HM46) `MOB DTE MEDIUM`→园区实际 `MOBIL NUTO H46`(75点)；无美孚特种油从空填回原牌号(Fuchs/绍尔/10W-30/聚乙二醇/40WT 41点，其中 15#MAXTOP→`Mobil Nuto H 32`)。云端 F12 脚本 `更新使用油号_F12脚本.js`(gitignore，按 lp.id writeBatch 分批 400)，本地 SEED 同步。standardOil 0 变化；54 个待补点不在表里未动。**背景**：这批起于「车间润滑油代用表/用量统计/采购请购单」系列（成果在 `桌面/设备室提交资料_2026-06/` 三个子文件夹：1-电机型号清单、2-设备切换倒泵计划、3-润滑油代用与用量）。园区**寄售油品只 9 种**(2号极压复合锂基脂XHP222/2号极压锂基脂EP2/46/68液压油/320/460/680齿轮油/15W-40/80W-90)，按此分「园区常备 vs 需采购」：扣库存(EP220 库存154桶够9年→0采购)后净采购约 80 桶；最终按用户手填「待采购数量」(海湾设备首次加油)生成请购单 10 项(`D:/青山/工作资料/请购/2026-6-27 高压酸浸车间润滑油采购请购单.xlsx`，沿用上次模板"通用物资+最终数据表自动加余量"，openpyxl 填数据会丢 WPS 附图 DISPIMG 图片但下拉验证保留)。**口径**：用量表只统计「使用牌号」不统计标准油号；桶规格大桶 209L、小用量(空压机油/10W-30/聚乙二醇/40WT)20L、脂 16kg。**美孚代用空缺**：6 种特种油(Fuchs Renolit高温脂/聚乙二醇PG220/HYDRA-CELL 40WT/绍尔空压机油等)美孚无直接对应,可代但需 OEM 确认
1. **按现场铭牌照片纠正设备台账 104 台泵电机 motor 字段**（2026-06-26）：用户给两批铭牌照片（`桌面/铭牌/` 按区域 + `桌面/设备信息收集表-铭牌图片/` 按位号命名，后者规范）。改 202·203 区 16 类泵+空压机。**关键纠错**：洗水泵 `Y280M-4`→上海电气 BPY-280M-4 90kW；浓硫酸输送泵=磁力泵 `YBX3-200L1-2`→上海电气 BPY-200L1-2 30kW；吹扫空压机(汉纬尔) `YX3-225M-2`→中达电机 YE3-225M-2 45kW；预热器 warman 泵 `AESV3`(看错)→TECO东元 EVSV355M(中预280)/EVSV350A(高预350)；闪后泵 BPY-355L2-6→L3-6。**补全厂家**：BPY 变频泵全是上海电气；浓硫酸给料泵一/二隔室=安徽皖南 YXVF315S-4 110kW / YXVF250M-4 55kW；地坑污水泵=上海电气 YE3-180M-4 18.5kW（浓硫酸区 YE3-200L-4 30kW）。**全厂电机品牌规律**：BPY 变频泵=上海电气、warman 泵=TECO东元、五二五泵=上海电气 BPY、浓硫酸给料泵=皖南 YXVF、密封液小泵=温州南洋/HEW/CEMP。云端 F12 脚本 `更新电机台账_F12脚本.js`（已 gitignore，按 tag 查询改 104 条、跑前打印旧值），本地 SEED 同步（json.dumps 默认分隔符匹配原格式 diff 最小）。**未动**：冲洗水泵/201污水泵/原矿浆（已正确）、密封液循环泵（SEED 是 CEMP 0.12kW 与温州南洋 YBX3 0.55kW 混装，待逐台核）。**踩坑**：第一版误以为剪切/闪后泵"已正确"跳过——其实看的是"已更新的 Excel"不是 SEED，SEED 里剪切泵=`BPY315L2-6/132KW`缺厂家、闪后泵型号 L2 错(应 L3)，git checkout 撤销后补做(104 条)。**副产物**（均 gitignore 的 xlsx）：`车间电机型号清单_2026-06-24.xlsx`（交上电查轴承润滑周期+单次加油量，待核仅剩起重机 ZD 起升电机未拍铭牌+絮凝剂制备成套）、`设备切换计划表_2026-06-24.xlsx`（倒泵轮换：泵类两周/预热器每周、按月第1·3周与2·4周、同区域集中+大泵分散；原矿浆晨曦FAJAR 5台3用2备/海湾TELUK 4台3用1备；预热器整线 warman↔五二五 对倒）
1. **删工器具+旧备件模块 → 新建二级库模块**（2026-06-21）：用户要求把工器具模块和旧备件（采购/随机）模块**整体删除**，新建「二级库」（现场库存台账）。**删除范围**：前端工器具(tools/tool-detail module + 购物车 bar + ~40 函数 + SEED_TOOLS_V9/HISTORY 种子)、旧备件(parts/random + ~30 函数 + SEED_SPARE_PARTS 66万字符 + V4/V5 迁移) 全删；云端 4 集合(spareparts/spareparthistory/tools/toolhistory)用 F12 脚本 `清空旧备件工器具_F12脚本.js` 清空（**用户跑，不进 git**）。文件 1.98MB→0.86MB。底部导航 6→5 项(工器具删，"备件"→"二级库"，沿用 `data-nav="parts"` 骨架)。**新二级库**：新集合 `secondstock`+`secondstockhistory`，57 条垫片种子(`SEED_SECONDSTOCK`，来自 `垫片二级库台账.xlsx`，总结存 472)。**带结存库存账**：可领用(出库减结存)/入库/编辑/删除/批量导入(粘贴 Excel)/导出，撤销+硬删双轨，**仅 admin 可写**。**库位双轨**：`location`(领出库位·仓库·只读) + `fieldLocation`(现场库位·二级库·管理员填，列表/筛选/卡片都用它)，57 条初始 fieldLocation 统一=`203-1`。**3 个踩坑(都修了)**：① 删除脚本误删了"润滑 UI 层"注释的 `/*` 开头→留下悬空 `*/`→整个 module 静默不执行(全部函数 undefined)，靠 Python 注释配平扫描定位；② `escapeAttr`/`renderInfoRow` 原属旧备件模块、被一起删了，二级库代码却用到→已在二级库块重新定义；③ `ssTxnBuffer`/`ssEditBuffer` 内联 oninput 需 `Object.defineProperty(window,...)` 桥接(同 woBuffer)。**预览模式回退**：`ssDataSource()` 在 `?preview=1` 且云端空时显示 SEED，方便本地看效果(写操作因权限 gate 预览测不了，要上线后真实 admin 登录测)。**本机无 node**：`node --check` 用不了，改用 Python 写括号/引号/注释配平校验器 + 浏览器 preview eval 验证。firestore.rules 加了 secondstock/secondstockhistory 白名单(需用户在 Console 发布)
2. **导入 37 条手写润滑记录（v3）**（2026-05-22）：用户给 `设备润滑记录汇总_v3.xlsx`（基于 30 张手写 PDF 修正），8 列：润滑日期/设备名/位号/润滑点/油种类/加注量/润滑方式/检查人。37 条全部按 (tag, point) 匹配上系统润滑点（point 别名：齿轮箱(减速机)→减速机）。**用户 3 个决策**：① 操作人唐仕彬/刘正威用名字记录（operatorId 留空）；② actualOil 按记录表原文存（美孚/壳牌牌号，如 MOB DTE MEDIUM、Omala SH 320、MOBIL NUTO H46）；③ 不符项全按实际记录导入（VT1油站 NUTO H32 727L vs 台账 15#MAXTOP 600L；推进液箱实际 NUTO H46 vs 台账 Nyvac FR 200D；112曲轴箱实际 80L vs 台账 100L —— 台账标准都不动，只记实际）。**实现**：F12 脚本写 37 条 lubehistory（id `lh_imp_v3_001`~`037`，带防重复检查 + 分批 400）+ 更新 37 个 lubepoint 的 lastLubeAt/nextLubeAt/status=已润滑（按各点最新润滑日期 + periodDays 算 nextLubeAt）。本地 SEED 同步更新 37 个润滑点状态。**注意**：浓硫酸给料泵推进液箱实际用 NUTO H46（抗磨液压油）而非台账的 Nyvac FR 200D（抗燃液压油），是两种不同油，用户确认按实际记录但暂不改台账——后续若确认现场长期用 NUTO H46 可考虑改标准油号
2. **用户自助设置企业微信手机号**（2026-05-06）：之前 wechatMobile 字段只能管理员通过用户管理 sheet 添加，工人没法自己改。给"我的"页面菜单加 📞 "企业微信手机号" 入口（COMMON_MENU 和 admin 菜单都加），点击弹 sheet 让用户自己填 11 位手机号。**实现**：① 加 `setMobile` sheet 类型（参考 setPassword 的结构）；② `confirmSetMobile()` 函数校验 11 位 + cloudSaveUser；③ 已有手机号时显示当前号 + "保存修改" + "清除手机号" 按钮；④ 加 phone icon SVG 到 ICON_SVG。这样部署后工人各自登录就能填，不用管理员一个个录入
2. **企业微信群机器人通知集成**（2026-05-06）：用户的工厂用企业微信，要工单事件实时推群。**架构**：EMS 浏览器 → Cloudflare Worker（中转避 CORS + 隐藏 webhook）→ 企业微信群机器人 webhook。**Worker 配置**：`https://ems-notify.haoxinglong404.workers.dev` · token `ems-2026-nickel-secret-x9k2`（写在 EMS 源码里，token 仅做软屏障防爬虫，被刷只会群里灌广告，可重建机器人换 key）。**EMS 改动**：① 加 `notifyWeChat(content, mobiles)` + `getMobilesByRole()` + `getMobileByEmpno()` helper（fetch 失败静默 → 不阻塞工单流程）；② users 表加 `wechatMobile` 字段（11 位手机号校验，编辑/创建账号都能填，写入 Firestore）；③ 5 个事件触发通知：**提报**→@生产主任、**生产批准**→@机修主任、**机修批准/经理直批**→@所有检修人、**驳回**→@报修人、**完工**→@报修人+所有生产人。**Cloudflare Worker 部署经验**：免费版无需绑卡，注册→Workers&Pages→Create→选 Hello World→改 worker.js→Deploy。**用户操作步骤**：① 企业微信建**内部群**（外部群不能加机器人）；② 群机器人/消息推送→自定义机器人→拿 webhook URL；③ 注册 Cloudflare 邮箱即可（不绑卡）；④ 创建 Worker 起名 ems-notify，粘贴脚本，Deploy。**踩坑**：① 外部群不能加机器人（含外部联系人/个人微信好友的群被禁）→ 必须建内部群；② PowerShell URL 必须双引号包起来（否则被当 cmdlet）；③ 企业微信 markdown 不支持 @mention，必须用 text 类型 + mentioned_mobile_list 数组
2. **工单两级审批 + 经理直批 + 默认看全部**（2026-05-06）：用户提需求改造工单流程：① 所有人可提报；② 必须先**生产主任**审批，再**机修主任**审批，才能接单；③ **经理 / 管理员** 可直批（跳过两级 → 直接 approved）；④ 验收只能由生产人员/经理/admin 操作；⑤ 检修主任和经理都能派单（之前只有经理能派）。**新状态**：`pending-maintenance-approval` 介于一级二级之间。**新角色助手**：拆 `canApproveWO` 为 `canApproveProductionWO`（生产主任+admin）和 `canApproveMaintenanceWO`（机修主任+admin），`canVerifyWO` 加 `isManager`。**双段审批字段**：`productionApproverId/Name/At/Comment` + `maintenanceApproverId/Name/At/Comment`，旧 `approverId` 等字段保留兼容。**经理直批**：写入 `managerBypass:true`（内部审计标记），但 UI **完全隐藏**——批准人显示纯名字、等待行不列哪些角色能批（按用户要求"不能让兄弟们知道权力的黑暗"）。**默认 tab 改为"全部"**：之前默认"我的待办"导致普通员工以为没工单，改成所有人进来就能看到所有工单。**经理直批按钮 / Toast 只对 manager+admin 可见**，其他人完全感知不到这个 shortcut。**改动 10+ 处**：CSS 加 `.pending-maintenance-approval` 样式 / WO_STATUS_MAP 加新状态 / 拆权限函数 / `approveWorkorder` 三种 mode（bypass/production/maintenance）/ `renderWoActions` 按状态+角色显示不同按钮 / 时间线分 ②③ 两级审批 / `isMyTodo` 经理两个 pending 都算待办 / 空状态加"看全部工单"按钮等
2. **加美孚牌号字段 539 条 + UI 详情页显示 + 导出 Excel 加列**（2026-05-06）：用户单位的合作供应商是美孚，需要在每个润滑点显示标准油号 + 美孚等价牌号。**字段**：lubepoint 加 `mobilOil` 字段，仅 18 个 Excel 明确给出的映射应用，6 个推断项（15# MAXTOP/绍尔/10W-30/DIN PG 220/40WT/Fuchs Renolit）暂不加。**主要映射**：VG320→MOBILGEAR EP 320、VG220→MOBILGEAR EP 220、N46/L-FC46/L-HM46→MOB DTE MEDIUM、SP320→MOBILGEAR 600 XP 320、Nyvac FR 200D→MOBIL NYVAC FR 200D、2#/3#锂基脂→MOBILUX EP 2/3 等。**UI 改动**：[index.html:6237-6240](index.html:6237) 详情页"标准油号"下方加"美孚牌号"行（仅 mobilOil 非空时显示，绿色字 var(--g-deep)）。**导出改动**：[index.html:9505](index.html:9505) Excel 表头从 14→15 列，加"美孚牌号"在"标准油号"后。**F12 脚本 idempotent + 分批**：每批 450 条避免 Firestore 500 限制，写入完成后小概率有 WebChannel 重连警告 (`400 Bad Request`) 是 listen 流的非致命中断，写入本身成功
2. **油号写法统一 117 条 + 备货 Excel 导出**（2026-05-06）：用户提需求"统计每个子项需要哪些油，按 208L 一桶"。先 Python 全表扫 standardOil 找出 31 种独立写法，发现大量同一油不同写法的潜在重复。用户决策保留品质要求差异（EP220、Mobilgear 600 XP 100、mobilgear 600 xp 220 不合并），只把"纯写法差异"的 7 组合并为 5 个标准油号：① VG320 系列 27 条（ISO VG 320×24 + CLP ISO VG320×3）→ VG320；② VG220 系列 50 条（L-CKC 220×33 + L-CKC VG220×17）→ VG220（注意：用户选 VG220 不选 L-CKC 220 当主名）；③ Nyvac 12 条（MOBIL NYVAC FR 200D）→ Nyvac FR 200D；④ 2#锂基脂 23 条（2号锂基脂）→ 2#锂基脂；⑤ 3#锂基脂 5 条（3号锂基脂）→ 3#锂基脂。**保留**：3 条特殊"3号锂基润滑脂或3号二硫化钼锂基润滑脂"（浓硫酸污水泵专用）+ 3 条 2#极压锂基脂（褐铁矿小减速机轴承专用）。**Excel 导出**：`润滑油备货统计_2026-05-06_v2.xlsx`，1 个全厂汇总 sheet + 5 个区域 sheet（201/202/203/218/316-1，201B 合并到 201），按 208L/桶计算桶数。**全厂数据**：油类合计 36899 L ≈ 177 桶（一次完整换油），按 1.3× 备货 ≈ 231 桶。**最大三个**：SP320 8400L (53桶·高压釜给料泵) / Nyvac FR 200D 7140L (45桶) / VG320 6062L (38桶)
2. **第二隔室浓硫酸给料泵油量再修正 12 条**（2026-05-06）：上一轮修正时把所有 12 条浓硫酸给料泵推进液箱都改成 180L 是错的——Excel 第一隔室 (PP-111/211/311 A/B) 推进液 180L、第二隔室 (PP-112/212/312 A/B) 推进液 110L。本次修正：6 条第二隔室推进液箱 180→110L + 6 条第二隔室曲轴箱 80→100L 共 12 条。**用户澄清的等价关系**：隔膜室=推进液箱、机座=曲轴箱、减速机=减速机；油品也等价（ISOVG68/N100 ≡ Mobilgear 600 XP 100、N32 ≡ MOBIL NYVAC FR 200D），不需要改油号，只需改油量。**经验**：① 解析 Excel 多隔室设备一定要看主行+续行的全部部位组合，不要只看第一行就总结；② 同一行多个数字（如"180/台"）单位往往省略，需要从上下文推断
2. **EMS vs Excel 对比修正 36 条**（2026-05-06）：用 Python 全量比对 SEED_LUBE_POINTS vs `完整版润滑计划表20241228.xlsx`，发现：① 油号差异 11 条（3 真差 + 8 OCR 错别字 酯/脂）；② 用量差异 27 条（21 高压釜搅拌齿轮箱 + 6 原矿浓密机搅拌器，SEED 偏小）；③ 周期差异 69 条（月→天精度，未改）；④ Excel 有 SEED 缺 224 条（高温预热器给料泵/浓硫酸给料泵的 隔膜室/止逆器/密封液总站减速机 等子润滑点，未补）。**本次修了 36 条**：(a) 3 条 202-PE-TH-101/201/301 驱动外密封油号 N46→VG220；(b) 21 条高压釜搅拌齿轮箱用量按 Excel 调整 (1-2 隔室 132kW: 119L→150L · 3-7 隔室 110kW: 110L→130L)；(c) 12 条 浓硫酸给料泵推进液箱（=Excel 隔膜腔）用量 50L→180L (PP-111/112/211/212/311/312 各 A/B)。周期、其他 Excel 缺项暂不动。**Excel 解析技巧**：合并单元格的设备名/位号要从主行继承到续行，位号"~"展开三种模式（A~C 字母范围 / 101A~301A 数字递增 / 103A/B~203A/B~303A/B 段间累计），需正则区分；Excel 量字符串如 "132KW的加油150L" 不能简单 regex，要识别 KW 在前的整体单位；用量比对要把 SEED g 值跟 Excel kg×1000 同级比较
2. **203 起重机按 Excel 标准对齐 + 12 絮凝剂减速机按国茂手册填 + 3 预热器污水坑电机填**（2026-05-06）：用户提供"完整版润滑计划表20241228.xlsx"覆盖 4 类 203 起重机的 3 个润滑部位（减速机/齿轮联轴器/卷筒内齿圈）。**起重机操作**：① 修 5 条 减速机齿轮箱→减速机 + L-CKC 220 + 4或5L · 180天；② 填 8 条空联轴器/齿圈 = 2#锂基脂/3#锂基脂 · 500g · 90天；③ 新增 32 条缺失（10 台 × 3 点 + CR-301 缺 2 点）lp_v12_001~032。**絮凝剂减速机**：12 台 218-PE-AG-003A~L 国茂 GRF109-...-M4 减速机，从《G系列减速电机使用说明书》第 37 页查到 GRF109 在 M4 安装方式下油量 19.2 L · 油号 L-CKC 220 · 周期 365 天（说明书 P19"使用一年左右更换"）。**3 预热器污水坑搅拌电机**：203-PE-AG-103/203/303·Y4kW-4P→Y112M-4 机座 → SKF 公式 4.96 g · 2#锂基脂 · 90 天。**重要发现**：国茂说明书 P19-20 明确写"63-180 机座电机输入单元用密封轴承不需补脂"，但 200-315 机座要补脂（页 20 表格按机座大小给出 g 数）。当前 12 台絮凝剂电机用的 YE3-160M-4（160 机座）按用户决策保留 SKF 12.5g/90天 不动（NDE 端可能仍需补脂）。**经验**：① F12 脚本不要把多个独立改动合并到一个大批次（用户无法分别确认/回滚）—— 每个用户请求建独立脚本；② 国茂减速机型号 GRF109-Y11-4P-30.77-M4-D450-ZPIEC 解析：109 机座、Y11=11kW 电机、4P=4 极、30.77=减速比、M4=安装方式、D450=输出轴、ZPIEC=配置；③ Y 系列电机功率→机座号映射：4kW@4P=Y112M-4
2. **21 条高压釜搅拌·机械密封轴承填脂资料 + 删 1 条 lp_0337 重复**（2026-05-06）：21 台高压釜搅拌器（203-PE-AG-101A~G + 201A~G + 301A~G）的机械密封 ESD64H 配套轴承润滑——批量填 **Fuchs Renolit H 443 HD 88（NLGI 2-3 锂基皂化含 EP）· 26 g · 3300h/150天周期**（信息来自 ESD64H 技术文档）。**附带**：发现 203-PE-AG-101A 有 2 条机械密封轴承（lp_0336 + lp_0337 完全重复），删 lp_0337。**机械密封另一项"密封液（隔离液）"用户决定不录润滑点**（按需补充，非定期）。SEED 603→602。**经验**：① 同设备同 point 出现重复 lp 是数据错误信号——查 22 vs 21 数量差时定位到此问题；② Fuchs Renolit H 443 HD 88 是德国进口专用脂，备件库要确认有无库存
2. **40 条电机润滑点按基座号填充加注量 + 删 17 条 71 座免润滑电机**（2026-05-06）：用户提供 SKF 公式表（g=0.005×OD×W），按电机基座号映射加注量。**填充 40 条**：80/90/160/180/200/250/315/355 座，统一 2#锂基脂·周期 90 天·periodHours=2160。**删 17 条**：71 座电机（HEW DCEx 71KH×6 + 南阳 YE4-71M2-4W×6 + YS7134×5），均是 0.37~0.55 kW 小电机，**铭牌确认轴承免润滑（密封轴承）·删除润滑点是正确做法**，等后续核实再单独决定要不要补回。**SEED**：620→603 条。**踩坑**：① 第一版 regex 把 ABB "180M 机座" 的 "180" 误抓成 80（前缀 80）→ 改成"机座"显式标注优先 + 标准型号优先；② F12 脚本里第一版用模板字符串 \`...${{var}}\\n...\` 触发语法错误（Python 输出 `\\n` 转义不一致），改用老式 `'...' + var + '...'` 拼接更稳定；③ 第一版批量更新 F12 脚本误写出 158 条（混进了原有 51/72/80 g 的非表条目），改用"严格筛 standardAmount 是表中精确值（3.29/3.9/12.5...）"的过滤器才正确拿到 40 条。**剩余待补**：156→99 条，主要是机械密封轴承 22 + 减速机 19 + 机架轴承 17 + 轴承室 11 等
2. **218 区 97 条 lubepoint tag 统一为设备表标准位号**（2026-05-06）：长期数据不一致问题——218 区 SEED_LUBE_POINTS 用的是 `218-TBD-PAC加药泵-01` 占位 tag，SEED_EQUIPMENTS 用 `218-PE-PP-001A-TBD` 标准 tag，两边 0 重叠，导致工人在润滑详情页看不到关联设备铭牌。Python 重写本地 SEED + F12 writeBatch 同步 97 条云端，1:1 映射 0 失败。**别名映射**：刮泥机→行车式刮泥机、潜水泵→污水池潜水泵、PAM搅拌器→PAM 搅拌器（带空格）、pac搅拌器→PAC 搅拌器。**附带修复**：20 条 lp.name 也统一为 eq.name。**经验**：① 写 F12 大脚本时不要用模板字符串多行（``...${var}...\n...``）—— Python 输出 `\n` 时容易转换不一致导致语法错误，**改用 `'..' + var + '..'` 老式拼接更稳定**；② 1:1 映射前要 `seen_eq_tags` 防多对一冲突；③ Python 重写 SEED 用 `json.dumps(separators=(',',':'), ensure_ascii=False)` 保持紧凑无空格风格
2. **润滑历史"加脂/换油"标签按油号判定**（2026-05-05）：[index.html:6219](index.html:6219)。原来用 `h.operationType` 看历史记录保存的快照值——批量修 75 条 lubepoint type 后，老历史记录因 operationType 仍是 grease 旧值，UI 仍显示"加脂"（实际是 N46 类油）。改为按 `h.actualOil` 是否含"脂"判断（与 `getLubeKind` 一致），老记录无需改数据自动显示正确。**经验**：写带元字段（operationType/category 等）的 history 记录时，能从 actualOil/actualType 等"事实字段"现算的，就不要在 history 里冗存 —— 否则后期改 type 就要数据迁移
2. **75 条润滑点 operationType 录错批量修正 grease→oil**（2026-05-05）：经用户核实，N46/L-FC46/MOBIL NYVAC FR 200D/mobilgear 600 xp 220/SP320/Omala S4 GXV 220 PAO/Nyvac FR 200D/15# MAXTOP/DIN 51502 CLP PG 220 共 9 种实际是油的油号被录成了 grease。F12 writeBatch 一次性更新云端 + Python 重写本地 SEED（保持 JSON 紧凑无空格）。**修正后 type 分布**：grease 297 / oil 323（共 620 条）。**效果**：UI 单位从 g 变 L，登记标签从"加脂"变"换油"；tab 分类无变化（getLubeKind 按油号判定）。**踩坑**：脚本必须 idempotent —— 跑前先 getDoc 校验当前 type 仍是 grease 且油号不含"脂"，否则跳过（防重复执行误改）。SEED 重写用 `json.dumps(separators=(',',':'), ensure_ascii=False)` 保持原文件紧凑风格，文件大小从 1945454→1945245（减 209 字节，对应 75×('grease'→'oil') 节省）
2. **润滑导出 Excel 字段 bug 修复 + 加"润滑点"列**（2026-05-05）：[index.html:9526-9540](index.html:9526)。原代码用 `h.lubePointTag`/`h.lubePointName` 但 schema 里实际是 `h.tag`/`h.name`（由 lubeExecBuffer 在 [index.html:6280-6282](index.html:6280) 写入）→ 导致导出表"位号""设备名称"列**全是空**。同时加列「润滑点」+ `h.point`（之前同设备多润滑点根本分不清），从 8 列变 9 列：序号/执行时间/位号/设备名称/**润滑点**/实际油号/实际量/操作人/备注。**起因**：今天恢复 lp_0263 历史时发现导出表无法按 tag 筛选只能靠 actualOil + 时间反推匹配
2. **lp_0263 测试历史误删后恢复**（2026-05-05）：202-PE-TH-301 小减速机轴承的飞书原始记录（2025-10-08·唐仕彬·2#锂基酯·5kg）在删除测试记录时被一并误删，从用户 5/5 早上 8:30 导出的 Excel（含被删数据快照）反推匹配（按"3 台褐铁矿浓密机·油号 2#锂基酯·量=5"+ 润滑点 sheet 的 lastLubeAt 交叉对位）后用 F12 脚本补录回 Firestore，actualAmount 写 5000（5kg→5000g 单位修正）。**经验**：① 删数据脚本要内置二次确认（特别是当只剩 1 条历史时 prompt 提示风险）；② 飞书 Excel 导入的"2#锂基酯"是 OCR 错误（应为"2#极压锂基脂"，极压丢了 + 脂错成酯），但恢复时保留原值不动（操作人/油号原样恢复）；③ 用户的"操作人不能变"的偏好已记忆
3. **润滑脂单位标签修正 kg→g**（2026-05-05）：208 个脂类润滑点（油号含"脂"）的 standardAmount 实际全部按"克"录入（电机轴承典型 51、油泵电机 4、轴承座 500、机架轴承 722——按 kg 算工程上不可能），但 UI 在 4 处硬编码 `lp.operationType === 'grease' ? 'kg' : 'L'` 一律标 kg。改为 'g'。**改动 4 行**：[index.html:6131](index.html:6131)（润滑卡片）·[6194](index.html:6194)（详情页+历史）·[6300](index.html:6300)（登记表单标签）·[6417](index.html:6417)（设备详情·润滑点 tab）。无数据迁移、无 Firestore 改动。**附带发现（未修）**：① 164 条 `operationType='grease'` 但油号是 N46/L-FC46（轴承箱油）·实际是 oil 录错了 type，对显示无大影响（getLubeKind 看油号字符判断 tab 分类）；② 3 台褐铁矿浓密机 `小减速机轴承` standardAmount=8000g（=8 kg）经用户 5/5 核实为正确值，不修
2. **Firestore 安全规则升级 · 匿名认证 + 集合白名单**（2026-05-03 · **当天全部完成**）：测试模式 5/19 到期前一次性闭环。**代码**：index.html 加 firebase-auth.js import + `signInAnonymously()` 在应用启动自动执行 + `init()` 第一行 `await authReady` 阻塞所有 Firestore 操作直到认证成功。**规则**：`firestore.rules` 12 集合白名单（users/equipments/workorders/lubepoints/lubehistory/spareparts/spareparthistory/tools/toolhistory/inspecttemplates/inspecthistory/meta）· 全部要求 `request.auth != null` · 兜底 `match /{path=**} { allow read,write: if false; }`。**部署链路**：commits 4273333+c7a65d2 push main → GitHub Pages 自动部署（不是 CLAUDE.md 之前误写的"用户手动上传"）→ Firebase Console 启 Anonymous → Console 发布 rules（用户在 F12 验证 uid + 写一笔工单成功后才发布）。**用户指南**：`FIRESTORE_SECURITY_DEPLOY.md` 4 步部署流程 + 回滚方案。**附带修复 1**：`woBuffer` 旧 bug —— 模块作用域 `let woBuffer` 不在 window 上，工单表单内联 `oninput="woBuffer.x=this.value"` 全部静默失败 → 提交时报"请填写联系方式"。修法：`Object.defineProperty(window,'woBuffer',{get/set})` 桥接（同样的桥接套路适用任何 oninput="moduleVar.x = ..." 的旧代码）。**附带修复 2**：CLAUDE.md "🔧 直接操作云端的技巧" 段落更新——以后改云端必须走 F12 浏览器会话（自带 anonymous Firebase Auth token），Python urllib + API key 会被规则拒。**经验**：① 规则发布瞬间生效，部署前要让代码在线 1-2 小时让所有人浏览器拿到新版本（避免缓存里的旧代码被规则拒）；② 部署后立刻在已登录浏览器试一笔写入再走人；③ 若规则发布后报 PERMISSION_DENIED 立刻把规则换成 `allow if true` 回滚（30 秒）
2. **巡检模块 v11 上线**（2026-04-29）：完整设备巡检功能。**数据**：17 个 type→模板（离心泵/搅拌器/柱塞泵/密封系统/地坑泵/隔膜泵/螺杆泵/风机/浓密机/液压设备/空压机/给料器/起重机/压力容器/贮槽/非标静设备/成套设备）·新增 2 个 Firestore 集合 inspecttemplates+inspecthistory · marker `inspect_init_v11_20260429`。**UI**：底栏改横滑 flex（7 项），顺序：设备→巡检→工单→备件→工器具→润滑→我的；宽屏左侧栏间距收紧（padding 28→14·gap 4→2·item padding 12→8·width 240→220）并修复了 narrow 模式 flex-basis 渗透 wide 的 bug；巡检主页 3 tab（待巡检/异常/历史）+ 4 概览卡（全部/逾期/到期/未初始）+ 区域/类型筛选 pills（仅待巡检 tab）+ 搜索；设备列表按区域工艺顺序排序（201→202→203→316-1→218→923→546）。**特殊项**：每模板首项"设备停机未运行"是单按钮"是"，点选后自动清空其他项+灰显，提交跳过其他项校验，记录带 stopped:true 标记。**权限**：admin 可删历史。**用户定制**：用户用 `巡检模板核对.html`（仿 `设备分类核对.html` 模式）逐项调整后导出 markdown，再批量 PATCH 云端 + 同步本地 SEED。**踩坑**：第一版用 `user.id` 写 inspectorId 字段失败（Firestore 不接受 undefined），系统实际是 `user.empno`，已改 `(user && user.empno) || ''` 兜底
2. **设备 type 字段标准化第二轮（巡检模块前置）**（2026-04-29）：再调 17 条。**11 台从离心泵迁地坑泵**（潜水/排污类单独分类）：218 排泥泵 6 + 218 污水池潜水泵 2 + 218 集水坑潜水泵 1 + 923 液下渣浆泵 2。**6 台从空压机修正为起重机**（203-PE-CR-101/201/301 LX5t-5m + 203-PE-CR-102/202/302 LD10t-9.5m，原来 type 录错）。雨水回用泵 546-JP-PP-001A/B/C（未装机）保留离心泵。**最终 17 类 type**：离心泵 101 / 搅拌器 69 / 柱塞泵 39 / 密封系统 36 / 地坑泵 32 / 压力容器 31 / 隔膜泵 28 / 贮槽 27 / 起重机 18 / 螺杆泵 12 / 非标静设备 12 / 风机 3 / 浓密机 3 / 液压设备 3 / 空压机 3 / 成套设备 4 / 给料器 1
2. **设备 type 字段标准化（巡检模块前置工作）**（2026-04-29）：71 台 type 字段调整。**变容积泵 57 台拆分**（按用户指定）：18 台→隔膜泵（高压釜给料泵 6 + 第一/二隔室浓硫酸给料泵 12）·39 台→柱塞泵（密封液循环泵 18 + 预热器给料泵密封液给料泵 12 + 高压釜搅拌冲洗水泵 6+3）。**3 处重复命名合并**：起重设备→起重机（10）·空气压缩机→空压机（2）·罗茨风机由"空气压缩机"纠正为"风机"（2，原因：脚本 if/elif 顺序匹配先吃掉了空气压缩机分支，需第二轮 PATCH 修正）。**最终 type 分布 17 类**：离心泵 112/搅拌器 69/柱塞泵 39/密封系统 36/压力容器 31/隔膜泵 28/贮槽 27/地坑泵 21/螺杆泵 12/起重机 12/非标静设备 12/空压机 9/风机 3/浓密机 3/液压设备 3/成套设备 4/给料器 1。本次为下一步"设备巡检模块"按设备类型配置巡检模板做准备
2. **218 区新建 2 台 PAM 加药装置子设备**（2026-04-28）：之前系统里没有这俩，新建记录使设备总数 420→**422**。① **eq_new_058 / 218-PE-SF-001-TBD / PAM 给料器**（**新引入位号缩写 SF = Screw Feeder**）：拓速 YS712-4 0.37kW 电机 + 安徽合力 MB L04 行星摩擦式 CVT（1/5 + 200~1000rpm 无级调速），用作 PAM 三槽一体自动泡药机控制干粉投加速度。② **eq_new_059 / 218-PE-FA-002-TBD / PAM 吸料泵**（FA-001 已被 132kW 罗茨风机占用，这台占 002）：亚士霸 YASHIBA XGB710-30BS6 旋涡风机 3kW · 318m³/h，用作 PAM 干粉真空吸送（协议设计套 2，现场仅 1 台）。**Firestore createDocument 经验**：先查 highest eq_new ID 再 +1（这次一开始用 055/056 报 409 Conflict，因为已被 546 区雨水回用泵占用，用 058/059 才成功）
2. **218 区 2 台污水池潜水泵从协议+清单补齐**（2026-04-28）：218-PE-PP-006A/B-TBD（eq_new_036/037）·南方泵业 100WQ100-30-15JY(I)·Q≥100m³/h·H≥30m·N=15kW·铸铁·IP68·2 台·寿命 5 年。**无实拍铭牌**——按"信息来源：钲清协议 BVVE24-FMI-HPAL-116 + 218 设备清单 xlsx · 实物铭牌待补"标注，motor 字段用模板"内嵌潜水电机 15kW · IP68（详细参数待铭牌确认）"。218-PE-PP-007 集水坑潜水泵在 218 资料里查不到匹配（协议仅 2 台 100WQ），暂留空。218 区资料目录见 `C:\\Users\\15576\\Desktop\\claude\\218设备资料收集_按设备分类\\` (18 设备分组 + 项目总资料)
2. **218 区 3 台 PAM 搅拌器铭牌+技术协议补齐**（2026-04-28）：218-PE-AG-002A/B/C-TBD（eq_new_013~015）·钲清环保。name 由 `PAM搅拌器` → `PAM 搅拌器`（与 PAC 统一加空格）。motor：皖南 YE3-80M2-4 三相异步 0.75kW · 380V/50Hz · 1.8A · 1430rpm · IE3 82.5% · 6204 轴承 · 17kg · 制造 2024.07（编号 82422333）。gearPump：国茂股份 **BLD0-17-Y0.75-ZP 摆线针轮** · 速比 17 · 输出≈84rpm（编号 SN00752105）。spec/specDetail 来自钲清协议（同 PAC）：桨叶 Ø300mm 单层双叶 316L · 搅拌轴 L=800mm 316L · 数量 3 · 配套 PAM 制备系统 3m³/h（含三槽一体自动泡药机）· 设计寿命 5 年。**协议 vs 实际**：本次匹配比 PAC 那次好 —— 电机型号一致（YE3-80M2-4）、速比一致（17），仅供应商（上海/茵梦达 → 皖南）和减速机机座号（BLD10 → BLD0，更小）有变。**协议描述错误**：BLD 系列为摆线针轮，协议里写"齿轮式"是错的，铭牌正确
2. **218 区 2 台 PAC 搅拌器铭牌+技术协议补齐**（2026-04-28）：218-PE-AG-001A/B-TBD（eq_new_016/017）·钲清环保。name 由 `pac搅拌器` → `PAC 搅拌器`。motor：皖南 YE3-90L-4 三相异步 1.5kW · 380V/50Hz · 3.5A · 1430rpm · IE3 85.3% · 6205 轴承 · 29kg · 制造 2025.01（编号 82498411/82498419）。gearPump：国茂股份 **BLD1-23-Y1.5-ZP 摆线针轮** · 速比 23 · 输出≈62rpm（编号 SN00763460/SN00763451）。spec/specDetail 来自技术协议 BVVE24-FMI-HPAL-116（C:\\Users\\15576\\Desktop\\claude\\218设备资料收集_按设备分类\\00_项目总资料\\）：桨叶 Ø600mm 双层二叶 316L · 搅拌轴 L=2000mm 316L · 配套 PAC 溶液箱 Φ1750×2300mm PE · 设计寿命 5 年。**关键发现**：协议设计电机为 YE3-100L2-4 **3 kW**（上海电气/茵梦达），减速机 BLD10-17-3（速比 17），但实拍铭牌为皖南 1.5 kW + BLD1-23（速比 23）—— **实际安装比设计降功率一半**，已在 specDetail 注明"以 motor/gearPump 为准"。**PDF 提取技巧**：pypdf 抽这份协议文本时**字符顺序是反的**（line[::-1]即可），原始 PDF 是中文公文格式，pypdf 6.10.2 也搞不定，需要 reverse line by line
2. **218 区 3 台行车式刮泥机铭牌+采购规格补齐**（2026-04-28）：3 台 218-PE-SC-001A/B/C-TBD（eq_new_018~020）·钲清环保·一次性补 6 字段。name 改为"行车式刮泥机"。motor 双电机：行走电机×2 皖南 TYCP80M1-8-15 永磁同步变频 0.55kW（100Hz/1500rpm/14kg/编号88195637）+ 升降电机 皖南 YE3EJ80M2-4 电磁制动 0.75kW（DC99V/8N·m 制动/22kg）。gearPump 双减速机：行走 国茂股份 GKA89R59-Y0.55-4P-951-M4-ZPIEC 速比 951 用油 L-CKC220 + 升降 国茂股份 GS99R59-Y0.75-4P-714-M4-A+B-ZPIEC 速比 714 用油 L-CKE/PG680 合成。supplier 三段：钲清环保（本体）/皖南（电机）/国茂股份（减速机）。spec：钲清环保 行车式刮泥机·轨道间距 14.5m。specDetail：配套行车桁架/驱动机构/刮泥耙/刮板升降/程序控制·设计功率 0.75×2+1.1 kW（**铭牌实测偏小**：0.55×2+0.75=1.85 kW vs 设计 2.6 kW，已在 specDetail 注明"以 motor 字段为准"）·碳钢防腐+水下 316L·设计寿命 10 年。**核对工具**：D:\\青山\\工作资料\\铭牌\\218\\刮泥机\\核对.html 是本次专门做的半屏图片查看器（滚轮缩放/拖拽平移/双击复位/ESC 关闭），用户在里面改完字段一键导出文本贴回来，下次类似情况可复用此模式
2. **218 区 12 台絮凝剂搅拌器 motor 按铭牌实测订正**（2026-04-28）：实拍铭牌后发现昨天填的几处需修正。motor 字段：电流 22.4A→21.5A（实测）；删除"冷却 IC416"和"额定转矩 71.5 N·m"（铭牌未标，是按通用值推算补的）；加 113 kg / 前后轴承 6309 / 制造 2025.01；安装 B5→IM B5。**踩坑记**：sync 脚本最早用 `\{[^{}]*"tag":"X"[^{}]*\}` 正则，但 json.dumps 默认会加空格 `"tag": "X"`，第二次同步时正则失效，导致脚本误把 motor 写进了 `SEED_TAG_FIXES_V3` 数组（碰巧那里也存了 tag）。修法：限定在 `SEED_EQUIPMENTS` 数组边界内查找 + 用 `"tag"\s*:\s*"X"` 容忍空格 + 加 sanity 检查（必须含 `area` 或 `name` 字段）。今后写 SEED 同步脚本必须遵循这套
2. **201 区 6 台原矿浓密机给料槽搅拌 motor 修正 + supplier 补齐**（2026-04-28）：6 台（201-PE-AG-001A/B/C + 201B-PE-AG-002A/B/C，eq_seed_0001~0006）按实拍铭牌更新。motor 由旧的 `电机:皖南/上电YE3-132KW-4/IEC/IP55/F/WF1` 改为 `主电机：上海电气 YE3-315M-4 WF1 · 132 kW · 380V/50Hz · 236 A · 1485 r/min · IE3 95.6% · cosφ 0.89 · F 级/IP55 · △接法 · 894 kg · 标准 GB/T 755 · 制造 2024.07`（修正：型号实为 315M 机座 + 4 极，旧记录把功率塞到型号位是错的；皖南供应商记录被铭牌否定）。supplier 补三段式 `恒丰泰精密机械（本体）/ 上海电气（电机）/ 南京高精齿轮 NGC（减速机）`。组内同款省个体序列号
2. **218 区 12 台絮凝剂搅拌器铭牌补齐 + motor/gearPump 拆分**（2026-04-27）：218-PE-AG-003A~L-TBD（eq_new_040~051）补 spec/specDetail/motor/gearPump/supplier 5 字段。上一会话云端把减速机塞到 motor 里了，本会话拆开：motor=安徽皖南 YE3-160M-4 11kW 主电机参数；gearPump=国茂 GRF109-Y11-4P-30.77-M4-D450-ZPIEC（编号 SN00763476，用油 L-CKC220）；spec=钲清环保絮凝搅拌机（DXJ 机架式）；supplier 三段式（钲清+皖南+国茂）；specDetail=立式搅拌机·主体碳钢防腐+水下316L·搅拌轴/桨叶316L·12台3套×4池·设计寿命10年·减速比30.77:1·输出转速≈47rpm。云端 12 条 PATCH + 本地 SEED 同步
2. **详情页返回列表的滚动位置修复**（2026-04-26）：switchModule 加 moduleScrollMap = new Map() · 切换前保存当前 module 的 .content scrollTop · 切换后用 rAF 恢复目标 module 的 scrollTop（首次访问默认 0）。修复"列表→详情→返回时跳到顶部"的 UX bug。副作用：底部 tab 间切换也各自保留 scroll 位置（mobile 友好）。原 `document.querySelector('.content').scrollTop = 0;` 这行被替换
2. **218 + 923 区 12 台设备铭牌补齐**（2026-04-26）：5 台 PAC 加药泵（218-PE-PP-001A~E-TBD）+ 5 台 PAM 加药泵（218-PE-PP-002A~E-TBD）+ 2 台液下渣浆泵（923-SP0301/0302）一次性补 spec/specDetail/motor/supplier。**PAC**：浙江爱力浦 JXM-A-400/0.5（400 L/H · 0.5 MPa）+ 宁波奉化安铃 YS7134 0.55kW · 1400r/min · 6.8kg · 制造 2024-11。**PAM**：浙江爱力浦 JZM-A-1000/0.35（1000 L/H · 0.35 MPa）+ 宁波奉化安铃 YE3-80M2-4 0.75kW · η80.7% · cosφ 0.82 · 9.8kg · 制造 2023-03。**923 液下渣浆泵**：上利石泵业 65SZPL-30 · 75m³/h · 35m · 510kg · 出厂 2024-12 · 编号 25011921 + 上海电气 YE3-200L-4 30kW · IE3 93.6% · IP56 · 212kg · 制造 2025-02。218 区按"先保留 TBD 位号录入设备信息"策略，TBD 改名后期 batch 处理
3. **316-1 区污水泵铭牌补齐**（2026-04-26）：316-1-PE-PP-002 污水泵（eq_seed_0349）补 motor + specDetail + supplier。主电机：上海电气 YE3 160M-4 WF1TH 11kW · 380V/50Hz · 21.5A · 1465r/min · IE3 91.4% · cosφ 0.85 · F/IP55 · △接法 · 108kg · 制造 2025-03。泵体：宜兴灵谷 80FYUC-35-30/35-1500+300 · 30m³/h · 35m · 1450r/min · 液下深度 1500mm · 520kg · 出厂 2025 · 编号 40YC1712（铭牌厂家位号 109-316-1-PE-PP-002，系统取 316-1-PE-PP-002）
4. **润滑历史导入 · 194 条 lubehistory + 426 个未初始润滑标记**（2026-04-25）：从飞书导出的 Excel 194 条真实润滑记录全部入库（lubeAt 用 Excel 实际日期 · 8 位操作员含 3 位已注册 + 5 位姓名占位 · 杨琨/杨锟统一为杨锟）。剩余 426 个润滑点 status='未初始润滑' + 清空 lastLubeAt/nextLubeAt（替代之前的"逾期 46077 天"占位显示）。UI 同步加新状态：getLubeStatus 返回 'pending-init' / renderLubeOverview 加"未初始"卡片（4 列）/ renderLubeCard 显示灰色徽章 / 加 .lube-status-tag.pending-init + .lube-ov-card.pending-init 样式。匹配技巧：tag 双重归一（去空格/折叠连字符）+ point trim → 194/194 全匹配
5. **角色架构重构 · 5 角色 → 8 角色**（2026-04-25）：新增 8 角色（生产员工/班长/主任 · 检修员工/班长/主任 · 经理 · 管理员），按部门 + 层级。删除 reader 角色。引入 12 个权限辅助函数（canApproveWO/canTakeWO/canVerifyWO/canExportData/canBatchImportTools/canEditEquipment/canManageUsers/canHardDelete/canAssignWO + isAdmin/isManager/isProduction/isMaintenance）。15 用户全部迁移到新角色（admin/manager/检修主任/检修班长/生产主任/生产班长 各若干）。所有原 user.role==='admin'/'tech'/'reporter' 等硬编码改用 helper 函数。MENU_BY_ROLE 改为 8 项。角色选择器 UI 5→8 选项
6. **设备列表宽屏中间列 + F12 调试工具**（2026-04-25）：≥1024px 卡片 eq-card-left 固定 360px + 中间 eq-card-extra 列显示电机/规格首行预览（hover tooltip 全文）。加 window.__emsStats() / __emsUsers() F12 助手用于快速看数据分布
7. **203 区收官 · 45 台 EP 配套系统补齐**（2026-04-24）：**A 组 高压釜搅拌事故冲洗水泵 3 台**（PP-114/214/314：上海电气 YE4-132S-4WF2 5.5kW + HYDRA-CELL G10XRSGSFEMB Wanner 美国 · 40WT HYDRA-OIL）；**B 组 冲洗水泵 3 台**（PP-116/216/316：BPY 200L-4 WF1TH 30kW 变频 + YIERYI G200 风机 + 石家庄 40D-A40 Q30m³/h H60mH₂O）；**C 组 阀门油压站 Z102-0084 整套 3 台**（EP-103/203/303：ABB IE3 180M-4 22kW + CONCENTRIC Hof GmbH 齿轮泵 + Cowan Dynamics E2H90 执行器 + WAROM FXMD 配电箱）；**D 组 SPN3M0001-00 补液站 3 台**（EP-102A/202A/302A：EagleBurgmann 德国 · 20L/min 55bar · 190L 水/乙二醇 50/50）；**E 组 CMXT-F54 补液站 3 台**（EP-102B/202B/302B：SINOSEAL · MAWP 5.0MPa · 20L/h · 1000L 水30%/乙二醇70%）；**F 组 HT SYS09863 密封液系统 9 台**（EP-X05A/B/C：EagleBurgmann Australasia · API Plan 53M HT · MAWP 50 kg/cm²@165°C）；**G 组 MT SYS-09864 密封液系统 6 台**（EP-X04A/B：API Plan 53M MT · 同参数 B1 序列）；**H 组 CMG3-53B(L) 中密控股 15 台**按级压力（MT1级 1.0/0.84 MPa · MT2级 1.2/0.95 · HT1级 1.2/0.94 · HT2级 2.1/1.85 · HT3级 2.9/2.60；机封腔实压=设定−0.4 MPa · 图号 SNSX24C3-161/166）。顺便修 EP-105A 分类：液压设备→密封系统
2. **203 区 118 台大批量补齐**（2026-04-24）：58 Ⅰ类静设备全标 N/A（压力容器/贮槽/非标静设备）；3 台 Flender B4SV 17 B 纠正型号；**57 台动力设备按铭牌**：高压釜 1-2 隔室搅拌 6 台（BPY-315M 132kW + H2SV10B + EKATO HWL2160NV + 正能 G-315AW 风机）、3-7 隔室 15 台（BPY-315S 110kW + H3SV9B）、高压釜给料泵 6 台（ABB 920kW + H3SH 20 + GEHO TZPM 2000HB）、密封液供给系统 D/E/F/G 4 组 30 台（定位为"整套系统"，含调压阀/安全阀等附件）
2. **本地预览模式基础设施**：`index.html` 加 `?preview=1` URL 开关 + 本地 SEED 覆盖云端字段显示；`preview.bat`/`preview.py` 一键起 localhost:8000 供测试；新工作流：改本地 → 预览确认 → 云端 + push
3. **202 区 22/45 台补齐**（2026-04-24）：3 贮槽+3 静态混合器=N/A；6 预热器给料泵（525 ZGF200-700 + BPY-3553-6 355kW + G-355AF 风机）；4 污水坑搅拌（GMC400-119E + YE3-112M-4 + 通力 TRF78）；3 预热器给料槽搅拌（GMR20000-19E + YE3-315L2-4 + Flender B4SV17-80）；3 褐铁矿浓密机（SGN-38 + 皖南 YE3-315S-4 110kW + Brevini SL6004 i=241.1 + CSE 液压站 + A600TL 风冷）
2. **201 区 20/20 台全部信息补齐完成**（2026-04-24）：污水泵 + 3 贮槽（N/A）+ 6 浓密机搅拌（NGC MH3S150）+ 1 污水坑搅拌 + 9 原矿浆泵（BPY-355L3-6 纠 L2→L3，含 G-355 散热风机）。约定：组内同款不写个体编号（工作量考虑）
2. **SEED 常量同步为当前线上快照（2026-04-24）**：SEED_EQUIPMENTS 361→420 / SEED_LUBE_POINTS→620 / SEED_SPARE_PARTS→1861 / SEED_TOOLS_V9→251。含 218/923/546 新区设备、52 个 TBD 位号、84 条协议待清点。v2-v10 迁移函数保留（markerId 幂等）
3. 底栏 grid 6 列 + cart bar 移出 .content 跟 nav 同级（紧贴 nav 上方）
4. 工器具购物车（领用 vs 借用 2 类）+ 归还流程 + 批量入库
5. 备件 nav 合并为单"备件"（内含 2 tab） + 数据导出（含 SheetJS CDN 懒加载）
6. 宽屏布局（≥1024px 左侧 240px 镍钴绿侧栏）
7. V4-V10 七次数据迁移

**🔧 直接操作云端的技巧**（**2026-05-03 后改用 F12 浏览器会话**）：
~~Python urllib + API key~~ 不再可用——规则已发布要求 `request.auth != null`，光 API key 没 Firebase Auth token 会被拒/超时。
**现行做法**：让用户在 EMS F12 控制台跑 JS（浏览器已带匿名认证 token）：
```js
// 在 EMS 网页 F12 console 里跑
(async () => {
  const a = await import('https://www.gstatic.com/firebasejs/12.12.0/firebase-app.js');
  const m = await import('https://www.gstatic.com/firebasejs/12.12.0/firebase-firestore.js');
  const db = m.getFirestore(a.getApp());
  // 查: m.getDocs(m.query(m.collection(db, 'workorders'), m.where('field', '==', x)))
  // 改: m.updateDoc(m.doc(db, 'equipments', id), { motor: '...' })
  // 删: m.deleteDoc(m.doc(db, 'workorders', id))
})();
```
数据流程：① 给用户 F12 脚本 ② 用户跑完确认 ③ 同步本地 SEED ④ commit + push。
**特殊例外**：DELETE 单条文档 + GET 单条文档（非 runQuery）有时仍能用 API key 工作（限流不严），但不要依赖。

**已知待办**：
- ✅ 生产模板误升级事故已回滚（2026-07-05 深夜用户批准执行：17 个 v11 模板写回 + 删 4 个新增文档 + 删 marker，回读核验 0 残留；线上巡检恢复正常）
- ✅ 数值点检 v2 已上线运行（2026-07-06 确认：rules 已发布、迁移已跑、工人已提交 35 条真实点检历史）
- 📝 数值点检暂缓设备后续视推行情况补做：潜水泵 9（要设计水下泵专用简化表）、成套设备 4（刮泥机/絮凝剂系统）、给料器 1
- 📝 218 区 54 台 TBD 临时位号待用户分配正式位号（含 spec 字段缺失 14 条）
- 📝 54 个润滑点待补充标准油号（机架轴承 17 + 电机 16 + 轴承室 11 + 减速机 7 + 轴承箱 3，多为 218 TBD 未投运设备 / 无铭牌设备）—— 2026-05 已从 156 补到 54
- 📝 浓硫酸给料泵推进液箱：现场实际用 NUTO H46 vs 台账 Nyvac FR 200D（不同油），待用户现场确认是否改标准油号（涉及抗燃安全）
- 📝 63 台正式位号动设备尚未润滑（203 区冲洗水泵/污水搅拌/密封液给料泵/起重机为主），待师傅现场补
- ✅ 消息通知（企业微信群机器人，2026-05-06 完成）
- 📸 图片上传（设备故障照片）/ 数据看板（未做）
- 🚀 **二级库上线待办（2026-06-21 push 后）**：① Firebase Console 发布 firestore.rules（加了 secondstock/secondstockhistory 白名单，不发布则二级库读写被拒）；② 代码上线 1-2h 后跑 `清空旧备件工器具_F12脚本.js` 清空旧 4 集合；③ 真实 admin 登录测领用/入库/编辑/批量导入（预览模式测不了写操作）。**注意**：本地 `file://` 直接打开会报 `requests-from-referer-<empty>-are-blocked`（API Key referrer 限制），要用 localhost 或线上访问

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
