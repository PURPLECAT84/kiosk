import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class KioskAdmin(Base):
    """
    [초보자용 교보재 지침 - 다대다 관계 테이블]
    하나의 키오스크를 여러 관리자(사장님, 알바생, 본사 직원 등)가 동시에 관리하고,
    반대로 하나의 사용자가 여러 키오스크를 스위칭하며 관리할 수 있도록 
    키오스크와 유저 간의 다대다(N:M) 연동 관계를 매핑하는 테이블입니다.
    """
    __tablename__ = "kiosk_admins"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kiosk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kiosks.id", ondelete="CASCADE"), nullable=False) # 관리 대상 키오스크 ID
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_info.id", ondelete="CASCADE"), nullable=False) # 관리자 유저 ID
    role: Mapped[str] = mapped_column(String(20), nullable=False) # 이 기기에 대한 이 사용자의 개별 관리 권한 (DEV, HEAD, MASTER, MANAGER, STAFF)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    # 관계 설정 (SQLAlchemy ORM 백필드 매핑)
    kiosk: Mapped["Kiosk"] = relationship("Kiosk", back_populates="kiosk_admins")
    user: Mapped["UserInfo"] = relationship("UserInfo")
