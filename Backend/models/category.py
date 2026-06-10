from sqlalchemy import String, ForeignKey, Integer
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.kiosk import Kiosk
    from models.shelve import Shelve
    from models.product import Product

class Category(Base):
    __tablename__ = "product_category"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shelve_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shelve_info.id"), nullable=False)
    kiosk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kiosks.id", ondelete="CASCADE"), nullable=False) # 기기 귀속을 위한 외래키
    name: Mapped[str] = mapped_column(String, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # 노출 순서 정렬용 필드

    shelve = relationship("Shelve", back_populates="categories")
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
    kiosk: Mapped["Kiosk"] = relationship("Kiosk", back_populates="categories")
