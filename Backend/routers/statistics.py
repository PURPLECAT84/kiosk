from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc
from datetime import date
from models.order import Order
from models.user import UserInfo, UserRole
from models.order_item import OrderItem
from models.kiosk import Kiosk
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

    # MANAGER 권한인 경우 본인 키오스크의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return {
                "today_sales" : 0,
                "today_orders" : 0,
                "monthly_sales": 0
            }
        sales_stmt = sales_stmt.where(Order.kiosk_id.in_(kiosk_ids))
        monthly_stmt = monthly_stmt.where(Order.kiosk_id.in_(kiosk_ids))
        order_stmt = order_stmt.where(Order.kiosk_id.in_(kiosk_ids))

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

    # MANAGER 권한인 경우 본인 키오스크의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return []
        stmt = stmt.where(Order.kiosk_id.in_(kiosk_ids))

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


@router.get("/settlement", summary="월간 정산 현황 (일별 매출 및 환불액 집계)")
def get_monthly_settlement(
    year: int,
    month: int,
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    지정된 연도와 월에 속하는 가동 키오스크의 일별 매출 합계, 주문 수 및 환불 집계 내역을 반환합니다.
    """
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드 권한이 없습니다."
        )

    try:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 연도 또는 월입니다.")

    stmt = (
        select(
            func.date(Order.created_date).label("date"),
            func.sum(Order.total_amount).label("sales"),
            func.count(Order.id).label("orders"),
            func.sum(func.coalesce(Order.refund_amount, 0)).label("refunds")
        )
        .where(
            Order.created_date >= start_date,
            Order.created_date < end_date,
            Order.status.in_(["Completed", "REFUNDED"])
        )
    )

    # X-Kiosk-Id 헤더 필터 추가
    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    # MANAGER 권한인 경우 본인 키오스크의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return []
        stmt = stmt.where(Order.kiosk_id.in_(kiosk_ids))

    stmt = stmt.group_by(func.date(Order.created_date)).order_by(func.date(Order.created_date).asc())
    results = db.execute(stmt).all()

    settlement_list = []
    for row in results:
        settlement_list.append({
            "date": str(row[0]),
            "sales": int(row[1] or 0),
            "orders": int(row[2] or 0),
            "refunds": int(row[3] or 0)
        })

    return settlement_list
