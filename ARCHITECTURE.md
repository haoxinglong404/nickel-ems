# 架构设计文档 · Nickel Plant EMS

> 本文件详细描述系统的内部实现。改代码前应先阅读相关章节。

---

## 📄 单文件架构

**`index.html` 是唯一入口**，所有 HTML、CSS、JS 都在这一个文件里。

```html
<!DOCTYPE html>
<html>
<head>
  <style>/* 所有 CSS */</style>
</head>
<body>
  <!-- 登录屏幕 -->
  <!-- 顶栏（多种，根据当前模块切换） -->
  <!-- 主内容区（含多个 <section class="module"> ） -->
  <!-- 底部导航 -->
  <!-- 浮动按钮、Sheet 弹层、欢迎卡等 -->
  
  <script type="module">
    // 所有 JS，包括 Firebase SDK 导入、数据层、UI 层
  </script>
</body>
</html>
```

**为什么单文件**：
1. 部署简单 —— 用户直接在 GitHub 网页上传一个文件就是部署
2. 无构建 —— 不需要 npm install、webpack 配置
3. 无依赖地狱 —— 只依赖 CDN 上的 Firebase SDK

---

## 🧩 模块切换机制（switchModule）

应用是**单页**的，通过切换 `<section class="module">` 的 `.active` class 来显示不同页面。

**当前有的 module**：

| data-module | 用途 | 触发方式 |
|---|---|---|
| `equipment` | 设备列表 | 底部导航 / 登录后默认 |
| `equipment-detail` | 设备详情 | 点击设备卡片 |
| `equipment-edit` | 编辑设备（管理员） | 详情页"编辑"按钮 |
| `workorder` | 工单列表 | 底部导航 |
| `workorder-create` | 提报工单 | FAB 浮动按钮 |
| `workorder-detail` | 工单详情 | 点击工单卡片 |
| `lube` | 润滑点列表 | 底部导航 |
| `lube-detail` | 润滑点详情 | 点击润滑点卡片 |
| `lube-execute` | 登记润滑执行 | 详情页"登记"按钮 |
| `parts` | 备件列表 | 底部导航 |
| `parts-detail` | 备件详情 | 点击备件卡片 |
| `parts-txn` | 领用/入库表单 | 详情页"领用/入库"按钮 |
| `profile` | 我的 | 底部导航 |
| `users` | 用户管理（管理员） | 我的 → 用户管理 |

**`switchModule(name)` 函数做的事**：

```javascript
function switchModule(name) {
  // 1. 切换 .module.active
  // 2. 切换顶栏（根据是否是详情/编辑页，显示返回顶栏）
  // 3. 切换底部导航高亮
  // 4. 如果是 hideMain = true 的场景，隐藏底部导航
  // 5. 触发渲染函数（renderXxx）
}
```

**加新 module 时必须**：
1. 在 HTML 里加 `<section class="module" data-module="xxx">`
2. 如果是详情/编辑页，加对应的 `<header class="detail-back" id="topbar-xxx">` 顶栏
3. 更新 `switchModule()` 里的所有相关判断
4. 如果是顶级模块，加到底部导航

---

## 🔥 Firebase 数据层

### 连接配置

```javascript
const firebaseConfig = {
  apiKey: 'AIzaSyCnRLkGLVHJDY__oO4x3hjGvuxI_4HpH-U',
  authDomain: 'nickel-ems.firebaseapp.com',
  projectId: 'nickel-ems',
  storageBucket: 'nickel-ems.firebasestorage.app',
  messagingSenderId: '996666304253',
  appId: '1:996666304253:web:e2cf6c35bf6dd60d26c094',
};
```

SDK 从 `gstatic.com` CDN 以 ES Module 方式导入：

```javascript
import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.12.0/firebase-app.js';
import {
  getFirestore, collection, doc, getDoc, getDocs,
  setDoc, deleteDoc, onSnapshot, writeBatch
} from 'https://www.gstatic.com/firebasejs/12.12.0/firebase-firestore.js';
```

### 数据流

