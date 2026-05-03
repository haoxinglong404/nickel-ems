# Firestore 安全规则升级 · 部署指南

> 创建：2026-05-03 · 必须在 **2026-05-19 测试规则到期前** 完成全部步骤

---

## 📋 总览

把 Firestore 从"测试模式（任何人可读写）"切换到"必须 Firebase Auth 才能读写"。

总共要做 **3 件事**，建议按顺序：

| # | 在哪做 | 大概耗时 | 是否可逆 |
|---|---|---|---|
| 1 | Firebase Console · 启用匿名认证 | 1 分钟 | ✅ 可逆 |
| 2 | GitHub Pages · 部署新 index.html（已加匿名登录代码） | 5 分钟 | ✅ 可逆 |
| 3 | Firebase Console · 部署 firestore.rules | 2 分钟 | ✅ 可逆 |

**强烈建议顺序**：1 → 2 → 3。如果 3 先做、2 没做，所有用户会瞬间断连。

---

## 步骤 1️⃣：启用匿名认证

1. 打开 https://console.firebase.google.com/project/nickel-ems
2. 左侧菜单 **Build → Authentication**
3. 第一次进可能要点 **Get started**
4. 切到 **Sign-in method** 标签页
5. 找到 **Anonymous**，点击右侧编辑图标 ✏️
6. 把 **Enable** 开关打开 → **Save**

✅ 完成标志：列表里 Anonymous 状态显示为 **Enabled**。

---

## 步骤 2️⃣：部署新 index.html

代码已改好（匿名登录在应用启动自动执行）。

**改动概览**：
- 加了 firebase-auth.js 的 import
- 加了 `signInAnonymously()` 调用
- `init()` 第一行 await `authReady`，确保所有 Firestore 操作在认证后才发起

**部署**：
1. 把当前分支的 `index.html` 上传到 GitHub Pages 仓库（您的常规流程）
2. 等 1 分钟让 GitHub Pages 刷新
3. 打开 EMS 网址，按 F5 强刷
4. 打开 F12 控制台，应该看到 `[Auth] 匿名登录成功 uid=xxx`
5. 正常登录工号、操作设备/工单/备件，确认一切正常

⚠️ **此时规则仍是测试模式**，所以即使匿名认证没启用，应用也能用——但 F12 会有红色 auth 错误。看到错误就回到步骤 1 检查。

---

## 步骤 3️⃣：部署新 Firestore 规则

⚠️ **必须确认步骤 1+2 都已完成且应用正常**，再做这一步。

1. 打开 https://console.firebase.google.com/project/nickel-ems/firestore/rules
2. 你会看到当前的测试模式规则（类似 `allow read, write: if request.time < timestamp.date(2026, 5, 19);`）
3. **全选删除**，粘贴新规则（内容见下方 ⬇️ 或 worktree 里的 `firestore.rules` 文件）
4. 点 **发布 Publish**
5. 立刻打开 EMS 应用 F5 强刷，做以下验证：
   - ✅ 登录成功
   - ✅ 设备列表能看到
   - ✅ 提交一个测试工单
   - ✅ F12 控制台无 `PERMISSION_DENIED` 报错

如果发现报错：回到 Console 把规则改回 `allow read, write: if true;` 临时放开，然后联系我排查。

---

## 步骤 4️⃣（可选 · 推荐）：API Key Referrer 锁定

现在 API Key 公开在 GitHub Pages 上，任何拿到 URL 的人都能用它构造请求。锁定 Referrer 后，只有从你的 GitHub Pages 域名打开的页面才能用这个 Key。

1. 打开 https://console.cloud.google.com/apis/credentials?project=nickel-ems
2. 找到名为 **Browser key (auto created by Firebase)** 的那一项
3. 点进去
4. **Application restrictions** 选 **HTTP referrers (websites)**
5. 在 **Website restrictions** 加：
   ```
   https://你的GitHub用户名.github.io/*
   https://你的GitHub用户名.github.io/仓库名/*
   ```
   （把"你的 GitHub 用户名"和"仓库名"换成实际值）
6. **Save**

⚠️ Referrer 锁定 5-10 分钟才生效。生效后，本地 `preview.bat` 也无法访问 Firebase。如需本地预览，临时移除限制或加 `http://localhost:8000/*`。

---

## 🔄 回滚预案

如果部署后出现问题，按这个顺序排查：

1. **F12 看到 `auth/...` 错误** → 步骤 1 没做，去 Console 启 Anonymous
2. **F12 看到 `PERMISSION_DENIED`** → 规则有 bug，临时改回测试模式：
   ```
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /{document=**} {
         allow read, write: if true;
       }
     }
   }
   ```
3. **应用空白卡死** → 步骤 2 部署的代码有问题，把 GitHub Pages 上的 index.html 回滚到上个 commit

---

## 📅 部署后维护

- 每次新增 Firestore 集合，要在 `firestore.rules` 加对应 match 块（否则规则白名单会拒绝）
- 如果将来要按角色细化权限（admin only、reporter only 等），需要先迁移到 Email/Password Auth（方案 2，本次未采用）
