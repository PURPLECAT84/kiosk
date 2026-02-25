from sqlalchemy import Integer, String, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.types import Uuid #<- 테이블에 저장 될 UUID 라는 타입 선언
from datetime import datetime

class Store(Base):
    __tablename__ = "store_info"
    id : Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    user_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("user_info.id"), nullable = False)
    type : Mapped[str] = mapped_column(String, nullable = False) 
    name : Mapped[str] = mapped_column(String(30), nullable = False, unique = True)
    address : Mapped[str] = mapped_column(String, nullable = False)
    created_date : Mapped[datetime] = mapped_column(DateTime, nullable = False, default = datetime.now)
   
    shelves = relationship("Shelve", back_populates = "store",cascade="all, delete-orphan")
    ownership = relationship("User", back_populates="store_authority_join")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")

