# Backend/schemas/billing_product.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# -----------------------------------------------------------------------------
# [초보자 가이드 - BillingProductCreate 스키마]
# 본사 관리자가 신규 요금 상품을 추가할 때 클라이언트(프론트엔드)가 전달하는 데이터 명세입니다.
# -----------------------------------------------------------------------------
class BillingProductCreate(BaseModel):
    name: str # 예: "월 정기 구독", "3개월 단일권"
    amount: int # 결제 금액 (원)
    billing_type: str # 결제 타입 ("REGULAR" 혹은 "ONETIME")
    period_months: int # 사용 가능 개월 수 (예: 1, 3, 12 등)

# -----------------------------------------------------------------------------
# [초보자 가이드 - BillingProductUpdate 스키마]
# 요금제 상품의 정보를 유연하게 수정할 때 사용되는 데이터 명세입니다.
# -----------------------------------------------------------------------------
class BillingProductUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[int] = None
    billing_type: Optional[str] = None
    period_months: Optional[int] = None
    is_active: Optional[bool] = None

# -----------------------------------------------------------------------------
# [초보자 가이드 - BillingProductResponse 스키마]
# 요금 상품 정보를 조회 시, DB 모델 객체를 Pydantic DTO로 바인딩하여 최종 반환하는 응답 명세입니다.
# -----------------------------------------------------------------------------
class BillingProductResponse(BaseModel):
    id: int
    name: str
    amount: int
    billing_type: str
    period_months: int
    is_active: bool
    created_at: datetime

    # SQLAlchemy 2.0 모델과의 자동 데이터 직렬화를 지원하도록 설정합니다.
    model_config = ConfigDict(from_attributes=True)
