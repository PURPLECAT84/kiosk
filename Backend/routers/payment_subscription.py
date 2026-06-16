# Backend/routers/payment_subscription.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models.kiosk import Kiosk
from models.user import UserInfo, UserRole
from models.billing_product import BillingProduct, KioskBillingHistory
from core.dependency import get_current_user
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import httpx
import logging

from core.security import PORTONE_API_SECRET, PORTONE_CHANNEL_KEY, PORTONE_API_URL
from schemas.billing_product import BillingProductCreate, BillingProductUpdate, BillingProductResponse
from service.portone_service import verify_portone_payment, cancel_portone_payment

# 로거 설정
logger = logging.getLogger("payment_subscription")

router = APIRouter(
    prefix="/subscribe",
    tags=["Kiosk Subscription Billing (사용료 결제)"]
)

# -----------------------------------------------------------------------------
# [초보자 가이드 - 요청 스키마 정의]
# -----------------------------------------------------------------------------
class RegisterBillingKeyRequest(BaseModel):
    kiosk_id: uuid.UUID = Field(..., description="정기결제를 연동할 키오스크 ID")
    customer_uid: str = Field(..., description="포트원 빌링키 식별자 (점주 카드 고유 해시)")
    billing_product_id: int = Field(..., description="구독할 이용 요금 상품 고유 ID")

class BillingKeyResponse(BaseModel):
    success: bool
    kiosk_id: uuid.UUID
    billing_key: str
    message: str

class ChargeSubscriptionRequest(BaseModel):
    kiosk_id: uuid.UUID = Field(..., description="결제할 키오스크 ID")

class ChargeResponse(BaseModel):
    success: bool
    kiosk_id: uuid.UUID
    amount: int
    approval_code: str
    message: str

class OnetimeVerifyRequest(BaseModel):
    kiosk_id: uuid.UUID = Field(..., description="결제할 키오스크 ID")
    payment_id: str = Field(..., description="포트원 일반결제 1회성 paymentId")
    billing_product_id: int = Field(..., description="결제한 이용 요금 상품 고유 ID")

# -----------------------------------------------------------------------------
# [초보자 가이드 - 본사 요금제 관리 CRUD API]
# -----------------------------------------------------------------------------
@router.post("/products", response_model=BillingProductResponse, status_code=status.HTTP_201_CREATED, summary="본사 이용 요금 상품 추가 (관리자 전용)")
def create_billing_product(
    product_data: BillingProductCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 권한 검증: DEV, HEAD, MASTER 상위 관리자만 요금제 생성을 허용합니다.
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER]:
        raise HTTPException(status_code=403, detail="요금제 상품을 관리할 권한이 없습니다.")
    
    new_product = BillingProduct(
        name=product_data.name,
        amount=product_data.amount,
        billing_type=product_data.billing_type,
        period_months=product_data.period_months,
        is_active=True
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/products", response_model=List[BillingProductResponse], summary="전체 이용 요금제 상품 조회")
def get_billing_products(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 일반 점주(MANAGER)는 활성화된 상품만 조회 가능, 관리자는 전체 조회 가능
    if current_user.role in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER]:
        stmt = select(BillingProduct).order_by(BillingProduct.id.asc())
    else:
        stmt = select(BillingProduct).where(BillingProduct.is_active == True).order_by(BillingProduct.id.asc())
        
    return db.scalars(stmt).all()

@router.patch("/products/{product_id}", response_model=BillingProductResponse, summary="이용 요금제 상품 수정 및 토글 (관리자 전용)")
def update_billing_product(
    product_id: int,
    product_data: BillingProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER]:
        raise HTTPException(status_code=403, detail="요금제 상품을 수정할 권한이 없습니다.")
        
    product = db.get(BillingProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="해당 요금제 상품을 찾을 수 없습니다.")
        
    # 수정할 값이 전달된 필드만 반영합니다.
    if product_data.name is not None: product.name = product_data.name
    if product_data.amount is not None: product.amount = product_data.amount
    if product_data.billing_type is not None: product.billing_type = product_data.billing_type
    if product_data.period_months is not None: product.period_months = product_data.period_months
    if product_data.is_active is not None: product.is_active = product_data.is_active
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/products/{product_id}", summary="이용 요금제 상품 영구 삭제 (관리자 전용)")
def delete_billing_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER]:
        raise HTTPException(status_code=403, detail="요금제 상품을 삭제할 권한이 없습니다.")
        
    product = db.get(BillingProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="해당 요금제 상품을 찾을 수 없습니다.")
        
    db.delete(product)
    db.commit()
    return {"message": "요금제 상품이 성공적으로 영구 삭제되었습니다."}

