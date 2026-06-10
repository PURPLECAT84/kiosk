from sqlalchemy import String, ForeignKey, Integer, DateTime
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from models.store import Store
    from models.order_item import OrderItem
    from models.kiosk import Kiosk

class Order(Base):
    __tablename__ = "order_info"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_no: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True) # 주문번호 필드 (추가)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False)
    kiosk_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("kiosks.id", ondelete="SET NULL"), nullable=True) # 기기 귀속을 위한 외래키
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=False)
    payment_provider: Mapped[str] = mapped_column(String, nullable=False)
    approval_code: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Completed")
    created_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)    
    refund_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 환불 금액 (추가)
    refund_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True) # 환불 사유 (추가)
    refund_method: Mapped[Optional[str]] = mapped_column(String, nullable=True) # 환불 방법 (추가)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True) # 환불 일시 (추가)

    store = relationship("Store", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    kiosk = relationship("Kiosk")