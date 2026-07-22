# Claude Code 项目备忘录 · Nickel Plant EMS

> **⚠️ AI 助理：每次会话开始时请完整阅读此文件，不要跳过任何"重要约定"。**
> 历史改动的完整纪要在 `HISTORY.md`（不自动加载，查某次改动细节时再读）。

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
- 认证：匿名认证（`signInAnonymously`，2026-05-03 上线）+ 工号登录 + 客户端密码校验
- 数据库：Firestore · **白名单安全规则已上线**（`firestore.rules`；改集合结构要同步 rules 并在 Console 发布，**漏 `meta` 会导致启动中断**）
- 存储：暂未使用

**Firestore 集合**（每个文档的 id 字段要和 Firestore doc id 一致）：
- `users` · 用户账号（id = 工号字符串）· 含 `wechatMobile` 字段（当前无实际用途，见"关键常量"企业微信段）
- `equipments` · 设备台账（**422** 台 · id = `eq_seed_XXXX` / `eq_new_XXX` / `eq_v6_XXX`）· `abcClass` 关键性等级（''/A/B/C，352 台已赋级 = A30/B69/C253，70 静设备未分类）· 342 台已改直观名（晨曦/海湾/N系列 前缀，命名规则见 memory project-equipment-rename-scheme）
- `maintenancelogs` · **检修记录**（id = `ml_时间戳_随机`）—— 2026-07-01 替代已删的工单模块；选二级库备件自动扣库存（联动 secondstock/secondstockhistory）
- `lubepoints` · 润滑点（**894** 个 · id = `lp_XXXX` + 历次拆点/补点系列 `lp_v6_*` ~ `lp_v21_*`，各系列来历见 HISTORY.md）
- `lubehistory` · 润滑执行记录
- `secondstock` · **二级库（现场库存台账）**（id = `ss_imp_NNN` 种子 / `ss_时间戳_随机` 新增）
- `secondstockhistory` · 二级库出入库历史（id = `ssh_时间戳_随机`）—— 带 `mlId` 字段的 = 检修记录的**账本投影**（每次保存检修记录整体重写：每备件恒一笔出库=当前用量，删记录笔就消失；**禁手动撤销/删除**）
- `inspecttemplates` · **点检模板**（**32 个** · id = `tpl_<key>`）—— 24 个 v2 结构化模板（`v:2` + `groups[{g,pts:[{p,ms:[{n,t:'num'/'chk',u,max,min,std,mth}]}]}]`，含离心泵 5 种密封变体/搅拌器 4 变体等）+ 8 个 v1 勾选模板（items 数组；静设备无"设备停机未运行"项）；每个模板带 `rev`（=`INSPECT_TPL_REV`）内容修订号，**改模板内容必须 +1 并配新迁移 marker**
- `inspecthistory` · 点检执行记录（id = `ih_时间戳_随机`）—— v2 设备只在**有异常时**写（带 `src:'v2'` 供历史 tab 去重），v1 设备每次写
- `inspectmonthly` · **月度数值点检表**（id = `im_<eqId>_<YYYYMM>`）—— 一台设备一月一文档，`days["日"]={at,by,byId,stopped,v:{测点key:数值或0/1},abn:[超限key],notes:{},note}`；**只订阅当月+上月**（where month in）→ 读取量恒定；同一天重复提交 = 覆盖当天（订正通道）
- `meta` · 一次性迁移幂等标记（id = `*_v[N]_YYYYMMDD`）
- ~~`workorders` / `spareparts` / `spareparthistory` / `tools` / `toolhistory`~~ —— **已废弃**（工器具/旧备件 2026-06-21、工单 2026-07-01 整体删除，云端已清空；rules 里 workorders 白名单暂留待删）

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
| lubepoints | `operationType` | `'oil'` / `'grease'` —— **但显示分类按 standardOil 是否含"脂"判断**，见 `getLubeKind()` |
| lubepoints | `maintenanceFree` | `true` = 免维护（`getLubeStatus()` 返回 `'exempt'`，不进逾期统计）|
| secondstockhistory | `type` | `in`（入库）/ `out`（领用）|
| secondstockhistory | `reverted` / `isCounter` | 撤销双轨标记，别用其他字段名 |
| secondstockhistory | `mlId` | 检修账本投影关联；带此字段的记录禁手动撤销/删除 |
| maintenancelogs | `category` | `fault` / `planned` / `preventive` |
| maintenancelogs | `deleted` | 软删（作废）标记；检修记录无彻底删除 |
| equipments | `abcClass` | `''` / `A` / `B` / `C` 关键性等级 |
| secondstock | `location` / `fieldLocation` | 领出库位（只读保留）/ 现场库位（列表/筛选用后者）|

