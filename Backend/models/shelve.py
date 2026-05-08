from sqlalchemy import String, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.types import Uuid #<- 테이블에 저장 될 UUID 라는 타입 선언
from datetime import datetime


class Shelve(Base):
    __tablename__ = "shelve_info"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default = uuid.uuid4, index = True)
    store_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("store_info.id"), nullable = False) 
    name : Mapped[str] = mapped_column(String(30), nullable = False)
    terminal_id : Mapped[str] = mapped_column(String, nullable = False)
    business_number : Mapped[str] = mapped_column(String, nullable = False)
    vender_code : Mapped[str] = mapped_column(String, nullable = False)

    store = relationship("Store", back_populates = "shelves")
    categories = relationship("Category", back_populates = "shelve", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="shelve", cascade="all, delete-orphan")