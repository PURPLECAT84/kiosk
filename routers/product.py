from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models import Store, User, Shelve, Category, Product
from schemas import ProductCreate, ProductResponse,ProductUpdate
from routers.users import get_current_user
from typing import List
import uuid

router = APIRouter(prefix = "/products", tags = ["products"])

AutherList = ["master" , "dev"]

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="상품등록")
async def upload_product(
    upload : ProductCreate,
    db : Session = Depends(get_db),
    uploader : User = Depends(get_current_user)
    
):
    # 1. 카테고리 확인 및 정보 역추적
    # 프론트엔드가 보낸 category_id 하나만으로, 카테고리를 찾습니다.
    target_category = db.get(Category, upload.category_id)
    if not target_category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

    # 2. 권한 확인 (카테고리가 알고 있는 store_id를 통해 매장 점주인지 확인)
    target_store = db.get(Store, target_category.store_id)
    if uploader.authority not in AutherList and uploader.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장에만 상품을 업로드 할 수 있습니다.")
    
    # 3. 중복 확인 (같은 매대 안에서 이름이 겹치는지 확인)
    # 🚨 작성하신 db.get(Product, upload.name)은 id(PK)로 찾을 때만 쓸 수 있습니다!
    # 이름과 매대ID 두 가지 조건으로 찾을 때는 db.scalar()를 씁니다.
    
    
    existing_product = db.scalar(select(Product).where(Product.name == upload.name,Product.shelve_id == target_category.shelve_id))
    
        
    if existing_product: 
        raise HTTPException(status_code=409, detail="해당 매대에 이미 같은 이름의 상품이 등록되어 있습니다.")
    
    # 4. 저장!
    # store_id와 shelve_id는 해커가 보낸 값이 아니라, 우리가 DB에서 찾은 안전한 target_category의 값을 넣습니다.
    new_product = Product(
        category_id=target_category.id,
        store_id=target_category.store_id,   # 안전한 역정규화 데이터
        shelve_id=target_category.shelve_id, # 안전한 역정규화 데이터
        barcode=upload.barcode,
        name=upload.name,
        price=upload.price,
        buy_from=upload.buy_from,
        image=upload.image
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get("/store/{store_id}", response_model= List[ProductResponse], summary="상품목록조회")
async def read_product_list(
    store_id : uuid.UUID,
    db: Session = Depends(get_db),
    current_user : User = Depends(get_current_user)):
    
    #매장찾기
    target_store = db.get(Store, store_id)
    if not target_store:
        raise HTTPException(status_code=404, detail="해당 매장을 찾을 수 없습니다")
    
    #권한체크

    if current_user.authority not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장 상품만 조회 할 수 있습니다.")

    products = db.scalars(select(Product).where(Product.store_id == store_id)).all()

    return products