（已废弃模块 workorders/spareparts/tools 等的字段约定已随模块删除失效，旧文见 git 历史。）

### ❌ 禁止用 localStorage 存业务数据

只能用来记：
- 当前会话 token（`SESSION_KEY`）
- 用户偏好（如上次联系方式自动填充）

所有业务数据必须在 Firestore。

### ❌ 禁止删除"首次启动种子数据"逻辑

`seedIfEmpty()`、`seedLubeIfEmpty()`、`seedInspectionTemplatesIfEmpty()`、`seedSecondStockIfEmpty()` 这些函数**保留不删**。它们只在云端对应集合为空时才写入，幂等安全。（`seedPreviewInspectDemo()` 仅 `?preview=1` 且云端月表空时注入内存演示数据，不写云端。）

---

## ✅ 必须遵守的命名和约定

### 位号命名规则

格式：`{区域}-{专业}-{类型}-{序号}{分支}`

示例：
- `201-PE-AG-001A` · 201 区域 · 工艺设备 · 搅拌器 · 001 · A 分支
- `316-1-MT-PP-003` · 316-1 区域 · 金属设备 · 泵 · 003

**绝对不要**生成不符合这个格式的位号。如果需要给设备加位号，先参考 Firestore `equipments` 集合里现有的格式。

### 文件改动必须满足

1. **每次修改 `index.html` 都要**：
   - **本机无 node**：语法校验用 Python 括号/引号/注释配平器 + preview 加载后查 `typeof window.fn` 全为 `function` + 控制台 0 报错
   - 修改后文件大小不能异常变化（正常约 **1.0 MB**，seed 常量占大头）
   - 验证所有 `onclick` 调用的函数都通过 `window.fn = fn` 暴露
   - 内联 `oninput="someVar.x = this.value"` 也要求 `someVar` 在 window 上（模块作用域 `let` 不行 —— 用 `Object.defineProperty(window,...)` 桥接，见 mlBuffer/ssTxnBuffer 的套路）

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

用户说："给检修记录加个导出 Excel 的按钮"。

**正确的流程**：

1. **先读 `ARCHITECTURE.md`** 了解现有模块结构
2. **用 Grep 工具**搜代码里是否已有导出相关代码（避免重复）
3. **规划改动**：哪里加按钮？用什么 JS 库？（能不加就不加 → 先看 xlsx-js-style 是否已引入）权限：谁能导出？
4. **提议方案**给用户确认（中文 + Markdown 格式，有结构、有取舍）
5. **动手改代码**，每一步精确操作、assert 成功
6. **验证**：Python 配平校验 + preview 实际加载 + 确认函数被 `window.` 暴露 + 检查 onclick 语法
7. **交付**：告诉用户"做了什么、怎么测试、已知限制"

---

## 📝 用户偏好（郝兴龙）

- **不要用英文解释**。必须中文为主，英文术语要配翻译。
- **不要让用户做技术决策**。我问"您想用方案 A 还是 B"之前，先给推荐。
- **不要给太多选项**。2-4 个最好，超过 5 个用户会困惑。
- **修改 UI 前先给视觉说明**（用 SVG/HTML 预览，而不是纯文字描述）。
- **严谨**：每次 str_replace 要 assert 成功，不能静默失败。
- **动手之前**告诉用户"我准备做 X、Y、Z"，让她确认。
- **每次代码改动 push 后**，必须更新本 CLAUDE.md 的"下次会话应该知道的上下文"段落：压缩版（1-3 行）追加到"最近做的改动"，**完整纪要追加到 `HISTORY.md` 顶部**；移除已完成的待办；有数据迁移则更新 marker 表。保证新会话能无缝接上项目。