# -----------------------------------------------------------------------------
# [초보자 가이드 - 정기 결제 카드 등록 및 자동결제 연동]
# 점주가 카드를 등록하면 포트원 V2를 통해 빌링키를 발급받고,
# 선택한 '정기결제 요금제' 기준 첫 달 결제 금액을 즉시 수납 처리한 뒤 개통합니다.
# -----------------------------------------------------------------------------
@router.post("/billing-key", response_model=BillingKeyResponse, summary="사용료 결제용 정기 결제 카드 등록 및 첫달 요금 결제")
async def register_billing_key(
    request: RegisterBillingKeyRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 1. 대상 키오스크 유효성 및 소유권 확인
    kiosk = db.get(Kiosk, request.kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크 기기를 찾을 수 없습니다.")
    if kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 소유의 키오스크 기기만 결제를 연동할 수 있습니다.")

    # 2. 선택 요금 상품 유효성 확인
    billing_product = db.get(BillingProduct, request.billing_product_id)
    if not billing_product:
        raise HTTPException(status_code=404, detail="선택하신 이용 요금제 상품을 찾을 수 없습니다.")
    if billing_product.billing_type != "REGULAR":
        raise HTTPException(status_code=400, detail="정기 구독용 상품이 아닙니다. 일반 단일 결제를 이용하세요.")

    try:
        # [모킹 또는 실 빌링키 등록]
        # V2 실연동 시에는 포트원 SDK를 거쳐 카드 정보를 토대로 빌링키를 생성합니다.
        # 테스트 환경이나 시크릿 키가 없는 경우 모킹 빌링키를 생성합니다.
        if PORTONE_API_SECRET and PORTONE_API_SECRET != "test_portone_secret":
            # 실무에서는 프론트엔드가 포트원 SDK를 띄워 빌링키 발급창을 띄우고
            # 완료 후 발급된 billingKey를 전달받거나, 백엔드에서 포트원 V2 빌링키 발급 API를 호출합니다.
            billing_key = f"PORTONE_BILLKEY_{uuid.uuid4().hex[:12].upper()}"
        else:
            billing_key = f"MOCK_BILLKEY_{uuid.uuid4().hex[:12].upper()}"

        # 3. [첫 달 이용료 즉시 선결제 승인]
        # 빌링키를 등록하면 즉시 1회차 자동 결제를 승인해 돈을 받아야 개통됩니다.
        payment_id = f"pay_sub_{uuid.uuid4().hex[:16]}"
        success = False
        approval_code = f"APP_{uuid.uuid4().hex[:8].upper()}"

        if PORTONE_API_SECRET and PORTONE_API_SECRET != "test_portone_secret":
            # 포트원 V2 빌링키 결제 승인 API 호출
            url = f"{PORTONE_API_URL}/payments/{payment_id}/billing-key"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"PortOne {PORTONE_API_SECRET}"
            }
            payload = {
                "billingKey": billing_key,
                "orderName": f"MOKI 서비스 이용 요금 - {billing_product.name}",
                "amount": {
                    "total": billing_product.amount
                },
                "currency": "KRW",
                "channelKey": PORTONE_CHANNEL_KEY
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload, timeout=10.0)
            
            if res.status_code == 200:
                res_data = res.json()
                approval_code = res_data.get("payment", {}).get("pgTxId") or approval_code
                success = True
            else:
                error_msg = res.json().get("message") or res.text
                logger.error(f"정기결제 첫달 선결제 실패: {error_msg}")
                raise ValueError(f"카드 승인 실패: {error_msg}")
        else:
            # Mock 결제 성공
            logger.info(f"[Mock] 첫달 요금 선결제 청구 성공: ID={payment_id}, 금액={billing_product.amount}원")
            success = True

        if success:
            # 4. 결제 성공 정보 기입 및 키오스크 개통 처리
            kiosk.billing_key = billing_key
            kiosk.payment_status = "NORMAL"
            kiosk.status = "OPERATING"
            # 다음 결제일은 해당 요금제의 period_months 개월 수만큼 뒤로 연장
            kiosk.next_payment_date = datetime.now() + timedelta(days=30 * billing_product.period_months)
            
            # 결제 이력(KioskBillingHistory) 추가
            history = KioskBillingHistory(
                kiosk_id=kiosk.id,
                billing_product_id=billing_product.id,
                billing_type="REGULAR",
                amount=billing_product.amount,
                status="SUCCESS",
                payment_date=datetime.now()
            )
            db.add(history)
            db.commit()
            db.refresh(kiosk)

            return BillingKeyResponse(
                success=True,
                kiosk_id=kiosk.id,
                billing_key=billing_key,
                message=f"[{billing_product.name}] 가입 및 카드 등록이 완료되었습니다. 다음 결제 예정일: {kiosk.next_payment_date.strftime('%Y-%m-%d')}"
            )
        else:
            raise ValueError("결제 승인 절차가 실패했습니다.")

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"정기결제 카드 연동 및 첫달 수납 실패: {str(e)}"
        )

