from sqlalchemy import Integer, String, DateTime, ForeignKey,Boolean
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.types import Uuid #<- 테이블에 저장 될 UUID 라는 타입 선언
from datetime import datetime


class Product(Base):
    __tablename__ = "product_list"
    id : Mapped[uuid.UUID] = mapped_column(primary_key = True, default = uuid.uuid4, index = True)
    category_id :Mapped[int] = mapped_column(ForeignKey("product_category.id"), nullable = False ) 
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("store_info.id"), nullable=False)
    shelve_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("shelve_info.id"), nullable=False)
    barcode : Mapped[str] = mapped_column(String, nullable = True)
    name : Mapped[str] = mapped_column(String, nullable = False)
    price : Mapped[int] = mapped_column(Integer, nullable = False)
    buy_from: Mapped[str] = mapped_column(String,nullable = True )
    created_date : Mapped[datetime] = mapped_column(DateTime, nullable = False, default = datetime.now)
    image : Mapped[str] = mapped_column(String, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0) # 1. 남은 재고 수량
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # 2. 강제 판매중단 스위치 (True/False)
    expiration_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True) # 3. 유통기한 (선택)



    shelve = relationship("Shelve", back_populates="products")
    category = relationship("Category", back_populates = "products")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
    

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