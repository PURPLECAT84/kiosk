from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models.category import Category
from models.shelve import Shelve
from models.store import Store
from models.user import UserInfo, UserRole
from schemas.category import CategoryCreate, CategoryResponse,CategoryUpdate
from routers.user import get_current_user
from typing import List
import uuid

router = APIRouter()

AutherList = [UserRole.MASTER, UserRole.DEV]

# -----------------------------------------------------------
# 1. 카테고리 생성 (POST)
# -----------------------------------------------------------
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="카테고리 생성")
async def create_category(
    category: CategoryCreate, 
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 1. 입력받은 매대(Shelve) 찾기

    target_shelve = db.get(Shelve, category.shelve_id)
      
    if not target_shelve:
        raise HTTPException(status_code=404, detail="해당 매대를 찾을 수 없습니다.")

    # 2. 매대가 속한 매장(Store) 찾기 (권한 체크 및 store_id 저장을 위해) ***1개 조건 검색 단순화***

    
    target_store = db.get(Store, target_shelve.store_id)


    # 3. 권한 확인 (본인 매장의 매대인가?)
    if current_user.role not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장에만 카테고리를 생성할 수 있습니다.")

    # 4. 중복 확인 (해당 매대 안에서 이름 중복 방지) ***2개 조건 검색 단순화***
   
    existing_category = db.scalar(select(Category).where(Category.name == category.name, Category.shelve_id == category.shelve_id))

    if existing_category:
        raise HTTPException(status_code=409, detail="이 매대에 이미 존재하는 카테고리 이름입니다.")

    # 5. 🔥 [핵심] 생성 및 저장 (store_id를 함께 저장합니다!)
    db_category = Category(
        name=category.name,
        shelve_id=target_shelve.id,
        store_id=target_store.id # 여기서 한 번 넣어두면 평생 편해집니다!
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    return db_category


# -----------------------------------------------------------
# 2. 특정 매대의 카테고리 목록 조회 (GET)
# -----------------------------------------------------------
@router.get("/shelve/{shelve_id}", response_model=List[CategoryResponse], summary="특정 매대의 카테고리 조회")
async def read_categories_by_shelve(
    shelve_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 1. 매대 및 소속 매장 확인
    shelve_stmt = select(Shelve).where(Shelve.id == shelve_id)
    target_shelve = db.execute(shelve_stmt).scalars().first()
    
    if not target_shelve:
        raise HTTPException(status_code=404, detail="해당 매대를 찾을 수 없습니다.")

    store_stmt = select(Store).where(Store.id == target_shelve.store_id)
    target_store = db.execute(store_stmt).scalars().first()

    # 2. 권한 확인
    if current_user.role not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장의 카테고리만 조회할 수 있습니다.")

    # 3. 매대에 속한 카테고리 전체 조회
    cat_stmt = select(Category).where(Category.shelve_id == shelve_id)
    categories = db.execute(cat_stmt).scalars().all()

    return categories


# -----------------------------------------------------------
# 3. 카테고리 수정 (PATCH) - 🔥 store_id 역정규화의 위력!
# -----------------------------------------------------------
@router.patch("/{category_id}", response_model=CategoryResponse, summary="카테고리 수정")
async def update_category(
    category_id: int,
    body: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 1. 수정할 카테고리 바로 찾기
    cat_stmt = select(Category).where(Category.id == category_id)
    target_category = db.execute(cat_stmt).scalars().first()
    
    if not target_category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

    # 2. 매장 바로 찾기 (매대(Shelve)를 거칠 필요 없이 바로 store_id로 직행!)
    store_stmt = select(Store).where(Store.id == target_category.store_id)
    target_store = db.execute(store_stmt).scalars().first()

    # 3. 권한 체크
    if current_user.role not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장의 카테고리만 수정할 수 있습니다.")

    # 4. 중복 체크 (이름을 바꿀 경우, 같은 매대 안에 동일한 이름이 있는지 검사)
    if body.name is not None:
        dup_stmt = select(Category).where(
            Category.name == body.name, 
            Category.shelve_id == target_category.shelve_id,
            Category.id != category_id # 자기 자신은 제외
        )
        if db.execute(dup_stmt).scalars().first():
            raise HTTPException(status_code=409, detail="해당 매대에 동일한 카테고리 이름이 존재합니다.")
            
        target_category.name = body.name

    # 5. 저장
    db.commit()
    db.refresh(target_category)

    return target_category


# -----------------------------------------------------------
# 4. 카테고리 삭제 (DELETE) - 🔥 코드가 정말 짧아집니다!
# -----------------------------------------------------------
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="카테고리 삭제")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    # 1. 카테고리 찾기
    cat_stmt = select(Category).where(Category.id == category_id)
    target_category = db.execute(cat_stmt).scalars().first()
    
    if not target_category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

    # 2. 매장 바로 찾기 및 권한 체크
    store_stmt = select(Store).where(Store.id == target_category.store_id)
    target_store = db.execute(store_stmt).scalars().first()

    if current_user.role not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장의 카테고리만 삭제할 수 있습니다.")

    # 3. 삭제
    db.delete(target_category)
    db.commit()

    return None


# -----------------------------------------------------------
# 5. 매장의 모든 카테고리 조회 (GET) - 프론트엔드 용
# -----------------------------------------------------------
@router.get("/store/{store_id}", response_model=List[CategoryResponse], summary="특정 매장의 모든 카테고리 조회")
async def read_categories_by_store(
    store_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    target_store = db.get(Store, store_id)
    if not target_store:
        raise HTTPException(status_code=404, detail="해당 매장을 찾을 수 없습니다.")
        
    if current_user.role not in AutherList and current_user.id != target_store.user_id:
        raise HTTPException(status_code=403, detail="본인 매장의 카테고리만 조회할 수 있습니다.")

    cat_stmt = select(Category).where(Category.store_id == store_id)
    categories = db.execute(cat_stmt).scalars().all()
    return categories