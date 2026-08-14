# 首问责任平台 — 后端 API

> 分支：`backend` | FastAPI + PostgreSQL 17 + pgvector | 2026-08-14

后端服务 + 数据库迁移 + 与 Agent / RAG 的对接收口。当前**前端直连 Agent**，后端 `/api/agui/*` 退化为「Agent 未接入时的降级兜底」。

---

## 快速开始

```bash
# 1. 环境变量
cp .env.example .env
# 编辑 .env，填入实际数据库密码和 JWT 密钥

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动数据库（PostgreSQL 17 + pgvector）
docker compose up -d

# 4. 数据库迁移（alembic：baseline → P3 → P5 → agent 兼容视图）
alembic upgrade head

# 5. 种子数据
cat scripts/seed.sql | docker exec -i swzr-pg psql -U swzr_admin -d shouwenzeren

# 6. 启动后端
uvicorn app.main:app --port 8000
```

启动后访问：
- **Swagger 文档**：`http://localhost:8000/docs`
- **ReDoc**：`http://localhost:8000/redoc`
- **健康检查**：`http://localhost:8000/health`

测试账号：`p0001` ~ `p0300`，密码统一 `swzr2026`。管理员：`p0001`（`system_role=管理员`）。

---

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口，注册路由 + CORS + 中间件 + lifespan(定时任务)
│   ├── api/
│   │   ├── v1/              # 业务路由层（/api/v1）
│   │   │   ├── auth.py      # 登录 / 注册 / 改密
│   │   │   ├── me.py        # 当前用户 / 更新资料 / 改密（PUT /me/password）
│   │   │   ├── people.py    # 人员名片 CRUD
│   │   │   ├── contents.py  # 内容 CRUD + 提交审核 + 审核 + 置顶
│   │   │   ├── reviews.py   # 他画像（标签）
│   │   │   ├── admin.py     # 管理看板 / 统计 / 审计日志
│   │   │   ├── departments.py # 部门
│   │   │   └── sessions.py  # 会话 CRUD + 消息列表
│   │   └── agui/            # AGUI 收口路由层（/api/agui）
│   │       ├── sessions.py  # 建会话 / 会话状态快照
│   │       ├── messages.py  # SSE 流式问答（Agent 未接入时降级）
│   │       ├── events.py    # 反馈 / 交互事件上报
│   │       └── schemas.py   # AGUI 请求体
│   ├── models/              # SQLAlchemy ORM
│   │   ├── user.py          # 用户
│   │   ├── department.py    # 部门
│   │   ├── content.py       # 内容（含 audit_trail jsonb）
│   │   ├── review.py        # 标签（PeerReview）
│   │   ├── session.py       # 会话 / 消息 / 查询日志（QueryLog）
│   │   ├── assistant.py     # 推荐日志 / 反馈（recommendation_logs / feedback）
│   │   └── admin.py         # 统计口径 / 统计结果 / 审计日志
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── core/                # 配置 / 数据库 / 安全
│   │   ├── config.py        # 环境变量（含 AGENT_BASE_URL）
│   │   ├── scheduler.py     # lifespan 定时刷新统计（每小时）
│   │   └── statistics.py    # 统计口径刷新（SELECT-only formula）
│   ├── middleware/          # 中间件
│   │   ├── auth.py          # JWT 鉴权 → request.state.user_id / user_role
│   │   ├── audit.py         # 操作审计落库（audit_logs）
│   │   └── deps.py          # get_current_user / require_admin / get_role_type
│   └── services/
│       ├── agent_client.py  # Agent 对接契约（当前前端直连，后端仅兜底）
│       └── publish_event.py # 内容发布/变更事件 → rag.publish_events
├── tests/                   # pytest（42 用例）
├── requirements.txt
└── .env.example

