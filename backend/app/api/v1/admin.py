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
from ...models.admin import AuditLog, StatisticsData

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/dashboard", summary="Dashboard", description="管理看板概览")
def dashboard(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    people_count = db.query(sa_func.count(User.id)).scalar() or 0
    content_count = db.query(sa_func.count(Content.id)).filter(Content.deleted_at.is_(None)).scalar() or 0
    dept_count = db.query(sa_func.count(User.department_id.distinct())).scalar() or 0
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_rec = db.query(sa_func.coalesce(sa_func.sum(Content.weekly_recommend_count), 0)).filter(
        Content.deleted_at.is_(None)
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
    content_count = db.query(sa_func.count(Content.id)).filter(Content.deleted_at.is_(None)).scalar() or 0
    dept_count = db.query(sa_func.count(User.department_id.distinct())).scalar() or 0
    now = datetime.now(timezone.utc)
    week_rec = db.query(sa_func.coalesce(sa_func.sum(Content.weekly_recommend_count), 0)).filter(
        Content.deleted_at.is_(None)
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
    ).filter(Content.deleted_at.is_(None)).group_by(Content.owner_id).order_by(
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


@router.get("/statistics/data", summary="Statistics Data", description="统计结果快照（定时刷新写入 statistics_data）")
def statistics_data(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    rows = (
        db.query(StatisticsData)
        .order_by(StatisticsData.stat_date.desc(), StatisticsData.id.desc())
        .limit(100)
        .all()
    )
    return [{
        "metricKey": r.metric_key,
        "value": float(r.value) if r.value is not None else None,
        "dimension": r.dimension,
        "statDate": r.stat_date.isoformat() if r.stat_date else None,
    } for r in rows]


@router.get("/statistics/{metric_key}", summary="Get Statistic Value", description="执行统计 SQL 获取实时值")
def get_statistic_value(metric_key: str, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    if metric_key == "total_users":
        return {"key": metric_key, "value": db.query(sa_func.count(User.id)).scalar() or 0}
    elif metric_key == "total_contents":
        return {"key": metric_key, "value": db.query(sa_func.count(Content.id)).filter(Content.deleted_at.is_(None)).scalar() or 0}
    elif metric_key == "total_reviews":
        from ...models.review import PeerReview
        return {"key": metric_key, "value": db.query(sa_func.count(PeerReview.id)).scalar() or 0}
    return {"key": metric_key, "value": 0}


@router.get("/audit-logs", summary="Audit Logs", description="操作审计日志列表（分页）")
def audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    require_admin(request)
    total = db.query(sa_func.count(AuditLog.id)).scalar() or 0
    rows = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [{
        "id": r.id,
        "userId": r.user_id,
        "action": r.action,
        "resourceType": r.resource_type,
        "resourceId": r.resource_id,
        "method": r.method,
        "path": r.path,
        "ip": r.ip,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]
    return {"total": total, "items": items}
