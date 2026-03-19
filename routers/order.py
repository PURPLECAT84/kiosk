# routers/order.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
import uuid
from typing import List
from datetime import datetime, time

from database import get_db
from models.order import Order
from models.user import User
from schemas.order import OrderCreate, OrderResponse

# 🔥 방금 만든 요리사(Service)와 문지기(Dependency) 호출!
from service.order_service import create_order_transaction
from core.dependency import get_current_user

router = APIRouter()

"""===================== 주문/결제 생성 ============================"""
@router.post("/", response_model=OrderResponse)
async def create_order(
        order_data: OrderCreate,
        db: Session = Depends(get_db)
):
    # 50줄이 넘던 복잡한 로직을 단 1줄로 요리사에게 전달!
    new_order = await create_order_transaction(db, order_data)
    return new_order


"""===================== 매출 리스트 조회 ============================"""
@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    store_id: uuid.UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db)
):
    stmt = select(Order).where(Order.store_id == store_id)

    if start_date:
        stmt = stmt.where(Order.created_date >= start_date)
    if end_date:
        # 날짜의 끝을 23:59:59 로 꽉 채워주는 로직
        end_date_max = datetime.combine(end_date.date(), time.max)
        stmt = stmt.where(Order.created_date <= end_date_max)
    
    stmt = stmt.order_by(desc(Order.created_date))
    return db.scalars(stmt).all()


"""===================== 주문 취소 (환불) ============================"""
@router.delete("/{order_id}", response_model=OrderResponse)
async def delete_orders(
    order_id: int,
    db: Session = Depends(get_db),
    # 🔒 문지기 배치: 로그인한(자물쇠를 푼) 사장님만 지울 수 있습니다!
    current_user: User = Depends(get_current_user) 
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="해당 주문 내역을 찾을 수 없습니다.")
    
    if order.status == "REFUNDED":
        raise HTTPException(status_code=400, detail="이미 취소(환불) 처리된 주문입니다.")
    
    # DB에서 삭제하지 않고 상태만 바꿈 (Soft Delete)
    order.status = "REFUNDED"
    db.commit()
    db.refresh(order)

    return order