alembic/                      # 数据库迁移（baseline → P3 → P5 → agent 兼容）
├── versions/
│   ├── 64c9fe23ca1b_initial_baseline.py
│   ├── c1d2e3f4a5b6_p3_admin_tables.py
│   ├── f1a2b3c4d5e6_p5_publish_events.py
│   └── a7b3c9d1e2f4_agent_compat_views.py
schema.sql                   # 全量 DDL 参考
docker-compose.yml           # PostgreSQL 17 + pgvector（swzr-pg）
scripts/                     # 种子数据生成 / seed.sql
```

---

## API 端点清单

> 前缀：`/api/v1`（业务）、`/api/agui`（问答收口） | Swagger `http://localhost:8000/docs` 有完整请求/响应示例

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录，返回 `{ token, user }` |
| POST | `/auth/register` | 管理员创建用户 |
| POST | `/auth/change-password` | 修改密码（旧版） |
| PUT | `/me/password` | 修改自己的密码（验旧改新，前端当前使用） |

### 当前用户

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/me` | 当前用户信息 |
| PUT | `/me/profile` | 更新个人资料 |

### 人员

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/people` | 人员列表（keyword / department_id / domain 筛选） |
| GET | `/people/{id}` | 人员详情 |
| PATCH | `/people/{id}` | 更新人员信息 |
| GET | `/people/{id}/reviews` | 某人标签历史（分页） |

### 内容

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/contents` | 内容列表（status / owner_id / pinned 筛选） |
| POST | `/contents` | 创建内容（status 可选，"待审核" 直接进审核队列） |
| GET | `/contents/{id}` | 内容详情 |
| PUT/PATCH | `/contents/{id}` | 编辑内容（仅作者 / 管理员） |
| DELETE | `/contents/{id}` | 软删除（仅作者 / 管理员） |
| POST | `/contents/{id}/submit` | 提交审核（**仅作者**） |
| POST | `/contents/{id}/audit` | 审核通过/驳回（**仅管理员**） |
| POST | `/contents/{id}/pin` | 切换置顶（**仅管理员**） |

### 他画像

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/reviews` | 打标签 |
| GET | `/reviews/sent` | 我发出的标签 |
| DELETE | `/reviews/{id}` | 删除标签 |
| GET | `/reviews/person/{id}` | 某人标签汇总 |
| GET | `/reviews/person/{id}/history` | 某人标签历史（分页） |

### 管理看板（仅管理员）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/dashboard` | 看板概览 |
| GET | `/admin/metrics` | 核心指标（人数、内容数、领域数、本周推荐） |
| GET | `/admin/rankings/recommend` | 推荐热度 TOP10 |
| GET | `/admin/trends/activity` | 近 7 天活动趋势（`?week=current\|previous`） |
| GET | `/admin/statistics` | 统计指标列表 |
| GET | `/admin/statistics/data` | 统计结果快照（定时刷新写入 `statistics_data`） |
| GET | `/admin/statistics/{key}` | 统计指标实时值 |
| GET | `/admin/audit-logs` | 操作审计日志（分页） |

### 部门

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/departments/tree` | 部门树（含成员数） |
| GET | `/departments/{id}` | 部门详情 |
| PATCH | `/departments/{id}` | 更新部门 |
| POST | `/departments` | 创建部门 |

### 会话

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sessions` | 我的会话列表 |
| POST | `/sessions` | 新建会话（接受前端自带 `id`，幂等） |
| PATCH | `/sessions/{id}` | 更新会话（重命名 / 摘要 / 轮次） |
| DELETE | `/sessions/{id}` | 软删除会话 |
| GET | `/sessions/{id}/messages` | 某会话消息列表 |

### AGUI 收口（`/api/agui`，前端直连 Agent 时的降级兜底）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/agui/sessions` | 新建问答会话 |
| GET | `/agui/sessions/{id}/state` | 会话状态快照 |
| POST | `/agui/sessions/{id}/messages` | 发消息（SSE 流式；Agent 未接入返回降级提示） |
| POST | `/agui/events` | 反馈 / 交互事件上报（`feedback_toggle` → `feedback` 表） |

---

## 本次新增功能（P3 之后 + RAG / Agent 相关）

### 1. 管理后台与统计（P3 ADM-05/06）

- **统计口径刷新**：`statistics_definitions`（口径 SQL，仅允许 `SELECT`）+ `statistics_data`（结果快照）。
  - `core/statistics.py`：遍历口径执行 formula，逐条容错（单个口径失败不阻塞）。
  - `core/scheduler.py`：FastAPI `lifespan` 内 asyncio 循环，启动时立即刷新一次，之后每小时刷新（不引入 APScheduler，避免多 worker 重复执行）。
