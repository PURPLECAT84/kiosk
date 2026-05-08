from sqlalchemy import String,ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.types import Uuid #<- 테이블에 저장 될 UUID 라는 타입 선언



class Category(Base):
    __tablename__ = "product_category"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    shelve_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("shelve_info.id"), nullable = False)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("store_info.id"), nullable=False)
    name : Mapped[str] = mapped_column(String, nullable = False) 

    shelve = relationship("Shelve", back_populates = "categories")
    products = relationship("Product", back_populates = "category", cascade="all, delete-orphan")
