# 从 0 到上手 Claude Code · 专属指南

> 📍 **这份文档专门写给项目发起人郝兴龙**。您不用懂编程，按照本文一步一步做，就能用 Claude Code 自主迭代系统。

---

## 🎯 目标

**完成本文档后，您将能够**：
1. 本地电脑有一份项目代码（`D:\nickel-ems`）
2. 用 Claude Code 直接跟 AI 说需求
3. AI 自己改代码、提交到 GitHub、自动部署
4. 您只需要**审批 + 点一下 Push**

---

## 📦 一次性准备（30 分钟）

### Step 1. 装 Git for Windows（5 分钟）

1. 访问 https://git-scm.com/download/win
2. 自动下载 64-bit Git for Windows Setup
3. 运行安装程序
4. **全部默认下一步即可**，不要改任何选项
5. 安装完打开"命令提示符"（Win 键 → 搜 cmd），输入：
   ```
   git --version
   ```
   看到版本号（比如 `git version 2.42.0`）说明装好了

### Step 2. 装 GitHub Desktop（5 分钟）

这是一个图形化管理 GitHub 的工具，比命令行直观。

1. 访问 https://desktop.github.com
2. 下载 → 安装 → 运行
3. 登录您的 GitHub 账号（`haoxinglong404`）

### Step 3. 装 Claude Code（10 分钟）

**前置条件**：您需要有 **Claude Pro、Max、Team 或 Enterprise 账号**。免费账号不能用 Claude Code。

如果还没有：
- 打开 https://claude.ai/upgrade
- 订阅 Pro（约 $20/月 USD）

**安装**：

1. 右键 Windows 开始菜单 → **终端（管理员）** 或 **PowerShell（管理员）**
2. 复制粘贴这行：
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
3. 按回车，等装完
4. **关闭终端、重新开一个**（让 PATH 生效）
5. 输入 `claude --version` 验证

**可能的问题**：

> `claude : 无法识别此命令`

原因是 PATH 没加上。解决：
1. 按 Win+R 输入 `sysdm.cpl`
2. 切到"高级"Tab → 环境变量
3. 用户变量里找 `Path`，点编辑 → 新建
4. 添加：`C:\Users\您的用户名\.local\bin`
5. 确定 → 关闭所有终端 → 重开一个 → 再试

### Step 4. 克隆项目到本地（5 分钟）

1. 打开 GitHub Desktop
2. 顶部 File → **Clone Repository**
3. URL Tab → 输入：
   ```
   https://github.com/haoxinglong404/nickel-ems
   ```
4. Local Path 选 `D:\nickel-ems`（或其他位置）
5. 点 Clone

完成后您的 `D:\nickel-ems` 目录里应该有：
- `index.html`
- `README.md`
- `CLAUDE.md`
- 其他 .md 文件

### Step 5. 配置 Git 身份（3 分钟）

命令提示符里输入：
```
git config --global user.name "haoxinglong404"
git config --global user.email "您的邮箱"
```

（这个邮箱要跟 GitHub 账号邮箱一致）

### Step 6. 测试 Claude Code（2 分钟）

1. 打开文件资源管理器进入 `D:\nickel-ems`
2. 在空白处 **右键 → 在终端中打开**（或 Shift+右键 → 在此处打开 PowerShell）
3. 输入：
   ```
   claude
   ```
4. 第一次会让您浏览器登录 Claude 账号 → 登录 → 回终端
5. 看到欢迎界面后输入：
   ```
   /help
   ```
6. 能看到帮助菜单说明一切正常 🎉

---

## 🎮 第一次真实使用（跟着做）

**场景**：您想让 Claude 给您加一个小功能作为测试。

### 1. 在项目目录打开 Claude Code

```
cd D:\nickel-ems
claude
```

### 2. 跟 AI 说需求

```
你好，请先读 CLAUDE.md 了解这个项目。然后帮我在底部导航的"我的"
页面加一行小字，显示"今天是 YYYY-MM-DD"，字很小、灰色的，
只是装饰。
```

### 3. 审查 Claude 的改动

Claude 会说"我打算改 X、Y、Z"，会让您批准。
- 可以看到具体的 diff（变化）
- 不满意可以说"不要这样，改成..."

### 4. 批准后让 Claude 推送

```
改得很好。请提交并推送到 GitHub，commit message 写
"feat: 我的页面显示今天日期"
```