```
用户操作
  ↓
UI 事件处理函数（如 submitWorkorder）
  ↓
cloudSaveXxx() 函数   →  setDoc(doc(db, 'collection', id), data)
  ↓
Firestore 写入成功
  ↓
onSnapshot 监听器触发（**所有在线客户端**都收到）
  ↓
更新本地 cache（如 woCache）
  ↓
如果当前页面是相关模块，调用 renderXxx() 重新渲染
```

**关键点**：
- **乐观 UI**：`submitWorkorder` 会立刻 `woCache.unshift(b)` 并切换页面，不等 Firestore 返回
- **实时订阅**：每个集合都有 `subscribeXxx()` 函数，在 `init()` 里启动
- **幂等种子**：`seedIfEmpty()` 只在云端集合为空时上传初始数据

### 集合设计详情

#### `users`
```typescript
{
  empno: string,        // 工号，等于 doc id
  name: string,
  role: 'admin' | 'reader' | 'reporter' | 'approver' | 'tech',
  password?: string,    // 明文（管理员有密码，其他无）
  createdAt: number,
}
```

#### `equipments`
```typescript
{
  id: string,           // eq_seed_0001 格式
  tag: string,          // 位号，如 201-PE-AG-001A
  name: string,
  type: string,
  area: string,         // 201 / 202 / 203 / 316-1
  status: 'running' | 'idle' | 'maintenance',
  responsible: string,
  spec: string,
  // ... 其他技术参数
}
```

#### `workorders`
```typescript
{
  id: string,
  code: string,             // WO20260419001
  status: 'pending-approval' | 'approved' | 'rejected' | 'in-progress' | 'pending-confirm' | 'done' | 'reopened',
  urgency: 'normal' | 'urgent' | 'critical',
  
  equipmentId: string,      // 'other' 表示非设备工作
  equipmentTag: string,
  equipmentName: string,
  
  issueTags: string[],
  issueDesc: string,
  
  contactName: string,      // 现场联系人（必填）
  contactPhone: string,     // 联系方式（必填，任意文本）
  
  reporterId: string,
  reporterName: string,
  reportedAt: number,       // ms timestamp
  
  approvedBy?: string,
  approvedAt?: number,
  rejectReason?: string,
  
  technicianId?: string,
  technicianName?: string,
  acceptedAt?: number,
  
  completionDesc?: string,
  completedAt?: number,
  
  closedAt?: number,
  closedBy?: string,
  
  createdAt: number,
  updatedAt: number,
  
  isImported?: boolean,     // 从 Excel 导入的标记
  subArea?: string,         // 作业子项（只有导入的工单有）
}
```

#### `lubepoints` & `lubehistory`
```typescript
// lubepoints
{
  id: string,           // lp_XXXX
  equipmentTag: string,
  partName: string,     // 部位（如"电机驱动端"）
  action: 'grease' | 'oil_change',  // 加脂 / 换油
  oilType: string,
  cycle: number,        // 周期（天）
  lastExecAt?: number,  // 上次执行时间戳
}

// lubehistory
{
  id: string,
  lubePointId: string,
  executorId: string,
  executorName: string,
  execAt: number,
  notes?: string,
}
```

#### `spareparts` & `spareparthistory`
```typescript
// spareparts
{
  id: string,           // sp_XXXXX
  name: string,
  spec: string,
  device: string,       // 装机设备描述
  quantity: number,     // 当前库存
  unit: string,
  source: 'long' | 'random',  // 长周期 / 随机备件
  materialCode?: string,
  supplier?: string,
  purchaseStatus?: string,
  purchaseNo?: string,
  location?: string,
  received?: string,
  remark?: string,
  isImport?: number,    // 是否进口
}

// spareparthistory
{
  id: string,           // ph_时间戳_随机
  sparePartId: string,
  sparePartName: string,
  type: 'in' | 'out',
  quantity: number,
  reason: string,       // 用途 or 来源
  operatorId: string,
  operatorName: string,
  createdAt: number,
  
  reverted?: boolean,   // 被撤销了吗
  revertedAt?: number,
  revertedBy?: string,
  
  isCounter?: boolean,  // 这条是不是反向记录
  revertsHistoryId?: string,  // 如果是反向记录，指向原记录
}
```

---

## 🔐 认证流程

**无正规认证** —— 因为部署在 GitHub Pages + Firestore 测试模式。

