from sqlalchemy import Integer, String, DateTime
from database import Base
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from sqlalchemy.types import Uuid #<- 테이블에 저장 될 UUID 라는 타입 선언
from datetime import datetime


class User(Base):
    __tablename__ = "user_info"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default = uuid.uuid4, index = True)
    email : Mapped[str] = mapped_column(String, nullable = False, unique = True) #중복불가, 고유갑 입력 설정
    password : Mapped[str] = mapped_column(String, nullable = False)
    name : Mapped[str] = mapped_column(String(30), nullable = False) #문자길이 정의가 필요 없다면 데이터 형식 뒷부분 생략 가능
    phone : Mapped[str] = mapped_column(String(20), nullable = False)
    address : Mapped[str] = mapped_column(String(100), nullable = False)
    authority : Mapped[str] = mapped_column(String(20), nullable = False, default = "manager") #기본값 설정
    joined_date : Mapped[datetime   ] = mapped_column(DateTime, nullable = False, default = datetime.now)

""" sqlalchemy 2.0 방식, 자동완성기능과 검증 측면에서 우수, But 기존 대비 코드가 복잡함"""