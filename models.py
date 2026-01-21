from sqlalchemy import Integer, String
from database import Base
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "user_info"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    email : Mapped[str] = mapped_column(nullable = False, unique = True) #중복불가, 고유갑 입력 설정
    name : Mapped[str] = mapped_column(String(30), nullable = False) #문자길이 정의가 필요 없다면 데이터 형식 뒷부분 생략 가능
    phone : Mapped[str] = mapped_column(String(20), nullable = False)
    address : Mapped[str] = mapped_column(String(100), nullable = False)
    authority : Mapped[str] = mapped_column(String(20), nullable = False, default = "manager") #기본값 설정

""" sqlalchemy 2.0 방식, 자동완성기능과 검증 측면에서 우수, But 기존 대비 코드가 복잡함"""