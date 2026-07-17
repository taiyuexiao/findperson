# 首问责任平台 Demo

这是一个基于 Vue 3 + Element Plus + Vite 的前端 Demo，用来演示首问责任平台的核心交互。当前实现沿用原静态 Demo 的视觉样式，并用 Vue Router、Pinia 和 AGUI 接入层组织页面与状态。

## 快速开始

安装依赖：

```bash
npm install --cache /private/tmp/npm-cache-codex
```

启动开发服务：

```bash
npm run dev
```

然后访问终端输出的本地地址，通常是 `http://127.0.0.1:5173/` 或 `http://localhost:5173/`。

生产构建：

```bash
npm run build
```

运行浏览器冒烟验证：

```bash
npm run smoke -- http://localhost:5174/
```

冒烟脚本会用本机 Chrome headless 打开页面、发送一条问答、切换到名片库，并生成截图到 `/private/tmp/first-responsibility-smoke.png`。

## 当前能力

- 智能问答 / Agent 页面：只承接四类动作，分别是推荐合适的人、修改个人信息、为他人做评价、发布内容。
- 名片库：支持按关键词和三级部门筛选人员，并进入人员主页。
- 个人中心：支持维护个人资料、发布内容、查看操作手册。
- 内容管理：支持新增内容、查看内容详情、置顶和删除本人内容。
- 后台看板：展示人员规模、内容规模、推荐热度和活跃趋势。

## 项目结构

- `index.html`：Vite 应用入口
- `src/main.js`：Vue 应用挂载入口
- `src/App.vue`：应用外壳，页面由 Vue Router 渲染
- `src/layouts/MainLayout.vue`：业务页左侧导航、顶部用户菜单和主工作区
- `src/views/`：登录、智能问答、名片库、个人中心、人员主页、内容发布、内容详情和后台页面
- `src/stores/`：Pinia 状态，承接认证、会话、AGUI、人员、内容、评价、反馈和后台数据
- `src/services/agui/`：AGUI 事件流、mock agent 和行为上报接入层
- `src/styles/element-theme.css`：Element Plus 主题覆盖
- `assets/main.css`：沿用原 Demo 的全局视觉样式
- `assets/logo.png`：平台 Logo

## 协作说明

- 当前数据来自前端内置模拟数据和 `localStorage`。
- 问答匹配、人员推荐、资料维护、评价、内容发布和后台看板当前仍为前端模拟逻辑。
- 平台不提供“内容检索”能力；已发布内容只作为本人内容管理、人员主页展示和推荐依据沉淀。
- 后续接入真实后端或 Agent 时，可优先替换 `services/api/*` 与 `services/agui/transport.js` 的接口实现。
