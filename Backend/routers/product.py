from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header
import shutil
import os
import re
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session
from database import get_db
from models.store import Store
from models.user import UserInfo, UserRole
from models.category import Category
from models.product import Product
from schemas.product import ProductCreate, ProductResponse, ProductUpdate, ProductStatusUpdate
from core.dependency import require_roles, get_current_user
from typing import List, Optional
import uuid

router = APIRouter()
allowed_roles = [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, summary="상품등록")
async def upload_product(
    upload: ProductCreate,
    db: Session = Depends(get_db),
    uploader: UserInfo = Depends(get_current_user)
):
    target_category = db.get(Category, upload.category_id)
    if not target_category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

    target_store = db.get(Store, target_category.store_id)
    if uploader.role not in [UserRole.MASTER, UserRole.DEV] and uploader.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장에만 상품을 업로드 할 수 있습니다.")
    
    # 중복 확인
    existing_product = db.scalar(
        select(Product).where(
            Product.name == upload.name, 
            Product.store_id == target_category.store_id
        )
    )
    if existing_product: 
        raise HTTPException(status_code=409, detail="매장에 이미 같은 이름의 상품이 등록되어 있습니다.")
    
    # sequence 자동 생성 (가장 마지막 순서로 배치)
    seq = upload.sequence
    if seq == 0:
        max_seq = db.scalar(select(func.max(Product.sequence)).where(Product.store_id == target_category.store_id))
        seq = (max_seq or 0) + 1

    new_product = Product(
        category_id=target_category.id,
        store_id=target_category.store_id,
        shelve_id=target_category.shelve_id,
        kiosk_id=upload.kiosk_id,
        barcode=upload.barcode,
        name=upload.name,
        price=upload.price,
        buy_from=upload.buy_from,
        image=upload.image,
        stock=upload.stock,
        stock_managed=upload.stock_managed,
        sequence=seq,
        is_active=True
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get("/store/{store_id}", response_model=List[ProductResponse], summary="상품목록조회")
async def read_product_list(
    store_id: uuid.UUID,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    target_store = db.get(Store, store_id)
    if not target_store:
        raise HTTPException(status_code=404, detail="해당 매장을 찾을 수 없습니다")
    
    if current_user.role not in [UserRole.MASTER, UserRole.DEV] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장 상품만 조회 할 수 있습니다.")

    stmt = select(Product).where(Product.store_id == store_id)

    # X-Kiosk-Id 헤더 필터 추가
    if x_kiosk_id:
        stmt = stmt.where(Product.kiosk_id == x_kiosk_id)

    # 검색 필터 지원
    if name:
        stmt = stmt.where(Product.name.contains(name))
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)

    # 노출 순서 sequence 오름차순 정렬
    stmt = stmt.order_by(Product.sequence.asc())
    
    products = db.scalars(stmt).all()
    return products


@router.patch("/store/{store_id}/product/{product_id}", response_model=ProductResponse, summary="상품정보수정")
async def update_product(
    store_id: uuid.UUID,
    product_id: uuid.UUID,
    update_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    target_store = db.get(Store, store_id)
    if not target_store:
        raise HTTPException(status_code=404, detail="해당 매장을 찾을 수 없습니다.")
    
    target_product = db.get(Product, product_id)
    if not target_product or target_product.store_id != store_id:
        raise HTTPException(status_code=404, detail="해당 상품을 찾을 수 없습니다.")
    
    if current_user.role not in [UserRole.MASTER, UserRole.DEV] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장 상품만 수정할 수 있습니다.")

    if update_data.name is not None and update_data.name != target_product.name:
        dup_stmt = select(Product).where(
            Product.name == update_data.name, 
            Product.store_id == store_id,
            Product.id != product_id
        )
        existing_product = db.scalar(dup_stmt)
        if existing_product:
            raise HTTPException(status_code=409, detail="이미 매장에 같은 이름의 상품이 등록되어 있습니다.")
        target_product.name = update_data.name

    # 필드 업데이트
    if update_data.category_id is not None:
        cat = db.get(Category, update_data.category_id)
        if cat:
            target_product.category_id = cat.id
            target_product.shelve_id = cat.shelve_id
    if update_data.barcode is not None:
        target_product.barcode = update_data.barcode
    if update_data.price is not None:
        target_product.price = update_data.price
    if update_data.buy_from is not None:
        target_product.buy_from = update_data.buy_from
    if update_data.image is not None:
        target_product.image = update_data.image
    if update_data.stock is not None:
        target_product.stock = update_data.stock
    if update_data.stock_managed is not None:
        target_product.stock_managed = update_data.stock_managed
    if update_data.sequence is not None:
        target_product.sequence = update_data.sequence
    if update_data.is_active is not None:
        target_product.is_active = update_data.is_active
    if update_data.kiosk_id is not None:
        target_product.kiosk_id = update_data.kiosk_id

    db.commit()
    db.refresh(target_product)
    
    return target_product 


@router.delete("/store/{store_id}/product/{product_id}", status_code=status.HTTP_204_NO_CONTENT, summary="상품삭제")
async def delete_product(   
    store_id: uuid.UUID,
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    target_store = db.get(Store, store_id)
    if not target_store:
        raise HTTPException(status_code=404, detail="해당 매장을 찾을 수 없습니다.")
    
    target_product = db.get(Product, product_id)
    if not target_product or target_product.store_id != store_id:
        raise HTTPException(status_code=404, detail="해당 상품을 찾을 수 없습니다.")
    
    if current_user.role not in [UserRole.MASTER, UserRole.DEV] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장 상품만 삭제할 수 있습니다.")

    db.delete(target_product)
    db.commit() 


"""===================== 상품 복사하기 (넘버링 적용) ============================"""
@router.post("/{product_id}/copy", response_model=ProductResponse, summary="상품 복사 (넘버링)")
async def copy_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="복사할 상품을 찾을 수 없습니다.")
        
    target_store = db.get(Store, product.store_id)
    if current_user.role not in [UserRole.MASTER, UserRole.DEV] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장의 상품만 복사할 수 있습니다.")

    # 복사 번호 넘버링 (e.g. 짜장면 -> 짜장면(복사1) -> 짜장면(복사2))
    base_name = re.sub(r"\s*\(복사\d+\)$", "", product.name).strip()
    n = 1
    while True:
        candidate_name = f"{base_name}(복사{n})"
        dup_stmt = select(Product).where(Product.store_id == product.store_id, Product.name == candidate_name)
        if not db.execute(dup_stmt).scalars().first():
            new_name = candidate_name
            break
        n += 1

    # sequence 설정 (마지막 순서로 배치)
    max_seq = db.scalar(select(func.max(Product.sequence)).where(Product.store_id == product.store_id)) or 0

    copied_product = Product(
        category_id=product.category_id,
        store_id=product.store_id,
        shelve_id=product.shelve_id,
        kiosk_id=product.kiosk_id,
        barcode=product.barcode,
        name=new_name,
        price=product.price,
        buy_from=product.buy_from,
        image=product.image,
        stock=product.stock,
        stock_managed=product.stock_managed,
        sequence=max_seq + 1,
        is_active=product.is_active
    )

    db.add(copied_product)
    db.commit()
    db.refresh(copied_product)
    return copied_product


"""===================== 상품 노출 순서 이동 (UP/DOWN 스왑) ============================"""
@router.post("/{product_id}/move", response_model=ProductResponse, summary="상품 노출 순서 이동 (up/down)")
async def move_product_sequence(
    product_id: uuid.UUID,
    direction: str, # 'up' or 'down'
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    target_store = db.get(Store, product.store_id)
    if current_user.role not in [UserRole.MASTER, UserRole.DEV] and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장 상품의 순서만 조정할 수 있습니다.")

    # Swap할 인접 상품을 찾습니다.
    if direction == "up":
        # 현재 상품보다 작은 sequence 중 가장 큰 값
        swap_stmt = (
            select(Product)
            .where(Product.store_id == product.store_id, Product.sequence < product.sequence)
            .order_by(desc(Product.sequence))
        )
    elif direction == "down":
        # 현재 상품보다 큰 sequence 중 가장 작은 값
        swap_stmt = (
            select(Product)
            .where(Product.store_id == product.store_id, Product.sequence > product.sequence)
            .order_by(Product.sequence.asc())
        )
    else:
        raise HTTPException(status_code=400, detail="올바르지 않은 방향 지시입니다 (up 또는 down만 가능)")

    adjacent_product = db.execute(swap_stmt).scalars().first()
    if adjacent_product:
        # sequence 값 서로 교환(Swap)
        temp_seq = product.sequence
        product.sequence = adjacent_product.sequence
        adjacent_product.sequence = temp_seq
        db.commit()
        db.refresh(product)

    return product


"""===================== 상품 재고/상태 빠른 변경 (리모컨) ============================"""
@router.patch("/{product_id}/status", summary="재고 및 판매상태 변경")
async def update_product_status(
    product_id: uuid.UUID,
    body: ProductStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value) 

    db.commit()
    db.refresh(product)
    
    return {    
        "message": f"[{product.name}] 상태가 업데이트 되었습니다.", 
        "current_stock": product.stock, 
        "is_active": product.is_active,
        "stock_managed": product.stock_managed
    }


from schemas.product import BulkStatusUpdate, BulkDelete

@router.post("/bulk-status", summary="상품 일괄 활성/비활성 상태 변경")
async def bulk_update_status(
    body: BulkStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if not body.product_ids:
        return {"message": "업데이트할 상품이 지정되지 않았습니다."}
    
    stmt = select(Product).where(Product.id.in_(body.product_ids))
    products = db.execute(stmt).scalars().all()
    
    for p in products:
        target_store = db.get(Store, p.store_id)
        if current_user.role not in [UserRole.MASTER, UserRole.DEV] and target_store.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="본인 매장의 상품만 일괄 수정할 수 있습니다.")
        p.is_active = body.is_active
        
    db.commit()
    return {"message": f"성공적으로 {len(products)}개 상품의 상태를 변경했습니다.", "is_active": body.is_active}


@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT, summary="상품 일괄 삭제")
async def bulk_delete_products(
    body: BulkDelete,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if not body.product_ids:
        return
        
    stmt = select(Product).where(Product.id.in_(body.product_ids))
    products = db.execute(stmt).scalars().all()
    
    for p in products:
        target_store = db.get(Store, p.store_id)
        if current_user.role not in [UserRole.MASTER, UserRole.DEV] and target_store.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="본인 매장의 상품만 일괄 삭제할 수 있습니다.")
        db.delete(p)
        
    db.commit()
    return None


import httpx
import mimetypes

@router.post("/image", summary="상품 이미지 단일 업로드 (Supabase Storage)")
async def upload_product_image(
    file: UploadFile = File(...),
    current_user: UserInfo = Depends(get_current_user)
):
    if file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="이미지 파일 크기는 2MB 이하여야 합니다.")
        
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'png'
    if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
        
    # Content-Type 감지
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type:
        mime_type = "image/png" if ext == "png" else "image/jpeg"

    # Supabase 환경 변수 로드
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase 설정 정보를 찾을 수 없습니다.")

    # 파일명 고유화
    filename = f"{uuid.uuid4()}.{ext}"
    
    # Supabase Storage 업로드 REST API 호출
    upload_url = f"{supabase_url}/storage/v1/object/products/{filename}"
    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": mime_type,
        "x-upsert": "true"
    }
    
    file_content = await file.read()
    
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(upload_url, content=file_content, headers=headers)
            if res.status_code != 200:
                # 버킷 생성 에러 등으로 인해 업로드가 실패한 경우, 로컬 static 폴더로 폴백 제공 (무중단 UX 보장)
                os.makedirs("static/images", exist_ok=True)
                file_path = f"static/images/{filename}"
                with open(file_path, "wb") as buffer:
                    buffer.write(file_content)
                return {"image_url": f"/static/images/{filename}"}
                
        # 성공 시 Supabase Public URL 반환
        public_url = f"{supabase_url}/storage/v1/object/public/products/{filename}"
        return {"image_url": public_url}
        
    except Exception as e:
        # 에러 발생 시 로컬 static 폴더로 폴백 제공 (오프라인/로컬 테스트 UX 보장)
        os.makedirs("static/images", exist_ok=True)
        file_path = f"static/images/{filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        return {"image_url": f"/static/images/{filename}"}