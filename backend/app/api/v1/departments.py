"""部门管理"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.department import Department
from ...schemas.departments import (
    DepartmentCreateRequest, DepartmentUpdateRequest,
    DepartmentResponse, DepartmentTreeNode,
)

router = APIRouter(prefix="/departments", tags=["部门"])


def _build_tree(dept: Department) -> DepartmentTreeNode:
    member_count = dept.members.count() if dept.members else 0
    leader_name = None
    try:
        leader_name = dept.leader.name if dept.leader else None
    except Exception:
        pass
    children = [_build_tree(c) for c in (dept.children or [])]
    return DepartmentTreeNode(
        id=dept.id, name=dept.name, level=dept.level,
        parent_id=dept.parent_id, leader_id=dept.leader_id,
        leader_name=leader_name, responsibility=dept.responsibility,
        status=dept.status, sort_order=dept.sort_order,
        children=children, member_count=member_count,
    )


@router.get("/tree", summary="Department Tree", description="部门树（含成员数）")
def department_tree(db: Session = Depends(get_db)):
    roots = db.query(Department).filter(Department.parent_id == None).order_by(Department.sort_order).all()
    return [_build_tree(r) for r in roots]


@router.get("/{dept_id}", response_model=DepartmentResponse, summary="Get Department", description="部门详情")
def get_department(dept_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")
    return dept


@router.patch("/{dept_id}", response_model=DepartmentResponse, summary="Update Department", description="更新部门")
def update_department(dept_id: int, body: DepartmentUpdateRequest, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dept, key, value)
    db.commit()
    db.refresh(dept)
    return dept


@router.post("", response_model=DepartmentResponse, status_code=201, summary="Create Department", description="创建部门")
def create_department(body: DepartmentCreateRequest, db: Session = Depends(get_db)):
    dept = Department(**body.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
