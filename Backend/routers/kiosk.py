from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models.kiosk import Kiosk
from models.store import Store
from models.user import UserInfo, UserRole
from schemas.kiosk import KioskCreate, KioskResponse, KioskUpdate
from core.dependency import require_roles
from typing import List
import uuid
import random
import string

router = APIRouter()

# 일반적인 키오스크 권한: DEV, HEAD, MASTER, MANAGER
general_roles = [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]
# 결제 정보 수정 권한: DEV, HEAD
billing_roles = [UserRole.DEV, UserRole.HEAD]

def generate_kiosk_code(db: Session) -> str:
    """KS + 6자리 알파벳 대문자 및 숫자 조합의 고유코드 생성"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "KS" + "".join(random.choice(chars) for _ in range(6))
        # 중복 체크
        stmt = select(Kiosk).where(Kiosk.code == code)
        if not db.execute(stmt).scalars().first():
            return code

@router.post("/", response_model=KioskResponse, status_code=status.HTTP_201_CREATED, summary="키오스크 생성")
async def create_kiosk(
    kiosk: KioskCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    # 매장 존재 여부 검증
    store_stmt = select(Store).where(Store.id == kiosk.store_id)
    store = db.execute(store_stmt).scalars().first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="매장을 찾을 수 없습니다")
    
    code = generate_kiosk_code(db)
    db_kiosk = Kiosk(
        code=code,
        store_id=kiosk.store_id,
        name=kiosk.name,
        model_name=kiosk.model_name,
        type=kiosk.type,
        status=kiosk.status,
        payment_status="NORMAL"
    )
    db.add(db_kiosk)
    db.commit()
    db.refresh(db_kiosk)
    
    setattr(db_kiosk, "store_name", store.name)
    return db_kiosk


@router.get("/", response_model=List[KioskResponse], summary="키오스크 조회")
async def read_kiosk(
    skip: int = 0,
    limit: int = 100,
    store_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk, Store.name).join(Store, Kiosk.store_id == Store.id)
    
    # MANAGER 권한인 경우 본인 매장의 키오스크만 조회되도록 필터링
    if current_user.role == UserRole.MANAGER:
        stmt = stmt.where(Store.user_id == current_user.id)
    elif store_id:
        stmt = stmt.where(Kiosk.store_id == store_id)
        
    stmt = stmt.offset(skip).limit(limit)
    results = db.execute(stmt).all()
    
    response_data = []
    for kiosk, store_name in results:
        setattr(kiosk, "store_name", store_name)
        response_data.append(kiosk)
        
    return response_data


@router.get("/{kiosk_id}", response_model=KioskResponse, summary="키오스크 상세 조회")
async def get_kiosk_detail(
    kiosk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk, Store.name).join(Store, Kiosk.store_id == Store.id).where(Kiosk.id == kiosk_id)
    result = db.execute(stmt).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다")
    
    kiosk, store_name = result
    
    # MANAGER 권한 검증: 본인 매장의 키오스크인지 체크
    if current_user.role == UserRole.MANAGER and kiosk.store.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 매장의 키오스크 정보만 열람할 수 있습니다")
        
    setattr(kiosk, "store_name", store_name)
    return kiosk


@router.patch("/{kiosk_id}", response_model=KioskResponse, summary="키오스크 정보 변경")
async def update_kiosk(
    kiosk_id: uuid.UUID,
    body: KioskUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk).where(Kiosk.id == kiosk_id)
    kiosk = db.execute(stmt).scalars().first()
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다")
        
    # MANAGER 권한 검증: 본인 매장의 키오스크인지 체크
    store_stmt = select(Store).where(Store.id == kiosk.store_id)
    store = db.execute(store_stmt).scalars().first()
    if current_user.role == UserRole.MANAGER and store.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 매장의 키오스크 정보만 수정할 수 있습니다")

    # 결제 정보 수정 권한 제한 검증
    if body.payment_status is not None or body.next_payment_date is not None:
        if current_user.role not in billing_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="결제 정보 변경 권한은 본사(HEAD) 또는 개발자(DEV) 권한만 가능합니다")

    if body.name is not None:
        kiosk.name = body.name
    if body.model_name is not None:
        kiosk.model_name = body.model_name
    if body.status is not None:
        kiosk.status = body.status
    if body.payment_status is not None:
        kiosk.payment_status = body.payment_status
    if body.next_payment_date is not None:
        kiosk.next_payment_date = body.next_payment_date
        
    db.commit()
    db.refresh(kiosk)
    
    # Response용 store_name 조회 및 바인딩
    setattr(kiosk, "store_name", store.name)
    
    return kiosk


@router.delete("/{kiosk_id}", status_code=status.HTTP_204_NO_CONTENT, summary="키오스크 삭제")
async def delete_kiosk(
    kiosk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(require_roles(general_roles))
):
    stmt = select(Kiosk).where(Kiosk.id == kiosk_id)
    kiosk = db.execute(stmt).scalars().first()
    if not kiosk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="키오스크를 찾을 수 없습니다")
        
    # MANAGER 권한 검증: 본인 매장의 키오스크인지 체크
    store_stmt = select(Store).where(Store.id == kiosk.store_id)
    store = db.execute(store_stmt).scalars().first()
    if current_user.role == UserRole.MANAGER and store.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인 매장의 키오스크만 삭제할 수 있습니다")
        
    db.delete(kiosk)
    db.commit()
    return None
