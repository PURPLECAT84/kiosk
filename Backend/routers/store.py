from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from database import get_db
from models.store import Store
from models.kiosk import Kiosk
from models.user import UserInfo, UserRole
from schemas.store import StoreCreate, StoreResponse, StoreUpdate
from core.dependency import require_roles
from typing import List
import uuid
import random
import string

router = APIRouter()
allowed_roles = [UserRole.DEV, UserRole.HEAD, UserRole.MASTER]

def generate_store_code(db: Session) -> str:
    """ST + 4자리 알파벳 대문자 및 숫자 조합의 고유코드 생성"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "ST" + "".join(random.choice(chars) for _ in range(4))
        # 중복 체크
        stmt = select(Store).where(Store.code == code)
        if not db.execute(stmt).scalars().first():
            return code

@router.post("/", response_model=StoreResponse, status_code=status.HTTP_201_CREATED, summary="매장 생성", description="신규매장 생성")
async def create_store(
    store: StoreCreate, 
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(allowed_roles))
):
    stmt = select(Store).where(Store.name == store.name)
    existing_store = db.execute(stmt).scalars().first()
    if existing_store:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 매장입니다")
    
    code = generate_store_code(db)
    owner_name = store.owner_name if store.owner_name else current_user.name
    
    db_store = Store(
        code=code,
        name=store.name,
        address=store.address,
        type=store.type,
        owner_name=owner_name,
        user_id=current_user.id,
        status="ACTIVE"
    )
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    
    # 생성된 매장도 kiosk_count는 0
    setattr(db_store, "kiosk_count", 0)
    return db_store


@router.get("/", response_model=List[StoreResponse], summary="매장 조회", description="전체 매장 리스트 조회 (키오스크 개수 포함)")
async def read_store(
    skip: int = 0, 
    limit: int = 100, 
    name: str | None = None, 
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(allowed_roles))
):
    # Outerjoin을 활용해 각 매장의 키오스크 개수를 집계합니다.
    stmt = (
        select(Store, func.count(Kiosk.id).label("kiosk_count"))
        .outerjoin(Kiosk, Store.id == Kiosk.store_id)
        .group_by(Store.id)
    )

    if name:
        stmt = stmt.where(Store.name.contains(name))

    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).all()

    response_data = []
    for store, kiosk_count in results:
        # Pydantic Response에서 읽어갈 수 있도록 kiosk_count 동적 설정
        setattr(store, "kiosk_count", kiosk_count)
        response_data.append(store)

    return response_data


@router.get("/{store_id}", response_model=StoreResponse, summary="매장 상세 조회")
async def get_store_detail(
    store_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(allowed_roles))
):
    # 단건 조회 시에도 키오스크 개수를 구합니다.
    stmt = (
        select(Store, func.count(Kiosk.id).label("kiosk_count"))
        .outerjoin(Kiosk, Store.id == Kiosk.store_id)
        .where(Store.id == store_id)
        .group_by(Store.id)
    )
    result = db.execute(stmt).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="매장을 찾을 수 없습니다")
    
    store, kiosk_count = result
    setattr(store, "kiosk_count", kiosk_count)
    return store


@router.patch("/{store_id}", response_model=StoreResponse, summary="매장정보 변경")
async def update_store(
    store_id: uuid.UUID,
    body: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(allowed_roles))
):
    stmt = select(Store).where(Store.id == store_id)
    store = db.execute(stmt).scalars().first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="매장을 찾을 수 없습니다")
    
    if body.type is not None:
        store.type = body.type
    if body.name is not None:
        store.name = body.name
    if body.address is not None:
        store.address = body.address
    if body.status is not None:
        store.status = body.status
    if body.owner_name is not None:
        store.owner_name = body.owner_name

    db.commit()
    db.refresh(store)

    # 수정 결과 리턴 시 kiosk_count 바인딩
    kiosk_stmt = select(func.count(Kiosk.id)).where(Kiosk.store_id == store.id)
    kiosk_count = db.execute(kiosk_stmt).scalar() or 0
    setattr(store, "kiosk_count", kiosk_count)

    return store


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT, summary="매장 삭제")
async def delete_store(
    store_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(allowed_roles))
):
    stmt = select(Store).where(Store.id == store_id)
    store = db.execute(stmt).scalars().first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="매장을 찾을 수 없습니다")
    
    db.delete(store)
    db.commit()
    return None