---

## 🎭 角色矩阵（权限设计必须参考这个）

**8 角色**（2026-04-25 重构）：生产员工 / 生产班长 / 生产主任 / 检修员工 / 检修班长 / 检修主任 / 经理（manager）/ 管理员（admin）。

**现行权限**（工单模块删除后大幅简化，2026-07-08 起）：

| 功能 | admin | 其他 7 角色 |
|---|---|---|
| 查看全部模块 | ✓ | ✓ |
| 润滑登记（含一键登记全部）| ✓ | ✓ |
| 点检提交 | ✓ | ✓ |
| 检修记录 登记/编辑/作废/恢复 | ✓ | ✗（只读）|
| 二级库 领用/入库/编辑/删除/批量导入 | ✓ | ✗（只读）|
| 编辑设备 / 用户管理 / 硬删历史 | ✓ | ✗ |

权限 helper：`isAdmin` / `isManager` / `isProduction` / `isMaintenance` + `canEditMl` / `canHardDelete`。（工单时代的 `canApproveWO` / `canTakeWO` / `canVerifyWO` / `canAssignWO` / `canBatchImportTools` 仍残留在代码里，已无调用场景。）

---

## 🔑 关键常量和入口

- **管理员初始账号**：工号 `6725102247` · 密码 `15086370152hxl`
- **副管理员**（翔总）：工号 `6724013003` · 登录弹专属欢迎卡
- **VIP 配置**：搜 `VIP_WELCOMES` 常量，添加新 VIP 在这里加
- **Firebase 配置**：搜 `firebaseConfig` 常量
- **SESSION_KEY**：`nickel_ems_session`（localStorage 里的会话键）
- **企业微信群通知（当前失效 · 用户 2026-07-22 决定先留着）**：`notifyWeChat()`（index.html 约 3707 行）原 5 个调用点全在工单模块，随工单删除后**无任何调用方**——现在不会发任何群通知；"我的"页面手机号设置入口（`wechatMobile` / `confirmSetMobile`）仍在但填了无效果。Cloudflare Worker `https://ems-notify.haoxinglong404.workers.dev` · token `ems-2026-nickel-secret-x9k2` 仍部署着。若恢复 = 把 notifyWeChat 挂到检修/点检事件；若放弃 = 删函数 + 设置入口 + Worker。

---

## 🚀 下次会话应该知道的上下文

当前版本：**v0.15**（v0.14 → 润滑加「导出五定表」按钮 + SheetJS 换 xlsx-js-style 带样式分支）

**底部导航**：设备 / 点检 / 检修 / 二级库 / 润滑 / 我的（**横滑 flex**；界面文字 2026-07-21 起「巡检」全站改叫「点检」，函数名/集合名未动）
> **检修模块**（`maintenance` module，`data-nav="maintenance"`，沿用原工单骨架 list/detail/create 三页 + `mlBuffer` 桥接）：**仅 admin 可登记/编辑/作废/恢复**，其他人只读；**无彻底删除**（只可作废=软删可恢复，作废时库存自动回补）。字段 `equipmentId/Tag/Name` · `category`(fault/planned/preventive) · `repairDate` · `faultParts[]`(标签多选) · `faultCause` · `measures` · `spareParts[]`(可从二级库挑/手填，**二级库的自动扣库存·手填的不扣**) · `repairerName` · `note` · 软删 `deleted`。常量 `ML_CATEGORY_MAP` / `COMMON_FAULT_PARTS` / `ABC_CLASS_MAP`。设备详情"相关记录"tab 读 `mlCache`。列表有类别筛选 + A/B/C 等级筛选（可叠加）+ 重点设备条（给料泵/搅拌器两组，`ML_KEY_EQ_GROUPS` 包含式匹配）→ 三级页 `maintenance-keyeq` / `maintenance-eqlog`（单台档案：记录 tab + 零件更换时间线按故障部位 tags 精确归类 + 寿命对比图）。段头「📊备件消耗」汇总导出（跟随当前筛选）。⚠️ `renderMlCard(ml, from)` 有第二参，不能直接 `.map(renderMlCard)`。
> **设备 A/B/C 分级**：`abcClass` 字段，设备卡/检修记录/详情显徽章（`.abc-badge`），设备编辑页有下拉。**本地 SEED 故意不同步 abcClass**（主 SEED id 按位置生成，注入易错；生产读云端不受影响）。桌面 `设备ABC分级清单_草稿_2026-07-01.xlsx` 留档。

