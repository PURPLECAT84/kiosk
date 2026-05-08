from sqlalchemy import text, String, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.types import Uuid #<- 테이블에 저장 될 UUID 라는 타입 선언
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import UserInfo

class Store(Base):
    __tablename__ = "store_info"
    id : Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)#매장 고유아이디
    user_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("user_info.id"), nullable = False)#회원 고유아이디
    type : Mapped[str] = mapped_column(String, nullable = False) #매장 타입
    name : Mapped[str] = mapped_column(String(30), nullable = False, unique = True)#매장 이름
    address : Mapped[str] = mapped_column(String, nullable = False)#매장 주소
    # 3. func.now()를 사용하여 DB 서버 시간 기준으로 통일
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))#매장 등록일,서버시간에 맞춤

    owner: Mapped["UserInfo"] = relationship("UserInfo", foreign_keys=[user_id], back_populates="owned_stores")
    staff_members: Mapped[List["UserInfo"]] = relationship("UserInfo", foreign_keys="[UserInfo.store_id]", back_populates="store")

    shelves = relationship("Shelve", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")