# -----------------------------------------------------------------------------
# [초보자 가이드 - 단일 결제 검증 API (1회성 이용권)]
# 점주가 1개월, 3개월 등 단일결제 요금제 상품을 골라 일반 신용카드/간편결제로 결제하면
# 프론트엔드가 결제 ID를 받아 백엔드에 알려주고 백엔드가 검증하여 기간을 연장합니다.
# -----------------------------------------------------------------------------
@router.post("/onetime-verify", summary="점주 이용 요금제 1회성 단일 결제 검증 및 기간 연장")
async def verify_onetime_subscription(
    request: OnetimeVerifyRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    kiosk = db.get(Kiosk, request.kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크 기기를 찾을 수 없습니다.")
    if kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 소유의 키오스크 기기만 결제할 수 있습니다.")

    billing_product = db.get(BillingProduct, request.billing_product_id)
    if not billing_product:
        raise HTTPException(status_code=404, detail="선택 요금제 상품을 찾을 수 없습니다.")
    if billing_product.billing_type != "ONETIME":
        raise HTTPException(status_code=400, detail="단일 결제 상품이 아닙니다. 정기구독(빌링키) 메뉴를 이용하세요.")

    try:
        # 포트원 V2 API를 통해 결제 내역의 무결성을 조회 검증합니다.
        # (금액 변조 대조 검증 포함)
        verified = await verify_portone_payment(request.payment_id, billing_product.amount)

        if verified["status"] == "PAID":
            # 1회성 결제이므로 기존 빌링키가 있었다면 구독이 자동 해지된 것으로 간주하여 지워줍니다.
            kiosk.billing_key = None
            kiosk.payment_status = "NORMAL"
            kiosk.status = "OPERATING"

            # 기간 연장 연산: 
            # 기존 다음 결제 예정일이 아직 남아있고 미래 시점이라면 그 날짜에 더해주고,
            # 이미 지났거나 없는 경우 오늘 날짜 기준으로 더해줍니다.
            base_date = kiosk.next_payment_date if (kiosk.next_payment_date and kiosk.next_payment_date > datetime.now()) else datetime.now()
            kiosk.next_payment_date = base_date + timedelta(days=30 * billing_product.period_months)

            # 결제 이력 등록
            history = KioskBillingHistory(
                kiosk_id=kiosk.id,
                billing_product_id=billing_product.id,
                billing_type="ONETIME",
                amount=billing_product.amount,
                status="SUCCESS",
                payment_date=datetime.now()
            )
            db.add(history)
            db.commit()

            return {
                "success": True,
                "message": f"[{billing_product.name}] 결제 검증이 완료되었습니다. 서비스 만료 예정일: {kiosk.next_payment_date.strftime('%Y-%m-%d')}"
            }
        else:
            raise ValueError(f"포트원 승인 상태가 PAID(완료)가 아닙니다. (현재 상태: {verified['status']})")

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"단일 결제 검증 및 이용권 부여 실패: {str(e)}"
        )

# -----------------------------------------------------------------------------
# [초보자 가이드 - 수동 강제 수납 (연체/정지 해제용)]
# -----------------------------------------------------------------------------
@router.post("/charge", response_model=ChargeResponse, summary="사용료 수동 수납/결제 승인 테스트")
async def charge_subscription(
    request: ChargeSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    kiosk = db.get(Kiosk, request.kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크 기기를 찾을 수 없습니다.")
    if kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 소유의 키오스크 기기만 결제할 수 있습니다.")
    if not kiosk.billing_key:
        raise HTTPException(status_code=400, detail="등록된 결제 카드가 없습니다. 먼저 카드를 등록해주세요.")
        
    try:
        # 가맹점 월 정기 이용료 요금제 정보(29000원 등)를 조회합니다.
        # 만약 바인딩된 상품 기록이 유실되었을 경우를 대비해 33,000원을 기본값으로 제공합니다.
        amount = 33000
        order_name = "MOKI 키오스크 월 이용료"

        # 최근 결제 히스토리에서 상품 금액을 추적
        stmt = select(KioskBillingHistory).where(KioskBillingHistory.kiosk_id == kiosk.id).order_by(KioskBillingHistory.id.desc()).limit(1)
        last_history = db.execute(stmt).scalar_one_or_none()
        if last_history and last_history.product:
            amount = last_history.product.amount
            order_name = f"MOKI 서비스 이용 요금 - {last_history.product.name}"

        payment_id = f"pay_sub_{uuid.uuid4().hex[:16]}"
        approval_code = f"SU{datetime.now().strftime('%y%m%d')}"

        if PORTONE_API_SECRET and PORTONE_API_SECRET != "test_portone_secret":
            # [포트원 V2 실 결제 승인 요청]
            url = f"{PORTONE_API_URL}/payments/{payment_id}/billing-key"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"PortOne {PORTONE_API_SECRET}"
            }
            payload = {
                "billingKey": kiosk.billing_key,
                "orderName": order_name,
                "amount": {
                    "total": amount
                },
                "currency": "KRW",
                "channelKey": PORTONE_CHANNEL_KEY
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload, timeout=10.0)
                
            if res.status_code == 200:
                res_data = res.json()
                approval_code = res_data.get("payment", {}).get("pgTxId") or approval_code
            else:
                error_msg = res.json().get("message") or res.text
                raise ValueError(error_msg)
        else:
            # [모킹 로직]
            approval_code = f"SU{datetime.now().strftime('%y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            logger.info(f"[Mock] 수동 빌링 청구 성공: ID={payment_id}, 금액={amount}원")
        
        # 결제 성공 시 기기 활성화
        kiosk.payment_status = "NORMAL"
        kiosk.status = "OPERATING"
        kiosk.next_payment_date = datetime.now() + timedelta(days=30)
        
        # 히스토리 적재
        history = KioskBillingHistory(
            kiosk_id=kiosk.id,
            billing_product_id=last_history.billing_product_id if last_history else None,
            billing_type="REGULAR",
            amount=amount,
            status="SUCCESS",
            payment_date=datetime.now()
        )
        db.add(history)
        db.commit()
        db.refresh(kiosk)
        
        return ChargeResponse(
            success=True,
            kiosk_id=kiosk.id,
            amount=amount,
            approval_code=approval_code,
            message="키오스크 사용료 수동 결제 승인이 완료되었습니다. 기기가 가동 상태로 활성화됩니다."
        )
        
    except Exception as e:
        db.rollback()
        
        # 실패 이력도 히스토리에 기재합니다.
        history = KioskBillingHistory(
            kiosk_id=kiosk.id,
            billing_product_id=last_history.billing_product_id if last_history else None,
            billing_type="REGULAR",
            amount=amount,
            status="FAILED",
            error_message=str(e),
            payment_date=datetime.now()
        )
        db.add(history)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"결제 승인 중 오류 발생: {str(e)}"
        )

# -----------------------------------------------------------------------------
# [초보자 가이드 - 정기결제 해지]
# -----------------------------------------------------------------------------
@router.delete("/{kiosk_id}", summary="정기결제 해지 (카드 정보 삭제)")
async def cancel_subscription(
    kiosk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    kiosk = db.get(Kiosk, kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크 기기를 찾을 수 없습니다.")
    if kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 소유의 키오스크 기기만 해지할 수 있습니다.")
        
    try:
        kiosk.billing_key = None
        # 정기 결제 카드를 지우면 다음 결제 시점에 돈이 안 들어오므로 WAITING 정지 예정으로 변환됩니다.
        kiosk.payment_status = "UNPAID"
        kiosk.status = "WAITING"
        kiosk.next_payment_date = None
        
        db.commit()
        return {"success": True, "message": "정기결제 카드가 성공적으로 삭제되었으며 사용이 정지됩니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
