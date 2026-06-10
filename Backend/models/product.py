from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.kiosk import Kiosk
    from models.shelve import Shelve
    from models.category import Category
    from models.order_item import OrderItem

class Product(Base):
    __tablename__ = "product_list"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("product_category.id"), nullable=False) 
    kiosk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kiosks.id", ondelete="CASCADE"), nullable=False) # 기기 귀속을 위한 외래키
    shelve_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shelve_info.id"), nullable=False)
    barcode: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    created_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    image: Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0) # 남은 재고 수량
    stock_managed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 재고 관리 ON/OFF 설정 (추가)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # 강제 판매중단 스위치 (True/False)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None) # 유통기한
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # 노출 순서 정렬용 필드

    shelve = relationship("Shelve", back_populates="products")
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    kiosk: Mapped["Kiosk"] = relationship("Kiosk", back_populates="products")