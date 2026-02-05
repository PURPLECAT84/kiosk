from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models import Store, User
from schemas import StoreCreate, StoreResponse, StoreUpdate
from routers.users import get_current_user
from typing import List
import uuid


router = APIRouter(prefix = "/stores", tags = ["stores"])
# prefix 설정: 이 파일의 모든 API는 앞에 /stores가 자동으로 붙음

@router.post("/", response_model = StoreResponse, status_code = status. HTTP_201_CREATED, summary = "매장 생성", description = "신규매장 생성")
async def create_store(store : StoreCreate, db : Session = Depends(get_db)
                       , current_user : User = Depends(get_current_user)):
    
    if current_user.authority not in ["master","dev"] :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "매장 생성 권한이 없습니다")

    stmt = select(Store).where(Store.name == store.name)
    exsisting_store = db.execute(stmt).scalars().first()

    if exsisting_store:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail = "이미 존재하는 매장입니다")

    db_store = Store(
        name = store.name,
        address = store.address,
        type = store.type, 
        user_id = store.user_id
    )

    db.add(db_store)
    db.commit()
    db.refresh(db_store)

    return db_store


@router.get("/", response_model = List[StoreResponse], summary = "매장 조회", description = " 전체 매장 리스트 조회")
async def read_store(skip: int = 0, limit : int = 10, 
                     name : str | None = None, current_user: User = Depends(get_db),
                     db : Session = Depends(get_db)):
    
    stmt = select(Store) #일단 "모든 매장을 가져와라"

    if name : 
      
        stmt = stmt.where(Store.name.contains(name)) #[검색 로직] 만약(if) 사용자가 검색어(name)를 보냈다면

    if current_user.authority in ["master", "dev"]:
        pass

    elif current_user.authority == "owner":
        stmt = stmt.where(Store.user_id == current_user.id)

    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= "매장조회 권한이 없습니다")



    stmt = stmt.offset(skip).limit(limit) #페이징(자르기) 적용

    stores = db.execute(stmt).scalars().all()#실행

    return stores