from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.kiosk import Kiosk
from models.user import UserInfo
from core.dependency import get_current_user
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import httpx
from core.security import PORTONE_API_SECRET, PORTONE_CHANNEL_KEY, PORTONE_API_URL

router = APIRouter(
    prefix="/subscribe",
    tags=["Kiosk Subscription Billing (사용료 결제)"]
)

class RegisterBillingKeyRequest(BaseModel):
    kiosk_id: uuid.UUID = Field(..., description="정기결제를 연동할 키오스크 ID")
    customer_uid: str = Field(..., description="포트원 빌링키 식별자 (점주 카드 고유 해시)")

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

@router.post("/billing-key", response_model=BillingKeyResponse, summary="사용료 결제용 정기 결제 카드 등록 (빌링키 발급)")
async def register_billing_key(
    request: RegisterBillingKeyRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    점주가 포트원 결제창을 통해 카드 정보를 입력하여 빌링키를 발급받으면,
    이를 특정 키오스크 기기에 귀속시키고 키오스크를 즉시 활성화(OPERATING, NORMAL) 상태로 개통합니다.
    """
    # 1. 키오스크 소유권 검증
    kiosk = db.get(Kiosk, request.kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크 기기를 찾을 수 없습니다.")
        
    if kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 소유의 키오스크 기기만 정기 결제를 연동할 수 있습니다.")
        
    try:
        # [모킹 로직] 포트원 API 연동 전까지 가상 빌링키 발급
        # 실제 API 호출 시: billing_key = portone.request_billing_key(customer_uid)
        mock_billing_key = f"MOCK_BILLKEY_{uuid.uuid4().hex[:12].upper()}"
        
        # 2. 키오스크 결제 정보 등록 및 활성화 상태 변경
        kiosk.billing_key = mock_billing_key
        kiosk.payment_status = "NORMAL"
        kiosk.status = "OPERATING"
        kiosk.next_payment_date = datetime.now() + timedelta(days=30) # 30일 뒤 결제 예정
        
        db.commit()
        db.refresh(kiosk)
        
        return BillingKeyResponse(
            success=True,
            kiosk_id=kiosk.id,
            billing_key=mock_billing_key,
            message="사용료 결제 카드가 성공적으로 등록되었으며, 기기가 정상 가동됩니다."
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"정기결제 카드 등록 중 오류 발생: {str(e)}"
        )

@router.post("/charge", response_model=ChargeResponse, summary="사용료 수동 수납/결제 승인 테스트")
async def charge_subscription(
    request: ChargeSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    연체 등으로 인해 정지된 키오스크 기기에 대해, 등록된 빌링키를 사용하여 수동으로 사용료(예: 33,000원)를 결제 및 재기동합니다.
    """
    kiosk = db.get(Kiosk, request.kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크 기기를 찾을 수 없습니다.")
        
    if kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 소유의 키오스크 기기만 결제할 수 있습니다.")
        
    if not kiosk.billing_key:
        raise HTTPException(status_code=400, detail="등록된 결제 카드가 없습니다. 먼저 카드를 등록해주세요.")
        
    try:
        if PORTONE_API_SECRET and PORTONE_API_SECRET != "test_portone_secret":
            # [포트원 V2 실 결제 승인 요청]
            payment_id = f"pay_sub_{uuid.uuid4().hex[:16]}"
            url = f"{PORTONE_API_URL}/payments/{payment_id}/billing-key"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"PortOne {PORTONE_API_SECRET}"
            }
            payload = {
                "billingKey": kiosk.billing_key,
                "orderName": "MOKI 키오스크 월 이용료",
                "amount": {
                    "total": 33000
                },
                "currency": "KRW",
                "channelKey": PORTONE_CHANNEL_KEY
            }
            
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload, timeout=10.0)
                
            if res.status_code == 200:
                res_data = res.json()
                approval_code = res_data.get("payment", {}).get("pgTxId") or f"SU{datetime.now().strftime('%y%m%d')}"
            else:
                try:
                    error_msg = res.json().get("message") or res.text
                except Exception:
                    error_msg = res.text
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"포트원 승인 실패: {error_msg}"
                )
        else:
            # [모킹 로직] 포트원 빌링키 기반 결제 요청
            approval_code = f"SU{datetime.now().strftime('%y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # 결제 성공 시 기기 활성화
        kiosk.payment_status = "NORMAL"
        kiosk.status = "OPERATING"
        kiosk.next_payment_date = datetime.now() + timedelta(days=30)
        
        db.commit()
        db.refresh(kiosk)
        
        return ChargeResponse(
            success=True,
            kiosk_id=kiosk.id,
            amount=33000, # 예시 한달 정액 사용료 33,000원
            approval_code=approval_code,
            message="키오스크 사용료 결제 승인이 완료되었습니다. 기기가 운영 상태로 활성화됩니다."
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"결제 승인 중 오류 발생: {str(e)}"
        )

@router.delete("/{kiosk_id}", summary="정기결제 해지 (카드 정보 삭제)")
async def cancel_subscription(
    kiosk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    점주가 해당 키오스크의 정기 결제를 해지합니다. 카드 정보(빌링키)가 영구 제거되며, 다음 기기 동기화 시 정지 상태가 됩니다.
    """
    kiosk = db.get(Kiosk, kiosk_id)
    if not kiosk:
        raise HTTPException(status_code=404, detail="해당 키오스크 기기를 찾을 수 없습니다.")
        
    if kiosk.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인 소유의 키오스크 기기만 해지할 수 있습니다.")
        
    try:
        kiosk.billing_key = None
        kiosk.payment_status = "UNPAID"
        kiosk.status = "WAITING"
        kiosk.next_payment_date = None
        
        db.commit()
        return {"success": True, "message": "정기결제 카드가 삭제되었으며 사용이 정지됩니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
