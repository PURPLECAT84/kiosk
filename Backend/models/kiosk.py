from sqlalchemy import text, String, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.store import Store
    from models.product import Product
    from models.category import Category
    from models.kiosk_admin import KioskAdmin

class Kiosk(Base):
    __tablename__ = "kiosks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True) # 키오스크 고유아이디
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False) # 고유코드 (8자리)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False) # 매장 고유아이디
    name: Mapped[str] = mapped_column(String(50), nullable=False) # 키오스크명
    model_name: Mapped[str] = mapped_column(String(50), nullable=True) # 모델명
    type: Mapped[str] = mapped_column(String(20), default="Store", nullable=False) # Type (Store / Restaurant)
    status: Mapped[str] = mapped_column(String(20), default="WAITING", nullable=False) # 상태 (OPERATING / WAITING)
    payment_status: Mapped[str] = mapped_column(String(20), default="NORMAL", nullable=False) # 결제상태 (NORMAL / UNPAID)
    next_payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True) # 다음결제일
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()")) # 생성일

    store: Mapped["Store"] = relationship("Store", back_populates="kiosks")
    products = relationship("Product", back_populates="kiosk", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="kiosk", cascade="all, delete-orphan")
    kiosk_admins = relationship("KioskAdmin", back_populates="kiosk", cascade="all, delete-orphan")
