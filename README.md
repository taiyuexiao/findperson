# 首问责任平台 — 后端 API（P1）

> 分支：`backend` | FastAPI + PostgreSQL | 2026-08-12

---

## 快速开始

```bash
# 1. 环境变量
cp .env.example .env
# 编辑 .env，填入实际数据库密码和 JWT 密钥

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动数据库（见 database 分支）
docker compose up -d

# 4. 数据库迁移 + 种子数据（见 database 分支）
alembic upgrade head
cat scripts/seed.sql | docker exec -i swzr-pg psql -U swzr_admin -d shouwenzeren

# 5. 启动后端
uvicorn app.main:app --reload --port 8000
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
│   ├── main.py              # FastAPI 入口，注册路由 + CORS
│   ├── api/v1/              # 路由层
│   │   ├── auth.py          # 登录 / 注册 / 改密
│   │   ├── me.py            # 当前用户
│   │   ├── people.py        # 人员名片 CRUD
│   │   ├── contents.py      # 内容 CRUD + 审核
│   │   ├── reviews.py       # 他画像（标签）
│   │   ├── admin.py         # 管理看板
│   │   ├── departments.py   # 部门
│   │   └── sessions.py      # 会话
│   ├── models/              # SQLAlchemy ORM
│   │   ├── user.py          # 用户
│   │   ├── department.py    # 部门
│   │   ├── content.py       # 内容（含 audit_trail jsonb）
│   │   ├── review.py        # 标签
│   │   └── session.py       # 会话 / 消息 / 查询日志
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── core/                # 配置 / 数据库 / 安全
│   └── middleware/          # 鉴权依赖
├── requirements.txt
└── .env.example
```

---

## API 端点清单

> 前缀：`/api/v1` | Swagger `http://localhost:8000/docs` 有完整请求/响应示例

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录，返回 `{ token, user }` |
| POST | `/auth/register` | 管理员创建用户 |
| POST | `/auth/change-password` | 修改密码 |

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
| PUT/PATCH | `/contents/{id}` | 编辑内容 |
| DELETE | `/contents/{id}` | 软删除 |
| POST | `/contents/{id}/submit` | 提交审核 |
| POST | `/contents/{id}/audit` | 审核通过/驳回 |
| POST | `/contents/{id}/pin` | 切换置顶 |

### 他画像

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/reviews` | 打标签 |
| GET | `/reviews/sent` | 我发出的标签 |
| DELETE | `/reviews/{id}` | 删除标签 |
| GET | `/reviews/person/{id}` | 某人标签汇总 |
| GET | `/reviews/person/{id}/history` | 某人标签历史（分页） |

### 管理看板

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/dashboard` | 看板概览 |
| GET | `/admin/metrics` | 核心指标（人数、内容数、领域数、本周推荐） |
| GET | `/admin/rankings/recommend` | 推荐热度 TOP10 |
| GET | `/admin/trends/activity` | 近 7 天活动趋势（`?week=current\|previous`） |
| GET | `/admin/statistics` | 统计指标列表 |
| GET | `/admin/statistics/{key}` | 统计指标实时值 |

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
| GET | `/sessions/{id}/messages` | 某会话消息列表 |

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

### 2. 内容状态：中文

| 数据库（英文） | API 返回（中文） |
|--------------|--------------|
| `draft` | 草稿 |
| `pending_review` | 待审核 |
| `published` | 已发布 |
| `rejected` | 已驳回 |

列表筛选仍用英文：`?status=pending_review`。

### 3. 审核流程

- 审核用专用端点 `POST /contents/{id}/audit`，不用 `PUT /contents/{id}`
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

---

## Swagger 使用说明

1. 启动后端 → `http://localhost:8000/docs`
2. 先调 `POST /auth/login`，用 `p0001` / `swzr2026` 登录
3. 复制 `token`
4. 点右上角 **Authorize** → 输入 `Bearer <token>`
5. 所有需鉴权接口可直接在 Swagger 上测试

---

## 数据库

数据库 DDL、种子数据、Docker 部署见仓库 **[database](../../tree/database)** 分支。

| 项目 | 说明 |
|------|------|
| 数据库 | PostgreSQL 17 + pgvector（`swzr-pg`） |
| 用户 | `swzr_admin` / `swzr_dev_2026` |
| 人员 | 300 人（P0001~P0300） |
| 内容 | 607 条种子 + 手动创建 |
| 部门 | 30 个（1 → 4 → 10 → 15） |
