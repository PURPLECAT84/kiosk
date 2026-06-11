from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models.kiosk import Kiosk
from models.category import Category
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from schemas.kiosk_client import KioskSyncResponse, KioskCategoryResponse, KioskProductResponse, MockPaymentRequest, MockPaymentResponse
from typing import List
import uuid
import random
from datetime import datetime

router = APIRouter()

@router.get("/sync/{kiosk_id}", response_model=KioskSyncResponse, summary="키오스크 상품/카테고리 동기화")
async def sync_kiosk(
    kiosk_id: str,
    db: Session = Depends(get_db)
):
    # 1. 키오스크 조회 (고유코드 또는 UUID)
    kiosk = None
    if len(kiosk_id) == 8:
        stmt = select(Kiosk).where(Kiosk.code == kiosk_id)
        kiosk = db.execute(stmt).scalars().first()
        
    if not kiosk:
        try:
            uuid_obj = uuid.UUID(kiosk_id)
            kiosk = db.get(Kiosk, uuid_obj)
        except ValueError:
            pass
            
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="등록되지 않은 키오스크 기기입니다")
    
    # 1-2. 사용료 결제 상태 검증 (연체 미납 시 차단)
    if kiosk.payment_status == "UNPAID":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="사용료 연체로 인해 키오스크 사용이 중지되었습니다. 파트너센터에서 결제 정보를 확인해주세요."
        )
    
    # 2. 점주 사업자명(매장명) 조회
    store_name = "미지정 매장"
    if kiosk.owner and kiosk.owner.businesses:
        store_name = kiosk.owner.businesses[0].store_name
    
    # 3. 카테고리 리스트 조회 (sequence 오름차순 정렬)
    cat_stmt = select(Category).where(Category.kiosk_id == kiosk.id).order_by(Category.sequence.asc())
    categories = db.execute(cat_stmt).scalars().all()
    
    cat_responses = []
    for cat in categories:
        # 4. 각 카테고리에 귀속된 상품 리스트 조회 (is_active=True인 활성 상품만 노출, sequence 오름차순 정렬)
        prod_stmt = select(Product).where(
            Product.category_id == cat.id,
            Product.is_active == True
        ).order_by(Product.sequence.asc())
        products = db.execute(prod_stmt).scalars().all()
        
        prod_responses = []
        for prod in products:
            # 재고에 따른 상태 설정
            status_val = "ACTIVE"
            if prod.stock_managed and prod.stock <= 0:
                status_val = "SOLDOUT"
            elif prod.expiration_date and prod.expiration_date < datetime.now():
                status_val = "SOLDOUT"
                
            prod_responses.append(KioskProductResponse(
                id=prod.id,
                category_id=prod.category_id,
                name=prod.name,
                price=prod.price,
                image=prod.image,
                stock=prod.stock,
                is_active=prod.is_active,
                sequence=prod.sequence,
                status=status_val
            ))
            
        cat_responses.append(KioskCategoryResponse(
            id=cat.id,
            name=cat.name,
            sequence=cat.sequence,
            products=prod_responses
        ))
        
    return KioskSyncResponse(
        store_name=store_name,
        kiosk_type=kiosk.type,
        categories=cat_responses
    )


@router.post("/pay/mock", response_model=MockPaymentResponse, summary="가상 결제 테스트 (Mock)")
async def mock_payment(
    request: MockPaymentRequest,
    db: Session = Depends(get_db)
):
    # 1. 키오스크 조회 (고유코드 또는 UUID)
    kiosk = None
    if len(request.kiosk_id) == 8:
        stmt = select(Kiosk).where(Kiosk.code == request.kiosk_id)
        kiosk = db.execute(stmt).scalars().first()
        
    if not kiosk:
        try:
            uuid_obj = uuid.UUID(request.kiosk_id)
            kiosk = db.get(Kiosk, uuid_obj)
        except ValueError:
            pass
            
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다")
    
    # 2. 주문번호(order_no) 결정
    order_no = None
    if kiosk.type == "Restaurant" and request.order_no:
        digits = "".join(c for c in request.order_no if c.isdigit())
        if len(digits) >= 10:
            order_no = digits
            
    if not order_no:
        current_date = datetime.now().strftime("%y%m%d")
        random_digits = "".join(random.choice("0123456789") for _ in range(6))
        order_no = current_date + random_digits
 
    # 3. 가상 승인번호 생성 (YYMMDD + 랜덤 6자리)
    approval_code = datetime.now().strftime("%y%m%d") + "".join(random.choice("0123456789") for _ in range(6))
    
    try:
        # 4. 영수증 DB 적재
        new_order = Order(
            order_no=order_no,
            kiosk_id=kiosk.id,
            total_amount=request.total_amount,
            payment_method=request.payment_method,
            payment_provider=request.payment_provider,
            approval_code=approval_code,
            status="Completed"
        )
        db.add(new_order)
        db.flush() # ID 획득을 위한 플러시
        
        # 5. 구매 품목 DB 적재 및 재고 차감 (재고관리 설정된 경우만)
        for item in request.items:
            prod_id = uuid.UUID(item["product_id"]) if isinstance(item["product_id"], str) else item["product_id"]
            product = db.get(Product, prod_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"상품({prod_id})을 찾을 수 없습니다")
            
            # 품절/정지 검증
            if not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{product.name}의 판매가 중지되었습니다.")
                
            if product.stock_managed:
                if product.stock < item["quantity"]:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{product.name}의 재고가 부족합니다.")
                # 재고 차감
                product.stock -= item["quantity"]
                if product.stock == 0:
                    product.is_active = False # 품절 시 비활성화
                
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                product_name=product.name,
                product_price=product.price,
                quantity=item["quantity"]
            )
            db.add(order_item)
            
        db.commit()
        db.refresh(new_order)
        
        return MockPaymentResponse(
            success=True,
            order_no=new_order.order_no,
            approval_code=new_order.approval_code,
            total_amount=new_order.total_amount,
            created_at=new_order.created_date
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