**模块结构**：
- 二级库（`parts` module，标题 Second Stock）：现场库存台账，**带结存的库存账**
  - 字段：`name`/`materialCode`/`sourceNo`/`unit`/`fieldLocation`(现场库位)/`location`(领出库位·只读)/`requestQty`/`inQty`/`quantity`(结存)/`usagePart`/`applicant`
  - module：`parts`(列表)/`parts-detail`(详情)/`parts-txn`(领用/入库)/`parts-edit`(新增/编辑)/`parts-history`(出入库历史·全员可看)
  - **仅 admin** 可领用/入库/编辑/删除/批量导入；其他人只读
  - 历史 type：`in`/`out`，带撤销(reverted/isCounter)+硬删双轨；带 `mlId` 的检修投影笔禁撤销/删除，显「🔧 检修」标签可跳检修详情
  - 辅助函数：`escapeAttr` / `renderInfoRow` / `ssDataSource`(预览模式云端空时回退 SEED)；`ssTxnBuffer`/`ssEditBuffer` 用 defineProperty 桥接 window
- 润滑模块顶部 3 tab：🛢️ 脂润滑 / ⛽ 油润滑 / 📝 待补充油号（**按 standardOil 是否含"脂"分**）
  - **列表按设备分组**：一台设备(同位号+同油种)=一张卡，多点位用 `renderLubeGroupCard`(含「一键登记全部」`openBulkLube`/`confirmBulkLube`：列需润滑点位，免维护自动跳过，writeBatch 各记一笔+顺延 nextLubeAt)、单点位用 `renderLubeCard`。分组 `groupLubePointsByDevice()`，徽章/筛选取最严重点位状态 `lubeGroupStatus()`。
  - **概览按设备统计**：4 个概览卡(逾期/即将/未初始/全部)=设备台数(每台归最严重状态，互斥)；列表计数「X 台设备 · Y 个点位」。
  - **免维护电机**：`maintenanceFree:true` → 'exempt'，排除统计；64 个电机已标（潜水密封电机/刮泥机行走升降/PAM·PAC 加药搅拌电机等）。液下渣浆泵电机不算免维护。
  - **电机=前/后轴承两点**：155 个需润滑电机各拆前/后轴承（`lp_v16_NNN`，前后各按原加注量）；免维护和无加注量电机不拆。
  - **打的下数**：黄油枪 1 下≈0.95g，`greasePumps(g)` 向下取整；`usesGreaseGun()` 排除联轴器/齿圈/开式齿。
  - 页头「📋 历史」→ `lube-history` 整页（全部/脂/油 tab + 自然日筛选 + 按天分组 + 导出）；「↓导出五定表」`exportLubeWudingXlsx`（内部自助格式；**正式交表走 HISTORY.md 里的填模板流程**）。

**已运行的一次性迁移**（marker 都在 `meta/` 集合。已废弃模块的 V4/V5/V9/V10 marker 文档仍在云端，但迁移函数已随模块删除，不会重跑）：
| Marker | 做的事 |
|---|---|
| `eq_seed_fix_v2_20260421` | 修 312A/B 位号冲突 + 删 201B 重复 |
| `eq_fix_v3_20260422` | 62 个位号规范化（TBD→正式 + 316-1 空格修复）|
| `eq_lube_fix_v6_20260423` | 修 10 个孤立润滑点 + 拆 002/003 设备 + 加 102B + 313B 润滑点 |
| `add_motor_lp_v7_20260423` | 202-PE-PP-005 高压水泵·电机润滑点 |
| `area_lube_v8_20260423` | 218/923/546 区 107 个新润滑点 |
| `inspect_init_v11_20260429` | 上传 17 个巡检模板（按 equipment.type 关联）|
| `inspect_tpl_v2_20260704` | 巡检模板升级 v2 数值点检结构 |