- **操作审计**：`audit_logs` 表 + `AuditMiddleware`，自动记录登录用户的 `POST/PUT/PATCH/DELETE` 操作（`/api/v1/auth/*`、`/health`、`/docs` 等跳过）。

### 2. 鉴权与权限加固

- `AuthMiddleware`：解析 JWT → 注入 `request.state.user_id` / `user_role`。
- `middleware/deps.py`：`get_current_user`（401 未登录）、`require_admin`（403 非管理员）、`get_role_type`。
- 内容接口补齐归属/角色校验：`audit` / `pin` 仅管理员，`submit` / `delete` 仅作者（或管理员）。

### 3. 会话 CRUD 补全

- 新增 `POST /sessions`（前端自带 `id` 幂等创建）、`PATCH /sessions/{id}`、`DELETE /sessions/{id}`（软删除）。此前 v1 只有 GET，导致 AGUI 消息落库时 `messages.session_id` 外键失败。

### 4. AGUI / Agent 收口

- `/api/agui/*`：问答 SSE 流式、会话状态、交互上报。
- `services/agent_client.py`：记录真实 Agent 契约 —— 端点 `POST {AGENT_BASE_URL}/agent/chat`（SSE 流式）、身份 `X-User-Id` 请求头、请求体 `{query, session_id}`。
- **当前前端直连 Agent**（`VITE_AGUI_BASE_URL` 指向 agent），后端 `/api/agui/*` 仅作 Agent 未接入时的降级兜底（返回「智能问答服务暂未接入，请稍后重试。」）。
- 业务落库：`recommendation_logs`（一行一个被推荐人）、`feedback`（赞踩三态）。

### 5. 发布事件信号（P5，RAG 重新索引）

- `rag.publish_events` 表 + `services/publish_event.py`：内容在「审核通过发布 / 编辑已发布 / 删除已发布」时写一条 `pending` 事件，供 RAG 服务消费后触发 `generate-from-db` + `index` 重新索引。后端只发信号，不重复实现切片/向量化/入库。

---

## 数据契约对齐（Agent / RAG，以本库为准）

三方（后端 / agent-service / knowledge-service）原用两套矛盾的数据模型。本次通过一个 Alembic 迁移（`a7b3c9d1e2f4_agent_compat_views`）把 agent 的只读查询对齐到本库：

| 依赖 | 本库 | agent 期望 | 对齐手段 |
|---|---|---|---|
| 人员表 | `users`(P0001, `active` bool) | `people`(p-0001, `status` text, `department` text) | **`public.people` 视图**（映射 users，补 department/status/role_type 等列） |
| 责任表 | `responsibility_assignments`(person_id+concept_id) | 完整责任事项(title/description/owner/time_limit…) | **补列 + 从 `agent.concepts`/`users` 回填** |
| 版本指针 | 无 | `rag_index_pointer`(active_version) | **补表**（active_version=0 表示「RAG 索引尚未构建」→ 检索走降级） |

rag 其余表结构差异（`rag_documents`/`rag_chunks`/`rag_index_jobs` 的两套列名、`index_version` INTEGER vs TEXT）**不在本迁移处理**，保持本库 rag 表不动，由 agent 团队改其 rag SQL 适配（见下）。

---

## 待其他团队调整

### Agent 团队（agent-service）

1. 连库配置改为本库：`app/config.py` → `pghost=localhost`、`pgdatabase=shouwenzeren`、`pguser=swzr_admin`、`pgpassword=swzr_dev_2026`。
2. 跳过 `init_db.py` / `import_v2_data.py`（本库已有数据 + `people` 视图，勿重建 v2 表 / 重新灌数据）。
3. 确认其查询命中 `public.people` 视图与 `responsibility_assignments` 补列（`_build_user_context` / `directory_search` / `MockResponsibilityRetriever`）。
4. 确认 `/agent/chat` SSE 流式契约与本库 `agent_client.py` 记录一致（`{query, session_id}` + `X-User-Id`）。

### RAG / Agent 团队（knowledge-service / rag 表）

