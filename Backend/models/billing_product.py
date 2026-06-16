# Backend/models/billing_product.py
from sqlalchemy import text, String, DateTime, ForeignKey, Integer, Boolean
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import datetime
from typing import Optional

# -----------------------------------------------------------------------------
# [초보자 가이드 - BillingProduct 모델]
# MOKI 본사가 등록해 둔 키오스크 월 이용료 상품 요금제 테이블입니다.
# 예: 1개월 단일권 (35,000원), 3개월 단일권 (100,000원), 월 정기결제 (29,000원) 등
# -----------------------------------------------------------------------------
class BillingProduct(Base):
    __tablename__ = "billing_products"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True) # 상품 고유번호
    name: Mapped[str] = mapped_column(String(100), nullable=False) # 요금제 이름
    amount: Mapped[int] = mapped_column(Integer, nullable=False) # 요금제 가격 (원)
    billing_type: Mapped[str] = mapped_column(String(20), default="REGULAR", nullable=False) # 결제 방식 ("REGULAR": 정기구독, "ONETIME": 1회성 결제)
    period_months: Mapped[int] = mapped_column(Integer, default=1, nullable=False) # 이용 가능 개월 수 (예: 1개월, 3개월 등)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 요금제 활성화 상태 (점주에게 노출 여부)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()")) # 생성일자

    # 관계 설정 (요금 상품 ➔ 결제 히스토리 간 1:N 관계)
    histories = relationship("KioskBillingHistory", back_populates="product")

# -----------------------------------------------------------------------------
# [초보자 가이드 - KioskBillingHistory 모델]
# 특정 키오스크 기기에 대해 점주가 이용 요금을 결제한 역사(히스토리)를 보존하는 테이블입니다.
# 정기 결제 결제일, 결제 결과, 영수증 금액 등을 기록합니다.
# -----------------------------------------------------------------------------
class KioskBillingHistory(Base):
    __tablename__ = "kiosk_billing_histories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True) # 히스토리 일련번호
    kiosk_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("kiosks.id", ondelete="SET NULL"), nullable=True) # 대상 키오스크 고유아이디 (키오스크가 삭제되어도 내역은 보존)
    billing_product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("billing_products.id", ondelete="SET NULL"), nullable=True) # 선택했던 요금 상품 번호 (상품이 삭제되어도 내역은 보존)
    
    billing_type: Mapped[str] = mapped_column(String(20), nullable=False) # 결제 방식 ("REGULAR" / "ONETIME")
    amount: Mapped[int] = mapped_column(Integer, nullable=False) # 실제 결제한 최종 금액 (할인이 적용된 경우 실 결제 금액)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS", nullable=False) # 결제 처리 상태 ("SUCCESS": 완료, "FAILED": 실패)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # 결제 실패 시 오류 사유 기록
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()")) # 결제 발생 일시
    
    promotion_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 사용된 프로모션(할인) 코드
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # 할인받은 금액

    # 관계 설정
    product = relationship("BillingProduct", back_populates="histories")
    kiosk = relationship("Kiosk")