**最近做的改动**（压缩版·按时间倒序·**每条的完整细节见 `HISTORY.md`**）：
1. **徐超工具集装箱二级库 55 条整体转移 + 垫片盘盈 +1**（07-22，纯云端数据·无代码/SEED 变更）：代码有下划线的 12 条垫片/密封环 → 203-1，其余 43 条 → 202集装箱；931.321.342 垫片盘盈结存 1→2 并补一笔入库。核验后 202集装箱 44→87、203-1 101→113，原库位清空。
2. **第1周润滑计划 71 点补录 + 海湾原矿浆泵电机点补建**（07-22，实际润滑 7-20/21，何甫林执行·非注册按名字记）：扫描版计划表 78 行登记 71 笔；**计划表 001F/G/H/L = 海湾 201B-PE-PP-002A~D**（现场对 9 台原矿浆泵连续编号），补建海湾电机前/后轴承 `lp_v21_001~008`，lubepoints → **894**；油嘴丢失 2 处/疑似漏扫 4 行/103A"无加油孔"/下轴承 230g vs 342g 等遗留见待办。
3. **界面「巡检」全站改名「点检」**（07-21，领导要求，已上线）：15 处显示文字；函数名/`inspect*` 集合名/字段名/注释未动，纯显示改动。
4. **201 给料槽搅拌 B/C 机架轴承登记**（07-16）：晨曦-B/C 上轴承≈4950g/下≈2970g，SHC 220，下次 12-23；至此 6 台给料槽搅拌机架轴承全打完。**「一管」口径修订为 ≈550cc≈495g**（旧账不追改）。
5. **218 回用/罗茨/反洗 9 台 27 点首次润滑补录**（07-16，实际 7-15，张承钢）：轴承室 9 + 电机前/后 18；SEED 旧状态顺手修正；反洗泵轴承室加注量未记录=标准量待定。
6. **褐铁矿浓密机 3 台补建主电机润滑点**（07-16）：`lp_v20_001~006` 前/后轴承 51g/90天 + 当日实际打脂登记。lubepoints → **886**。
7. **一批润滑点定标/结构修正**（07-16）：PAC 减速机 300g、PAM 200g（2#锂基脂/60天）；絮凝剂搅拌 12 台机架轴承 30g/80天；罗茨风机轴承室 VG220 20L；回用水泵 3#脂 50g/30天；11 个免维护潜水电机移出待补；**PAC/PAM 机架轴承 5 点现场核实无此结构已删**；液下渣浆泵拆上/下轴承（`lp_v19`）。待补油号 54→10。
8. **高压釜给料泵 6 台补建 ABB 电机润滑点**（07-16）：`lp_v18_001~012`，驱动端 90g/非驱动端 75g/80天；**非驱动端是绝缘轴承 6322/C3 VL0241，换轴承必须买绝缘型号**；出厂脂 UNIREX N2，等效使用油定为**壳牌 Gadus S5 V100 2（需采购）**。同日纯云端对账修正 43 条润滑记录 + 高预 18 台初次加油 A/B 归位。
9. **15 台 warman 轴承箱换油号**（07-14）：中预 6 + 高预 9 统一 Shell Omala 150（使用油号 Mobil Gear EP150）；**高预从 46# 液压油跨度换 150# 齿轮油，现场换油要放净**。同日纠错高预 warman/五二五 规格整组对调：warman 改回 1.7L/80天、五二五改回 20L/330天（NUTO H46）。
10. **设备名直观化改名三批完成 342/422 台**（07-09~10）：201 区 20 台（晨曦/海湾前缀）、202 区 44 台、203 区 278 台（N系列前缀；预热器给料泵改分级泵写法）；lubehistory/inspectmonthly 等历史快照一并刷新；`ML_KEY_EQ_GROUPS` 两处改包含式；VE-103A/CM-201 两台用户留不改。
11. **删 SEED_NEW_EQUIPMENTS_V2 灾备隐患**（07-09）：无 marker 判重、极端场景会重灌 2026-04 旧占位数据，整块删除。
12. **五定表正式交表流程定型**（07-09）：**不做替代表，直接往设备室模板副本灌系统数据**——跑 repo 根 `填五定表_模板填充脚本.py`（gitignore）；周期列填纯数字=天、日期写真 datetime、模板公式/保护全不动。**以后每次交表重跑此流程**（细节/openpyxl 坑见 HISTORY.md）。
13. **润滑页「导出五定表」按钮**（07-09）：`exportLubeWudingXlsx` 复刻模板结构 0 公式（内部自助/备用格式）；SheetJS CDN 换 **xlsx-js-style@1.2.0**（loadXlsxLib 先加载 cpexcel.js 兜底旧 .xls 中文）；Fuchs Renolit 21 点补「（锂基脂）」后缀归位脂 tab。
14. **检修联动账本"重写投影"式 + 闭环收死**（07-08）：每次保存/作废/恢复检修记录 → 删该 mlId 全部旧账本笔 → 按当前 spareParts 重开出库笔（每备件恒一笔=当前用量，删记录笔消失+库存回补）；检修记录无彻底删除；带 mlId 账本笔禁手动撤销/删除（唯一修改入口=改检修记录本身）。
15. **检修选二级库备件自动扣库存 + 检修权限收紧仅 admin**（07-08）：台账差额法 + writeBatch 原子写 + 结存不足拦截；手填备件不扣库存。
16. **二级库出入库历史页 + 润滑历史页**（07-08）：`parts-history` / `lube-history` module，全员可见，类型 tab + 自然日筛选 + 按天分组 + 导出；详情页 from 参数原路返回。
17. **点检到期改自然日 + 早 6 点**（07-07）：`calcNextInspectAt` = 上次点检日历日 + N 天的 06:00；`formatRelTime` 同步按自然日算。
18. **静设备移出点检 + 趋势页勾选测点 + 等级筛选**（07-06）：点检范围 318 台（A30/B69/C219）；趋势页 chk 测点显每日点条；列表加 A/B/C 筛选；历史/异常卡可点进趋势；检修重点设备条/零件时间线同日上线。
19. **点检模板按现场实况精修**（07-05）：离心泵 5 密封变体/搅拌器 4 变体等；34 台不做点检；`INSPECT_TPL_REV` 修订号机制；**迁移函数加 localhost 一律不跑守卫**（生产模板误升级事故当晚已回滚闭环）。
20. **点检升级数值点检 v2**（07-04）：v2 模板 + `inspectmonthly` 月表 + 频率按等级 A=1/B=2/C=7 天 + 超限标红强制备注 + 趋势页 + 导出；已上线真实使用。顺手补 `inspectExecBuffer` / `lubeExecBuffer` 的 window 桥接。
21. **21 台高压釜搅拌减速机油号更正 PAO**（07-03）：ISO VG 320 PAO / Mobil SHC Gear 320；**PAO 与矿物油不混用，换油放净**；加注量（台账 150/130L vs 铭牌≈119L）待定夺。
22. **修 6 条阀门油压站电机轴承 oil→grease**（07-02）；**补回删工单时误删的 `formatFullTime` / `formatShortTime`**（教训：大块删模块前对通用小工具函数先 grep 全部调用方）。
23. **检修列表 A/B/C 筛选 + 备件消耗汇总导出**（07-01）：`mlClassFilter` 可与类别叠加；`openMlPartsSummary` 按 name+unit 合计导出给采购。
24. **删工单模块 → 建检修记录模块 + 设备 ABC 分级**（07-01）：工单 3 section + ~20 函数 + 种子整删，云端集合已清空；检修模块复用骨架（现行设计见上方导航注记）；`abcClass` 352 台写云端。
25. **更早改动**（2026-04 ~ 06：润滑分组/免维护/电机拆点/加注量审核/二级库建立/删工器具旧备件/油号统一/铭牌补齐 104 台/安全规则上线/巡检 v11/角色重构/企业微信集成等 48 条）：**完整纪要全部在 `HISTORY.md`**。