1. rag 表写入适配：`rag_documents` / `rag_chunks` / `rag_index_jobs` 列名与 `index_version` 类型（INTEGER vs TEXT）与本库不同，需改其 rag SQL 适配（视图救不了写入）。
2. 消费 `rag.publish_events`：后端已写 `pending` 事件，但目前没有消费者，需 knowledge-service 接入调度，触发 `generate-from-db` + `index`。

### 前端

1. `stores/sessions.js` 的 `loadSessions()` 未拆后端分页响应 `{items:[...]}`（误把对象当数组取 `.length`），导致历史会话每次刷新只显示一条空白；`normalizeSession` 读 camelCase（`turnCount`/`updatedAt`）而后端返回 snake_case（`turn_count`/`updated_at`），需对齐字段名。

---

## 前后端约定

### 1. 字段命名：camelCase

所有响应 JSON 字段名均为 camelCase：

```json
{
  "ownerId": "P0001",
  "ownerName": "茅泽婉",
  "auditTrail": [...],
  "publishedAt": "2026-08-12",
  "weeklyQueryCount": 12
}
```

请求体同样支持 camelCase（Pydantic `alias` 兼容）。

> 例外：`GET /sessions` 的 `SessionResponse` 目前仍返回 snake_case（`turn_count`/`updated_at`），前端会话列表需按此对齐（见「待前端调整」）。

### 2. 内容状态：中文

| 数据库（英文） | API 返回（中文） |
|--------------|--------------|
| `draft` | 草稿 |
| `pending_review` | 待审核 |
| `published` | 已发布 |
| `rejected` | 已驳回 |

列表筛选仍用英文：`?status=pending_review`。

### 3. 审核流程

- 审核用专用端点 `POST /contents/{id}/audit`（**仅管理员**），不用 `PUT /contents/{id}`
- 请求体：`{ action: "approve"|"reject", reason: "" }`
- 审核记录写入 `auditTrail`（jsonb），字段：
  ```json
  {
    "operator": "P0001",
    "operated_at": "2026-08-12T16:30:00+08:00",
    "result": "published",
    "reason": ""
  }
  ```
- 时间：北京时间，精确到秒

### 4. 他画像

- 打标签 `POST /reviews`：传 `{ personId, tag }`，后端自动补 `reviewer` + `date`
- 加载"我的标签"需合并：`/reviews/sent`（发出的）+ `/people/{myId}/reviews`（收到的）

### 5. 内容 ID

- 种子数据：`A00001` ~ `A00607`
- 手动创建：`C00001`、`C00002`...（5 位序号）

---

## 前端修改清单

前端同学基于旧代码需同步以下文件（`github-sync/src/` 下）：

| 文件 | 改动 |
|------|------|
| `components/admin/AuditList.vue` | 审核卡片可点击 + 展示正文 + `@click.stop` |
| `views/MineView.vue` | `v-if="!profile"` 防加载崩溃 |
| `views/ContentDetailView.vue` | 审核字段 `operator` / `operated_at` |
| `stores/content.js` | 审核改用 `POST /{id}/audit` |
| `stores/reviews.js` | 同时加载发出+收到标签 |
| `services/api/content.js` | 新增 `auditContent` 方法 |
| `stores/sessions.js` | 会话加载拆分页 + 字段名对齐（见「待前端调整」） |

---

## Swagger 使用说明

1. 启动后端 → `http://localhost:8000/docs`
2. 先调 `POST /auth/login`，用 `p0001` / `swzr2026` 登录
3. 复制 `token`
4. 点右上角 **Authorize** → 输入 `Bearer <token>`
5. 所有需鉴权接口可直接在 Swagger 上测试

---

## 数据库

| 项目 | 说明 |
|------|------|
| 数据库 | PostgreSQL 17 + pgvector（`swzr-pg`，见 `docker-compose.yml`） |
| 迁移 | `alembic upgrade head`（baseline → P3 → P5 → agent 兼容） |
| 用户 | `swzr_admin` / `swzr_dev_2026` |
| Schema | `public`（业务）/ `agent`（概念等）/ `rag`（索引 + `publish_events` + `rag_index_pointer`） |
| 人员 | 300 人（P0001~P0300） |
| 内容 | 607 条种子 + 手动创建 |
| 部门 | 30 个（1 → 4 → 10 → 15） |
