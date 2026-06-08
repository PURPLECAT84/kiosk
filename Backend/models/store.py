from sqlalchemy import text, String, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import UserInfo
    from models.kiosk import Kiosk

class Store(Base):
    __tablename__ = "stores"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True) # 매장 고유아이디
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False) # 고유코드 (6자리)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_info.id"), nullable=False) # 회원 고유아이디
    type: Mapped[str] = mapped_column(String, nullable=False) # 매장 타입 (e.g. Store / Restaurant)
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True) # 매장 이름
    owner_name: Mapped[str] = mapped_column(String(50), nullable=True) # 점주명
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False) # 상태 (ACTIVE / INACTIVE)
    address: Mapped[str] = mapped_column(String, nullable=False) # 매장 주소
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()")) # 매장 등록일

    owner: Mapped["UserInfo"] = relationship("UserInfo", foreign_keys=[user_id], back_populates="owned_stores")
    staff_members: Mapped[List["UserInfo"]] = relationship("UserInfo", foreign_keys="[UserInfo.store_id]", back_populates="store")

    shelves = relationship("Shelve", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    kiosks = relationship("Kiosk", back_populates="store", cascade="all, delete-orphan")