**🔧 直接操作云端的技巧**：
- **首选：预览会话直接写云端** —— admin 登录 `?preview=1`（localhost）后浏览器已带匿名 auth token，可在该会话里 `import` firebase 模块直接 getDocs/updateDoc/writeBatch 批量读写云端（近期大批数据修正都走这条路）。改完硬刷清缓存再验证。注意：预览只覆盖 SEED_EQUIPMENTS 显示，**润滑点等读云端**。
- 备选：给用户 F12 脚本在线上 EMS 控制台跑（脚本要 idempotent + 防呆确认 + 分批 400）。
- ~~Python urllib + API key~~ 不可用（规则要求 auth token）。
- 数据流程：改云端 → 回读核验 → 同步本地 SEED → commit + push。

**已知待办**：
- 📝 **第1周润滑计划遗留（07-22，问何甫林）**：①晨曦C电机后轴承（lp_v16_006）+ 海湾C电机前轴承（lp_v21_005）**油嘴丢失**待补油嘴后补打补登；②304A电机后/304B电机前/絮凝剂203A电机后/203B前后 5 点计划表缺行，是漏扫还是没打待核；③絮凝剂103A"无加油孔免维护"待现场核实（同型号103B有加油孔，未标 maintenanceFree）；④低预给料槽搅拌机架下轴承标准量 230g vs 计划表 342g（实际350~355g）待核定
- 📝 数值点检暂缓设备视推行情况补做：潜水泵 9（要设计水下泵简化表）、成套设备 4、给料器 1
- 📝 218 区 54 台 TBD 临时位号待用户分配正式位号（含 spec 字段缺失 14 条）
- 📝 10 个润滑点待补油号（218 悬挂起重机 4 + 546 未装机雨水回用泵 6）；另反洗泵 3 点轴承室**加注量待定**（standardAmount=null）
- 📝 罗茨风机说明书要求「皮带端/驱动端黄油杯 360h 补 2#脂」——现场是否确有黄油杯部位待核实，有则另建润滑点
- 📝 `getLubeStatus`「即将」阈值固定 30 天 → 周期 30 天的点刚润滑完立即显示"即将·剩29天"，要不要按周期比例改待用户定夺
- 📝 浓硫酸给料泵推进液箱：现场实际用 NUTO H46 vs 台账 Nyvac FR 200D（涉及抗燃安全），待现场确认是否改标准油号
- 📝 63 台正式位号动设备尚未润滑（203 区冲洗水泵/污水搅拌/密封液给料泵/起重机为主），待师傅现场补
- 📝 企业微信通知失效（notifyWeChat 无调用方，详见"关键常量"段）——用户决定**先留着**，恢复或删除待定
- 📝 firestore.rules 里 workorders 白名单待删（下次动 rules 时顺手）
- 📸 图片上传（设备故障照片）/ 数据看板（未做）

