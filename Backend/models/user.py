import enum
import uuid
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from database import Base

# 순환 참조 에러 방지용 가짜 import!
if TYPE_CHECKING:
    from models.kiosk import Kiosk

# 2. Enum 정의 (Python 표준 라이브러리 사용)
class UserRole(str, enum.Enum):
    DEV = "DEV" # 개발자
    HEAD = "HEAD" # 본사
    MASTER = "MASTER" # 관리자
    MANAGER = "MANAGER" # 점주
    STAFF = "STAFF" # 직원
    NONE = "NONE" # 권한 없음

class UserStatus(str, enum.Enum):
    PENDING = "PENDING" # 승인 대기
    ACTIVE = "ACTIVE" # 활성
    BANNED = "BANNED" # 정지

# 👤 유저 기본 정보 테이블
class UserInfo(Base):
    __tablename__ = "user_info"
    """회원 가입 / 로그인 시 필수(자동) 입력"""
    # mapped_column을 사용하여 더 직관적으로 정의
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) #회원 고유아이디
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False) #이메일
    password: Mapped[str] = mapped_column(String(255), nullable=False) #비밀번호 (해시)
    name: Mapped[str] = mapped_column(String(50), nullable=False) #이름
    phone: Mapped[str] = mapped_column(String(20)) #전화번호
    is_business_verified: Mapped[bool] = mapped_column(Boolean, default=False) #사업자 확인여부
    is_identity_verified: Mapped[bool] = mapped_column(Boolean, default=False) #본인 확인여부
    ci: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True) #본인확인 고유값 (CI)
    di: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) #중복가입 확인값 (DI)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )#가입일,서버시간에 맞춤

    """회원 가입 시 필수 아님, HEAD, MASTER와 같은 상위 권한자가 매장 등록(활성화) 시 수정 및 입력"""
    # Enum 적용
    role: Mapped[UserRole] = mapped_column(default=UserRole.NONE) #권한
    status: Mapped[UserStatus] = mapped_column(default=UserStatus.PENDING) #상태
    portone_store_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 점주 개별 포트원 Store ID
    portone_channel_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 점주 개별 포트원 Channel Key
   

    # 관계 설정 (1:N)
    businesses: Mapped[List["BusinessInfo"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    kiosks: Mapped[List["Kiosk"]] = relationship(
        "Kiosk", foreign_keys="[Kiosk.user_id]", back_populates="owner", cascade="all, delete-orphan"
    )


# 🏢 사업자 등록 정보 테이블
class BusinessInfo(Base):
    __tablename__ = "business_info"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)#사업자 고유아이디
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_info.id", ondelete="CASCADE"))#회원 고유아이디
    
    business_number: Mapped[str] = mapped_column(String(20), unique=True)#사업자 번호
    business_name: Mapped[str] = mapped_column(String(100), nullable=False)#사업자명
    representative_name: Mapped[str] = mapped_column(String(50))#대표자 이름
    representative_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)#대표자 전화번호
    store_name: Mapped[str] = mapped_column(String(100), nullable=False)#설치매장명
    
    document_url: Mapped[Optional[str]] = mapped_column(String)#사업자등록증 이미지 파일 경로
    is_verified: Mapped[bool] = mapped_column(default=False)#사업자 확인여부
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )#사업자 등록일,서버시간에 맞춤

    # 관계 설정 (N:1)
    owner: Mapped["UserInfo"] = relationship(back_populates="businesses")