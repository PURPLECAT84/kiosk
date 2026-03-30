from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc
from datetime import date
from models.order import Order
from models.user import User
from models.order_item import OrderItem
from database import get_db
from core.dependency import get_current_user

router = APIRouter()

@router.get("/summary", summary = "오늘의 대시보드 요약")
def get_dashboard_summary (db : Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    
    if current_user.authority not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드는 사장님만 볼 수 있는 1급 기밀입니다!"
        )

    today_start = date.today()
    month_start = today_start.replace(day=1)

    total_sales = db.scalar(
        select(func.sum(Order.total_amount)).where(Order.created_date >= today_start)
    )

    if total_sales == None:
        total_sales = 0

    monthly_sales = db.scalar(
        select(func.sum(Order.total_amount)).where(Order.created_date >= month_start)
    )

    if monthly_sales == None:
        monthly_sales = 0

    total_order = db.scalar(
        select(func.count(Order.id)).where(Order.created_date >= today_start)
    )

    if total_order == None:
        total_order = 0


    return {
        "today_sales" : total_sales,
        "today_orders" : total_order,
        "monthly_sales": monthly_sales
    }



@router.get("/best-sellers", summary="오늘의 베스트셀러 Top 5")
def get_best_sellers(db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    
    if current_user.authority not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드는 사장님만 볼 수 있는 1급 기밀입니다!"
        )

    today_start = date.today()

    # 🚂 기차 칸을 엔터로 나누면 읽기가 훨씬 편해집니다!
    stmt = (
        select(OrderItem.product_name, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)    # 스테이플러 철컥!
        .where(Order.created_date >= today_start)       # 오늘 팔린 것만
        .group_by(OrderItem.product_name)               # 메뉴별로 묶어!
        .order_by(func.sum(OrderItem.quantity).desc())  # 수량 내림차순! (괄호 위치 수정)
        .limit(5)                                       # 5개만 잘라!
    )

    result = db.execute(stmt).all()

    best_seller_list = []

    for row in result:
        # row[0]은 이름, row[1]은 판매 수량!
        best_seller_list.append({"product_name": row[0], "total_sold": row[1]})

    return best_seller_list






