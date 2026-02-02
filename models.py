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

""" sqlalchemy 2.0 방식, 자동완성기능과 검증 측면에서 우수, But 기존 대비 코드가 복잡함"""

class Store(Base):
    __tablename__ = "store_info"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default = uuid.uuid4, index = True)
    type : Mapped[str] = mapped_column(String, nullable = False) 
    name : Mapped[str] = mapped_column(String(30), nullable = False, unique = True)
    address : Mapped[str] = mapped_column(String, nullable = False)
    created_date : Mapped[datetime] = mapped_column(DateTime, nullable = False, default = datetime.now)

    shelves = relationship("Shelve", back_populates = "store") 



class Shelve(Base):
    __tablename__ = "shelve_info"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default = uuid.uuid4, index = True)
    store_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("store_info.id"), nullable = False) 
    name : Mapped[str] = mapped_column(String(30), nullable = False)
    terminal_id : Mapped[str] = mapped_column(String, nullable = False)
    business_number : Mapped[str] = mapped_column(String, nullable = False)
    vender_code : Mapped[str] = mapped_column(String, nullable = False)

    store = relationship("Store", back_populates = "shelves")
    categories = relationship("Category", back_populates = "shelve")
 

class Category(Base):
    __tablename__ = "product_category"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    shelve_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("shelve_info.id"), nullable = False)
    name : Mapped[str] = mapped_column(String, nullable = False) 

    shelve = relationship("Shelve", back_populates = "categories")
    product = relationship("Product", back_populates = "category")


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
   

