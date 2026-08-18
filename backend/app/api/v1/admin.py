"""管理看板"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...middleware.deps import require_admin, get_current_user
from ...models.user import User
from ...models.content import Content
from ...models.session import QueryLog

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/dashboard", summary="Dashboard", description="管理看板概览")
def dashboard(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    people_count = db.query(sa_func.count(User.id)).scalar() or 0
    content_count = db.query(sa_func.count(Content.id)).filter(Content.is_deleted == False).scalar() or 0
    dept_count = db.query(sa_func.count(User.department_id.distinct())).scalar() or 0
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_rec = db.query(sa_func.coalesce(sa_func.sum(Content.weekly_recommend_count), 0)).filter(
        Content.is_deleted == False
    ).scalar() or 0
    return {
        "peopleCount": people_count,
        "contentCount": content_count,
        "domainCount": dept_count,
        "weeklyRecommendationTotal": week_rec,
    }


@router.get("/metrics", summary="Metrics", description="管理看板核心指标（对齐前端 useAdminStore.metrics）")
def metrics(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    people_count = db.query(sa_func.count(User.id)).scalar() or 0
    content_count = db.query(sa_func.count(Content.id)).filter(Content.is_deleted == False).scalar() or 0
    dept_count = db.query(sa_func.count(User.department_id.distinct())).scalar() or 0
    now = datetime.now(timezone.utc)
    week_rec = db.query(sa_func.coalesce(sa_func.sum(Content.weekly_recommend_count), 0)).filter(
        Content.is_deleted == False
    ).scalar() or 0
    return {
        "peopleCount": people_count,
        "contentCount": content_count,
        "domainCount": dept_count,
        "weeklyRecommendationTotal": week_rec,
    }


@router.get("/rankings/recommend", summary="Recommend Ranking", description="本周推荐热度排行 TOP10（对齐前端 useAdminStore.ranking）")
def recommend_ranking(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    top = db.query(
        Content.owner_id,
        sa_func.sum(Content.weekly_recommend_count).label("value")
    ).filter(Content.is_deleted == False).group_by(Content.owner_id).order_by(
        sa_func.sum(Content.weekly_recommend_count).desc()
    ).limit(10).all()
    result = []
    for owner_id, value in top:
        person = db.query(User).filter(User.id == owner_id).first()
        result.append({
            "person": {
                "id": owner_id,
                "name": person.name if person else "",
                "department": person.department.name if person and person.department else "",
                "role": person.role or "" if person else "",
            },
            "value": value or 0,
        })
    return result


@router.get("/trends/activity", summary="Activity Trend", description="近 7 天活动趋势（对齐前端 useAdminStore.trend）")
def activity_trend(
    request: Request,
    week: str = Query("current", description="current | previous"),
    db: Session = Depends(get_db),
):
    require_admin(request)
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    if week == "previous":
        now -= timedelta(days=7)
    week_start = now - timedelta(days=now.weekday())
    trend = []
    for i in range(7):
        day_start = week_start + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = db.query(sa_func.count(QueryLog.id)).filter(
            QueryLog.created_at >= day_start, QueryLog.created_at < day_end
        ).scalar() or 0
        trend.append({"day": day_start.strftime("%m-%d"), "value": count, "percent": 0})
    max_val = max(t["value"] for t in trend) if trend else 1
    for t in trend:
        t["percent"] = round(t["value"] / max_val * 100) if max_val > 0 else 0
    return trend


@router.get("/statistics", summary="List Statistics", description="统计指标列表")
def list_statistics(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    return [
        {"key": "total_users", "label": "总用户数"},
        {"key": "total_contents", "label": "总内容数"},
        {"key": "total_reviews", "label": "总标签数"},
    ]


@router.get("/statistics/{metric_key}", summary="Get Statistic Value", description="执行统计 SQL 获取实时值")
def get_statistic_value(metric_key: str, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    if metric_key == "total_users":
        return {"key": metric_key, "value": db.query(sa_func.count(User.id)).scalar() or 0}
    elif metric_key == "total_contents":
        return {"key": metric_key, "value": db.query(sa_func.count(Content.id)).filter(Content.is_deleted == False).scalar() or 0}
    elif metric_key == "total_reviews":
        from ...models.review import PeerReview
        return {"key": metric_key, "value": db.query(sa_func.count(PeerReview.id)).scalar() or 0}
    return {"key": metric_key, "value": 0}


# ---------------------------------------------------------------- 推荐反馈可视化(验收:反馈数据进库 + 后台展示)

@router.get("/feedback/summary", summary="Feedback Summary", description="推荐反馈汇总(有帮助率/趋势/点踩原因分布)")
def feedback_summary(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    from sqlalchemy import text as sa_text
    totals = db.execute(sa_text(
        "SELECT feedback_type, count(*) AS n FROM agent.feedback_events"
        " WHERE feedback_type IN ('like','dislike') GROUP BY feedback_type"
    )).all()
    up = sum(int(r.n) for r in totals if r.feedback_type == "like")
    down = sum(int(r.n) for r in totals if r.feedback_type == "dislike")
    total = up + down
    # 近 7 天趋势(按自然日)
    trend_rows = db.execute(sa_text(
        "SELECT date_trunc('day', created_at + interval '8 hours') AS day,"
        "       feedback_type, count(*) AS n"
        " FROM agent.feedback_events"
        " WHERE feedback_type IN ('like','dislike')"
        "   AND created_at >= now() - interval '7 days'"
        " GROUP BY 1, 2 ORDER BY 1"
    )).all()
    days: dict[str, dict] = {}
    for r in trend_rows:
        key = r.day.strftime("%m-%d")
        slot = days.setdefault(key, {"day": key, "up": 0, "down": 0})
        slot["up" if r.feedback_type == "like" else "down"] = int(r.n)
    # 点踩原因分布
    reason_rows = db.execute(sa_text(
        "SELECT COALESCE(NULLIF(reason,''),'未填写') AS reason, count(*) AS n"
        " FROM agent.feedback_events WHERE feedback_type='dislike'"
        " GROUP BY 1 ORDER BY n DESC"
    )).all()
    return {
        "up": up, "down": down, "total": total,
        "helpfulRate": round(up / total * 100, 1) if total else 0,
        "trend": list(days.values()),
        "reasons": [{"reason": r.reason, "count": int(r.n)} for r in reason_rows],
    }


@router.get("/feedback/recent", summary="Feedback Recent", description="最近反馈明细(含用户问题与推荐人选)")
def feedback_recent(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    require_admin(request)
    from sqlalchemy import text as sa_text
    rows = db.execute(sa_text(
        "SELECT e.id, e.created_at, e.user_id, u.name AS user_name,"
        "       e.feedback_type, e.reason, e.trace_id, e.message_id,"
        "       e.payload, l.query_summary, l.ranked_candidates"
        " FROM agent.feedback_events e"
        " LEFT JOIN public.users u ON u.id = e.user_id"
        " LEFT JOIN agent.agent_recommendation_logs l"
        "   ON l.trace_id = e.trace_id AND e.trace_id <> ''"
        "  AND l.message_id = e.message_id"
        " WHERE e.feedback_type IN ('like','dislike')"
        " ORDER BY e.created_at DESC LIMIT :limit"
    ), {"limit": limit}).all()
    import json as _json
    result = []
    for r in rows:
        payload = r.payload if isinstance(r.payload, dict) else (_json.loads(r.payload) if r.payload else {})
        ctx = payload.get("context") or payload
        # 推荐人选:优先反馈上下文里带的名单,否则从推荐日志取
        candidates = ctx.get("candidates") or []
        if not candidates and r.ranked_candidates:
            rc = r.ranked_candidates if isinstance(r.ranked_candidates, list) else _json.loads(r.ranked_candidates)
            candidates = [c.get("person_id", "") for c in rc[:5]]
        result.append({
            "id": r.id,
            "createdAt": (r.created_at + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            "user": r.user_name or r.user_id,
            "question": ctx.get("question") or r.query_summary or "",
            "candidates": candidates,
            "value": "up" if r.feedback_type == "like" else "down",
            "reason": r.reason or "",
        })
    return result
