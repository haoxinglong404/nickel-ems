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
- `equipments` · 设备台账（**422** 台 · id = `eq_seed_XXXX` / `eq_new_XXX` / `eq_v6_XXX`）
- `workorders` · 工单（id = `wo_时间戳_随机`）
- `lubepoints` · 润滑点（**620** 个 · id = `lp_XXXX` / `lp_v6_001` / `lp_v7_001` / `lp_v8_NNN`）
- `lubehistory` · 润滑执行记录
- `spareparts` · 备件（**1861** 条 · id = `sp_XXXXX` / `sp_tbd_NNN` 协议待清点）
- `spareparthistory` · 备件出入库记录（id = `ph_时间戳_随机`）
- `tools` · **工器具台账**（251 件 · id = `tl_seed_XXXX`）—— 2026-04-23 新增模块
- `toolhistory` · 工器具出入库历史（id = `th_seed_XXXX` / `th_时间戳_随机`）
- `inspecttemplates` · **巡检模板**（**17 个** · id = `tpl_<key>`）—— 2026-04-29 新增模块
- `inspecthistory` · 巡检执行记录（id = `ih_时间戳_随机`）
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

当前版本：**v0.9**（v0.8 + 工器具模块 + 购物车 + 7 次数据迁移 + 备件/润滑分 tab + 宽屏布局）

**底部导航 6 项**：设备 / 工单 / 备件 / 工器具 / 润滑 / 我的（grid `repeat(6,1fr)`，label 9px）

**模块结构**：
- 备件模块顶部 2 tab：📦 采购 / 🎲 随机（不同 module，tab 间用 `switchModule` 切换）
- 润滑模块顶部 3 tab：🛢️ 脂润滑 / ⛽ 油润滑 / 📝 待补充油号（**按 standardOil 是否含"脂"分**）
- 工器具：常显购物车 bar 紧贴 nav 上方（**不在 .content 内，跟 .bottom-nav 同级**，仅 tools 模块显示）
  - 卡片 2 按钮：`+ 加入领用单`（消耗）/ `+ 加入借用单`（要还）
  - 顶部 3 按钮：归还（选借用人→选物品）/ 批量入库（admin only，粘贴 Excel）/ 导出
  - 历史 type：`in`/`out`/`consume`/`return`，对应**入库/借用/领用/归还**

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

**最近做的改动**（按时间倒序）：
1. **Firestore 安全规则升级 · 匿名认证 + 集合白名单**（2026-05-03 · **当天全部完成**）：测试模式 5/19 到期前一次性闭环。**代码**：index.html 加 firebase-auth.js import + `signInAnonymously()` 在应用启动自动执行 + `init()` 第一行 `await authReady` 阻塞所有 Firestore 操作直到认证成功。**规则**：`firestore.rules` 12 集合白名单（users/equipments/workorders/lubepoints/lubehistory/spareparts/spareparthistory/tools/toolhistory/inspecttemplates/inspecthistory/meta）· 全部要求 `request.auth != null` · 兜底 `match /{path=**} { allow read,write: if false; }`。**部署链路**：commits 4273333+c7a65d2 push main → GitHub Pages 自动部署（不是 CLAUDE.md 之前误写的"用户手动上传"）→ Firebase Console 启 Anonymous → Console 发布 rules（用户在 F12 验证 uid + 写一笔工单成功后才发布）。**用户指南**：`FIRESTORE_SECURITY_DEPLOY.md` 4 步部署流程 + 回滚方案。**附带修复 1**：`woBuffer` 旧 bug —— 模块作用域 `let woBuffer` 不在 window 上，工单表单内联 `oninput="woBuffer.x=this.value"` 全部静默失败 → 提交时报"请填写联系方式"。修法：`Object.defineProperty(window,'woBuffer',{get/set})` 桥接（同样的桥接套路适用任何 oninput="moduleVar.x = ..." 的旧代码）。**附带修复 2**：CLAUDE.md "🔧 直接操作云端的技巧" 段落更新——以后改云端必须走 F12 浏览器会话（自带 anonymous Firebase Auth token），Python urllib + API key 会被规则拒。**经验**：① 规则发布瞬间生效，部署前要让代码在线 1-2 小时让所有人浏览器拿到新版本（避免缓存里的旧代码被规则拒）；② 部署后立刻在已登录浏览器试一笔写入再走人；③ 若规则发布后报 PERMISSION_DENIED 立刻把规则换成 `allow if true` 回滚（30 秒）
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
- 📝 218 区 52 台 TBD 临时位号待用户分配正式位号（含 spec 字段缺失 48 条）
- 📝 156 个润滑点待补充标准油号 + 周期
- 📸 图片上传（设备故障照片）
- 📬 消息通知 / 数据看板

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
