# 首问责任平台

首问责任平台是面向组织内部协作场景的首问责任人推荐与业务协同平台。本仓库是项目的阶段性交付版本：已完成可运行的前端应用、核心业务流程和 AGUI 接入层，后端服务、真实 Agent 和持久化数据仍在后续建设范围内。

项目基于 Vue 3、Element Plus 和 Vite 构建，使用 Vue Router 管理页面路由、Pinia 管理业务状态，并预留了面向 AGUI 事件流的对接能力。

## 快速开始

安装依赖：

```bash
npm install
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

## 已完成能力

- 账户与工作台：提供登录入口、主导航、用户菜单及修改密码交互。
- 智能问答 / Agent：支持推荐合适的人、修改个人信息、为他人做评价、发布内容四类业务动作，并提供会话历史、推荐卡片和详情侧栏。
- 人员名片库：支持按关键词和三级部门筛选人员，查看人员主页、职责画像、他人评价和发布内容。
- 个人中心与内容管理：支持维护个人资料、发布内容、查看内容详情、置顶和删除本人内容。
- 后台看板：展示人员规模、内容规模、推荐热度和活跃趋势。
- 前端接入层：封装了 API 服务、模拟数据、AGUI 事件流转换和行为上报接口，便于后续替换真实服务。

## 项目结构

- `index.html`：Vite 应用入口
- `src/main.js`：Vue 应用挂载入口
- `src/App.vue`：应用外壳，页面由 Vue Router 渲染
- `src/layouts/MainLayout.vue`：业务页左侧导航、顶部用户菜单和主工作区
- `src/views/`：登录、智能问答、名片库、个人中心、人员主页、内容发布、内容详情和后台页面
- `src/stores/`：Pinia 状态，承接认证、会话、AGUI、人员、内容、评价、反馈和后台数据
- `src/services/agui/`：AGUI 事件流、mock agent 和行为上报接入层
- `src/styles/element-theme.css`：Element Plus 主题覆盖
- `assets/main.css`：全局视觉样式
- `assets/logo.png`：平台 Logo

## 当前边界与后续工作

- 当前数据由前端内置模拟数据和 `localStorage` 驱动，适用于界面联调、流程验证和需求演示。
- 认证、人员、内容、评价、会话和后台统计尚未连接真实后端服务。
- 问答匹配与人员推荐当前使用模拟 Agent 逻辑；接入真实 Agent 后，可替换 `src/services/agui/transport.js`。
- 后端接口接入可从 `src/services/api/` 开始替换；页面与状态层保持现有调用契约即可。
- 平台当前不提供独立的内容检索能力，已发布内容用于个人内容管理、人员主页展示和推荐依据沉淀。
