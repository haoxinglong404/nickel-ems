# 部署指南 · Nickel Plant EMS

本文描述如何部署新版本到生产环境（GitHub Pages）。

---

## 🎯 部署架构

```
本地 index.html
  ↓ git push
GitHub 仓库 (haoxinglong404/nickel-ems)
  ↓ GitHub Pages 自动构建（约 1-2 分钟）
生产环境 URL: https://haoxinglong404.github.io/nickel-ems/
```

**没有构建步骤、没有 CI/CD**。Push 就是部署。

---

## 🚀 日常部署流程（用 Claude Code）

### 前提
- 本地已 clone 仓库到 `D:\nickel-ems`（或其他路径）
- `git` 已配置好（知道 GitHub 账号）
- 已安装 Claude Code

### 标准流程

```bash
# 进入项目目录
cd D:\nickel-ems

# 启动 Claude Code
claude

# 跟 AI 说需求，比如：
> 给工单列表加个"仅显示我的"筛选按钮

# AI 会：
# 1. 读 CLAUDE.md 理解项目
# 2. 读 index.html 相关代码
# 3. 修改代码
# 4. 用 node --check 验证语法
# 5. 告诉您改了什么

# 审查 Claude 的改动
> 解释你的改动

# 如果满意，让 Claude 提交
> 提交并推送

# Claude 会：
# - git add index.html
# - git commit -m "feat: 加 '仅我的' 工单筛选"
# - git push origin main

# 等 1-2 分钟，GitHub Pages 会自动部署
# 清缓存打开网页验证
```

---

## 📋 手动部署流程（不用 Claude Code）

如果没有 Claude Code，还是按老方法：

### Step 1. 获取新版 index.html

从本次对话下载，或者自己改。

### Step 2. 改名

确保文件名**一定是** `index.html`（不是 `ems-v0.8.html` 之类）。

**Windows 注意**：
- 默认隐藏扩展名，改完可能变成 `index.html.html`
- 解决办法：文件资源管理器 → 查看 → 勾选"文件扩展名"

### Step 3. 上传 GitHub

**方法 A · 网页上传**：
1. 打开 https://github.com/haoxinglong404/nickel-ems
2. 点 **Add file → Upload files**
3. 拖入 `index.html`（会覆盖旧的）
4. 下面写 Commit message（可选，比如 `update to v0.8.1`）
5. 点 **Commit changes**

**方法 B · GitHub Desktop**：
1. 把新 `index.html` 复制进本地仓库目录（覆盖）
2. 打开 GitHub Desktop，会看到 index.html 有改动
3. 下面写 Summary → Commit to main
4. 右上角 Push origin

### Step 4. 等部署

GitHub Pages 通常 1-2 分钟内完成。可在仓库的 **Actions** Tab 看到 "pages build and deployment" 变绿。

### Step 5. 清缓存访问

**手机端**：
- 完全关闭浏览器 App（后台也要关），重开
- 或地址栏加 `?v=20260419a` 强制新版
- 或无痕模式打开

**电脑端**：
- `Ctrl + Shift + R` 强制刷新
- 或 `Ctrl + F5`

---

## 🔍 验证部署成功

1. 打开网页，查看**底部"我的" → 关于本系统 → 版本号**
2. 应该显示预期的版本（比如 `v0.8 · Spare Parts`）
3. 测试刚加的新功能

---

## 🆘 部署问题排查

### 问题：上传后网页还是旧版

**可能原因 1：缓存**
- 解决：清缓存、无痕模式、加 `?v=xxx` 参数

**可能原因 2：上传的是旧文件**
- 解决：打开 GitHub 仓库，点 index.html，在文件内容里 Ctrl+F 搜版本号

**可能原因 3：改名失败（变成 index.html.html）**
- 解决：删除错误文件，重新改名上传

**可能原因 4：GitHub Pages 还在构建**
- 解决：等 1-2 分钟，看仓库 Actions Tab

### 问题：打开白屏

**可能原因**：JS 语法错误导致脚本崩溃

- 解决：F12 打开浏览器控制台看红色错误
- 如果是 Claude Code 改的：跟它说"部署后白屏，控制台错误是 XXX，修一下"

### 问题：数据没了

**几乎不可能**——数据在 Firebase 云端，不是本地。但如果真的没了：

