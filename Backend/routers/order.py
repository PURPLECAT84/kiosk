# routers/order.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from sqlalchemy.sql import exists
import uuid
from typing import List, Optional
from datetime import datetime, time
from models.product import Product
from models.kiosk import Kiosk
from database import get_db
from models.order import Order
from models.user import UserInfo, UserRole
from schemas.order import OrderCreate, OrderResponse, OrderRefundRequest

from service.order_service import create_order_transaction
from core.dependency import get_current_user

router = APIRouter()

def mask_order_no(order_no: str | None) -> str | None:
    """전화번호 형태(010으로 시작하는 10~11자리)의 주문번호를 마스킹합니다."""
    if not order_no:
        return order_no
    digits = "".join(c for c in order_no if c.isdigit())
    if digits.startswith("010") and (len(digits) == 10 or len(digits) == 11):
        if len(digits) == 11:
            return f"{digits[:3]}-****-{digits[7:]}"
        else:
            return f"{digits[:3]}-***-{digits[6:]}"
    return order_no

"""===================== 주문/결제 생성 ============================"""
@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    new_order = await create_order_transaction(db, order_data)
    return new_order


"""===================== 매출 리스트 조회 ============================"""
@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    kiosk_id: uuid.UUID,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 권한 검증: 키오스크 존재 여부 및 본인 키오스크 소유권 체크
    target_kiosk = db.get(Kiosk, kiosk_id)
    if not target_kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크를 찾을 수 없습니다.")

    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER] and target_kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 키오스크의 매출 내역만 조회할 수 있습니다.")
    
    stmt = select(Order).where(Order.kiosk_id == kiosk_id)
    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    if start_date:
        stmt = stmt.where(Order.created_date >= start_date)
    if end_date:
        end_date_max = datetime.combine(end_date.date(), time.max)
        stmt = stmt.where(Order.created_date <= end_date_max)
    
    stmt = stmt.order_by(desc(Order.created_date))
    orders = db.scalars(stmt).all()

    response_orders = []
    for order in orders:
        pydantic_order = OrderResponse.model_validate(order)
        pydantic_order.order_no = mask_order_no(pydantic_order.order_no)
        response_orders.append(pydantic_order)

    return response_orders


"""===================== 영수증 상세 보기 (마스킹 해제) ============================"""
@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="해당 주문 내역을 찾을 수 없습니다.")
        
    # 권한 체크: 본인 키오스크의 주문인지 확인
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER] and order.kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 키오스크의 주문만 열람할 수 있습니다.")
        
    return order


"""===================== 주문 취소 (환불) - 기본 취소 ============================"""
@router.delete("/{order_id}", response_model=OrderResponse)
async def delete_orders(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user) 
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="해당 주문 내역을 찾을 수 없습니다.")
    if order.status == "REFUNDED":
        raise HTTPException(status_code=400, detail="이미 취소(환불) 처리된 주문입니다.")
        
    # 권한 체크
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER] and order.kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 키오스크의 주문만 환불 처리할 수 있습니다.")
    
    # 1. 주문 상태 변경 및 기본 환불 정보 기록
    order.status = "REFUNDED"
    order.refund_amount = order.total_amount
    order.refund_reason = "점주 즉시 환불"
    order.refund_method = order.payment_method
    order.refunded_at = datetime.now()

    # 2. 재고(Stock) 롤백 로직 (재고관리 설정된 경우만)
    for item in order.items:
        product = db.get(Product, item.product_id)
        if product:
            if getattr(product, "stock_managed", True):
                product.stock += item.quantity
            product.is_active = True 

    db.commit()
    db.refresh(order)
    return order


"""===================== 상세 환불 처리 ============================"""
@router.post("/{order_id}/refund", response_model=OrderResponse)
async def refund_order(
    order_id: int,
    refund_data: OrderRefundRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="해당 주문 내역을 찾을 수 없습니다.")
    if order.status == "REFUNDED":
        raise HTTPException(status_code=400, detail="이미 취소(환불) 처리된 주문입니다.")
        
    # 권한 체크
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER] and order.kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 키오스크의 주문만 환불 처리할 수 있습니다.")
    
    # 1. 주문 상태 변경 및 환불 정보 기록
    order.status = "REFUNDED"
    order.refund_amount = refund_data.refund_amount
    order.refund_reason = refund_data.refund_reason
    order.refund_method = refund_data.refund_method
    order.refunded_at = datetime.now()

    # 2. 재고(Stock) 롤백 로직 (재고관리 설정된 경우만)
    for item in order.items:
        product = db.get(Product, item.product_id)
        if product:
            if getattr(product, "stock_managed", True):
                product.stock += item.quantity
            product.is_active = True 

    db.commit()
    db.refresh(order)
    return order