---

## 🧪 测试建议

本项目没有单元测试框架（故意为之 —— 用户是非技术人员，不需要维护测试）。

AI 助理在修改代码时的**最低质量标准**：

1. **语法正确**：本机无 node，用 Python 括号/引号/注释配平校验 + preview 实际加载验证（控制台 0 报错、`typeof window.fn` 全 `function`）
2. **函数暴露**：所有 `onclick="fn()"` 的 `fn` 都在 `window.fn = fn` 里
3. **元素齐全**：`getElementById('xxx')` 调用的 `xxx` 都在 HTML 里存在
4. **module 协同**：新 module 在 `switchModule()` 的所有分支里都处理到了
5. **字段一致**：Firestore 写入的字段名与读取的字段名一致

每次交付前必须跑一遍这 5 条。

---

## 🛡 安全规则（现状）

**已上线（2026-05-03）**：匿名认证 + 集合白名单 + 兜底 `match /{path=**} { allow read,write: if false; }`，全部集合要求 `request.auth != null`。规则文件 `firestore.rules`。**加新集合必须同步 rules 并在 Console 发布；重发 rules 必须含 `meta`**（漏了会导致启动读迁移标记被拒、init 中断）。

**尚未实施（将来可加强）**：`users` 仅 admin 可写、按角色细分写权限、硬删除审计字段（`deletedBy`/`deletedAt`）。目前任何匿名认证的客户端都能写白名单集合——客户端权限判断只是 UI 层拦截，不是服务端强制。

---

*本文件刻意保持紧凑（目标 ≤35KB）：只放"下次会话要用的活知识"；历史纪要放 `HISTORY.md`；改完记得两边都更新。*
