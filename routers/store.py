from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models.models import Store, User
from schemas.store import StoreCreate, StoreResponse, StoreUpdate
from routers.users import get_current_user
from typing import List
import uuid


router = APIRouter(prefix = "/stores", tags = ["stores"])
AutherList = ["master" , "dev"]
# prefix 설정: 이 파일의 모든 API는 앞에 /stores가 자동으로 붙음

@router.post("/", response_model = StoreResponse, status_code = status. HTTP_201_CREATED, summary = "매장 생성", description = "신규매장 생성")
async def create_store(store : StoreCreate, db : Session = Depends(get_db)
                       , current_user : User = Depends(get_current_user)):
    
    if current_user.authority not in AutherList :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "매장 생성 권한이 없습니다")

    stmt = select(Store).where(Store.name == store.name)
    exsisting_store = db.execute(stmt).scalars().first()

    if exsisting_store:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail = "이미 존재하는 매장입니다")

    authority_stmt = select(User).where(User.email == store.user_email) #회원가입한 회원 중 권한 부여할 이메일 검색
    target_user = db.execute(authority_stmt).scalars().first() #검색 실행하고 데이터 형식 벗겨서 제일 위(첫) 데이터 확인

    if not target_user: #만약 검색한 이메일이 아니면
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "해당 이메일을 찾을 수 없습니다")
    
    if target_user.authority == "manager" :   #만약 해당 회원이 매니저면 점주로 승급시켜
        target_user.authority ="owner"
        db.add(target_user)
    
    db_store = Store(
        name = store.name,
        address = store.address,
        type = store.type, 
        user_id = target_user.id #스키마가 아니라, target_user는 User 모델 객체이므로 '.id'를 가져와야 함. Store 테이블의 user_id 칸에 <--- User 객체의 id(PK)를 넣음
    )

    db.add(db_store)
    db.commit()
    db.refresh(db_store)

    return db_store


@router.get("/", response_model = List[StoreResponse], summary = "매장 조회", description = " 전체 매장 리스트 조회")
async def read_store(skip: int = 0, limit : int = 10, 
                     name : str | None = None, current_user: User = Depends(get_current_user),
                     db : Session = Depends(get_db)):
    
    stmt = select(Store) #일단 "모든 매장을 가져와라"

    if name : 
      
        stmt = stmt.where(Store.name.contains(name)) #[검색 로직] 만약(if) 사용자가 검색어(name)를 보냈다면

    if current_user.authority in AutherList: #제약 없음 (다 보여줌)
        pass

    elif current_user.authority == "owner":
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
    current_user: User = Depends(get_current_user)
    ):

    stmt = select(Store).where(Store.id == store_id) #검색은 models(실제 테이블)에서 찾아서 매칭
    store = db.execute(stmt).scalars().first()

    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "매장을 찾을 수 없습니다")
    
    if current_user.authority not in AutherList and store_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="본인의 매장만 수정할 수 있습니다")
    
    if body.type is not None : 
        if current_user.authority not in AutherList:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "매장 타입은 관리자만 수정할 수 있습니다")
        
        store.type = body.type

    if body.name:
        store.name = body.name
    
    if body.address:
        store.address = body.address

    db.commit()
    db.referesh()

    return store

@router.delete("/{store_id}", status_code = status.HTTP_204_NO_CONTENT, summary = "매장 삭제")
async def delete_store(
    store_id : uuid.UUID,
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    stmt = select(Store).where(Store.id == store_id)
    store = db.execute(stmt).scalars().first()

    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "매장을 찾을 수 없습니다")
    
    if current_user.authority not in AutherList and store.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="매장 삭제 권한이 없습니다")

    db.delete(store)
    db.commit()

    return None