1. 用户输入工号 → `findUser(empno)` 在 Firestore 查
2. 管理员账号有 `password` 字段 → 弹窗输入密码
3. 其他账号无密码 → 直接登录
4. 登录成功 → `localStorage.setItem(SESSION_KEY, empno)`
5. 进入系统 → `getCurrentUser()` 从 localStorage 读 empno + 从 Firestore cache 读 user

---

## 🎭 各模块的实现要点

### 设备模块 (equipment)

- 分页加载（`eqPageSize`、`eqPageNum`），避免一次渲染 361 个
- 按区域 tab 筛选
- 搜索按位号/名称/专业/类型/责任人
- 详情页懒加载图片（目前无图片，保留架构）

### 工单模块 (workorder)

- **3 种 Tab**：我的待办 / 全部（管理员） / 我提报的
- `isMyTodo(wo, user)` 判断工单是否在"我的待办"（对不同角色逻辑不同）
- 状态机：
  ```
  pending-approval → approved → in-progress → pending-confirm → done
                  ↘ rejected
                  ↻ reopened（从 done 重开）
  ```
- 审批是**单签**（只要一个审批人审就行），不是并联

### 润滑模块 (lube)

- 首次启动自动导入 511 个点 + 每个点的"最后润滑时间"
- **无审批**，执行即入库
- 三卡筛选：逾期 / 即将到期 / 全部
- 逾期计算：`(now - lastExecAt) > cycle * 86400_000`

### 备件模块 (parts)

- 四卡筛选：全部 / 长周期 / 随机 / 低库存（≤ 3）
- 领用/入库会**同时**写 `spareparthistory` 和 `spareparts.quantity`（通过两次 setDoc）
- 撤销：生成反向记录 + 标记原记录 `reverted: true`
- 硬删除：直接 deleteDoc + 按规则调整库存

### 用户管理 (users)

- 只有管理员可见
- 自我保护：不能降级/删除自己
- 最后一管理员保护：如果要降级/删除最后一个 admin，拒绝
- 5 种角色选项：admin / reader / reporter / approver / tech

---

## 🎨 CSS 组织

CSS 直接内联在 `<style>` 里，按以下顺序组织：

1. **Reset + base**（重置浏览器默认）
2. **CSS 变量**（`:root` 里定义所有颜色、字体、间距）
3. **通用组件**（按钮、卡片、输入框、空状态等）
4. **布局**（顶栏、底部导航、主内容区）
5. **每个模块的专属样式**（如 `.wo-card`、`.parts-card`）
6. **动画**
7. **响应式**（`@media`）

**不要用 CSS 预处理器**（Sass/Less 都不行），保持纯 CSS。

---

## 📦 种子数据

所有初始数据都以 `SEED_XXX` 常量内联在 HTML 里：

```javascript
const SEED_EQUIPMENTS = [...];         // 361 条
const SEED_LUBE_POINTS = [...];        // 511 条
const SEED_SPARE_PARTS = [...];        // 1777 条
const SEED_IMPORTED_WORKORDERS = [...]; // 6 条
```

**幂等逻辑**：`seedIfEmpty()` 等函数只在 Firestore 对应集合为空时才写入。所以：
- 部署新版本不会重复写数据
- 清空 Firestore 后重新打开会重新 seed
- 修改种子数据不会影响已经 seed 过的数据（需要手动清 Firestore 再重 seed）

---

## 🧰 如何扩展

### 加新集合

1. 在 `ARCHITECTURE.md` 定义文档结构
2. 写 `cloudSaveXxx` 和 `subscribeXxx` 函数
3. 在 `init()` 里调用 subscribe
4. 写对应的 UI 层
5. 如果需要种子数据，写 `seedXxxIfEmpty`

### 加新角色

1. 在 `ROLES` 常量里加定义
2. 在 `MENU_BY_ROLE` 里加菜单
3. 审视权限矩阵（见 CLAUDE.md）
4. 更新用户管理界面的角色选项

### 加新模块

1. 在 HTML 里加 `<section class="module">`
2. 加底部导航条目（如果是主模块）
3. 更新 `switchModule()`
4. 写渲染函数 + 数据层

---

*本文件会随项目演化而更新。见 CHANGELOG.md 了解版本差异。*
