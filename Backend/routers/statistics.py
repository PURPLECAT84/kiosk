from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc
from datetime import date
from models.order import Order
from models.user import UserInfo, UserRole
from models.order_item import OrderItem
from models.store import Store
from database import get_db
from core.dependency import get_current_user
from typing import Optional
import uuid

router = APIRouter()

@router.get("/summary", summary = "오늘의 대시보드 요약")
def get_dashboard_summary (
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드 권한이 없습니다."
        )

    today_start = date.today()
    month_start = today_start.replace(day=1)

    sales_stmt = select(func.sum(Order.total_amount)).where(Order.created_date >= today_start)
    monthly_stmt = select(func.sum(Order.total_amount)).where(Order.created_date >= month_start)
    order_stmt = select(func.count(Order.id)).where(Order.created_date >= today_start)

    # X-Kiosk-Id 헤더 필터 추가
    if x_kiosk_id:
        sales_stmt = sales_stmt.where(Order.kiosk_id == x_kiosk_id)
        monthly_stmt = monthly_stmt.where(Order.kiosk_id == x_kiosk_id)
        order_stmt = order_stmt.where(Order.kiosk_id == x_kiosk_id)

    # MANAGER 권한인 경우 본인 매장의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        store_ids = db.scalars(select(Store.id).where(Store.user_id == current_user.id)).all()
        if not store_ids:
            return {
                "today_sales" : 0,
                "today_orders" : 0,
                "monthly_sales": 0
            }
        sales_stmt = sales_stmt.where(Order.store_id.in_(store_ids))
        monthly_stmt = monthly_stmt.where(Order.store_id.in_(store_ids))
        order_stmt = order_stmt.where(Order.store_id.in_(store_ids))

    total_sales = db.scalar(sales_stmt) or 0
    monthly_sales = db.scalar(monthly_stmt) or 0
    total_order = db.scalar(order_stmt) or 0

    return {
        "today_sales" : total_sales,
        "today_orders" : total_order,
        "monthly_sales": monthly_sales
    }


@router.get("/best-sellers", summary="오늘의 베스트셀러 Top 5")
def get_best_sellers(
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드 권한이 없습니다."
        )

    today_start = date.today()

    stmt = (
        select(OrderItem.product_name, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.created_date >= today_start)
    )

    # X-Kiosk-Id 헤더 필터 추가
    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    # MANAGER 권한인 경우 본인 매장의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        store_ids = db.scalars(select(Store.id).where(Store.user_id == current_user.id)).all()
        if not store_ids:
            return []
        stmt = stmt.where(Order.store_id.in_(store_ids))

    stmt = (
        stmt.group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    )

    result = db.execute(stmt).all()

    best_seller_list = []
    for row in result:
        best_seller_list.append({"product_name": row[0], "total_sold": row[1]})

    return best_seller_list







