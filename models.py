from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    joined_date : Mapped[datetime] = mapped_column(DateTime, nullable = False, default = datetime.now)

    store_authority_join = relationship("Store", back_populates = "ownership", cascade="all, delete-orphan") 
    
    
    """cascade 옵션 추가 user가 삭제되면 연결된 store_info도 같이 삭제됨
    cascade="all, delete-orphan"의 의미:

all: 부모에게 일어나는 모든 상태 변화(삭제, 병합 등)를 자식에게도 전파.

delete-orphan: 부모와의 연결이 끊어진(리스트에서 pop되거나 부모가 삭제된) 자식을 "고아"로 취급하여 DB에서 완전히 삭제(DELETE)함.

주의: 이 설정이 적용되면 User 한 명을 삭제하는 순간, 그 유저가 가진 매장, 선반, 카테고리, 상품 수천 개가 한 번에 DB에서 사라짐. 복구가 불가능하니 운영 환경에서는 신중해야 함. 
(실무에서는 보통 is_active=False 처리하는 'Soft Delete'를 많이 씁니다.) 지금 개발 단계에서는 데이터 무결성을 유지하면서 깔끔하게 지우기 위해 모든 단계에 적용"""



""" sqlalchemy 2.0 방식, 자동완성기능과 검증 측면에서 우수, But 기존 대비 코드가 복잡함"""

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
 

class Category(Base):
    __tablename__ = "product_category"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    shelve_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("shelve_info.id"), nullable = False)
    name : Mapped[str] = mapped_column(String, nullable = False) 

    shelve = relationship("Shelve", back_populates = "categories")
    product = relationship("Product", back_populates = "category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "product_list"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default = uuid.uuid4, index = True)
    category_id :Mapped[int] = mapped_column(ForeignKey("product_category.id"), nullable = False ) 
    barcode : Mapped[str] = mapped_column(String, nullable = True, unique = True)
    name : Mapped[str] = mapped_column(String, nullable = False)
    price : Mapped[int] = mapped_column(Integer, nullable = False)
    buy_from: Mapped[str] = mapped_column(String,nullable = True )
    created_date : Mapped[datetime] = mapped_column(DateTime, nullable = False, default = datetime.now)

    category = relationship("Category", back_populates = "product")


"""
[ForeignKey 클래스]

예시) category_id :Mapped[int] = mapped_column(ForeignKey("product_category.id"), nullable = False )

1. Mapped[int] 연결할 데이터 타입과 일치시켜야함
2. product_category.id" : 연결할 테이블명.열 이름


[relationship 함수]

예시) shelve = relationship("Shelve", back_populates = "categories")
1. shelve : relationship 전용 변수명
2. "Shelve" : 관계(부/자) 를 맺고자 하는 클래스명
3. back_populates = "categories" :  관계(부/자) 에서 정의 한 전용 변수

""" 
   