1. 打开 Firebase 控制台 → Firestore
2. 检查各 collection 是否有数据
3. 如果云端是空的，重新打开网页，`seedIfEmpty` 会重新导入

### 问题：首次启动卡在"同步中"

**原因**：首次启动要上传约 3150 条种子数据（420 设备 + 620 润滑点 + 1861 备件 + 251 工器具）

- 解决：**耐心等 1-2 分钟**，不要刷新
- 网速差的话可能更久

---

## 🔐 关键时刻：Firestore 规则升级

**重要**：约 **2026-05-19**（当前从上次设置过去 30 天），Firestore 测试模式规则会到期，届时**所有读写都会被拒绝**，系统直接瘫痪。

### 必须做的升级

打开 [Firebase 控制台 → Firestore → 规则](https://console.firebase.google.com/project/nickel-ems/firestore/rules)，替换为：

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    
    // 所有集合默认要求登录（客户端状态下我们没做真正的登录，但保留防御）
    // 实际上，因为我们没用 Firebase Auth，需要让所有读写开放但加速率限制
    
    match /users/{userId} {
      allow read: if true;      // 登录时要查用户
      allow write: if true;     // 暂时开放（生产应改成 admin only）
    }
    
    match /equipments/{eqId} {
      allow read: if true;
      allow write: if true;
    }
    
    match /workorders/{woId} {
      allow read: if true;
      allow write: if true;
    }
    
    match /lubepoints/{lpId} {
      allow read: if true;
      allow write: if true;
    }
    
    match /lubehistory/{lhId} {
      allow read: if true;
      allow write: if true;
    }
    
    match /spareparts/{spId} {
      allow read: if true;
      allow write: if true;
    }
    
    match /spareparthistory/{phId} {
      allow read: if true;
      allow write: if true;
    }
  }
}
```

**⚠️ 注意**：这份规则是**仅供测试**的"伪生产规则"（实际上仍然开放）。真正的生产规则需要：
1. 接入 Firebase Authentication
2. 改成"登录 + 角色验证"模式
3. 在代码里调用 `signInWithCustomToken` 或 `signInAnonymously`

**建议在 v1.0 做正式安全升级**。

---

## 📦 回滚（Rollback）

如果新版本出问题，需要快速回滚到旧版：

### 方法 A · Git 回滚（推荐）

```bash
cd D:\nickel-ems
git log --oneline          # 看历史
git revert <commit-hash>    # 回滚某次提交
git push origin main
```

### 方法 B · GitHub 网页

1. 打开仓库 → Commits
2. 找到想回滚的版本
3. 点 Browse files → Download ZIP
4. 解压取出 `index.html` → 重新 Upload 覆盖

### 方法 C · 直接上传旧版

本地电脑里如果存了 v0.7 的 index.html，直接上传覆盖即可。

---

## 🌐 域名和托管

- **托管商**：GitHub Pages（免费）
- **限额**：每月 100 GB 带宽、软限制 1 GB 仓库大小
- **当前仓库**：`index.html` 约 1.1 MB（远低于限制）
- **自定义域名**：暂无，用 `haoxinglong404.github.io/nickel-ems/`

**升级自定义域名**（未来考虑）：
1. 买个域名（比如 `ems.mycompany.com`）
2. DNS 里加 CNAME 指向 `haoxinglong404.github.io`
3. 仓库 Settings → Pages → Custom domain 填域名
4. 等 10-30 分钟生效

---

## 📊 Firebase 配额监控

免费额度：
- **存储**：1 GB 总容量
- **读取**：50,000 次/天
- **写入**：20,000 次/天
- **流量**：10 GB/月

**实际用量预估**（5 人团队）：
- 每天读取：~2,000 次（远低于 50K）
- 每天写入：~200 次（远低于 20K）
- 存储：~10 MB（远低于 1 GB）

**结论**：免费额度至少能用 3-5 年。如果要升级 Blaze（按量付费）方案，预算也就 1 美金/月。

监控方法：[Firebase 控制台 → 用量和账单](https://console.firebase.google.com/project/nickel-ems/usage)

---

*本文件会随基础设施演化更新。如有变更需求，跟 Claude Code 说"更新 DEPLOY.md"即可。*
