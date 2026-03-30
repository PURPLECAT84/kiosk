from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import shutil
import os
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models.store import Store
from models.user import User
from models.category import Category
from models.product import Product
from schemas.product import ProductCreate, ProductResponse,ProductUpdate
from routers.user import get_current_user
from typing import List
import uuid


from schemas.product import ProductStatusUpdate
from core.dependency import get_current_user

router = APIRouter()

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

@router.patch("/store/{store_id}/product/{product_id}", response_model=ProductResponse, summary="상품정보수정")
async def update_product(
    store_id : uuid.UUID,
    product_id : uuid.UUID, # ✅ URL 변수명과 일치시킴
    update_data : ProductUpdate,
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    # 1. 매장 확인
    target_store = db.get(Store, store_id)
    if not target_store:
        raise HTTPException(status_code=404, detail="해당 매장을 찾을 수 없습니다.")
    
    # 2. 상품 확인 및 소속 검증 (완벽한 방어 로직! 🛡️)
    target_product = db.get(Product, product_id)
    if not target_product or target_product.store_id != store_id:
        raise HTTPException(status_code=404, detail="해당 상품을 찾을 수 없습니다.")
    
    # 3. 권한 확인
    if current_user.authority not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장 상품만 수정할 수 있습니다.")

    # 4. 이름 업데이트 시 중복 검사 (최적화 💡)
    if update_data.name is not None:
        # 이름이 들어왔을 때만 같은 매대 안에서 중복되는지 확인 (자기 자신은 제외)
        dup_stmt = select(Product).where(
            Product.name == update_data.name, 
            Product.shelve_id == target_product.shelve_id, 
            Product.id != product_id
        )
        existing_product = db.scalar(dup_stmt)

        if existing_product:
            raise HTTPException(status_code=409, detail="해당 매대에 이미 같은 이름의 상품이 등록되어 있습니다.")
        
        target_product.name = update_data.name

    # 5. 나머지 필드 업데이트
    if update_data.price is not None:
        target_product.price = update_data.price
    if update_data.buy_from is not None:
        target_product.buy_from = update_data.buy_from
    if update_data.image is not None:
        target_product.image = update_data.image
        
    # (선택 꿀팁) 만약 필드가 10개가 넘어가면 이전에 알려드렸던 아래 3줄로 퉁칠 수 있습니다!
    # update_dict = update_data.model_dump(exclude_unset=True)
    # for key, value in update_dict.items():
    #     setattr(target_product, key, value)

    db.commit()
    db.refresh(target_product)
    
    return target_product 


@router.delete("/store/{store_id}/product/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="상품삭제")
async def delete_product(   
    store_id : uuid.UUID,
    product_id : uuid.UUID, # ✅ URL 변수명과 일치시킴
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    # 1. 매장 확인
    target_store = db.get(Store, store_id)
    if not target_store:
        raise HTTPException(status_code=404, detail="해당 매장을 찾을 수 없습니다.")
    
    # 2. 상품 확인 및 소속 검증 (완벽한 방어 로직! 🛡️)
    target_product = db.get(Product, product_id)
    if not target_product or target_product.store_id != store_id:
        raise HTTPException(status_code=404, detail="해당 상품을 찾을 수 없습니다.")
    
    # 3. 권한 확인
    if current_user.authority not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장 상품만 삭제할 수 있습니다.")

    # 4. 삭제
    db.delete(target_product)
    db.commit() 



"""===================== 상품 재고/상태 빠른 변경 (리모컨) ============================"""
@router.patch("/{product_id}/status", summary="재고 및 판매상태 변경")
async def update_product_status(
    product_id: uuid.UUID,
    body: ProductStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 🔥 핵심: 사용자가 스웨거에서 '명시적으로 입력한(보낸)' 값만 딕셔너리로 뽑아냅니다.
    # (입력 안 한 건 아예 키(key) 자체가 안 나옵니다!)
    update_data = body.model_dump(exclude_unset=True)

    # 파이썬의 getattr, setattr을 쓰면 코드가 엄청나게 짧고 우아해집니다!
    for key, value in update_data.items():
        setattr(product, key, value) 
        # 설명: product.stock = 10, product.expiration_date = None 처럼 알아서 쏙쏙 들어갑니다.

    db.commit()
    db.refresh(product)
    
    return {    
        "message": f"[{product.name}] 상태가 업데이트 되었습니다.", 
        "current_stock": product.stock, 
        "is_active": product.is_active,
        "expiration_date": product.expiration_date
    }


@router.post("/image", summary="상품 이미지 단일 업로드")
async def upload_product_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="이미지 파일 크기는 2MB 이하여야 합니다.")
        
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
        
    os.makedirs("static/images", exist_ok=True)
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"static/images/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"image_url": f"/static/images/{filename}"}