from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models.store import Store
from models.user import UserInfo, UserRole
from schemas.store import StoreCreate, StoreResponse, StoreUpdate
from routers.user import get_current_user
from typing import List
import uuid


router = APIRouter()
AutherList = [UserRole.MASTER, UserRole.DEV]
# prefix 설정: 이 파일의 모든 API는 앞에 /stores가 자동으로 붙음

@router.post("/", response_model = StoreResponse, status_code = status. HTTP_201_CREATED, summary = "매장 생성", description = "신규매장 생성")
async def create_store(store : StoreCreate, db : Session = Depends(get_db)
                       , current_user : UserInfo = Depends(get_current_user)):
    # 누구나 매장을 만들고자 할 때 권한 체크를 해제하거나 변경합니다.
    # if current_user.role not in AutherList :
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "매장 생성 권한이 없습니다")

    stmt = select(Store).where(Store.name == store.name)
    exsisting_store = db.execute(stmt).scalars().first()

    if exsisting_store:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail = "이미 존재하는 매장입니다")
    
    if current_user.role == UserRole.STAFF :   #만약 해당 회원이 매니저가 아니면 점주(MANAGER)로 승급시켜
        current_user.role = UserRole.MANAGER
        db.add(current_user)
    
    db_store = Store(
        name = store.name,
        address = store.address,
        type = store.type, 
        user_id = current_user.id
    )

    db.add(db_store)
    db.commit()
    db.refresh(db_store)

    return db_store


@router.get("/", response_model = List[StoreResponse], summary = "매장 조회", description = " 전체 매장 리스트 조회")
async def read_store(skip: int = 0, limit : int = 10, 
                     name : str | None = None, current_user: UserInfo = Depends(get_current_user),
                     db : Session = Depends(get_db)):
    
    stmt = select(Store) #일단 "모든 매장을 가져와라"

    if name : 
      
        stmt = stmt.where(Store.name.contains(name)) #[검색 로직] 만약(if) 사용자가 검색어(name)를 보냈다면

    if current_user.role in AutherList: #제약 없음 (다 보여줌)
        pass

    elif current_user.role == UserRole.MANAGER or current_user.role == UserRole.STAFF:
        stmt = stmt.where(Store.user_id == current_user.id)

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "매장조회 권한이 없습니다")



    stmt = stmt.offset(skip).limit(limit) #페이징(자르기) 적용

    stores = db.execute(stmt).scalars().all()#실행

    return stores

@router.patch("/{store_id}", response_model= StoreResponse, summary = "매장정보 변경")
async def update_store(
    store_id : uuid.UUID,
    body : StoreUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
    ):

    stmt = select(Store).where(Store.id == store_id) #검색은 models(실제 테이블)에서 찾아서 매칭
    store = db.execute(stmt).scalars().first()

    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "매장을 찾을 수 없습니다")
    
    if current_user.role not in AutherList and store_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인의 매장만 수정할 수 있습니다")
    
    if body.type is not None : 
        if current_user.role not in AutherList:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "매장 타입은 관리자만 수정할 수 있습니다")
        
        store.type = body.type

    if body.name:
        store.name = body.name
    
    if body.address:
        store.address = body.address

    db.commit()
    db.refresh(store)

    return store

@router.delete("/{store_id}", status_code = status.HTTP_204_NO_CONTENT, summary = "매장 삭제")
async def delete_store(
    store_id : uuid.UUID,
    db : Session = Depends(get_db),
    current_user : UserInfo = Depends(get_current_user)
):
    stmt = select(Store).where(Store.id == store_id)
    store = db.execute(stmt).scalars().first()

    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "매장을 찾을 수 없습니다")
    
    if current_user.role not in AutherList and store.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="매장 삭제 권한이 없습니다")

    db.delete(store)
    db.commit()

    return None