Claude 会：
- `git add .`
- `git commit -m "feat: ..."`
- `git push origin main`

### 5. 等部署 + 测试

约 1-2 分钟后，打开 https://haoxinglong404.github.io/nickel-ems/

如果没看到变化，清缓存或加 `?v=20260421`。

---

## 💬 跟 Claude Code 沟通的黄金模板

### 模板 1：加新功能

```
请读 CLAUDE.md 了解项目。

需求：[具体描述]

比如：给工单列表加一个"导出 Excel"按钮，只有管理员能看到。
按钮在工单 Tab 的顶部，点击后导出当前筛选结果为 .xlsx 文件。

请先给我一个改动方案，我确认后再动手。
```

### 模板 2：修 bug

```
请读 CLAUDE.md 了解项目。

Bug：[复现步骤]

比如：登录翔总的账号（6724013003）后，欢迎卡弹出来了，
但背景没有虚化，是纯黑的。应该像我这边一样是半透明绿色。

请先诊断原因，再修。
```

### 模板 3：改 UI

```
请读 CLAUDE.md 了解项目。

UI 问题：备件详情页的"库存数量"那个数字太小了，
用户老看不清楚，希望放大到 48px，且用深绿色。

改完告诉我改了哪些 CSS 类。
```

### 模板 4：查文档

```
请读 CLAUDE.md 和 ARCHITECTURE.md。

我想知道：工单状态是怎么变化的？哪些角色能改状态？
```

---

## 🚨 危险操作警示

### ❌ 不要说的话

- "帮我重构整个项目" — 会改得面目全非
- "用 React 重写吧" — 违反不引入框架的原则
- "删掉 .git 目录" — 会丢 Git 历史
- "把 Firestore 里所有工单删了" — 数据不可恢复

### ✅ 安全的说法

- "只改 XX 函数"
- "加一个小功能"
- "修这一个 bug"
- "给我解释一下"

---

## 🆘 紧急情况处理

### 情况 1：Claude 改坏了，想回滚

在 Claude Code 终端里：
```
/revert
```

或者用 GitHub Desktop：
1. 打开 History Tab
2. 右键"未推送"的 commit
3. 选 "Revert changes in this commit"

### 情况 2：不知道 Claude 在干什么

按 `Ctrl+C` 打断它。

### 情况 3：上传后系统挂了

打开 https://github.com/haoxinglong404/nickel-ems/commits/main
找到**上一个好版本**，Browse files → 下载 index.html → 覆盖上传。

### 情况 4：Claude 回答的内容太技术听不懂

直接说：
```
请用非技术语言跟我解释，假设我是个对编程一窍不通的工厂管理员。
```

---

## 💡 提效小技巧

### 1. 用斜杠命令

在 Claude Code 里输入 `/` 会看到：
- `/help` - 帮助
- `/model` - 切换模型（Opus 复杂任务、Sonnet 日常）
- `/clear` - 清空当前对话
- `/compact` - 压缩上下文（对话变长时用）

### 2. 让 Claude 边做边说

```
请一步一步做，每改一个文件都跟我说一声。
```

### 3. 让 Claude 自我检查

```
改完后用 node --check 检查 JS 语法，确认没问题再告诉我。
```

### 4. 养成习惯：改完测试

Claude 改完代码后，**您自己打开网页测试一下**，确认功能正常再 push。

---

## 📚 进阶学习（有兴趣再看）

- [Claude Code 官方文档](https://code.claude.com/docs)
- [Firebase Firestore 入门](https://firebase.google.com/docs/firestore)
- 本项目的 `ARCHITECTURE.md` — 系统内部设计
- 本项目的 `CLAUDE.md` — AI 协作的约定

---

## 🎯 最后的话

这份文档只是起点。真正的掌握来自**您自己每天用 Claude Code**。

前几次可能磕磕绊绊，一周后您会发现：
- 💡 需求沟通更直接了（不用等我回答）
- 🚀 迭代速度更快了（分钟级，不是小时级）
- 🎨 尝试新想法的成本更低了

**这是一个从"被动使用者"到"主动掌控者"的转变。**

遇到问题随时问我（在 Claude.ai 聊天），也可以随时问 Claude Code（它知道整个项目的上下文）。

祝您玩得开心 🌿

—— 您的 AI 助手
